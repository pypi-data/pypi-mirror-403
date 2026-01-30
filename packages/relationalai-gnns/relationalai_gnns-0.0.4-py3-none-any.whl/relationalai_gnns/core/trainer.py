from typing import Optional

from relationalai_gnns.common.exceptions import ValidationError
from relationalai_gnns.common.export import OutputConfig
from relationalai_gnns.common.job_models import JobTypes, ModelSelectionStrategy, PayloadTypes

from .api_request_handler import APIRequestHandler
from .config_trainer import TrainerConfig
from .connector import BaseConnector, LocalConnector, SnowflakeConnectorDirectAccess
from .dataset import Dataset
from .job_manager import JobMonitor
from .utils import extract_all_table_paths


class Trainer:
    def __init__(self, connector: BaseConnector, config: TrainerConfig):
        """
        Trainer class for the GNN-RLE.

        Initializes and manages the training process for a GNN model.

        :param connector: Connector object used to interact with the data source.
        :type connector: Connector
        :param config: Configuration object containing all training hyperparameters.
        :type config: TrainerConfig
        """

        self.connector = connector
        self.api_handler = APIRequestHandler(connector)
        self.config = config.to_dict()

    def _add_inference_export_config(self, **model_params):
        """Get dataset metadata from MLflow artifacts."""

        payload = {
            "payload_type": PayloadTypes.ADD_INFERENCE_EXPORT,
            "config": self.config,
            **{k: v for k, v in model_params.items() if v is not None},
        }
        return self.api_handler.make_request(payload)

    def _submit_job(self, dataset_metadata: dict, job_type: JobTypes) -> JobMonitor:
        """
        Helper method to submit a job request to the remote training system.

        Args:
            dataset_metadata (dict): The dataset metadata for training/inference.
            job_type (JobTypes): The type of job - "train", "inference", or "both".

        Returns:
            JobMonitor: An object representing the submitted job.
        """
        payload = {
            "payload_type": PayloadTypes.JOB,
            "dataset_metadata": dataset_metadata,
            "model_configuration": self.config,
            "job_type": job_type,
        }
        tables = extract_all_table_paths(dataset_metadata)
        job_data = self.api_handler.make_request(payload, tables)

        if self.connector.is_native_app:
            payload_logs = {
                "payload_type": PayloadTypes.SEND_LOGS,
                "job_id": job_data["job_id"],
                "stream_name": "progress",
            }

            _ = self.api_handler.make_request(payload_logs)

        if job_data:
            job_monitor = JobMonitor(connector=self.connector, job_id=job_data["job_id"], job_type=job_type)
            return job_monitor

    def _get_dataset_metadata(self, experiment_name, **params):
        """Get dataset metadata from MLflow artifacts."""
        payload = {
            "payload_type": PayloadTypes.REQUEST_DATASET_CONFIG,
            "experiment_name": experiment_name,
            **{k: v for k, v in params.items() if v is not None},
        }
        return self.api_handler.make_request(payload)

    def fit(self, dataset: Dataset) -> JobMonitor:
        """
        Submit a training job.

        :param dataset: The dataset to be used for training.
        :type dataset: Dataset
        :returns: An object to monitor the submitted job, check its status, track model progress, and retrieve metrics
            after training.
        :rtype: JobMonitor
        """
        return self._submit_job(dataset_metadata=dataset.metadata_dict, job_type=JobTypes.TRAIN)

    def predict(
        self,
        output_alias: str,
        output_config: OutputConfig = None,
        test_batch_size: int = 128,
        experiment_name: Optional[str] = None,
        dataset: Optional[Dataset] = None,
        test_table: Optional[str] = None,
        model_run_id: Optional[str] = None,
        registered_model_key: Optional[str] = None,
        extract_embeddings: bool = False,
        materialize_results: bool = True,
        flatten_output: bool = False,
    ) -> JobMonitor:
        """
        Submits an inference job.

        Either a dataset or an experiment name must be provided. If `experiment_name`
        and  `model_run_id` is specified, the dataset
        used in that experiment will be reused, avoiding the need to redefine it.

        If materialize_results is True, the method waits for the job to complete and creates permanent tables.
        This causes the method to run synchronously (blocking) rather than executing in the background.

        Inference logic:

        1. One of `dataset` or (`experiment_name` and `model_run_id`) must be provided.
        - If `experiment_name` and `model_run_id` is provided, the dataset used in that experiment will be reused.

        2. A model must be selected using one of the following options:
        a. `registered_model_key`: Use a specific registered model.
        b. `model_run_id`: Use a specific model run ID.

        3. The `test_table` argument is only valid when `experiment_name` is provided.

        :param output_config: Configuration specifying where to save results.
                            Use `OutputConfig.local()` or `OutputConfig.snowflake()`.
        :type output_config: OutputConfig

        :param output_alias: An alias to append to the result tables of predictions and embeddings.
        :type output_alias: str

        :param test_batch_size: Test batch size to use during inference. Defaults to 128.
        :type test_batch_size: int, optional

        :param experiment_name: Name of the experiment to run inference for.
        :type experiment_name: str, optional

        :param dataset: Dataset to run inference on. Required if `experiment_name` is not provided.
        :type dataset: Dataset, optional

        :param test_table: Fully qualified test table path. Required only when using `experiment_name`.
        :type test_table: str, optional

        :param registered_model_key: Fully qualified model key in the format 'database.schema.model.version'..
        :type registered_model_key: str, optional

        :param model_run_id: Run inference using this specific model run ID.
        :type model_run_id: str, optional

        :param extract_embeddings: If True, extract node embeddings.
        :type extract_embeddings: bool, optional

        :param materialize_results: If True, wait for job completion and create permanent tables.
            This makes the method run synchronously (blocking) instead of in the background.
        :type materialize_results: bool

        :param flatten_output: If True - Flatten the inference output
        (used in Multi-label Node Classification and Link Prediction).
        Drop ground truth column (if present) for all tasks.
        :type flatten_output: bool

        :returns: An object representing the submitted job, which can be used to monitor job status, retrieve metrics,
                and track progress.
        :rtype: JobMonitor
        """

        # Step 1: Validate input requirements
        if not model_run_id and not registered_model_key:
            raise ValidationError("Either `model_run_id` or `registered_model_key` must be provided.")

        if model_run_id and registered_model_key:
            raise ValidationError("Specify only one of `model_run_id` or `registered_model_key`, not both.")

        if not dataset and not experiment_name:
            raise ValidationError("Either `dataset` or `experiment_name` must be provided.")

        model_selection_strategy = (
            ModelSelectionStrategy.REGISTERED if registered_model_key else ModelSelectionStrategy.CUSTOM_RUN
        )

        # Step 2: Obtain dataset metadata
        # - If dataset object is provided, use its metadata directly
        # - Otherwise, retrieve metadata
        if not dataset:
            if not test_table:
                raise ValidationError("Test table is mandatory when using an experiment name.")

            metadata_dict = self._get_dataset_metadata(
                experiment_name=experiment_name,
                model_run_id=model_run_id,
                registered_model_key=registered_model_key,
                model_selection_strategy=model_selection_strategy,
            )
            if not metadata_dict:
                return None
        else:
            metadata_dict = dataset.metadata_dict

        if not metadata_dict:
            return None

        # Step 3: Configure inference and export parameters
        # Configure inference and export parameters
        if output_config.type == "snowflake":
            snowflake_settings = output_config.settings
            self.config = self._add_inference_export_config(
                test_batch_size=test_batch_size,
                model_selection_strategy=model_selection_strategy,
                model_run_id=model_run_id,
                registered_model_key=registered_model_key,
                extract_embeddings=extract_embeddings,
                output_alias=output_alias,
                database_name=snowflake_settings.database_name,
                schema_name=snowflake_settings.schema_name,
                flatten_output=flatten_output,
            )
            if (
                materialize_results
                and self.connector.connector_type == "snowflake"
                and not isinstance(self.connector, LocalConnector)
                and not isinstance(self.connector, SnowflakeConnectorDirectAccess)
            ):
                self._check_write_permissions(snowflake_settings.database_name, snowflake_settings.schema_name)

        elif output_config.type == "local":
            local_settings = output_config.settings
            self.config = self._add_inference_export_config(
                test_batch_size=test_batch_size,
                model_selection_strategy=model_selection_strategy,
                model_run_id=model_run_id,
                registered_model_key=registered_model_key,
                extract_embeddings=extract_embeddings,
                output_alias=output_alias,
                artifacts_dir=local_settings.artifacts_dir,
                extension=local_settings.extension,
                flatten_output=flatten_output,
            )
        if not self.config:
            return None

        if test_table is not None and experiment_name is not None:
            metadata_dict["task"]["source"]["test"] = test_table

        if not metadata_dict.get("task", {}).get("source", {}).get("test"):
            raise ValidationError("Dataset metadata is missing a test table.")

        # Step 4: Submit the inference job and return a monitor to track progress
        job = self._submit_job(dataset_metadata=metadata_dict, job_type=JobTypes.INFERENCE)
        if materialize_results and self.connector.is_native_app:
            job.materialize_results()
        return job

    def fit_predict(
        self,
        dataset: Dataset,
        output_alias: str,
        output_config: OutputConfig = None,
        test_batch_size: int = 128,
        extract_embeddings: bool = False,
        materialize_results: bool = True,
        flatten_output: bool = False,
    ) -> JobMonitor:
        """
        Submits a job that performs both training and inference.

        This function trains a GNN model using the provided dataset and then runs inference on the test data. The
        dataset must include a test table.

        If materialize_results is True, the method waits for the job to complete and creates permanent tables. This
        causes the method to run synchronously (blocking) rather than executing in the background.

        :param dataset: The dataset to be used for training and inference. Must include a test table.
        :type dataset: Dataset
        :param output_config: Configuration specifying where to save results. Use `OutputConfig.local()` or
            `OutputConfig.snowflake()`.
        :type output_config: OutputConfig
        :param output_alias: An alias to append to the result tables for predictions and embeddings.
        :type output_alias: str
        :param test_batch_size: Test batch size to use during inference. Defaults to 128.
        :type test_batch_size: int, optional
        :param extract_embeddings: Set to True to extract node embeddings.
        :type extract_embeddings: bool
        :param materialize_results: If True, wait for job completion and create permanent tables. This makes the method
            run synchronously (blocking) instead of in the background.
        :type materialize_results: bool
        :param flatten_output: If True - Flatten the inference output
        (used in Multi-label Node Classification and Link Prediction).
            Drop ground truth column (if present) for all tasks.
        :type flatten_output: bool
        :returns: An object representing the submitted job. This object can be used to check job status, retrieve
            training metrics, and monitor progress.
        :rtype: JobMonitor :example: # Snowflake output trainer.fit_predict( dataset=dataset,
            output_config=OutputConfig.snowflake( database_name="SYNTHETIC_ACADEMIC_RANKING_DB", schema_name="PUBLIC" ),
            output_alias="my_predictions" )
        """

        test_table = dataset.metadata_dict.get("task", {}).get("source", {}).get("test")
        if not test_table:
            raise ValidationError("Dataset metadata is missing a test table.")

        # Configure inference and export parameters
        if output_config.type == "snowflake":
            snowflake_settings = output_config.settings
            self.config = self._add_inference_export_config(
                test_batch_size=test_batch_size,
                model_selection_strategy="current",
                model_run_id=None,
                registered_model_key=None,
                extract_embeddings=extract_embeddings,
                output_alias=output_alias,
                database_name=snowflake_settings.database_name,
                schema_name=snowflake_settings.schema_name,
                flatten_output=flatten_output,
            )
            if (
                materialize_results
                and self.connector.connector_type == "snowflake"
                and not isinstance(self.connector, LocalConnector)
                and not isinstance(self.connector, SnowflakeConnectorDirectAccess)
            ):
                self._check_write_permissions(snowflake_settings.database_name, snowflake_settings.schema_name)

        elif output_config.type == "local":
            local_settings = output_config.settings
            self.config = self._add_inference_export_config(
                test_batch_size=test_batch_size,
                model_selection_strategy="current",
                model_run_id=None,
                registered_model_key=None,
                extract_embeddings=extract_embeddings,
                output_alias=output_alias,
                artifacts_dir=local_settings.artifacts_dir,
                extension=local_settings.extension,
                flatten_output=flatten_output,
            )
        if not self.config:
            return None

        job = self._submit_job(dataset_metadata=dataset.metadata_dict, job_type=JobTypes.TRAIN_INFERENCE)
        if materialize_results and self.connector.is_native_app:
            job.materialize_results()
        return job

    def _check_write_permissions(self, database_name: str, schema_name: str) -> None:
        """
        Check if the current role has write permissions to the specified database and schema.

        Args:
            database_name (str): Name of the database to check
            schema_name (str): Name of the schema to check

        Raises:
            PermissionError: If the role lacks write permissions
        """
        try:
            self.connector._exec(f"USE ROLE {self.connector.role}")
            self.connector._exec(f"USE DATABASE {database_name}")
            self.connector._exec(f"USE SCHEMA {schema_name}")
            self.connector._exec("CREATE OR REPLACE TABLE test_write (id INT)")
            self.connector._exec("DROP TABLE test_write")
        except Exception as e:
            raise PermissionError(f"Error: {str(e)}") from e

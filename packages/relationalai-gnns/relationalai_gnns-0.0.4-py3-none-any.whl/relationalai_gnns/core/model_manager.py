import re
from typing import Optional

from relationalai_gnns.common.exceptions import ModelManagerError
from relationalai_gnns.common.job_models import PayloadTypes

from .api_request_handler import APIRequestHandler
from .connector import BaseConnector


class ModelManager:
    """Manager for registering and handling models via the connector."""

    def __init__(self, connector: BaseConnector):
        """
        Initialize the ModelManager.

        Args:
            connector (BaseConnector): Connector to communicate with the backend service.
        """
        self.connector = connector
        self.api_handler = APIRequestHandler(connector)

    def list_models(self):
        """Get dataset metadata from MLflow artifacts."""

        payload = {
            "payload_type": PayloadTypes.REQUEST_LIST_MODELS,
        }
        return self.api_handler.make_request(payload)

    def delete_model(self, experiment_name: str, model_run_id: str):
        """Get dataset metadata from MLflow artifacts."""

        payload = {
            "payload_type": PayloadTypes.DELETE_MODEL,
            "experiment_name": experiment_name,
            "model_run_id": model_run_id,
        }
        return self.api_handler.make_request(payload)

    def register_model(
        self,
        model_run_id: str,
        experiment_name: str,
        model_name: str,
        version_name: str,
        database_name: str,
        schema_name: str,
        comment: Optional[str] = None,
    ):
        """
        Register a trained model in the Model Registry.

        The model is registered under the specified name and version.
        Registration is only allowed if a valid `model_run_id` exists.
        Duplicate version names for a model are not allowed.

        Args:
            model_run_id (str): Unique identifier of the trained model run.
            experiment_name (str): Name of the experiment associated with the model.
            model_name (str): Name to assign to the registered model.
            version_name (str): Version name for the model.
            database_name (str): Database where the model is registered.
            schema_name (str): Schema in the database.
            comment (Optional[str]): Optional comment for registration.

        Raises:
            ValueError: If the registration fails due to a request error or other exceptions.
        """
        payload = {
            "payload_type": PayloadTypes.REGISTER_MODEL,
            "model_name": model_name,
            "version_name": version_name,
            "database_name": database_name,
            "schema_name": schema_name,
            "model_run_id": model_run_id,
            "experiment_name": experiment_name,
            "comment": comment,
        }

        try:
            registered_model = self.api_handler.make_request(payload)
            print(
                f"✅ Successfully registered model "
                f"'{registered_model['database_name']}.{registered_model['schema_name']}."
                f"{registered_model['model_name']}.{registered_model['version_name']}'"
            )
        except Exception as e:
            error_msg = re.sub(r"To auto-generate `version_name`, skip that argument\.", "", str(e)).strip()
            raise ModelManagerError(f"❌ Error during model registration: {error_msg}")

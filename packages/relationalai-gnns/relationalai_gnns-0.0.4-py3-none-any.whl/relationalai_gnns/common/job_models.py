from datetime import datetime
from enum import Enum
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

from .export import FileExtension


class JobStatus(str, Enum):
    """Helper class to set job status."""

    QUEUED = "QUEUED"
    COMPLETED = "COMPLETED"
    RUNNING = "RUNNING"
    CANCELED = "CANCELED"
    FAILED = "FAILED"
    CREATED = "CREATED"


class JobTypes(str, Enum):
    """Job types for the job payload."""

    TRAIN = "train"
    INFERENCE = "inference"
    TRAIN_INFERENCE = "train_inference"


class PayloadTypes(str, Enum):
    """Payload types for different request."""

    JOB = "JOB"
    FETCH_TABLE = "FETCH_TABLE"
    VALIDATE_CONFIG = "VALIDATE_CONFIG"
    ADD_INFERENCE_EXPORT = "ADD_INFERENCE_EXPORT"
    REGISTER_MODEL = "REGISTER_MODEL"
    SEND_LOGS = "SEND_LOGS"
    REQUEST_QUEUE_STATUS = "REQUEST_QUEUE_STATUS"
    REQUEST_DATASET_CONFIG = "REQUEST_DATASET_CONFIG"
    REQUEST_LOGS = "REQUEST_LOGS"
    REQUEST_JOB_STATUS = "REQUEST_JOB_STATUS"
    REQUEST_LIST_MODELS = "REQUEST_LIST_MODELS"
    DELETE_MODEL = "DELETE_MODEL"


class ModelSelectionStrategy(str, Enum):
    """Enumeration of possible strategies for selecting the model to use for inference."""

    REGISTERED = "registered"
    CUSTOM_RUN = "custom_run"
    CURRENT = "current"


class RequestRegisterModel(BaseModel):
    """Model for registering a GNN model to MLFlow."""

    payload_type: Literal[PayloadTypes.REGISTER_MODEL]
    experiment_name: str
    model_run_id: str
    database_name: str
    schema_name: str
    model_name: str
    version_name: str
    comment: Optional[str] = None


class RequestQueueStatus(BaseModel):
    """Model for gettting the status of a job."""

    payload_type: Literal[PayloadTypes.REQUEST_QUEUE_STATUS]


class RequestJobStatus(BaseModel):
    """Model for gettting the status of a job."""

    payload_type: Literal[PayloadTypes.REQUEST_JOB_STATUS]
    job_id: str


class SendLogs(BaseModel):
    """Model for gettting the status of a job."""

    payload_type: Literal[PayloadTypes.SEND_LOGS]
    job_id: str
    stream_name: str


class RequestTableModel(BaseModel):
    """Model for requesting table data."""

    payload_type: Literal[PayloadTypes.FETCH_TABLE]
    source: str
    connector: str


class JobModel(BaseModel):
    """Model for requesting model-related jobs."""

    payload_type: Literal[PayloadTypes.JOB]
    job_type: JobTypes
    dataset_metadata: Optional[Dict] = None
    model_configuration: Optional[Dict] = None

    model_config = {"protected_namespaces": ()}


class RequestDatasetConfig(BaseModel):
    """Model for requesting dataset configuration."""

    payload_type: Literal[PayloadTypes.REQUEST_DATASET_CONFIG]
    experiment_name: str
    config_path: str = "dataset_config.yaml"
    model_run_id: Optional[str] = None
    registered_model_key: Optional[str] = None
    model_selection_strategy: Optional[ModelSelectionStrategy] = None

    model_config = {"protected_namespaces": ()}


class JobResult(BaseModel):
    """Pydantic base model to represent the result of a job (e.g., training)"""

    job_id: str
    status: JobStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    experiment_name: Optional[str] = None
    job_type: Optional[str] = None
    model_run_id: Optional[str] = None
    result: Optional[Dict] = None
    export_paths: Optional[Dict] = None
    error: Optional[str] = None

    model_config = {"protected_namespaces": ()}

    def mark_started(self):
        """Set started_at timestamp."""
        if self.status == JobStatus.RUNNING and self.started_at is None:
            self.started_at = datetime.utcnow()
            self.mark_updated()

    def mark_updated(self):
        """Set updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def mark_finished(self):
        """Set finish time stamp upon termination status."""
        if self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED]:
            self.finished_at = datetime.utcnow()
            self.mark_updated()


class PydanticConfigType(str, Enum):
    """Enum representing different configuration types."""

    MODEL_CONFIG = "model_config"
    DATASET_CONFIG = "dataset_config"


class RequestConfigValidation(BaseModel):
    """Model for validating configs."""

    payload_type: Literal[PayloadTypes.VALIDATE_CONFIG]
    config: dict
    type: PydanticConfigType


class InferenceExportParameters(BaseModel):
    """Model for inference and export parameters."""

    # Core payload
    payload_type: Literal[PayloadTypes.ADD_INFERENCE_EXPORT]
    config: dict

    # Inference parameters
    test_batch_size: Optional[int] = 128
    model_selection_strategy: Optional[ModelSelectionStrategy] = None
    model_run_id: Optional[str] = None
    registered_model_key: Optional[str] = Field(
        default=None,
        pattern=r"^[\w]+\.[\w]+\.[\w]+\.[\w]+$",
        description="Fully qualified model key in the format 'database.schema.model.version'.",
    )
    extract_embeddings: bool = False
    flatten_output: bool = False

    # Export parameters
    output_alias: Optional[str] = None
    # snowflake
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    # local
    artifacts_dir: Optional[str] = None
    extension: Optional[FileExtension] = None

    model_config = {"protected_namespaces": ()}


class RequestListModels(BaseModel):
    """
    Request schema for listing all models.

    Attributes:
        payload_type (Literal[PayloadTypes.LIST_MODELS]):
            The type of request payload, fixed to "LIST_MODELS".
    """

    payload_type: Literal[PayloadTypes.REQUEST_LIST_MODELS]


class DeleteModel(BaseModel):
    """Request schema for deleting a registered model."""

    payload_type: Literal[PayloadTypes.DELETE_MODEL]
    model_run_id: str
    experiment_name: str

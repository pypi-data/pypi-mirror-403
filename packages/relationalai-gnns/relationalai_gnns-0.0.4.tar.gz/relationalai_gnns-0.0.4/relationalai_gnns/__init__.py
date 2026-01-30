from .common.exceptions import ConnectionError, InternalError, ValidationError
from .common.export import OutputConfig, SnowflakeSettings
from .core.config_trainer import ExperimentConfig, TrainerConfig
from .core.connector import LocalConnector, SnowflakeConnector, SnowflakeConnectorDirectAccess
from .core.dataset import Dataset
from .core.gnn_table import CandidateKey, ForeignKey, GNNTable
from .core.job_manager import JobHandler, JobManager, JobMonitor
from .core.metrics import EvaluationMetric
from .core.model_manager import ModelManager
from .core.provider import Provider
from .core.task import LinkTask, NodeTask, Task, TaskType
from .core.trainer import Trainer
from .core.types import ColumnDType
from .external.db_diagram import create_schema_graph

# Import version from auto-generated file
try:
    from ._version import __version__
except ImportError:
    # Fallback for development installations without setuptools-scm
    __version__ = "0.0.0.dev0"

__all__ = [
    "Trainer",
    "TrainerConfig",
    "SnowflakeConnector",
    "SnowflakeConnectorDirectAccess",
    "Dataset",
    "CandidateKey",
    "LocalConnector",
    "ForeignKey",
    "GNNTable",
    "JobHandler",
    "JobManager",
    "EvaluationMetric",
    "JobMonitor",
    "JobMonitorError",
    "JobManagerError",
    "JobHandlerError",
    "Provider",
    "Task",
    "LinkTask",
    "NodeTask",
    "TaskType",
    "ColumnDType",
    "OutputConfig",
    "SnowflakeSettings",
    "create_schema_graph",
    "ValidationError",
    "ConnectionError",
    "InternalError",
    "ExperimentConfig",
    "ModelManager",
    "__version__",
]

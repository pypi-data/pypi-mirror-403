from enum import Enum
from typing import Dict, List, Literal, Optional

import pydantic
from pydantic import Field, ValidationInfo, field_validator, model_validator
from typing_extensions import Self

# --- Enums ---


class MetricName(str, Enum):
    """Metric names for all available metrics."""

    # binary classification
    AVERAGE_PRECISION = "average_precision"
    ACCURACY = "accuracy"  # also multi-class classification
    F1 = "f1"
    ROC_AUC = "roc_auc"
    # multilabel classification
    MULTILABEL_AUPRC_MICRO = "multilabel_auprc_micro"
    MULTILABEL_AUROC_MICRO = "multilabel_auroc_micro"
    MULTILABEL_PRECISION_MICRO = "multilabel_precision_micro"
    MULTILABEL_AUPRC_MACRO = "multilabel_auprc_macro"
    MULTILABEL_AUROC_MACRO = "multilabel_auroc_macro"
    MULTILABEL_PRECISION_MACRO = "multilabel_precision_macro"
    # multiclass classification
    MACRO_F1 = "macro_f1"
    MICRO_F1 = "micro_f1"
    # regerssion
    R2 = "r2"
    MAE = "mae"
    RMSE = "rmse"
    # all link prediction problems
    LINK_PREDICTION_PRECISION = "link_prediction_precision"
    LINK_PREDICTION_RECALL = "link_prediction_recall"
    LINK_PREDICTION_MAP = "link_prediction_map"


class TaskType(str, Enum):
    r"""The type of the tasks."""

    REGRESSION = "regression"
    BINARY_CLASSIFICATION = "binary_classification"
    MULTILABEL_CLASSIFICATION = "multilabel_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REPEATED_LINK_PREDICTION = "repeated_link_prediction"
    LINK_PREDICTION = "link_prediction"


class TableDataFormat(str, Enum):
    """Table data formats."""

    PARQUET = "parquet"
    CSV = "csv"
    DUCKDB = "duckdb"
    SNOWFLAKE = "snowflake"
    RAI_LINK = "rai_link"


class ColumnDType(str, Enum):
    """Column data types."""

    float_t = "float"
    category_t = "category"
    datetime_t = "datetime"
    text_t = "text"
    embedding_t = "embedding"
    integer_t = "integer"
    multi_category_t = "multi_categorical"


class KeysDType(str, Enum):
    """Data types for candidate/foreign keys."""

    float_t = "float"
    text_t = "text"
    integer_t = "integer"


class TableType(str, Enum):
    """Table types."""

    NODE = "node"
    EDGE = "edge"


# --- Consts ---
METRICS_REQUIRING_K = {
    MetricName.LINK_PREDICTION_MAP,
    MetricName.LINK_PREDICTION_PRECISION,
    MetricName.LINK_PREDICTION_RECALL,
}


# --- Helper classes ---
class TaskMetricMapping:
    """Mapping of TaskType to valid MetricName values."""

    TASK_TYPE_TO_METRICS: Dict[TaskType, List[MetricName]] = {
        TaskType.REGRESSION: [MetricName.RMSE, MetricName.MAE, MetricName.R2],
        TaskType.MULTILABEL_CLASSIFICATION: [
            MetricName.MULTILABEL_AUPRC_MACRO,
            MetricName.MULTILABEL_AUPRC_MICRO,
            MetricName.MULTILABEL_AUROC_MACRO,
            MetricName.MULTILABEL_AUROC_MICRO,
            MetricName.MULTILABEL_PRECISION_MACRO,
            MetricName.MULTILABEL_PRECISION_MICRO,
        ],
        TaskType.BINARY_CLASSIFICATION: [
            MetricName.F1,
            MetricName.ACCURACY,
            MetricName.ROC_AUC,
            MetricName.AVERAGE_PRECISION,
        ],
        TaskType.MULTICLASS_CLASSIFICATION: [MetricName.ACCURACY, MetricName.MICRO_F1, MetricName.MACRO_F1],
        TaskType.LINK_PREDICTION: [
            MetricName.LINK_PREDICTION_MAP,
            MetricName.LINK_PREDICTION_PRECISION,
            MetricName.LINK_PREDICTION_RECALL,
        ],
        TaskType.REPEATED_LINK_PREDICTION: [
            MetricName.LINK_PREDICTION_MAP,
            MetricName.LINK_PREDICTION_PRECISION,
            MetricName.LINK_PREDICTION_RECALL,
        ],
    }

    @classmethod
    def get_valid_metrics(cls, task_type: TaskType):
        """Retrieve a list of valid metrics for a task type."""
        return cls.TASK_TYPE_TO_METRICS[task_type]

    @classmethod
    def is_valid_metric(cls, task_type: TaskType, metric: MetricName) -> bool:
        """Check if a metric is valid for a task type."""
        return metric.value.lower() in cls.TASK_TYPE_TO_METRICS[task_type]


# --- Models ---


class ColumnSchema(pydantic.BaseModel):
    """Column schema model."""

    class Config:
        use_enum_values = True

    name: str
    dtype: ColumnDType
    format: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def convert_name_to_str(cls, value):
        """Support int column names in the .yaml."""
        return str(value)


class CandidateKeySchema(pydantic.BaseModel):
    """Candidate_Key schema model."""

    name: str
    is_feature: bool = Field(default=False)


class ForeignKeySchema(pydantic.BaseModel):
    """Foreign_Key schema model."""

    name: str
    link_to: str = Field(pattern=r"^[a-zA-Z]\w*\.[a-zA-Z]\w*$")
    is_feature: bool = Field(default=False)


class ConnectorConfig(pydantic.BaseModel):
    """Configuration model for a connector."""

    class Config:
        use_enum_values = True

    name: TableDataFormat
    dataset_name: str
    extra_fields: Optional[Dict[str, str]] = {}


class TableSchema(pydantic.BaseModel):
    """Table schema model: definition"""

    class Config:
        use_enum_values = True

    name: str = Field(description="name of the table")
    source: str = Field(description="full path to the file or table")
    columns: Optional[List[ColumnSchema]] = Field(default_factory=list)
    candidate_keys: Optional[List[CandidateKeySchema]] = Field(default_factory=list)
    foreign_keys: Optional[List[ForeignKeySchema]] = Field(default_factory=list)
    time_column: Optional[str] = None
    extra_fields: Optional[Dict[str, str]] = Field(default_factory=dict)

    @property
    def column_dict(self) -> Dict[str, ColumnSchema]:
        """Convert list of columns to a dictionary with column names as keys."""
        return {col_schema.name: col_schema for col_schema in self.columns}


class ValidatedTableSchema(TableSchema):
    """Table schema model with metadata validations."""

    type: TableType

    @model_validator(mode="after")
    def validate_non_empty_columns(self) -> Self:
        if len(self.columns) <= 0:
            raise ValueError(f"Table: {self.name} has no columns defined.")
        return self

    @model_validator(mode="after")
    def validate_no_duplicates_in_columns(self) -> Self:
        column_name_lst = [c.name for c in self.columns]
        if len(column_name_lst) != len(set(column_name_lst)):
            raise ValueError(f"Table: {self.name} contains duplicate column names.")
        return self

    @model_validator(mode="after")
    def validate_no_duplicates_in_cks(self) -> Self:
        ck_name_lst = [c.name for c in self.candidate_keys]
        if len(ck_name_lst) != len(set(ck_name_lst)):
            raise ValueError(f"Table: {self.name} contains duplicate candidate key names.")
        return self

    @model_validator(mode="after")
    def validate_type_of_cks(self) -> Self:
        col_type_dict = {}
        for c in self.columns:
            col_type_dict[c.name] = c.dtype
        for ck in self.candidate_keys:
            if not (col_type_dict[ck.name] in (item.value for item in KeysDType)):
                raise ValueError(
                    f"Invalid type ({col_type_dict[ck.name]}) for candidate key: {ck.name} in table: {self.name}."
                )
        return self

    @model_validator(mode="after")
    def validate_no_duplicates_in_fks(self) -> Self:
        fk_name_lst = [f.name for f in self.foreign_keys]
        if len(fk_name_lst) != len(set(fk_name_lst)):
            raise ValueError(f"Table: {self.name} contains duplicate foreign key names.")
        return self

    @model_validator(mode="after")
    def validate_existence_of_ck(self) -> Self:
        column_name_lst = [c.name for c in self.columns]

        for ck in self.candidate_keys:
            if not (ck.name in column_name_lst):
                raise ValueError(f"Table: {self.name}: candidate key {ck.name} not in columns.")
        return self

    @model_validator(mode="after")
    def validate_existence_of_fk(self) -> Self:
        column_name_lst = [c.name for c in self.columns]

        for fk in self.foreign_keys:
            if not (fk.name in column_name_lst):
                raise ValueError(f"Table: {self.name}: foreign key {fk.name} not in columns.")
        return self

    @model_validator(mode="after")
    def validate_existence_of_time_column(self) -> Self:
        if not (self.time_column is None):
            column_name_lst = [c.name for c in self.columns]

            if not (self.time_column in column_name_lst):
                raise ValueError(f"Table: {self.name}: time column {self.time_column} not in columns.")
        return self

    @model_validator(mode="after")
    def validate_type_of_time_column(self) -> Self:
        if not (self.time_column is None):
            tm_clmn = None
            for c in self.columns:
                if c.name == self.time_column:
                    tm_clmn = c
                    break

            if not (tm_clmn is None):
                if tm_clmn.dtype != ColumnDType.datetime_t:
                    raise ValueError(f"Table: {self.name}: time column is not of datetime type")
        return self

    @model_validator(mode="after")
    def validate_edge_table_columns(self) -> Self:
        if self.type == TableType.EDGE:
            fk_name_lst = [fk.name for fk in self.foreign_keys]
            if len(fk_name_lst) != 2:
                raise ValueError(f"Table: {self.name} should contain only 2 foreign key columns.")
            column_name_lst = [c.name for c in self.columns]
            if not (set(fk_name_lst) == set(column_name_lst)):
                raise ValueError(f"Table: {self.name} should contain only the foreign keys in columns.")
        return self


class EvaluationMetric(pydantic.BaseModel):
    """Class representing an evaluation metric."""

    name: str
    eval_at_k: Optional[int] = Field(default=None)

    @field_validator("eval_at_k", mode="before")
    @classmethod
    def validate_eval_at_k(cls, value, values: ValidationInfo):
        """Validate if eval_at_k is not None for link prediction metrics."""
        metric_name = MetricName(values.data.get("name"))

        if metric_name in METRICS_REQUIRING_K and value is None:
            raise ValueError(f"eval_at_k cannot be None for metric {metric_name.value}")
        return value


class TaskMeta(pydantic.BaseModel):
    """Task metadata model."""

    class Config:
        use_enum_values = True

    name: str
    source: Dict[Literal["train", "test", "validation"], Optional[str]]
    columns: List[ColumnSchema]
    time_column: Optional[str] = None
    label_column: Optional[str] = None
    target_entity_column: str
    target_link_to: str = Field(pattern=r"^[a-zA-Z]\w*\.[a-zA-Z]\w*$")
    current_time: bool = Field(default=True)
    source_entity_column: Optional[str] = None
    source_link_to: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z]\w*\.[a-zA-Z]\w*$")
    task_type: TaskType
    evaluation_metric: EvaluationMetric
    extra_fields: Optional[Dict[str, str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_non_empty_columns(self) -> Self:
        if len(self.columns) <= 0:
            raise ValueError("Task table has no columns defined.")
        return self

    @model_validator(mode="after")
    def validate_no_duplicates_in_columns(self) -> Self:
        column_name_lst = [c.name for c in self.columns]
        if len(column_name_lst) != len(set(column_name_lst)):
            raise ValueError("Task table contains duplicate column names.")
        return self

    @model_validator(mode="after")
    def validate_existence_of_time_column(self) -> Self:
        if not (self.time_column is None):
            column_name_lst = [c.name for c in self.columns]

            if not (self.time_column in column_name_lst):
                raise ValueError(f"Time column {self.time_column} not in task table columns.")
        return self

    @model_validator(mode="after")
    def validate_existence_of_label_column(self) -> Self:
        if not (self.label_column is None):
            column_name_lst = [c.name for c in self.columns]

            if not (self.label_column in column_name_lst):
                raise ValueError(f"Label column {self.label_column} not in task table columns.")
        return self

    @model_validator(mode="after")
    def validate_existence_of_target_entity_column(self) -> Self:
        column_name_lst = [c.name for c in self.columns]

        if not (self.target_entity_column in column_name_lst):
            raise ValueError(f"Target entity column {self.target_entity_column} not in task table columns.")
        return self

    @model_validator(mode="after")
    def validate_existence_of_source_entity_column(self) -> Self:
        if not (self.source_entity_column is None):
            column_name_lst = [c.name for c in self.columns]

            if not (self.source_entity_column in column_name_lst):
                raise ValueError(f"Source entity column {self.source_entity_column} not in task table columns.")
        return self

    @model_validator(mode="after")
    def validate_type_of_time_column(self) -> Self:
        if not (self.time_column is None):
            tm_clmn = None
            for c in self.columns:
                if c.name == self.time_column:
                    tm_clmn = c
                    break

            if not (tm_clmn is None):
                if tm_clmn.dtype != ColumnDType.datetime_t:
                    raise ValueError("Task table time column is not of datetime type")
        return self

    @model_validator(mode="after")
    def validate_task_type_parameters(self) -> Self:
        if self.task_type in {
            TaskType.REGRESSION,
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTILABEL_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        }:
            if self.label_column is None:
                raise ValueError(f"Task {self.task_type} requires a label column.")

            if not (self.source_entity_column is None):
                raise ValueError(f"Task {self.task_type} should not have a source entity column.")

            if not (self.source_link_to is None):
                raise ValueError(f"Task {self.task_type} should not have a source link.")

        if self.task_type in {TaskType.REPEATED_LINK_PREDICTION, TaskType.LINK_PREDICTION}:
            if not (self.label_column is None):
                raise ValueError(f"Task {self.task_type} should not have a label column.")

            if self.source_entity_column is None:
                raise ValueError(f"Task {self.task_type} requires a source entity column.")

            if self.source_link_to is None:
                raise ValueError(f"Task {self.task_type} requires a source link.")

        return self

    @field_validator("evaluation_metric")
    @classmethod
    def validate_metric_for_task(cls, value, values: ValidationInfo):
        """Check if the evaluation metric is valid for a task type."""
        metric_name = value.name
        task_type = values.data.get("task_type")

        metric_name = MetricName(metric_name)
        if not TaskMetricMapping.is_valid_metric(TaskType(task_type), metric_name):
            raise ValueError(f"Metric {metric_name.name} is not valid for {task_type}")
        return value

    @property
    def column_dict(self) -> Dict[str, ColumnSchema]:
        """Convert list of columns to a dictionary with column names as keys."""
        return {col_schema.name: col_schema for col_schema in self.columns}


class DatasetMeta(pydantic.BaseModel):
    """Dataset metadata model."""

    # Connector type.
    connector: ConnectorConfig
    # Table schemas.
    tables: List[ValidatedTableSchema]
    # Task metadata.
    task: TaskMeta

    @model_validator(mode="after")
    def validate_tables_in_FKs(self) -> Self:
        tbl_name_set = set()
        for t in self.tables:
            tbl_name_set.add(t.name)
        for t in self.tables:
            for fk in t.foreign_keys:
                tbl_name = fk.link_to[: fk.link_to.index(".")]
                if not (tbl_name in tbl_name_set):
                    raise ValueError(
                        f"Foreign key {fk.name} in table {t.name} references a non-existent table {tbl_name}."
                    )
        return self

    @model_validator(mode="after")
    def validate_columns_in_FKs(self) -> Self:
        tbl_ck_dict = {}
        for t in self.tables:
            tbl_ck_dict[t.name] = set()
            for ck in t.candidate_keys:
                tbl_ck_dict[t.name].add(ck.name)
        for t in self.tables:
            for fk in t.foreign_keys:
                tbl_name, col_name = fk.link_to.split(".")

                if tbl_name in tbl_ck_dict.keys():
                    if not (col_name in tbl_ck_dict[tbl_name]):
                        raise ValueError(
                            f"FK {fk.name} in {t.name} references {col_name} which is not a candidate key in {tbl_name}."
                        )
        return self

    @model_validator(mode="after")
    def validate_column_types_in_FKs(self) -> Self:
        tbl_ck_type_dict = {}
        tbl_fk_type_dict = {}
        for t in self.tables:
            tbl_col_type_dict = {}
            for c in t.columns:
                tbl_col_type_dict[c.name] = c.dtype

            tbl_ck_type_dict[t.name] = {}
            for ck in t.candidate_keys:
                tbl_ck_type_dict[t.name][ck.name] = tbl_col_type_dict[ck.name]

            tbl_fk_type_dict[t.name] = {}
            for fk in t.foreign_keys:
                tbl_fk_type_dict[t.name][fk.name] = tbl_col_type_dict[fk.name]

        for t in self.tables:
            for fk in t.foreign_keys:
                tbl_name, col_name = fk.link_to.split(".")

                if tbl_name in tbl_ck_type_dict.keys():
                    if t.name in tbl_fk_type_dict.keys():
                        if col_name in tbl_ck_type_dict[tbl_name].keys():
                            if fk.name in tbl_fk_type_dict[t.name].keys():
                                if not (tbl_ck_type_dict[tbl_name][col_name] == tbl_fk_type_dict[t.name][fk.name]):
                                    raise ValueError(
                                        f"FK {fk.name} in {t.name} has a different type with the CK it references."
                                    )
        return self

    @model_validator(mode="after")
    def validate_table_in_target(self) -> Self:
        tbl_name_set = set()
        for t in self.tables:
            tbl_name_set.add(t.name)

        tbl_name = self.task.target_link_to[: self.task.target_link_to.index(".")]

        if not (tbl_name in tbl_name_set):
            raise ValueError(f"Target link in task references a non-existent table {tbl_name}.")

        return self

    @model_validator(mode="after")
    def validate_column_in_target(self) -> Self:
        tbl_ck_dict = {}
        for t in self.tables:
            tbl_ck_dict[t.name] = set()
            for ck in t.candidate_keys:
                tbl_ck_dict[t.name].add(ck.name)

        tbl_name, col_name = self.task.target_link_to.split(".")

        if tbl_name in tbl_ck_dict.keys():
            if not (col_name in tbl_ck_dict[tbl_name]):
                raise ValueError(
                    f"Target link in task references {col_name} which is not a candidate key in {tbl_name}."
                )
        return self

    @model_validator(mode="after")
    def validate_table_in_source(self) -> Self:
        if not (self.task.source_link_to is None):
            tbl_name_set = set()
            for t in self.tables:
                tbl_name_set.add(t.name)

            tbl_name = self.task.source_link_to[: self.task.source_link_to.index(".")]
            if not (tbl_name in tbl_name_set):
                raise ValueError(f"Source link in task references a non-existent table {tbl_name}.")

        return self

    @model_validator(mode="after")
    def validate_column_in_source(self) -> Self:
        if not (self.task.source_link_to is None):
            tbl_ck_dict = {}
            for t in self.tables:
                tbl_ck_dict[t.name] = set()
                for ck in t.candidate_keys:
                    tbl_ck_dict[t.name].add(ck.name)

            tbl_name, col_name = self.task.source_link_to.split(".")

            if tbl_name in tbl_ck_dict.keys():
                if not (col_name in tbl_ck_dict[tbl_name]):
                    raise ValueError(
                        f"Source link in task references {col_name} which is not a candidate key in {tbl_name}."
                    )
        return self

    @model_validator(mode="after")
    def validate_column_type_in_target(self) -> Self:
        tbl_ck_type_dict = {}
        for t in self.tables:
            tbl_col_type_dict = {}
            for c in t.columns:
                tbl_col_type_dict[c.name] = c.dtype

            tbl_ck_type_dict[t.name] = {}
            for ck in t.candidate_keys:
                tbl_ck_type_dict[t.name][ck.name] = tbl_col_type_dict[ck.name]

        task_col_type_dict = {}
        for c in self.task.columns:
            task_col_type_dict[c.name] = c.dtype

        tbl_name, col_name = self.task.target_link_to.split(".")

        if tbl_name in tbl_ck_type_dict.keys():
            if not (task_col_type_dict[self.task.target_entity_column] == tbl_ck_type_dict[tbl_name][col_name]):
                raise ValueError(
                    f"Target link in task has a different type than the column {col_name} that it references."
                )
        return self

    @model_validator(mode="after")
    def validate_column_type_in_source(self) -> Self:
        if not (self.task.source_link_to is None):
            tbl_ck_type_dict = {}
            for t in self.tables:
                tbl_col_type_dict = {}
                for c in t.columns:
                    tbl_col_type_dict[c.name] = c.dtype

                tbl_ck_type_dict[t.name] = {}
                for ck in t.candidate_keys:
                    tbl_ck_type_dict[t.name][ck.name] = tbl_col_type_dict[ck.name]

            task_col_type_dict = {}
            for c in self.task.columns:
                task_col_type_dict[c.name] = c.dtype

            tbl_name, col_name = self.task.source_link_to.split(".")

            if tbl_name in tbl_ck_type_dict.keys():
                if not (task_col_type_dict[self.task.source_entity_column] == tbl_ck_type_dict[tbl_name][col_name]):
                    raise ValueError(
                        f"Source link in task has a different type than the column {col_name} that it references."
                    )
        return self

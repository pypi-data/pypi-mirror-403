from abc import abstractmethod
from typing import Dict, Literal, Optional, Set

from tabulate import tabulate

from relationalai_gnns.common.dataset_model import ColumnDType, EvaluationMetric, TaskMeta, TaskType

from .connector import BaseConnector
from .gnn_table import ForeignKey, GNNTable, SDKTableType
from .utils import CustomAttributeError

__all__ = ["TaskType"]


class Task(GNNTable):
    """
    Base class to define all kinds of tasks.

    Inherits from GNNTable to implement logic of adding composite/foreign key columns, time columns and determine dtypes
    """

    # helper dict to differentiate different task types (node vs link)
    task_type_dict = {
        TaskType.LINK_PREDICTION: "link",
        TaskType.REPEATED_LINK_PREDICTION: "link",
        TaskType.BINARY_CLASSIFICATION: "node",
        TaskType.MULTICLASS_CLASSIFICATION: "node",
        TaskType.MULTILABEL_CLASSIFICATION: "node",
        TaskType.REGRESSION: "node",
    }

    task_data_source: Dict[Literal["train", "test", "validation"], str]

    def __init__(
        self,
        connector: BaseConnector,
        name: str,
        task_data_source: Dict[Literal["train", "test", "validation"], str],
        task_type: TaskType,
        entity_columns: Set[ForeignKey],
        time_column: Optional[str] = None,
        evaluation_metric: Optional[EvaluationMetric] = None,
        current_time: Optional[bool] = True,
    ):
        """
        Base class describing a task.

        Inherits from the GNNTable class.

        :param connector: The connector object used to interact with the data backend.
        :type connector: BaseConnector
        :param name: The name of the task, describing the task at hand.
        :type name: str
        :param task_data_source: A dictionary with three keys: "train", "test", and "validation",
            each pointing to the path of the corresponding dataset. The path is the
             name of a Snowflake table in the format <Database.Schema.Table>.
        :type task_data_source: Dict[Literal["train", "test", "validation"], str]
        :param time_column: The name of the time column. Can also be set later using the
            ``set_time_column`` function.
        :type time_column: str, optional
        :param entity_columns: The foreign key(s) representing entity references.
            - For ``NodeTask``: refers to the column to the node entity ``Table.Column``.
            - For ``LinkTask``: refers to the source and target node entity ``Table.Column``.
        :type entity_columns: Set[ForeignKey]
        :param evaluation_metric: The evaluation metric to optimize for.
        :type evaluation_metric: EvaluationMetric, optional
        :param current_time: A flag indicating whether to use the current time of the task table.
            If set to ``False``, the current time of the task table will be reduced by one time unit.
            Useful when the task table should not access database table values at the same time stamp.
            Default: True
        :type current_time: bool, optional
        """

        super().__init__(
            connector=connector,
            source=task_data_source["train"],
            name=name,
            foreign_keys=entity_columns,
            type=SDKTableType.TASK,
            time_column=time_column,
        )
        # create task tables schema and see if there are any errors
        self.table_schema = self._create_table_schema(validate=True)

        self.task_data_source = task_data_source  # table data source for /train/test/val
        self.task_type = task_type  # task type
        self.evaluation_metric = evaluation_metric  # evaluation metrics for task
        self._current_time = current_time  # set current time for task

        if self.evaluation_metric is None:
            self._set_default_eval_metric()
            print(f"No evaluation metric detected, defaulting to {self.evaluation_metric.name}")

    def set_evaluation_metric(self, evaluation_metric: EvaluationMetric):
        """
        Helper function to set the evaluation metric.

        :param evaluation_metric: The name of the evaluation metric to optimize for. Optional.
        :type evaluation_metric: EvaluationMetric
        """
        if self.task_type_dict[self.task_type] == "link" and evaluation_metric.eval_at_k is None:
            self.evaluation_metric = EvaluationMetric(name=evaluation_metric.name, eval_at_k=12)
            print("eval_at_k was not set, defaulting to 12")
        else:
            self.evaluation_metric = evaluation_metric

    def _set_default_eval_metric(self):
        """Helper function to return a default evaluation metric, if not specified by the user."""
        if self.evaluation_metric is None:
            if self.task_type == TaskType.REGRESSION:
                self.evaluation_metric = EvaluationMetric(name="rmse")
            elif self.task_type == TaskType.BINARY_CLASSIFICATION:
                self.evaluation_metric = EvaluationMetric(name="roc_auc")
            elif self.task_type == TaskType.LINK_PREDICTION or self.task_type == TaskType.REPEATED_LINK_PREDICTION:
                self.evaluation_metric = EvaluationMetric(name="link_prediction_map", eval_at_k=12)
            elif self.task_type == TaskType.MULTICLASS_CLASSIFICATION:
                self.evaluation_metric = EvaluationMetric(name="macro_f1")
            else:
                self.evaluation_metric = EvaluationMetric(name="multilabel_auroc_macro")

    @abstractmethod
    def show_task(self):
        """Pretty print task information."""
        pass

    @abstractmethod
    def _create_task(self):
        """Helper function to create TaskMeta."""
        pass

    # --- Override functions to update self.table_schema -----#
    def update_column_dtype(self, col_name: str, dtype: ColumnDType):
        super().update_column_dtype(col_name, dtype)
        self.table_schema = self._create_table_schema(validate=False)

    def remove_column(self, col_name: str):
        # read-only attributes should not be allowed to dropped or unset
        if isinstance(self, NodeTask):
            if col_name in [self.target_entity_column, self.label_column]:
                raise AttributeError(f"Column '{col_name}' cannot be removed (init-only).")
        if isinstance(self, LinkTask):
            if col_name in [self.source_entity_column, self.target_entity_column]:
                raise AttributeError(f"Column '{col_name}' cannot be removed (init-only).")

        super().remove_column(col_name)
        self.table_schema = self._create_table_schema(validate=False)

    def add_column(self, col_name: str, dtype: ColumnDType):
        super().add_column(col_name, dtype)
        self.table_schema = self._create_table_schema(validate=False)

    def set_time_column(self, col_name: str):
        super().set_time_column(col_name)
        self.table_schema = self._create_table_schema(validate=False)

    def unset_time_column(self, col_name: str):
        super().unset_time_column(col_name)
        self.table_schema = self._create_table_schema(validate=False)

    @property
    def current_time(self):
        return self._current_time

    @current_time.setter
    def current_time(self, value):
        raise CustomAttributeError("❌ Cannot set 'current_time' after initialization. It is read-only.")


class LinkTask(Task):
    """
    Class representing link based tasks.

    It can be used for classic or repeater link prediction tasks.
    """

    def __init__(
        self,
        connector: BaseConnector,
        name: str,
        task_data_source: Dict[Literal["train", "test", "validation"], str],
        source_entity_column: ForeignKey,
        target_entity_column: ForeignKey,
        task_type: Literal[TaskType.LINK_PREDICTION, TaskType.REPEATED_LINK_PREDICTION],
        time_column: Optional[str] = None,
        evaluation_metric: Optional[EvaluationMetric] = None,
        current_time: Optional[bool] = True,
    ):
        """
        Link task.

        :param connector: The connector object used for interacting with the data backend.
        :type connector: BaseConnector

        :param name: The name of the task, which can describe the task at hand.
        :type name: str

        :param task_data_source: A dictionary with three keys: "train", "test", and "validation",
            each pointing to the path of the corresponding dataset. The path is the
            name of a Snowflake table in the format <Database.Schema.Table>.
        :type task_data_source: Dict[Literal["train", "test", "validation"], str]

        :param source_entity_column: A ForeignKey that specifies the name of the source entity column
        in the link task table and points to the referenced source entity GNNTable and its corresponding
        column
        :type source_entity_column: ForeignKey



        :param target_entity_column: A ForeignKey that specifies the name of the target entity column
        in the link task table and points to the referenced target entity GNNTable and its corresponding
        column
        :type target_entity_column: ForeignKey

        :param task_type: The type of the task, which can be either link prediction or repeated link prediction.
        :type task_type: Literal[TaskType.LINK_PREDICTION, TaskType.REPEATED_LINK_PREDICTION]

        :param time_column: Optional. The name of the time column. This can also be set later
            using the `set_time_column` function.
        :type time_column: Optional[str]

        :param evaluation_metric: Optional. The name of the evaluation metric to optimize for.
        :type evaluation_metric: Optional[EvaluationMetric]

        :param current_time: Optional. If set to False the current time of the task table will be reduced
                    by one time unit. Useful when the time column at the task table does not need to see the
                    values from the database tables at the same time stamp
        :type current_time: Optional[bool]
        """

        entity_columns = {source_entity_column, target_entity_column}

        if len(entity_columns) < 2:
            raise ValueError("❌ Source and target entity columns must be distinct for LinkTask.")

        super().__init__(
            connector=connector,
            name=name,
            task_data_source=task_data_source,
            task_type=task_type,
            time_column=time_column,
            entity_columns=entity_columns,
            evaluation_metric=evaluation_metric,
            current_time=current_time,
        )
        # to be filled when create_task is called
        self._source_entity_column = source_entity_column.column_name
        self._source_link_to = source_entity_column.link_to
        self._target_entity_column = target_entity_column.column_name
        self._target_link_to = target_entity_column.link_to
        self.task_info = self._create_task()

    def _create_task(self) -> TaskMeta:
        """
        Instantiate the TaskMeta object for this LinkTask.

        :return: A TaskMeta object containing metadata about the link task.
        """
        task_info = TaskMeta(
            name=self.name,
            source=self.task_data_source,
            columns=self.table_schema.columns,
            time_column=self.time_column,
            task_type=self.task_type,
            evaluation_metric=self.evaluation_metric,
            target_entity_column=self.target_entity_column,
            target_link_to=self.target_link_to,
            source_entity_column=self.source_entity_column,
            source_link_to=self.source_link_to,
            current_time=self.current_time,
        )
        return task_info

    def show_task(self):
        """Display formatted information about the current task."""

        print("Task Information")
        print("=" * 50)
        print(f"Task name:                {self.name}")
        print(f"Task type:                {self.task_type.value}")
        print(f"Evaluation Metric:        {self.evaluation_metric}")

        print("\nTask Table Sources:")
        print("-" * 50)
        for key, val in self.task_data_source.items():
            print(f"  • {key}: {val}")

        headers = [
            "Column Name",
            "Data Type",
            "Format",
            "Is Time Column",
            "Source Entity Column",
            "Source Link To",
            "Target Entity Column",
            "Target Link To",
        ]

        task_table = []
        for col_name, col in self._column_schemas.items():
            row = {
                "Column Name": col_name,
                "Data Type": col.dtype,
                "Format": col.format if col.format is not None else "",
                "Is Time Column": True if col_name == self.time_column else "",
                "Source Entity Column": True if col_name == self.source_entity_column else "",
                "Source Link To": self.source_link_to if col_name == self.source_entity_column else "",
                "Target Entity Column": True if col_name == self.target_entity_column else "",
                "Target Link To": self.target_link_to if col_name == self.target_entity_column else "",
            }
            task_table.append(list(row.values()))

        print(tabulate(task_table, headers=headers, tablefmt="grid"))

    @property
    def source_entity_column(self):
        return self._source_entity_column

    @source_entity_column.setter
    def source_entity_column(self, value):
        raise CustomAttributeError("❌ Cannot set 'source_entity_column' after initialization. It is read-only.")

    @property
    def source_link_to(self):
        return self._source_link_to

    @source_link_to.setter
    def source_link_to(self, value):
        raise CustomAttributeError("❌ Cannot set 'source_link_to' after initialization. It is read-only.")

    @property
    def target_entity_column(self):
        return self._target_entity_column

    @target_entity_column.setter
    def target_entity_column(self, value):
        raise CustomAttributeError("❌ Cannot set 'target_entity_column' after initialization. It is read-only.")

    @property
    def target_link_to(self):
        return self._target_link_to

    @target_link_to.setter
    def target_link_to(self, value):
        raise CustomAttributeError("❌ Cannot set 'target_link_to' after initialization. It is read-only.")


class NodeTask(Task):
    """
    Class representing a node task.

    It can be node binary/multi-label/multi-class classification, or node regression
    """

    # If we specify time in task it should have a field in thee database
    def __init__(
        self,
        connector: BaseConnector,
        name: str,
        task_data_source: Dict[Literal["train", "test", "validation"], str],
        target_entity_column: ForeignKey,
        label_column: str,
        task_type: Literal[
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
            TaskType.MULTILABEL_CLASSIFICATION,
            TaskType.REGRESSION,
        ],
        time_column: Optional[str] = None,
        evaluation_metric: Optional[EvaluationMetric] = None,
        current_time: Optional[bool] = True,
    ):
        """
        Node task.

        :param connector: The connector object used for interacting with the data backend.
        :type connector: BaseConnector

        :param name: The name of the task, which can describe the task at hand.
        :type name: str

        :param task_data_source: A dictionary with three keys: "train", "test", and "validation",
            each pointing to the path of the respective dataset. The path can be a `.csv` or `.parquet` file,
            or the name of a Snowflake table in the form `<Database.Schema.Table>`.
        :type task_data_source: Dict[Literal["train", "test", "validation"], str]

        :param target_entity_column: A ForeignKey for the target entity column in the node task
        table that links to the Candidate Key of the GNNTable that we want to do predictions for.
        :type target_entity_column: ForeignKey

        :param label_column: The column in the task table that holds the values that will be used to train the model.
        :type label_column: str

        :param task_type: The type of the node task, which can be binary classification, multi-class classification,
            multi-label classification, or regression.
        :type task_type: Literal[TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION,
            TaskType.MULTILABEL_CLASSIFICATION, TaskType.REGRESSION]

        :param time_column: Optional. The name of the time column. This can also be set later
            using the `set_time_column` function.
        :type time_column: Optional[str]

        :param evaluation_metric: Optional. The name of the evaluation metric to optimize for.
        :type evaluation_metric: Optional[EvaluationMetric]

        :param current_time: Optional. If set to False the current time of the task table will be reduced
                    by one time unit. Useful when the time column at the task table does not need to see the
                    values from the database tables at the same time stamp
        :type current_time: Optional[bool]
        """

        entity_columns = {target_entity_column}
        super().__init__(
            connector=connector,
            name=name,
            task_data_source=task_data_source,
            task_type=task_type,
            entity_columns=entity_columns,
            time_column=time_column,
            evaluation_metric=evaluation_metric,
            current_time=current_time,
        )

        # initialize it calling the create_task function
        self._label_column = label_column
        if self.label_column not in list(self._column_schemas.keys()):
            raise ValueError(f"❌ Label column: {self.label_column} does not exist in the task table")

        self._target_entity_column = target_entity_column.column_name
        self._target_link_to = target_entity_column.link_to
        self.task_info = self._create_task()

    def _create_task(self) -> TaskMeta:
        """
        Instantiate the TaskMeta object for this NodeTask.

        :return: A TaskMeta object containing metadata about the node task.
        """
        task_info = TaskMeta(
            name=self.name,
            source=self.task_data_source,
            columns=self.table_schema.columns,
            time_column=self.time_column,
            task_type=self.task_type,
            evaluation_metric=self.evaluation_metric,
            label_column=self.label_column,
            target_entity_column=self.target_entity_column,
            target_link_to=self.target_link_to,
            current_time=self.current_time,
        )
        return task_info

    @property
    def label_column(self):
        return self._label_column

    @label_column.setter
    def label_column(self, value):
        raise CustomAttributeError("❌ Cannot set 'label_column' after initialization. It is read-only.")

    @property
    def target_entity_column(self):
        return self._target_entity_column

    @target_entity_column.setter
    def target_entity_column(self, value):
        raise CustomAttributeError("❌ Cannot set 'target_entity_column' after initialization. It is read-only.")

    @property
    def target_link_to(self):
        return self._target_link_to

    @target_link_to.setter
    def target_link_to(self, value):
        raise CustomAttributeError("❌ Cannot set 'target_link_to' after initialization. It is read-only.")

    def show_task(self):
        """Display formatted information about the current task."""
        if self.task_info is None:
            print("Please create the dataset first")
            return

        print("Task Information")
        print("=" * 50)
        print(f"Task name:                {self.name}")
        print(f"Task type:                {self.task_type.value}")
        print(f"Evaluation Metric:        {self.evaluation_metric}")

        print("\nTask Table Sources:")
        print("-" * 50)
        for key, val in self.task_data_source.items():
            print(f"  • {key}: {val}")

        headers = [
            "Column Name",
            "Data Type",
            "Format",
            "Is Time Column",
            "Label Column",
            "Target Entity Column",
            "Target Link To",
        ]

        task_table = []
        for col_name, col in self._column_schemas.items():
            row = {
                "Column Name": col_name,
                "Data Type": col.dtype,
                "Format": col.format if col.format is not None else "",
                "Is Time Column": True if col_name == self.time_column else "",
                "Label Column": True if col_name == self.label_column else "",
                "Target Entity Column": True if col_name == self.target_entity_column else "",
                "Target Link To": self.target_link_to if col_name == self.target_entity_column else "",
            }
            task_table.append(list(row.values()))

        print(tabulate(task_table, headers=headers, tablefmt="grid"))

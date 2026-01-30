import json
from typing import Dict, List, Union

import sqlalchemy
from sqlalchemy import Column, ForeignKey, MetaData, Table, create_engine

from relationalai_gnns.common.dataset_model import ColumnDType, ColumnSchema
from relationalai_gnns.core.gnn_table import CandidateKey
from relationalai_gnns.core.gnn_table import ForeignKey as GNNForeignKey
from relationalai_gnns.external.db_diagram import create_schema_graph

from .connector import BaseConnector
from .custom_sqlalchemy_dtypes import (
    CustomARRAY,
    CustomBLOB,
    CustomDateTime,
    CustomFloat,
    CustomInteger,
    CustomString,
    CustomVARCHAR,
)
from .gnn_table import GNNTable
from .task import LinkTask, NodeTask, TaskType


class Dataset:
    """
    Base class for describing a dataset.

    Handles task metadata construction, validation of consistency across
    candidate/foreign keys, database connectivity checks ..., and visualization
    of dataset metadata
    """

    def __init__(
        self,
        connector: BaseConnector,
        dataset_name: str,
        tables: List[GNNTable],
        task_description: Union[NodeTask, LinkTask],
    ):
        """
        Initializes the dataset and loads task and dataset data.

        :param connector: The connector object used for interacting with the data backend.
        :type connector: BaseConnector

        :param dataset_name: The name of the dataset.
        :type dataset_name: str

        :param tables: A list of table objects that are part of the dataset.
        :type tables: List[GNNTable]

        :param task_description: The task for the GNN, either a `NodeTask` or a `LinkTask`.
        :type task_description: Union[NodeTask, LinkTask]
        """
        self.connector = connector
        self.dataset_name = dataset_name
        self.tables = tables
        self.task_description = task_description
        # Construct metadata dict
        self._run_sanity_checks()
        # init. from create dataset
        self.experiment_name = "_".join(
            (self.dataset_name, self.task_description.task_type.value, self.task_description.name)
        )
        self.metadata_dict = self._construct_metadata_dict()

    def visualize_dataset(self, show_dtypes: bool = False):
        """
        Helper function to visualize the dataset. Returns a `pydot.core.dot` graph object that can be visualized in an
        IPython notebook.

        Example usage:
            from IPython.display import Image, display
            graph = dataset.visualize_dataset()
            plt = Image(graph.create_png())
            display(plt)

        :param show_dtypes: Optional. Whether to show the SQLAlchemy dtypes of each column.
            Default is `False`.
        :type show_dtypes: bool

        :returns: A graph visualization object of the dataset.
        :rtype: pydot.core.dot
        """

        sql_alch_meta = self._create_sql_alchemy_metadata
        graph = create_schema_graph(
            engine=create_engine("sqlite://"),  # Use a temporary in-memory sqlite db.
            metadata=sql_alch_meta,
            show_datatypes=show_dtypes,
            show_indexes=False,
            rankdir="TB",
            concentrate=True,
        )
        return graph

    def print_data_config(self):
        """Prints the final dataset config."""
        print(json.dumps(self.metadata_dict, indent=4))

    def _column_to_dict(self, column: ColumnSchema) -> Dict:
        """
        Convert a ColumnSchema into a dictionary representation.

        :param column: The column schema.
        :type column: ColumnSchema
        :return: The dictionary representation of the column.
        :rtype: Dict
        """
        column_dict = {}
        column_dict["name"] = column.name
        column_dict["dtype"] = column.dtype
        if column.format is not None:
            column_dict["format"] = column.format
        return column_dict

    def _foreign_key_to_dict(self, foreign_key: GNNForeignKey) -> Dict:
        """
        Convert a ForeignKey into a dictionary representation.

        :param foreign_key: The foreign key.
        :type foreign_key: ForeignKey
        :return: The dictionary representation of the foreign key.
        :rtype: Dict
        """

        foreign_key_dict = {}
        foreign_key_dict["name"] = foreign_key.column_name
        foreign_key_dict["link_to"] = foreign_key.link_to
        if foreign_key.is_feature is True:
            foreign_key_dict["is_feature"] = foreign_key.is_feature
        return foreign_key_dict

    def _candidate_key_to_dict(self, candidate_key: CandidateKey) -> Dict:
        """
        Convert a CandidateKey into a dictionary representation.

        :param candidate_key: The candidate key.
        :type candidate_key: CandidateKey
        :return: The dictionary representation of the candidate key.
        :rtype: Dict
        """
        candidate_key_dict = {}
        candidate_key_dict["name"] = candidate_key.column_name
        if candidate_key.is_feature is True:
            candidate_key_dict["is_feature"] = candidate_key.is_feature
        return candidate_key_dict

    def _construct_metadata_dict(self) -> Dict:
        """
        Construct the metadata dictionary.

        :return: A dictionary containing the dataset metadata.
        :rtype: Dict
        """
        metadata_dict = {
            "connector": {
                "name": self.connector.connector_type,
                "dataset_name": self.dataset_name,
                "experiment_name": self.experiment_name,
            }
        }
        metadata_dict["tables"] = []
        # add table information
        for table in self.tables:
            table_meta_dict = {}
            table_meta_dict["name"] = table.name
            table_meta_dict["source"] = table.source
            table_meta_dict["type"] = table.type.value
            if table.time_column is not None:
                table_meta_dict["time_column"] = table.time_column
            table_meta_dict["columns"] = []
            # add table column information
            for column in table._column_schemas.values():
                table_meta_dict["columns"].append(self._column_to_dict(column))
            if len(table.foreign_keys) != 0:
                table_meta_dict["foreign_keys"] = []
                # add table foreign key information
                for foreign_key in table.foreign_keys:
                    table_meta_dict["foreign_keys"].append(self._foreign_key_to_dict(foreign_key))
            if len(table.candidate_keys) != 0:
                table_meta_dict["candidate_keys"] = []
                # add table candidate key information
                for candidate_key in table.candidate_keys:
                    table_meta_dict["candidate_keys"].append(self._candidate_key_to_dict(candidate_key))
            metadata_dict["tables"].append(table_meta_dict)
        # add task information
        metadata_dict["task"] = {}
        metadata_dict["task"]["name"] = self.task_description.name
        metadata_dict["task"]["source"] = self.task_description.task_data_source
        metadata_dict["task"]["columns"] = []

        for column in self.task_description.table_schema.columns:
            metadata_dict["task"]["columns"].append(self._column_to_dict(column))

        if self.task_description.time_column is not None:
            metadata_dict["task"]["time_column"] = self.task_description.time_column

        metadata_dict["task"]["task_type"] = self.task_description.task_type.value
        metadata_dict["task"]["current_time"] = self.task_description.current_time

        if self.task_description.task_type_dict[self.task_description.task_type] == "node":
            metadata_dict["task"]["label_column"] = self.task_description.label_column
            metadata_dict["task"]["target_entity_column"] = self.task_description.target_entity_column
            metadata_dict["task"]["target_link_to"] = self.task_description.target_link_to
            metadata_dict["task"]["evaluation_metric"] = {"name": self.task_description.evaluation_metric.name}
        else:
            metadata_dict["task"]["source_entity_column"] = self.task_description.source_entity_column
            metadata_dict["task"]["source_link_to"] = self.task_description.source_link_to
            metadata_dict["task"]["target_entity_column"] = self.task_description.target_entity_column
            metadata_dict["task"]["target_link_to"] = self.task_description.target_link_to
            metadata_dict["task"]["evaluation_metric"] = {
                "name": self.task_description.evaluation_metric.name,
                "eval_at_k": self.task_description.evaluation_metric.eval_at_k,
            }

        return metadata_dict

    def _run_sanity_checks(self):
        """Runs sanity all checks."""
        # validate all tables
        for table in self.tables:
            table.validate_table()
        self._check_time_column_consistency()
        self._check_ckey_fkey_consistency()
        self._check_db_connectivity()
        if self.task_description.task_type in [TaskType.LINK_PREDICTION, TaskType.REPEATED_LINK_PREDICTION]:
            self._check_link_task_consistency()
        else:
            self._check_node_task_consistency()

    def _check_time_column_consistency(self):
        """
        If a time column has been defined in the task, but
        there's no time column defined in the data, throw
        an error (and vice versa)
        Raises:
            ValueError: If time column does not exist in data tables
                but exists in task table
            ValueError: If the time column does exist in the data
                tables but does not exist in the task table

        """
        # see if have at least one table with a time column
        time_col_tables = []
        for table in self.tables:
            if table.time_column is not None:
                time_col_tables.append(table.name)

        # task has time column data does not
        if self.task_description.time_column is not None and len(time_col_tables) == 0:
            raise ValueError(
                f"❌ task has a time column defined: {self.task_description.time_column}"
                " but there is no time column defined in the data tables"
            )
        # task does not have a time column but data has
        if self.task_description.time_column is None and len(time_col_tables) != 0:
            raise ValueError(
                f"❌ No time column is defined for the task, while the following data tables - "
                f"{time_col_tables} contain a time column."
            )

    def _construct_table_dict(self) -> Dict[str, GNNTable]:
        """
        Helper function that scans through the data tables and returns a table dict.

        Returns:
            table_dict (Dict[str,GNNTable]): Key: table name, value: GNNTable
        """
        table_dict = {}
        for table in self.tables:
            table_dict[table.name] = table
        return table_dict

    def _check_ckey_fkey_consistency(self):
        """
        Checks if the data tables have consistent candidate and foreign keys
        Raises:
            ValueError: If foreign keys point to non existent candidate keys
            ValueError: If foreign key and corresponding candidate key have
                different dtypes
            ValueError: If there is a badly formatted foreign key
        """
        # start by constructing a helper dict that will map tables to table names
        table_dict = self._construct_table_dict()
        for table in self.tables:
            if table.foreign_keys is not None:
                fkeys = table.foreign_keys
                for fkey in fkeys:
                    link_to = fkey.link_to.split(".")
                    if len(link_to) != 2:
                        raise ValueError(f"❌ Badly formatted foreign key: {fkey}")
                    table_name, ckey_name = link_to[0], link_to[1]
                    if table_name not in table_dict:
                        raise ValueError(
                            f"❌ Foreign key {fkey.column_name} points to table {table_name}, "
                            "which does not exist in the dataset tables."
                        )
                    if len(table_dict[table_name].candidate_keys) == 0:
                        raise ValueError(
                            f"❌ Foreign key {fkey.column_name} points "
                            f"to table {table_name}. However "
                            f"{table_name} does not have any candidate key columns."
                        )

                    ckeys = [ckey.column_name for ckey in table_dict[table_name].candidate_keys]
                    if ckey_name not in ckeys:
                        raise ValueError(
                            f"❌ Foreign key {fkey.column_name} points "
                            f"to column {ckey_name} in table {table_name}. "
                            f"However there is no such candidate key column."
                        )
                    # check that dtypes match
                    dtype_fkey = table._column_schemas[fkey.column_name].dtype
                    dtype_ckey = table_dict[table_name]._column_schemas[ckey_name].dtype
                    if dtype_fkey != dtype_ckey:
                        raise ValueError(
                            f"❌ Foreign key {fkey.column_name} in table {table.name} "
                            f"has a different dtype ({dtype_fkey}) than candidate key "
                            f"{ckey_name} in table {table_name} ({dtype_ckey})."
                        )

    def _check_db_connectivity(self):
        """
        Check if the database tables form a connected graph.

        Here we do not care if foreign keys point to non-existent
        candidate keys since we can "catch" that with the _check_ckey_fkey_consistency call
        Raises:
            ValueError if the database tables are not connected
        """
        # start by constructing a helper dict that will map tables to table names
        table_dict = self._construct_table_dict()
        # now we will instantiate an undirected graph where the key will
        # be a table name and values will be a list of tables that connect to
        # that table
        graph = {}
        # add nodes
        for table_name in table_dict:
            graph[table_name] = []
        # add indirected edges
        for source_table_name, table in table_dict.items():
            if table.foreign_keys is not None:
                # edges are essentially defined by fkeys
                fkeys = table.foreign_keys
                for fkey in fkeys:
                    link_to = fkey.link_to.split(".")
                    dest_table_name = link_to[0]
                    # add edge
                    graph[source_table_name].append(dest_table_name)
                    graph[dest_table_name].append(source_table_name)
        # now we can simply implement depth first search to see if we are connected
        # set with visited nodes
        visited = set()
        # start node - any node will do
        start_node = next(iter(graph))

        def dfs(node):
            """Helper recursive depth-first search."""
            visited.add(node)
            for neigh in graph.get(node, []):
                if neigh not in visited:
                    dfs(neigh)

        dfs(start_node)
        disconnected_tables = graph.keys() - visited
        if len(visited) != len(graph):
            raise ValueError(
                f"❌ Found the following tables in the database: {list(graph)}. "
                f"The database does not seem to be connected. "
                f"\nThe disconnected tables are : {disconnected_tables}. "
                f"\nPlease make sure to add proper candidate and foreign keys to establish connections."
            )

    def _check_link_task_consistency(self):
        """
        Checks if source/target entity column of a link task exist
        Checks if source/target link of a link task exists and is a valid link to
            a candidate key of an existing table
        Raises:
            ValueError: If source entity column does not exist in task table
            ValueError: If source link to points to a table that
                does not exist in database tables
            ValueError: If source link to points to a candidate key that
                is not a candidate key in the corresponding table
            ValueError: If source link to points to a candidate key that
                has different dtype than source entity column
            ValueError: If target entity column does not exist in task table
            ValueError: If target link to points to a table that
                does not exist in database tables
            ValueError: If target link to points to a candidate key that
                is not a candidate key in the corresponding table
            ValueError: If target link to points to a candidate key that
                has different dtype than target entity column
        """
        table_dict = self._construct_table_dict()

        source_entity_column = self.task_description.source_entity_column
        source_table = self.task_description.source_link_to.split(".")[0]
        source_fkey_name = self.task_description.source_link_to.split(".")[1]
        target_entity_column = self.task_description.target_entity_column
        target_table = self.task_description.target_link_to.split(".")[0]
        target_fkey_name = self.task_description.target_link_to.split(".")[1]

        column_names = {col.name for col in self.task_description._column_schemas.values()}

        for kind, col in [("Source", source_entity_column), ("Target", target_entity_column)]:
            if col not in column_names:
                raise ValueError(f"❌ {kind} entity column {col} does not exist in task table")

        if source_table not in table_dict:
            raise ValueError(
                f"❌ Source link to {self.task_description.source_link_to} "
                f"points to table {source_table}, "
                "which does not exist."
            )
        if target_table not in table_dict:
            raise ValueError(
                f"❌ Target link to {self.task_description.target_link_to} "
                f"points to table {target_table} "
                "which does not exist."
            )

        ckey_names = [ckey.column_name for ckey in table_dict[source_table].candidate_keys]
        if source_fkey_name not in ckey_names:
            raise ValueError(
                f"❌ Source link to {self.task_description.source_link_to} points "
                f"to column {source_fkey_name} in table {source_table}, "
                f"which is not a candidate key column"
            )

        task_dtype = self.task_description._column_schemas[source_entity_column].dtype
        table_dtype = table_dict[source_table]._column_schemas[source_fkey_name].dtype
        if task_dtype != table_dtype:
            raise ValueError(
                f"❌ Source entity column {source_entity_column} in task has a different dtype "
                f"({task_dtype}) than source link to column {source_fkey_name} in table {source_table} "
                f"({table_dtype})."
            )
        ckey_names = [ckey.column_name for ckey in table_dict[target_table].candidate_keys]
        if target_fkey_name not in ckey_names:
            raise ValueError(
                f"❌ Target link to {self.task_description.target_link_to} points "
                f"to column {target_fkey_name} in table {target_table}, "
                f"which is not a candidate key column"
            )

        task_dtype = self.task_description._column_schemas[target_entity_column].dtype
        table_dtype = table_dict[target_table]._column_schemas[target_fkey_name].dtype
        if task_dtype != table_dtype:
            raise ValueError(
                f"❌ Target entity column {target_entity_column} in task has a different dtype "
                f"({task_dtype}) than target link to column {target_fkey_name} in table {target_table} "
                f"({table_dtype})."
            )

    def _check_node_task_consistency(self):
        """
        Checks if label column and target entity column of a node task exist
        Checks if target link of a node task exists and is a valid link to
            a candidate key of an existing table
        Raises:
            ValueError: If label column does not exist in task table
            ValueError: If target entity column does not exist in task table
            ValueError: If target link to points to a table that
                does not exist in database tables
            ValueError: If target link to points to a candidate key that
                is not a candidate key in the corresponding table
            ValueError: If target link to points to a candidate key that
                has different dtype than target entity column
        """

        table_dict = self._construct_table_dict()

        label_column = self.task_description.label_column
        target_entity_column = self.task_description.target_entity_column
        target_table = self.task_description.target_link_to.split(".")[0]
        target_fkey_name = self.task_description.target_link_to.split(".")[1]

        column_names = {col.name for col in self.task_description._column_schemas.values()}

        for kind, col in [("Label column", label_column), ("Target entity column", target_entity_column)]:
            if col not in column_names:
                raise ValueError(f"❌ {kind} {col} does not exist in task table")

        if target_table not in table_dict:
            raise ValueError(
                f"❌ Target link to {self.task_description.target_link_to} "
                f"points to table {target_table} "
                "which does not exist."
            )

        ckey_names = [ckey.column_name for ckey in table_dict[target_table].candidate_keys]
        if target_fkey_name not in ckey_names:
            raise ValueError(
                f"❌ Target link to {self.task_description.target_link_to} points "
                f"to column {target_fkey_name} in table {target_table}, "
                f"which is not a candidate key column"
            )

        task_dtype = self.task_description._column_schemas[target_entity_column].dtype
        table_dtype = table_dict[target_table]._column_schemas[target_fkey_name].dtype
        if task_dtype != table_dtype:
            raise ValueError(
                f"❌ Target entity column {target_entity_column} in task has a different dtype "
                f"({task_dtype}) than target link to column {target_fkey_name} in table {target_table} "
                f"({table_dtype})."
            )

    @property
    def _create_sql_alchemy_metadata(self) -> sqlalchemy.MetaData:
        """
        Create sql achemy metadata describing the table and the task.

        Returns:
            metadata (sqlalchemy.MetaData): The sql alchemy metadata
        """
        metadata = MetaData()
        metadata.table_types = {}
        # create the database tables
        for table in self.tables:
            table_name = table.name
            metadata.table_types[table_name] = table.type.value
            cols = []
            for col_name, col_schema in table._column_schemas.items():
                match_fk = next((fk for fk in table.foreign_keys if fk.column_name == col_name), None)
                match_ck = next((ck for ck in table.candidate_keys if ck.column_name == col_name), None)
                col = self._make_sqlalchemy_column(col_name, col_schema, match_ck, match_fk)
                cols.append(col)
            # here essentially we dynamicaly update metadata
            _ = Table(table_name, metadata, *cols)
        # add task
        task_cols = []
        for col_name, col_schema in self.task_description._column_schemas.items():
            match_fk = next((fk for fk in self.task_description.foreign_keys if fk.column_name == col_name), None)
            col = self._make_sqlalchemy_column(col_name, col_schema, None, match_fk)
            task_cols.append(col)
        metadata.table_types[self.task_description.name] = "task"
        _ = Table(self.task_description.name, metadata, *task_cols)
        return metadata

    def _make_sqlalchemy_column(
        self, col_name: str, col_schema: ColumnSchema, match_ck: CandidateKey = None, match_fk: ForeignKey = None
    ) -> Column:
        """
        Helper function to create a SQLAlchemy table column
        Args:
            col_name (str): The column name
            col_schema (ColumnSchema): The column schema
        Return:
            col (Column): The SQL alchemy column
        Raise:
            ValueError: if the col_type is not a known ColumnDType
        """
        dtype_mapping_dict = {
            ColumnDType.category_t: CustomVARCHAR,
            ColumnDType.datetime_t: CustomDateTime,
            ColumnDType.embedding_t: CustomBLOB,
            ColumnDType.float_t: CustomFloat,
            ColumnDType.integer_t: CustomInteger,
            ColumnDType.multi_category_t: CustomARRAY,
            ColumnDType.text_t: CustomString,
        }
        col_type = col_schema.dtype
        is_pkey = False
        link_to = None
        if match_ck is not None:
            is_pkey = True
        elif match_fk is not None:
            link_to = match_fk.link_to
            # foreign/primary keys will overwrite column dtypes
            # and go first
        if is_pkey:
            col = Column(col_name, dtype_mapping_dict[col_type](), primary_key=True)
        elif link_to is not None:
            col = Column(col_name, dtype_mapping_dict[col_type](), ForeignKey(link_to))
        else:
            if col_type in dtype_mapping_dict:
                col = Column(col_name, dtype_mapping_dict[col_type]())
            else:
                raise ValueError(f"❌ Unknown column dtype {col_type}")
        return col

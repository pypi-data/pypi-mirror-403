from enum import Enum
from typing import Optional, Set, Union

from pydantic import BaseModel, Field
from tabulate import tabulate

from relationalai_gnns.common.dataset_model import ColumnDType, ColumnSchema, KeysDType, TableSchema

from .api_request_handler import APIRequestHandler
from .connector import BaseConnector


class SDKTableType(Enum):
    NODE = "node"
    EDGE = "edge"
    TASK = "task"


class ForeignKey(BaseModel):
    """
    Helper class representing a foreign key entry.

    :param column_name: The name of the foreign key column.
    :type column_name: str
    :param link_to: The table and column name that the foreign key links to.
        Format: <table_name>.<column_name>
    :type link_to: str
    :param is_feature: A flag indicating whether the foreign key should be treated as a GNN feature.
    :type is_feature: bool
    """

    column_name: str
    link_to: str
    is_feature: bool = Field(default=False)

    def __eq__(self, other):
        if isinstance(other, ForeignKey):
            return self.column_name == other.column_name
        return False

    def __hash__(self):
        # hash only on the column name
        # we can not have the same column to link to different tables
        return hash(self.column_name)


class CandidateKey(BaseModel):
    """
    Helper class representing a candidate key entry.

    :param column_name: The name of the candidate key column.
    :type column_name: str
    :param is_feature: Whether the candidate key should be treated as a GNN feature.
    :type is_feature: bool
    """

    column_name: str
    is_feature: bool = Field(default=False)

    def __eq__(self, other):
        if isinstance(other, CandidateKey):
            return self.column_name == other.column_name
        return False

    def __hash__(self):
        # hash only on the column name
        # we can not have the same column to link to different tables
        return hash(self.column_name)


class GNNTable:
    """
    Class representing a GNN Table.

    The GNN Table is a metadata class that defines the table attributes that will be used as an input to the GNN \
    relational learning engine.
    """

    def __init__(
        self,
        connector: BaseConnector,
        source: str,
        name: str,
        type: Union[str, SDKTableType],
        candidate_keys: Optional[Set[CandidateKey]] = None,
        foreign_keys: Optional[Set[ForeignKey]] = None,
        time_column: Optional[str] = None,
    ):
        """
        Class constructor for the GNNTable class.

        A table must define either a candidate key or at least one foreign key.
        Tables without a candidate or foreign key are considered invalid.

        :param connector: The connector object used to interact with the data backend.
        :type connector: Connector

        :param source: The data source. Can be a path to a `.csv` or `.parquet` file,
            or the name of a Snowflake table in the form `<Database.Schema.Table>`.
        :type source: str

        :param type: The table type - it would either be 1) node 2) edge or 3) task
        :type type: str

        :param candidate_keys: The list of candidate keys columns. Note: either a candidate key
            or at least one foreign key must be provided.
        :type candidate_keys: Optional[Set[CandidateKey]]

        :param foreign_keys: A set of foreign keys for the table.
            Note: either a candidate key
            or at least one foreign key must be provided.
        :type foreign_keys: Optional[Set[ForeignKey]]

        :param time_column: Optional. The name of the column representing time.
            This can also be set later using the `set_time_column()` method.
        :type time_column: Optional[str]
        """
        self.source = source
        self.name = name

        # initialize loader and read some sample data so we can auto-infer column dtypes
        self.connector = connector

        # assign the type of the table - node or edge or task
        # TASK for task table
        if isinstance(type, str):
            try:
                type = SDKTableType(type)
            except ValueError:
                raise ValueError(f"Invalid type: {type}. Must be one of {[t.value for t in SDKTableType]}")
        self.type = type

        self.api_handler = APIRequestHandler(connector)
        # fetch data and try to do an initial dtype inference
        result = self._request_data()
        self.column_names, infered_column_dtypes = result

        # initialize the column schema and populate them.
        self._column_schemas = {}
        # set with column names for which we can not infer a dtype
        self._columns_without_dtypes = set()
        # set with column names that the user has removed
        self._discarded_columns = set()

        # go through all the dataframe columns
        for col in self.column_names:
            dtype = infered_column_dtypes[col]
            if dtype is not None:  # inference of dtype is successful
                col_schema = ColumnSchema(name=col, dtype=dtype)
                self._column_schemas[col] = col_schema
            else:
                self._columns_without_dtypes.add(col)

        # print a warning for columns whose dtypes could not be inferred
        if len(self._columns_without_dtypes):
            print(
                "We could not infer the dtype for the below columns. "
                "Please add column manually using the add_column(...) method."
            )
            print(tabulate([[col] for col in self._columns_without_dtypes], headers=["Column Name"], tablefmt="grid"))

        # init placeholders for candidate keys, foreign keys and time column
        # init foreign keys and candidate keys as a set to avoid duplicates
        self.candidate_keys = set()
        self.foreign_keys = set()
        self.time_column = None

        # try to set candidate keys, foreign keys and time columns if specified by user
        # if we fail we will fall back to "set" methods
        if candidate_keys is not None:
            for ckey in candidate_keys:
                # error if column does not exist
                self._check_column_existence_on_init(ckey.column_name)
                # only set candidate key if we could infer the dtype
                if ckey.column_name in self._column_schemas:
                    # only set candidate key if the dtype is acceptable
                    if self._column_schemas[ckey.column_name].dtype in (item.value for item in KeysDType):
                        self.set_candidate_key(candidate_key=ckey)
                    else:
                        print(
                            f"Column {ckey.column_name} has dtype "
                            f"{self._column_schemas[ckey.column_name].dtype}. "
                            "Only integer, float and text columns are allowed as candidate keys. "
                            "If the inferred dtype is incorrect, please change the column dtype "
                            "using the update_column_dtype and then set the candidate key."
                        )
                else:
                    print(f"We could not infer the dtype for candidate key: {ckey}")
                    print("Please add column manually using the add_column(...) method")
                    print("and then set the candidate key")

        if foreign_keys is not None:
            for fkey in foreign_keys:
                # error if column does not exist
                self._check_column_existence_on_init(fkey.column_name)
                # only set foreign key if we could infer the dtype
                if fkey.column_name in self._column_schemas:
                    # only set foreign key if the dtype is acceptable
                    if self._column_schemas[fkey.column_name].dtype in (item.value for item in KeysDType):
                        self.set_foreign_key(foreign_key=fkey)
                    else:
                        print(
                            f"Column {fkey.column_name} has dtype "
                            f"{self._column_schemas[fkey.column_name].dtype}. "
                            "Only integer, float and text columns are recommended as foreign keys. "
                            "If the inferred dtype is incorrect, please change the column dtype "
                            "using the update_column_dtype and then set the foreign key."
                        )
                else:
                    print(f"We could not infer the dtype for foreign key: {fkey}")
                    print("Please add column manually using the add_column(...) method")
                    print("and then set the foreign key")

        if time_column is not None:
            # error if column does not exist
            self._check_column_existence_on_init(time_column)
            if time_column in self._column_schemas:
                if self._column_schemas[time_column].dtype == ColumnDType.datetime_t:
                    self.set_time_column(col_name=time_column)
                else:
                    # if inferred dtype is not datetime, user needs to explicitly add it using set_time_columm
                    print(f"Automatic inference of dtype for {time_column} failed")
                    print(f"Column dtype was assigned to: {self._column_schemas[time_column].dtype}")
                    print("Please change the column dtype to datetime and then set the time column")
            else:
                # the dtype of time column could not be inferred at all
                print(f"We could not infer the dtype for time column: {time_column}")
                print("Please add column manually using the add_column(...) method")
                print("and then set the time column")

    def update_column_dtype(self, col_name: str, dtype: ColumnDType):
        """
        Update the data type of existing column in the GNN table.

        The column must already exist in the table. If it does not, it must be added first.

        :param col_name: The name of the column to update.
        :type col_name: str
        :param dtype: The new data type to assign to the column.
        :type dtype: ColumnDtype
        :raises ValueError: If the column does not exist in the GNN table.
        :raises ValueError: If the column is a time column and the new dtype is not a datetime.
        :raises ValueError: If the column is a key column and the new dtype is not integer, float or text.
        """
        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)
        if self.time_column == col_name and dtype != ColumnDType.datetime_t:
            raise ValueError(f"❌ Column {col_name} is a time column, and only dtype of datetime is allowed.")
        if col_name in {ck.column_name for ck in self.candidate_keys} and dtype not in (item for item in KeysDType):
            raise ValueError(
                f"❌ Column {col_name} is a candidate key, and only dtype of integer, float or text are allowed."
            )
        if col_name in {fk.column_name for fk in self.foreign_keys} and dtype not in (item for item in KeysDType):
            raise ValueError(
                f"❌ Column {col_name} is a foreign key, and only dtype of integer, float or text are allowed."
            )
        self._column_schemas[col_name].dtype = dtype.value

    def remove_column(self, col_name: str):
        """
        Remove an existing column from the GNN table.

        If the column is used as a candidate key, foreign key, or time column, it will be removed from the respective
        sets or attribute as well.

        :param col_name: The name of the column to remove from the GNN table.
        :type col_name: str
        :raises ValueError: If the column does not exist in the GNN table.
        """
        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)
        self._column_schemas.pop(col_name)
        # add the column to set of columns removed by user
        self._discarded_columns.add(col_name)
        # if column was a time column remove it
        if self.time_column == col_name:
            self.time_column = None

        # if column was a candidate key remove it
        ckeys_to_remove = set()
        if self.candidate_keys is not None:
            for ckey in self.candidate_keys:
                if ckey.column_name == col_name:
                    ckeys_to_remove.add(ckey)
            self.candidate_keys.difference_update(ckeys_to_remove)

        # if column was a foreign key remove it
        fkeys_to_remove = set()
        if self.foreign_keys is not None:
            for fkey in self.foreign_keys:
                if fkey.column_name == col_name:
                    fkeys_to_remove.add(fkey)
            self.foreign_keys.difference_update(fkeys_to_remove)

    def add_column(self, col_name: str, dtype: ColumnDType):
        """
        Add a column that exists in the original dataset but not yet in the GNN table.

        :param col_name: The name of the column to add.
        :type col_name: str
        :param dtype: The data type of the column.
        :type dtype: ColumnDType
        :raises ValueError: If the column is already part of the GNN table.
        :raises ValueError: If the column does not exist in the original dataset.
        """
        if col_name in self._column_schemas:
            raise ValueError(
                f"❌ {col_name} is already in the GNN table, use set/unset methods to change its values. "
                f"Columns not part of the GNN table: {self._discarded_columns | self._columns_without_dtypes}"
            )
        elif col_name not in self._discarded_columns | self._columns_without_dtypes:
            raise ValueError(
                f"❌ {col_name} is not part of the data. "
                f"Columns not part of the GNN table: {self._discarded_columns | self._columns_without_dtypes}"
            )

        self._column_schemas[col_name] = ColumnSchema(name=col_name, dtype=dtype.value)

        # if column has been added to GNNTable, remove it from discarded_columns set if present.
        # And also from column_without_dtypes set.
        if col_name in self._discarded_columns:
            self._discarded_columns.discard(col_name)
        elif col_name in self._columns_without_dtypes:
            self._columns_without_dtypes.discard(col_name)

    def set_candidate_key(self, candidate_key: CandidateKey):
        """
        Set an existing column in the GNN table as a candidate key.

        :param candidate_key: The candidate key definition to apply.
        :type candidate_key: CandidateKey
        :raises ValueError: If the referenced column does not exist in the GNN table.
        :raises ValueError: If the referenced column's dtype is not integer, float or text.
        :raises ValueError: If the column has already been set as candidate key, and user is resetting it.
        """

        col_name = candidate_key.column_name

        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)

        if self._column_schemas[col_name].dtype not in (item.value for item in KeysDType):
            raise ValueError(
                f"❌ Column {col_name} has dtype {self._column_schemas[col_name].dtype}. "
                "Only integer, float and text columns can be used as candidate keys. "
                "If the inferred dtype is incorrect, please change the column dtype "
                "using the update_column_dtype and then set the candidate key."
            )

        if candidate_key in self.candidate_keys:
            raise ValueError(
                "❌ Duplicate candidate keys detected, please unset column as a candidate key and try again. "
                f"Current candidate keys {self.candidate_keys} "
                f"Trying to set duplicate key with column name: {candidate_key.column_name}"
            )
        self.candidate_keys.add(candidate_key)

    def unset_candidate_key(self, candidate_key: CandidateKey):
        """
        Unet an existing column in the GNN table as a candidate key.

        :param candidate_key: The candidate key definition to apply.
        :type candidate_key: CandidateKey
        :raises ValueError: If the referenced column does not exist in the GNN table.
        :raises KeyError: If the candidate key is not part of the declared candidate keys.
        """

        col_name = candidate_key.column_name

        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)

        if candidate_key not in self.candidate_keys:
            raise KeyError(
                f"❌ Candidate key {candidate_key} does not exist " f"Current candidate keys: {self.candidate_keys}"
            )

        self.candidate_keys.remove(candidate_key)

    def set_foreign_key(self, foreign_key: ForeignKey):
        """
        Set an existing column in the GNN table as a foreign key.

        :param foreign_key: The foreign key definition to apply.
        :type foreign_key: ForeignKey
        :raises ValueError: If the referenced column does not exist in the GNN table.
        :raises ValueError: If the referenced column's dtype is not integer, float or text.
        :raises ValueError: If the column has already been set as foreign key, and user is resetting it.
        :raises ValueError: If there is a self-referencing foreign key (e.g., customer.customer_id →
            customer.customer_id).
        """

        col_name = foreign_key.column_name
        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)

        if self._column_schemas[col_name].dtype not in (item.value for item in KeysDType):
            raise ValueError(
                f"❌ Column {col_name} has dtype {self._column_schemas[col_name].dtype}. "
                "Only integer, float and text columns can be used as foreign keys. "
                "If the inferred dtype is incorrect, please change the column dtype "
                "using the update_column_dtype and then set the foreign key."
            )

        if foreign_key in self.foreign_keys:
            raise ValueError(
                "❌ Duplicate foreign keys detected, please unset column as a foreign key and try again. "
                f"Current foreign keys {self.foreign_keys} "
                f"Trying to set duplicate key with column name: {foreign_key.column_name}"
            )

        # Detect self-referencing foreign keys (e.g., customer.customer_id → customer.customer_id)
        link_to_table, link_to_col = foreign_key.link_to.split(".")

        if (self.name == link_to_table) and (foreign_key.column_name == link_to_col):
            raise ValueError(
                f"❌ Self-referencing foreign key detected: "
                f"{self.name}.{foreign_key.column_name} → {link_to_table}.{link_to_col}. "
                f"This relationship is not allowed."
            )

        self.foreign_keys.add(foreign_key)

    def unset_foreign_key(self, foreign_key: ForeignKey):
        """
        Unset an existing column in the GNN table as a foreign key.

        :param foreign_key: The foreign key definition to apply.
        :type foreign_key: ForeignKey
        :raises ValueError: If the referenced column does not exist in the GNN table.
        :raises KeyError: If the foreign key is not part of the declared foreign keys.
        """

        col_name = foreign_key.column_name
        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)
        if foreign_key not in self.foreign_keys:
            raise KeyError(f"❌ Foreign key {foreign_key} does not exist " f"Current foreign keys: {self.foreign_keys}")
        self.foreign_keys.remove(foreign_key)

    def set_time_column(self, col_name: str):
        """
        Set an existing column in the GNN table as the time column.

        If a different time column is already set, it will be replaced.

        :param col_name: The name of the existing column to set as the time column.
        :type col_name: str
        :raises ValueError: If the column does not exist in the GNN table.
        :raises ValueError: If the column's data type is not datetime.
        """

        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)
        if self._column_schemas[col_name].dtype != ColumnDType.datetime_t:
            raise ValueError(
                f"❌ Column {col_name} has dtype {self._column_schemas[col_name].dtype}. "
                "Only datetime columns can be used as time columns"
            )
        self.time_column = col_name

    def unset_time_column(self, col_name: str):
        """
        Unset an existing column as the time column in the GNN table.

        :param col_name: The name of the existing column to unset as the time column.
        :type col_name: str
        :raises ValueError: If the column does not exist in the GNN table.
        :raises ValueError: If the column is not currently set as the time column.
        """
        if col_name not in self._column_schemas:
            self._raise_error_col_not_in_meta(col_name)

        if self.time_column == col_name:
            self.time_column = None
        else:
            raise ValueError(f"❌ {col_name} is not a time column, current time column set to {self.time_column}")

    def validate_table(self):
        """
        Helper function that performs various tests to validate metadata.

        Checks:
            - If there are any unmapped or unused columns.
            - If the table has at least one candidate key or one foreign key.
            - If the table is of type edge it has exactly two foreign key columns.

        :raises ValueError: If no candidate or foreign keys are present.
        :raises ValueError: If a foreign key is set as a time column.
        :raises ValueError: If a candidate key is set as a time column.
        :raises ValueError: If a table of type edge has more than two columns.
        :raises ValueError: If a table of type edge has not two foreign keys.
        :raises ValueError: If the time column of table has no defined data type.
        :raises ValueError: If the time column was removed from the data but the time column attribute is still set.
        :raises ValueError: If the specified time column does not exist in the current data columns.
        :raises ValueError: If the time column is not of datetime type.
        """
        if len(self._discarded_columns) > 0:
            print(f"Some columns were removed by the user from table {self.name}. Columns: {self._discarded_columns}")
            print("To include these columns in your dataset, please add them manually using the 'add_column' method.")
        if len(self._columns_without_dtypes) > 0:
            print(
                f"Some columns whose dtype cannot be inferred, and \
                hence will not be considered: {self._columns_without_dtypes}"
            )
            print(
                "To include these columns in your dataset, \
                  please add them manually using the 'add_column' method."
            )

        if (self.candidate_keys is None or len(self.candidate_keys) == 0) and (
            self.foreign_keys is None or len(self.foreign_keys) == 0
        ):
            raise ValueError(
                f"❌ Table: '{self.name}' has no candidate or foreign key columns "
                "Please set foreign or candidate key columns."
            )

        # check to see if the time column, exists has the right type and is a candidate or foreign key
        if self.time_column is not None:
            if self.time_column in self._columns_without_dtypes:
                raise ValueError(f"❌ Time column in table '{self.name} does not have a dtype' . ")

            if self.time_column in self._discarded_columns:
                raise ValueError(f"❌ Time column does not exist in table '{self.name}' . ")

            if self.time_column not in self._column_schemas.keys():
                raise ValueError(f"❌ Time column does not exist in table '{self.name}' . ")

            if not (self._column_schemas[self.time_column].dtype == ColumnDType.datetime_t):
                raise ValueError(f"❌ Time column dtype in table '{self.name} is not datetime' . ")

            if self.candidate_keys is not None:
                for ckey in self.candidate_keys:
                    if ckey.column_name == self.time_column:
                        raise ValueError(
                            f"❌ Table '{self.name}' has a candidate key {ckey.column_name} that is also a time column. "
                            "Operation not allowed: a candidate key can not be a time column."
                        )

            if self.foreign_keys is not None:
                for fkey in self.foreign_keys:
                    if fkey.column_name == self.time_column:
                        raise ValueError(
                            f"❌ Table '{self.name}' has a foreign key {fkey.column_name} that is also a time column. "
                            "Operation not allowed: a foreign key can not be a time column."
                        )

        if self.type == SDKTableType.EDGE:
            if len(self._column_schemas) != 2:
                raise ValueError(
                    f"❌ Table '{self.name}' of type edge has columns {self._column_schemas}. "
                    "GNNTables of type edge should have exactly two foreign key columns. "
                )
            if self.foreign_keys is None or len(self.foreign_keys) != 2:
                raise ValueError(
                    f"❌ Table '{self.name}' of type edge has foreign keys {self.foreign_keys}. "
                    "GNNTables of type edge should have exactly two foreign keys."
                )

    def show_table(self):
        """Pretty Print formatted table schema information."""

        # Table header
        print(f"\nTable: {self.name}")
        print(f"Source: {self.source}")
        print(f"Type: {self.type.value}")

        # Prepare and print column information using tabulate
        headers = [
            "Column Name",
            "Data Type",
            "Format",
            "Is Feature",
            "Is Candidate Key",
            "Is Foreign Key",
            "Link to",
            "Is Time Column",
        ]

        ck_map = {ck.column_name: {"is_feature": ck.is_feature} for ck in self.candidate_keys}
        fk_map = {fk.column_name: {"link_to": fk.link_to, "is_feature": fk.is_feature} for fk in self.foreign_keys}

        table = []
        for col_name, col in self._column_schemas.items():
            # Default: feature unless explicitly disabled in CK/FK
            is_feature = True
            if col_name in ck_map and ck_map[col_name]["is_feature"] is False:
                is_feature = False
            if col_name in fk_map and fk_map[col_name]["is_feature"] is False:
                is_feature = False

            link_to = ""
            if col_name in fk_map:
                link_to = fk_map[col_name]["link_to"]

            row = {
                "Column Name": col_name,
                "Data Type": col.dtype,
                "Format": col.format if col.format is not None else "",
                "Is Feature": True if is_feature else "",
                "Is Candidate Key": True if col_name in ck_map else "",
                "Is Foreign Key": True if col_name in fk_map else "",
                "Foreign Key -> Link to": link_to,
                "Is Time Column": True if col_name == self.time_column else "",
            }
            table.append(list(row.values()))

        # print columns whose dtype could not be inferred
        for col in self._columns_without_dtypes:
            row = {
                "Column Name": col,
                "Data Type": "Not defined",
                "Format": "",
                "Is Feature": "",
                "Is Candidate Key": "",
                "Is Foreign Key": "",
                "Foreign Key -> Link to": "",
            }
            table.append(list(row.values()))

        print(tabulate(table, headers=headers, tablefmt="grid"))

    def _create_table_schema(self, validate: bool = True) -> TableSchema:
        """Create the table metadata."""
        if validate:
            self.validate_table()
        table_schema = TableSchema(
            name=self.name,
            source=self.source,
            columns=list(self._column_schemas.values()),
            time_column=self.time_column,
        )
        return table_schema

    def _check_column_existence_on_init(self, col_name: str):
        """
        Checks if the col_name exists on the sample data dataframe, throws an assertion error if it does not exist.

        Called only upon class initialization
        Args:
            col_name (str): The name of the column
        Raise:
            ValueError: If col_name does not exist in the data
        """
        if col_name not in self.column_names:
            raise ValueError(f"❌ Column: {col_name} does not exist in the data")

    def _request_data(self):
        """
        Ping the rest API to fetch data.

        Args:
            timeout (int): Timeout in seconds to await for the request to return data
        Returns:
            columns (List[str]): A list with the column names
            column_dtypes (Dict[str, ColumnDType]): A dict with the column dtypes
                that where successfully infered (if we can not infer a column dtype
                then that column will not appear in this dictionary)
        """
        payload = {
            "payload_type": "FETCH_TABLE",
            "source": self.source,
            "connector": self.connector.connector_type,
        }

        json_data = self.api_handler.make_request(payload, [self.source])
        column_names = json_data["columns"]
        column_dtypes = json_data["dtypes"]
        return column_names, column_dtypes

    def _raise_error_col_not_in_meta(self, col_name: str):
        """
        Raise value error if column name is not in GNN table metadata
        Args:
            col_name (str): The column name
        """
        raise ValueError(
            f"❌ {col_name} is not part of the GNN table "
            f"GNN Table columns: {self._column_schemas.keys()} "
            f"Columns not part of the GNN table: {self._discarded_columns | self._columns_without_dtypes}"
        )

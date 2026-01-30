import json
from typing import Dict, Optional

import snowflake.connector
from pydantic import BaseModel, Field, PrivateAttr, model_validator
from snowflake.snowpark import Session

from relationalai_gnns.common.exceptions import ConnectionError, ValidationError
from relationalai_gnns.common.export import OutputConfig

from .provider import Provider

ENGINE_TYPE_GNN = "ML"


class BaseConnector(BaseModel):
    """Base class for all connector types."""

    connector_type: str
    headers: Dict = Field(default_factory=dict)
    is_native_app: bool = False
    endpoint_url: Optional[str] = None


class LocalConnector(BaseConnector):
    """Connector for establishing a local connection."""

    connector_type: str
    port: Optional[int] = None
    url: Optional[str] = None

    @model_validator(mode="after")
    def validate_url_configuration(self) -> "LocalConnector":
        """Ensures proper URL configuration and builds endpoint_url if needed."""
        if not self.endpoint_url:
            if not (self.url and self.port):
                raise ValidationError("Either endpoint_url or both url and port must be provided")
            self.endpoint_url = f"{self.url}:{self.port}"
        return self


class SnowflakeConnectorDirectAccess(BaseConnector):
    """Connector for Snowflake with direct access."""

    # Fixed connector properties
    connector_type: str = Field(default="snowflake", frozen=True)

    # Credential properties
    user: str
    password: str
    account: str
    # Configuration properties
    endpoint_url: Optional[str] = None
    # Request properties
    headers: Dict[str, str] = Field(default_factory=dict, exclude=True)
    # Private properties - not included in serialization
    _session: Optional[Session] = PrivateAttr(default=None)

    class Config:
        arbitrary_types_allowed = True

    @model_validator(mode="after")
    def infer_headers(self) -> "SnowflakeConnector":
        """Automatically retrieves and sets Snowflake authentication token."""
        try:
            # Prepare token for the request headers
            ctx = snowflake.connector.connect(
                user=self.user,
                password=self.password,
                account=self.account,
                session_parameters={"PYTHON_CONNECTOR_QUERY_RESULT_FORMAT": "json"},
            )

            # Fetch session token
            token_data = ctx._rest._token_request("ISSUE")
            token = token_data.get("data", {}).get("sessionToken")

            if not token:
                raise ConnectionError("Failed to retrieve session token from Snowflake")

            # Set authentication header
            self.headers = {"Authorization": f'Snowflake Token="{token}"'}

        except Exception:
            raise ConnectionError(
                "❌ Failed to connect to Snowflake. Please check your credentials and connection settings."
            )

        return self


class SnowflakeConnector(BaseConnector, Provider):
    """Connector for Snowflake."""

    # Fixed connector properties
    connector_type: str = Field(default="snowflake", frozen=True)

    # Credential properties
    user: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    account: Optional[str] = None
    warehouse: Optional[str] = None
    app_name: Optional[str] = None
    auth_method: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    oauth_token: Optional[str] = None
    host: Optional[str] = None

    # Configuration properties
    engine_name: Optional[str] = None
    is_native_app: bool = True

    # Private properties - not included in serialization
    _session: Optional[Session] = PrivateAttr(default=None)

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context) -> None:
        """Post-initialization hook for model setup."""
        self._initialize_session()
        self._check_engine_availability()

    def _check_engine_availability(self):
        """Verify that the engine exists and is in READY state."""
        try:
            engine_details = self._get_gnn_engine_details(self.engine_name)
            engine_status = engine_details[0]["STATUS"]

            if engine_status != "READY":
                raise ConnectionError(f"Engine '{self.engine_name}' is not ready (status: {engine_status})")

        except Exception:
            raise ConnectionError(
                f"Engine '{self.engine_name}' is not available. Please ensure it exists and is in READY state."
            )

    def cancel_job(self, job_id: str):
        """Cancel a running job by job_id."""
        res = self._exec(f"CALL {self.app_name}.experimental.cancel_job('{ENGINE_TYPE_GNN}', '{job_id}');")
        return res

    def exec_job(self, payload: dict, tables: Optional[list[str]] = None):
        """Execute an asynchronous job with optional table references."""
        # Convert payload to JSON
        payload_json = json.dumps(payload)

        references = []
        if tables:
            # Check access to all tables first
            for table_path in tables:
                if not self._check_table_access(table_path):
                    raise PermissionError(
                        f"Cannot access table '{table_path}'. "
                        f"Verify the table exists and you have the required permissions."
                    )

            references_tables = [
                f"{self.app_name}.api.object_reference('{self._get_object_type(table_path)}', '{table_path}')"
                for table_path in tables
            ]
            references = f"[{', '.join(references_tables)}]"

        # Execute the async job
        sql_query = f"CALL {self.app_name}.experimental.exec_job_async('{ENGINE_TYPE_GNN}', '{self.engine_name}', \
                    '{payload_json}', {references})"

        # results will contain (job_id, state, data)
        results = self._exec(sql_query)

        # Extract job information
        data = results[0].DATA
        data = json.loads(data)
        return data

    def _check_table_access(self, table_path: str) -> bool:
        """Check if we have access to a specific table."""
        try:
            # Attempt a minimal query to verify access
            check_query = f"SELECT 1 FROM {table_path} LIMIT 0"
            self._exec(check_query)
            return True
        except Exception:
            return False

    def get_job_metadata(self, job_id: str):
        """Retrieve metadata for a specific job."""
        res = self._exec(f"CALL {self.app_name}.experimental.get_job_metadata('{ENGINE_TYPE_GNN}', '{job_id}');")
        res_metadata = json.loads(res[0]["RESULT_METADATA"])
        return res_metadata

    def get_job_events(self, job_id: str, continuation_token: str = ""):
        """Get job events with optional continuation token."""
        results = self._exec(
            f"SELECT {self.app_name}.experimental.get_job_events('{ENGINE_TYPE_GNN}', '{job_id}', '{continuation_token}');"
        )
        if not results:
            return {"events": [], "continuation_token": None}
        row = results[0][0]
        return json.loads(row)

    def get_job(self, job_id: str):
        """Get job details by job_id."""
        results = self._exec(f"CALL {self.app_name}.experimental.get_job('{ENGINE_TYPE_GNN}', '{job_id}');")
        return self.job_list_to_dicts(results)

    def list_jobs(self, state=None, limit=None):
        """List jobs filtered by state and/or limited in number."""
        state_clause = f"AND STATE = '{state.upper()}'" if state else ""
        limit_clause = f"LIMIT {limit}" if limit else ""
        results = self._exec(
            f"SELECT ID,STATE,CREATED_BY,CREATED_ON,FINISHED_AT,DURATION,PAYLOAD,ENGINE_NAME \
            FROM {self.app_name}.experimental.jobs \
            where type='{ENGINE_TYPE_GNN}' {state_clause} ORDER BY created_on DESC {limit_clause};"
        )
        return self.job_list_to_dicts(results)

    def _get_gnn_engine_details(self, name: str):
        """Get the GNN engine details by name."""
        results = self._exec(f"CALL {self.app_name}.experimental.get_engine('{ENGINE_TYPE_GNN}', '{name}');")
        return results

    @staticmethod
    def job_list_to_dicts(results):
        """Convert job list results to a list of dictionaries."""
        if not results:
            return []
        return [
            {
                "job_id": row["ID"],
                "status": row["STATE"],
                "created_by": row["CREATED_BY"],
                "created_on": row["CREATED_ON"],
                "finished_at": row["FINISHED_AT"],
                "duration": row["DURATION"] if "DURATION" in row else 0,
                "engine": row["ENGINE_NAME"],
                "payload_type": json.loads(row["PAYLOAD"])["payload_type"],
            }
            for row in results
        ]

    def _get_object_type(self, fully_qualified_name: str) -> str | None:
        """Determines if the given Snowflake object is a TABLE or VIEW."""
        parts = fully_qualified_name.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid fully qualified name: {fully_qualified_name}")

        database, schema, object_name = (part.upper() for part in parts)

        sql = f"""
            SELECT TABLE_TYPE
            FROM {database}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = '{object_name}'
        """

        result = self._exec(sql)

        if result:
            object_type = result[0]["TABLE_TYPE"]
            # Normalize "BASE TABLE" to "TABLE"
            if object_type == "BASE TABLE":
                return "TABLE"
            # Return the object type as-is for other types (e.g., "VIEW").
            return object_type
        # If no results were returned, return None to indicate the object was not found.
        return None

    def _get_views_with_job_id(self, job_id: str):
        """Get all views that contain a specific job id."""
        job_id = job_id.replace("-", "_")
        result = self._exec(f"SHOW VIEWS IN SCHEMA {self.app_name}.RESULTS")
        secure_view_names = [f"{self.app_name}.RESULTS.{row['name']}" for row in result]

        matching_views = []
        for secure_view in secure_view_names:
            if job_id.upper() in secure_view.upper():
                matching_views.append(secure_view)

        return matching_views

    def materialize_job_results(self, job_id: str, output_config: OutputConfig) -> None:
        """Materialize all secure views related to the given job_id into tables in the specified output config."""
        source_views = self._get_views_with_job_id(job_id)
        job_id_normalized = job_id.replace("-", "_").upper()

        for source_view in source_views:
            view_name = source_view.split(".")[-1]
            table_name = view_name.split(f"{job_id_normalized}_")[-1]

            dest_table = (
                f"{output_config.settings.database_name}." f"{output_config.settings.schema_name}." f"{table_name}"
            )

            sql = f"CREATE TABLE {dest_table} AS SELECT * FROM {source_view}"
            self._exec(sql)

    def materialize_view_as_table(self, source_view: str, output_config: OutputConfig) -> None:
        """Materialize a secure view into table in the specified output config."""
        view_name = source_view.split(".")[-1]
        dest_table = f"{output_config.settings.database_name}." f"{output_config.settings.schema_name}." f"{view_name}"

        sql = f"CREATE TABLE {dest_table} AS SELECT * FROM {source_view}"
        self._exec(sql)

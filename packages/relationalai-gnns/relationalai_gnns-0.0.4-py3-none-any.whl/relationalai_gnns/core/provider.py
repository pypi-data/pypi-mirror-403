import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from cryptography.hazmat.primitives import serialization
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.exceptions import SnowparkSQLException

from relationalai_gnns.common.exceptions import ValidationError

ENGINE_TYPE_GNN = "ML"


class Provider:
    def __init__(
        self,
        account: Optional[str] = None,
        warehouse: Optional[str] = None,
        app_name: Optional[str] = None,
        user: Optional[str] = None,
        role: Optional[str] = None,
        auth_method: str = "password",
        password: Optional[str] = None,
        private_key_path: Optional[Union[str, Path]] = None,
        private_key_passphrase: Optional[str] = None,
        oauth_token: Optional[str] = None,
        host: Optional[str] = None,
    ):
        """
        Initialize a new Provider instance with support for multiple authentication methods.

        :param account: Snowflake account identifier.
        :type account: Optional[str]
        :param warehouse: Snowflake warehouse.
        :type warehouse: Optional[str]
        :param app_name: Snowflake Native app name.
        :type app_name: Optional[str]
        :param user: Snowflake username (required for password and key_pair auth).
        :type user: Optional[str]
        :param role: Snowflake role.
        :type role: Optional[str]
        :param auth_method: Authentication method ('password', 'key_pair', 'browser', 'oauth' or 'active_session'). Use
            'active_session' when executing inside a Snowflake notebook. When using 'active_session', account, password,
            warehouse, and user need not to be set. Defaults to 'password'.
        :type auth_method: str
        :param password: Snowflake password (required if auth_method is 'password').
        :type password: Optional[str]
        :param private_key_path: Path to private key file (required if auth_method is 'key_pair').
        :type private_key_path: Optional[Union[str, Path]]
        :param private_key_passphrase: Optional passphrase for encrypted private key.
        :type private_key_passphrase: Optional[str]
        :param oauth_token: OAuth access token (required if auth_method is 'oauth').
        :type oauth_token: Optional[str]
        :param host: Optional Snowflake host for OAuth authentication.
        :type host: Optional[str]
        """
        self.account = account
        self.warehouse = warehouse
        self.app_name = app_name
        self.user = user
        self.role = role
        self.auth_method = auth_method.lower()
        self.password = password
        self.private_key_path = private_key_path
        self.private_key_passphrase = private_key_passphrase
        self.oauth_token = oauth_token
        self.host = host

        # Validate authentication parameters
        if self.auth_method not in ["password", "key_pair", "browser", "oauth", "active_session"]:
            raise ValueError(
                "❌ auth_method must be one of: 'password', 'key_pair', 'browser', 'oauth', 'active_session'"
            )

        if self.auth_method == "password":
            if not user:
                raise ValueError("❌ Username is required when using password authentication")
            if not password:
                raise ValueError("❌ Password is required when using password authentication")

        elif self.auth_method == "key_pair":
            if not user:
                raise ValueError("❌ Username is required when using key pair authentication")
            if not private_key_path:
                raise ValueError("❌ Private key path is required when using key pair authentication")

        elif self.auth_method == "oauth":
            if not oauth_token:
                raise ValueError("❌ OAuth token is required when using OAuth authentication")

        elif self.auth_method == "active_session":
            if not app_name:
                raise ValueError("❌ app_name is required when using 'active_session authentication")

        self._initialize_session()

    def _load_private_key(self) -> bytes:
        """
        Load and process private key from file.

        Returns:
            bytes: The private key in bytes format required by Snowflake
        """
        try:
            with open(self.private_key_path, "rb") as f:
                p_key = serialization.load_pem_private_key(
                    f.read(),
                    password=(self.private_key_passphrase.encode() if self.private_key_passphrase else None),
                )

            return p_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        except Exception as e:
            raise ValueError(f"❌ Failed to load private key: {str(e)}")

    def _initialize_session(self) -> None:
        """
        Initialize a Snowflake session using provided connection parameters.

        If initialization fails, sets the session to None.
        """
        try:
            if self.auth_method == "active_session":
                self._session = get_active_session()
                if self.role:
                    self._session.use_role(self.role)
                self.user = self._session.get_current_user().replace('"', "")
            else:
                self._session = Session.builder.configs(self._get_connection_params()).create()
        except Exception as e:
            raise ValueError(f"❌ Error initializing Snowflake session: {e}")

    def _get_connection_params(self) -> Dict[str, str]:
        """
        Build the Snowflake connection parameters based on authentication method.

        Returns:
            Dict[str, str]: Dictionary containing connection parameters.
        """
        connection_parameters = {
            "account": self.account,
            "warehouse": self.warehouse,
            "role": self.role,
        }

        # Add user if provided (required for password and key_pair auth)
        if self.user:
            connection_parameters["user"] = self.user

        if self.auth_method == "password":
            connection_parameters["password"] = self.password

        elif self.auth_method == "key_pair":
            connection_parameters.update(
                {
                    "private_key": self._load_private_key(),
                    "authenticator": "SNOWFLAKE_JWT",
                }
            )

        elif self.auth_method == "browser":
            connection_parameters["authenticator"] = "externalbrowser"

        else:  # oauth
            connection_parameters.update({"authenticator": "oauth", "token": self.oauth_token})
            if self.host:
                connection_parameters["host"] = self.host

        return connection_parameters

    def _exec(
        self,
        code: str,
    ) -> Any:
        """
        Execute a SQL statement in Snowflake and return the result.

        Args:
            code (str): SQL code to execute.

        Returns:
            Any: Result of the query execution.
        """
        if not self._session:
            self._initialize_session()

        try:
            sess_results = self._session.sql(code)
            return sess_results.collect()
        except Exception as e:
            raise e

    def delete_gnn(self, name: str):
        """
        Delete a GNN engine.

        :param name: Name of the GNN engine to delete.
        :type name: str
        :raises: Exception if the GNN engine is not found or deletion fails.
        """
        try:
            self._exec(f"CALL {self.app_name}.experimental.delete_engine('{ENGINE_TYPE_GNN}', '{name}');")
            return True
        except SnowparkSQLException as e:
            # Check if the error is specifically about engine not found
            if "engine not found" in str(e).lower():
                print(f"❌ GNN engine {name} not found")
                return False  # This is fine
            else:
                # Re-raise other SnowparkSQLExceptions
                raise
        except Exception:
            # Handle any other unexpected exceptions
            raise RuntimeError(
                f"Failed to delete GNN engine '{name}'. Please check if you have " f"sufficient permissions."
            )

    def resume_gnn(self, name: str):
        """
        Resume a previously created GNN engine.

        :param name: Name of the GNN engine to resume.
        :type name: str
        :raises: Exception if the GNN engine is not found or resume fails.
        """
        try:
            self._exec(f"CALL {self.app_name}.experimental.resume_engine_async('{ENGINE_TYPE_GNN}', '{name}');")
            return True
        except SnowparkSQLException as e:
            # Check if the error is specifically about engine not found
            if "engine not found" in str(e).lower():
                raise ValidationError(f"GNN engine '{name}' not found")
            else:
                # Re-raise other SnowparkSQLExceptions
                raise
        except Exception:
            # Handle any other unexpected exceptions
            raise RuntimeError(
                f"❌ Failed to resume GNN engine '{name}'. Please check if the engine exists and is in a resumable state."
            )

    def get_gnn(self, name: str):
        """
        Retrieve details of a specific GNN engine.

        :param name: Name of the GNN engine to fetch.
        :type name: str
        :returns: A dictionary containing the engine's details, or None if not found.
        :rtype: dict or None
        :raises: Exception if retrieval fails for reasons other than engine not found.
        """
        try:
            results = self._exec(f"CALL {self.app_name}.experimental.get_engine('{ENGINE_TYPE_GNN}', '{name}');")
            return self.gnn_list_to_dicts(results)[0]
        except SnowparkSQLException as e:
            # Check if the error is specifically about engine not found
            if "engine not found" in str(e).lower():
                return None
            else:
                # Don't expose internal error details
                raise RuntimeError(f"Failed to retrieve GNN engine '{name}'. Please check your permissions.")
        except Exception:
            # Handle any other unexpected exceptions without exposing internal details
            raise RuntimeError(
                f"Failed to get GNN engine '{name}'. Please check if the engine exists and you have access permissions."
            )

    def create_gnn(
        self,
        name: str,
        size: Optional[str] = "HIGHMEM_X64_S",
        settings: Optional[Dict] = None,
        flag_async: bool = False,
    ):
        """
        Create a new GNN engine in Snowflake.

        Parameters:
            name (str): Name of the GNN engine to create.
            size (Optional[str], default="HIGHMEM_X64_S"): Size specification for the engine.
                Supported values include "HIGHMEM_X64_S" and "GPU_NV_S". Default: "HIGHMEM_X64_S"
            settings (Optional[Dict], default=None): Additional engine settings. For example,
                to set the auto-suspend time, use: {"auto_suspend_mins": 15}.
            flag_async (bool): If the GNN engine creation is async. Default: False

        Raises:
            Exception: If the GNN engine already exists or creation fails.
        """
        if settings is None:
            settings = {}

        engine_config: Dict[str, Any] = settings

        try:
            if flag_async:
                # no need not expose this option in external documentation
                self._exec(
                    f"CALL {self.app_name}.experimental.create_engine_async(\
                    '{ENGINE_TYPE_GNN}', '{name}', '{size}', {engine_config});"
                )
            else:
                self._exec(
                    f"CALL {self.app_name}.experimental.create_engine(\
                    '{ENGINE_TYPE_GNN}', '{name}', '{size}', {engine_config});"
                )
            return True
        except SnowparkSQLException as e:
            # Check if the error is specifically about engine already exists
            if "engine already exists" in str(e).lower():
                raise ValidationError(f"GNN engine '{name}' already exists")
            else:
                # Re-raise other SnowparkSQLExceptions
                raise
        except Exception:
            # Handle any other unexpected exceptions
            raise RuntimeError(
                f"❌ Failed to create GNN engine '{name}'. Please check your permissions and that the name is unique."
            )

    def list_gnns(self, state: Optional[str] = None):
        """
        List available GNN engines, optionally filtered by state.

        :param state: Optional status filter (e.g., "RUNNING", "STOPPED"). Defaults to None.
        :type state: Optional[str]
        :returns: A list of dictionaries containing engine details.
        :rtype: List[Dict]
        """

        where_clause = f"WHERE TYPE='{ENGINE_TYPE_GNN}'"
        where_clause = f"{where_clause} AND STATUS = '{state.upper()}'" if state else where_clause
        statement = f"SELECT NAME,ID,SIZE,STATUS,CREATED_BY,CREATED_ON,UPDATED_ON,SETTINGS \
                    FROM {self.app_name}.experimental.engines {where_clause};"
        results = self._exec(statement)
        return self.gnn_list_to_dicts(results)

    @staticmethod
    def gnn_list_to_dicts(results):
        """Convert raw Snowflake engine query results to a list of structured dictionaries."""
        if not results:
            return []

        processed_results = []

        for row in results:
            simplified_settings = {}
            if row["SETTINGS"]:
                for endpoint_name, endpoint_info in json.loads(row["SETTINGS"]).items():
                    if endpoint_name == "mlflowendpoint":
                        if isinstance(endpoint_info, dict) and "ingress_url" in endpoint_info:
                            simplified_settings[endpoint_name] = f"https://{endpoint_info['ingress_url']}"

            processed_row = {
                "name": row["NAME"],
                "id": row["ID"],
                "size": row["SIZE"],
                "state": row["STATUS"],
                "created_by": row["CREATED_BY"],
                "created_on": row["CREATED_ON"],
                "updated_on": row["UPDATED_ON"],
                "settings": simplified_settings,
            }

            processed_results.append(processed_row)

        return processed_results

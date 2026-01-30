import uuid
from typing import Dict

import requests

from relationalai_gnns.common.exceptions import ValidationError

from .connector import BaseConnector, Optional
from .utils import extract_error_message, wrap_user


class APIRequestHandler:
    """Handles making API requests to the backend connector and parsing error responses in a consistent way."""

    def __init__(self, connector: "BaseConnector"):
        """
        Initialize the APIRequestHandler with a connector.

        Args:
            connector (BaseConnector): Connector to communicate with the backend service.
        """
        self.connector = connector
        self.router_url = f"{connector.endpoint_url}/v1alpha1/jobs/create"

    def make_request(self, payload: Dict, tables: Optional[list[str]] = None) -> Dict:
        """
        Make an API request with the given payload.

        Uses HTTP POST for non native app requests and falls back to connector's
        SQL stored procedure execution for native app.

        Args:
            payload (Dict): The JSON payload to send.
            tables (List[str]): Tables to submit for processing and retrieve references for.

        Returns:
            Dict: The JSON response data from the API.
        """
        try:
            if not self.connector.is_native_app:
                job_id = str(uuid.uuid4())
                url = f"{self.router_url}/{job_id}"

                response = requests.post(url, json=wrap_user(payload), headers=self.connector.headers, timeout=60)
                response.raise_for_status()
                return response.json().get("data", {})

            # SQL stored procedure approach
            return self.connector.exec_job(payload, tables)

        except requests.RequestException as e:
            error_message = self._parse_request_exception(getattr(e, "response", None) or e)
            self._categorize_and_raise_error(error_message)

        except Exception as e:
            error_message = extract_error_message(str(e))
            self._categorize_and_raise_error(error_message)

    def _parse_request_exception(self, response) -> str:
        """
        Extracts and formats the error message from a failed requests response.

        Args:
            response: Can be a `requests.Response` or a `requests.RequestException`.

        Returns:
            str: Parsed error message or a fallback string if parsing fails.
        """
        # If response is an exception, get the underlying response object
        http_response = getattr(response, "response", response)

        try:
            if hasattr(http_response, "json"):
                return http_response.json().get("detail", "No detail provided")
            else:
                return str(http_response)
        except (ValueError, AttributeError):
            return "Failed to parse error response"

    def _is_validation_error(self, error_message: str) -> bool:
        """Check if the error message indicates a validation/configuration issue."""
        validation_patterns = [
            "insufficient parameters",
            "not found",
            "invalid parameter",
            "missing required",
            "unsupported",
            "bad request",
        ]

        return any(pattern in error_message for pattern in validation_patterns)

    def _categorize_and_raise_error(self, error_message: str) -> None:
        """
        Categorize the error and raise the appropriate exception type.

        Args:
            error_message: The error message to categorize and raise

        Raises:
            ValidationError: For user-fixable parameter/configuration issues
            RuntimeError: For system/network errors
        """
        if self._is_validation_error(error_message):
            raise ValidationError(error_message)
        else:
            raise RuntimeError(error_message)

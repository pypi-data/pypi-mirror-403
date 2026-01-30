"""
Custom exception classes for user-friendly error handling in the GNN SDK.

These exceptions are designed to provide clear, actionable error messages to users while maintaining internal debugging
capabilities.
"""


# ----------------------
# GNN-related Exceptions
# ----------------------


class GNNError(Exception):
    """Base exception for all GNN-related errors."""

    pass


class ValidationError(GNNError):
    """
    Raised when user input or configuration validation fails.

    Used for issues like:
    - Missing required configuration fields
    - Invalid parameter values
    - Malformed dataset metadata
    """

    pass


class ConnectionError(GNNError):
    """
    Raised when database or API connection issues occur.

    Used for issues like:
    - Snowflake connection failures
    - API endpoint unreachable
    - Authentication failures
    """

    pass


class InternalError(GNNError):
    """
    Raised when internal system errors occur.

    Used for issues like:
    - Unexpected model training failures
    - Internal processing errors
    - System resource issues
    """

    pass


# ----------------------
# Job-related Exceptions
# ----------------------


class ModelManagerError(Exception):
    """Raised when an operation in the model manager fails."""

    pass


class JobError(Exception):
    """Base class for job-related exceptions with optional error codes."""

    def __init__(self, message: str, code: str = None):
        self.code = code
        super().__init__(message)


class JobManagerError(JobError):
    """Error raised by JobManager."""


class JobHandlerError(JobError):
    """Error raised by JobHandler."""


class JobMonitorError(JobError):
    """Error raised by JobMonitor."""

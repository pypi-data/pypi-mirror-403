"""
Caliper Exceptions

Re-exports common errors and adds Caliper-specific exceptions.
"""

from timeback_common import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimebackError,
    ValidationError,
)


class UnsupportedOperationError(APIError):
    """Raised when an operation is not supported on the current platform."""

    def __init__(self, operation: str) -> None:
        super().__init__(
            f"{operation}() is not supported on this platform",
            status_code=None,
        )


class JobFailedError(APIError):
    """Raised when a job fails during wait_for_completion."""

    def __init__(self, job_id: str, error: str | None = None) -> None:
        self.job_id = job_id
        message = f"Job {job_id} failed"
        if error:
            message += f": {error}"
        super().__init__(message)


__all__ = [
    "APIError",
    "AuthenticationError",
    "ForbiddenError",
    "JobFailedError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimebackError",
    "UnsupportedOperationError",
    "ValidationError",
]

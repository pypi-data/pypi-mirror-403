"""
Verlex Error Types

All errors that can be raised by the Verlex client SDK.
"""


class VerlexError(Exception):
    """Base exception for all Verlex errors."""
    pass


class AuthenticationError(VerlexError):
    """Authentication failed."""
    pass


class NotAuthenticatedError(AuthenticationError):
    """Not authenticated - need to call auth() or provide api_key."""
    pass


class InvalidAPIKeyError(AuthenticationError):
    """Invalid API key provided."""
    pass


class ExecutionError(VerlexError):
    """Error during job execution."""
    pass


class JobFailedError(ExecutionError):
    """Job execution failed."""

    def __init__(self, job_id: str, message: str, logs: str = ""):
        self.job_id = job_id
        self.logs = logs
        super().__init__(f"Job {job_id} failed: {message}")


class JobTimeoutError(ExecutionError):
    """Job exceeded timeout."""

    def __init__(self, job_id: str, timeout_seconds: int):
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Job {job_id} timed out after {timeout_seconds} seconds")


class SerializationError(VerlexError):
    """Failed to serialize function or result."""
    pass


class NetworkError(VerlexError):
    """Network communication error."""
    pass


class RateLimitError(VerlexError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class InsufficientCreditsError(VerlexError):
    """Not enough credits to run the job."""

    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient credits: need ${required:.2f}, have ${available:.2f}. "
            f"Add credits at https://verlex.dev/billing"
        )


class QuotaExceededError(VerlexError):
    """Account quota exceeded."""
    pass


class GPUUnavailableError(VerlexError):
    """Requested GPU type is not available."""

    def __init__(self, gpu_type: str, available_types: list = None):
        self.gpu_type = gpu_type
        self.available_types = available_types or []
        msg = f"GPU type '{gpu_type}' is not available"
        if self.available_types:
            msg += f". Available: {', '.join(self.available_types)}"
        super().__init__(msg)


class ConfigurationError(VerlexError):
    """Invalid configuration."""
    pass

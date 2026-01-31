"""
Verlex - Run your code in the cloud for the price of a coffee.

A Python SDK that lets you execute code on the cheapest available cloud
infrastructure across AWS, GCP, and Azure - all with a single function call.

Usage:
    >>> import verlex
    >>>
    >>> with verlex.GateWay(api_key="gw_your_key") as gw:
    ...     result = gw.run(my_function)
    ...     print(result)

Quick one-liner:
    >>> result = verlex.cloud(my_function, api_key="gw_your_key")
"""

__version__ = "0.1.0"
__author__ = "Verlex Team"

# Primary API - Context Manager
from verlex.client import (
    GateWay,
    AsyncJob,
    JobResult,
    AuthSession,
)

# Module-level functions
from verlex.client import (
    auth,
    logout,
    whoami,
    get_session,
    cloud,
)

# Error types
from verlex.errors import (
    VerlexError,
    ExecutionError,
    AuthenticationError,
    NotAuthenticatedError,
    InvalidAPIKeyError,
    InsufficientCreditsError,
    QuotaExceededError,
    GPUUnavailableError,
    JobFailedError,
    JobTimeoutError,
    SerializationError,
    NetworkError,
    RateLimitError,
    ConfigurationError,
)

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Primary API
    "GateWay",
    "AsyncJob",
    "JobResult",
    "AuthSession",

    # Authentication
    "auth",
    "logout",
    "whoami",
    "get_session",

    # Quick execution
    "cloud",

    # Error Types
    "VerlexError",
    "ExecutionError",
    "AuthenticationError",
    "NotAuthenticatedError",
    "InvalidAPIKeyError",
    "InsufficientCreditsError",
    "QuotaExceededError",
    "GPUUnavailableError",
    "JobFailedError",
    "JobTimeoutError",
    "SerializationError",
    "NetworkError",
    "RateLimitError",
    "ConfigurationError",
]

"""
Verlex Client - Thin HTTP client for Verlex cloud execution.

All logic runs on the Verlex backend. This client just serializes
functions and sends them to the API.
"""

from __future__ import annotations

import os
import time
import base64
import threading
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass

import httpx
import cloudpickle

from verlex.errors import (
    VerlexError,
    AuthenticationError,
    NotAuthenticatedError,
    InvalidAPIKeyError,
    ExecutionError,
    JobFailedError,
    JobTimeoutError,
    SerializationError,
    NetworkError,
    RateLimitError,
    InsufficientCreditsError,
    GPUUnavailableError,
)

T = TypeVar('T')

# Default API URL
DEFAULT_API_URL = "https://api.verlex.dev"

# Global session state
_current_session: Optional["AuthSession"] = None


@dataclass
class AuthSession:
    """Authentication session state."""
    api_key: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    tier: str = "free"
    priority: bool = True
    flexible: bool = True


@dataclass
class JobResult:
    """Result of a cloud execution."""
    value: Any
    job_id: str
    provider: Optional[str] = None
    region: Optional[str] = None
    instance_type: Optional[str] = None
    execution_time_seconds: float = 0.0
    cost: float = 0.0

    def __repr__(self) -> str:
        return f"JobResult(value={self.value!r}, job_id='{self.job_id}', cost=${self.cost:.4f})"


class GateWay:
    """
    Verlex GateWay - Run your code in the cloud.

    Usage:
        >>> import verlex
        >>>
        >>> with verlex.GateWay(api_key="gw_xxx") as gw:
        ...     result = gw.run(my_function)
        ...     print(result)

    Pricing modes:
        priority=True:  +25% margin, immediate execution
        priority=False: +12% margin, up to 10 min wait

    Migration:
        flexible=True:  Can migrate between providers for savings
        flexible=False: Sticky - stay on one provider
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        priority: bool = True,
        flexible: bool = True,
        api_url: Optional[str] = None,
        timeout: int = 3600,
        verbose: bool = True,
    ):
        """
        Initialize GateWay client.

        Args:
            api_key: Your Verlex API key. If not provided, uses VERLEX_API_KEY env var.
            priority: True = immediate (+25%), False = patient (+12%)
            flexible: True = can migrate, False = sticky
            api_url: API URL (defaults to https://api.verlex.dev)
            timeout: Default job timeout in seconds
            verbose: Print status messages
        """
        self.api_key = api_key or os.getenv("VERLEX_API_KEY")
        self.priority = priority
        self.flexible = flexible
        self.api_url = api_url or os.getenv("VERLEX_API_URL", DEFAULT_API_URL)
        self.default_timeout = timeout
        self.verbose = verbose

        self._client: Optional[httpx.Client] = None
        self._session: Optional[AuthSession] = None
        self._active = False
        self._jobs: List[str] = []

    def __enter__(self) -> "GateWay":
        """Enter context - authenticate and prepare client."""
        if not self.api_key:
            raise NotAuthenticatedError(
                "No API key provided. Either pass api_key parameter or set VERLEX_API_KEY environment variable."
            )

        if self.verbose:
            print("Verlex - Initializing cloud execution...")

        # Create HTTP client
        self._client = httpx.Client(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        # Validate API key
        try:
            response = self._client.get("/v1/auth/me")
            if response.status_code == 401:
                raise InvalidAPIKeyError("Invalid API key")
            elif response.status_code == 200:
                data = response.json()
                self._session = AuthSession(
                    api_key=self.api_key,
                    user_id=data.get("user_id"),
                    email=data.get("email"),
                    tier=data.get("tier", "free"),
                    priority=self.priority,
                    flexible=self.flexible,
                )
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to connect to Verlex API: {e}")

        self._active = True

        if self.verbose:
            mode = "priority" if self.priority else "patient"
            flex = "flexible" if self.flexible else "sticky"
            print(f"   Ready | Mode: {mode}, {flex}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context - cleanup."""
        self._active = False

        if self._client:
            self._client.close()
            self._client = None

        if self.verbose and self._jobs:
            print(f"\nVerlex session complete. Jobs: {len(self._jobs)}")

        return False

    def _ensure_active(self) -> None:
        """Ensure we're inside an active context."""
        if not self._active:
            raise RuntimeError(
                "GateWay must be used as a context manager:\n"
                "    with verlex.GateWay(api_key='...') as gw:\n"
                "        result = gw.run(my_function)"
            )

    def run(
        self,
        func: Callable[..., T],
        *args,
        gpu: Optional[str] = None,
        gpu_count: int = 1,
        cpu: Optional[int] = None,
        memory: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> T:
        """
        Execute a function in the cloud and return the result.

        Args:
            func: The function to execute remotely
            *args: Arguments to pass to the function
            gpu: GPU type (e.g., "T4", "A100", "H100")
            gpu_count: Number of GPUs (default: 1)
            cpu: CPU cores (auto-detected if not specified)
            memory: Memory (e.g., "16GB", auto-detected if not specified)
            timeout: Timeout in seconds
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The return value of the function
        """
        self._ensure_active()

        # Serialize the function
        try:
            payload = cloudpickle.dumps((func, args, kwargs))
            payload_b64 = base64.b64encode(payload).decode("utf-8")
        except Exception as e:
            raise SerializationError(f"Failed to serialize function: {e}")

        # Build request
        request_data = {
            "payload": payload_b64,
            "priority": self.priority,
            "flexible": self.flexible,
            "timeout": timeout or self.default_timeout,
        }

        # Add resource requirements
        if gpu:
            request_data["gpu"] = gpu
            request_data["gpu_count"] = gpu_count
        if cpu:
            request_data["cpu"] = cpu
        if memory:
            request_data["memory"] = memory

        # Submit job
        try:
            response = self._client.post(
                "/v1/jobs/run",
                json=request_data,
                timeout=60.0,  # Longer timeout for job submission
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to submit job: {e}")

        if response.status_code == 401:
            raise InvalidAPIKeyError("Invalid API key")
        elif response.status_code == 402:
            data = response.json()
            raise InsufficientCreditsError(
                required=data.get("required", 0),
                available=data.get("available", 0),
            )
        elif response.status_code == 429:
            raise RateLimitError(retry_after=int(response.headers.get("Retry-After", 60)))
        elif response.status_code != 200:
            raise ExecutionError(f"Job submission failed: {response.text}")

        data = response.json()
        job_id = data.get("job_id")
        self._jobs.append(job_id)

        if self.verbose:
            print(f"   Job submitted: {job_id[:12]}...")

        # Poll for completion
        result = self._wait_for_job(job_id, timeout or self.default_timeout)
        return result

    def _wait_for_job(self, job_id: str, timeout: int) -> Any:
        """Poll for job completion and return result."""
        start_time = time.time()
        poll_interval = 1.0

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise JobTimeoutError(job_id, timeout)

            try:
                response = self._client.get(f"/v1/jobs/{job_id}/status")
            except httpx.RequestError as e:
                raise NetworkError(f"Failed to check job status: {e}")

            if response.status_code != 200:
                raise ExecutionError(f"Failed to get job status: {response.text}")

            data = response.json()
            status = data.get("status")

            if status == "completed":
                # Get result
                result_response = self._client.get(f"/v1/jobs/{job_id}/result")
                if result_response.status_code != 200:
                    raise ExecutionError(f"Failed to get result: {result_response.text}")

                result_data = result_response.json()
                result_b64 = result_data.get("result")

                if result_b64:
                    try:
                        result_bytes = base64.b64decode(result_b64)
                        return cloudpickle.loads(result_bytes)
                    except Exception as e:
                        raise SerializationError(f"Failed to deserialize result: {e}")
                return None

            elif status == "failed":
                error_msg = data.get("error", "Unknown error")
                logs = data.get("logs", "")
                raise JobFailedError(job_id, error_msg, logs)

            elif status in ("pending", "queued", "provisioning", "running"):
                # Still running, wait and poll again
                time.sleep(poll_interval)
                # Gradually increase poll interval
                poll_interval = min(poll_interval * 1.2, 5.0)
            else:
                raise ExecutionError(f"Unknown job status: {status}")

    def run_async(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> "AsyncJob[T]":
        """
        Submit a function for async execution (non-blocking).

        Returns an AsyncJob that can be awaited or polled.

        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments

        Returns:
            AsyncJob object
        """
        self._ensure_active()
        return AsyncJob(self, func, args, kwargs)

    def analyze(self, func: Callable) -> Dict[str, Any]:
        """
        Analyze a function to get resource recommendations.

        Args:
            func: The function to analyze

        Returns:
            Dictionary with CPU, memory, GPU recommendations
        """
        self._ensure_active()

        try:
            payload = cloudpickle.dumps(func)
            payload_b64 = base64.b64encode(payload).decode("utf-8")
        except Exception as e:
            raise SerializationError(f"Failed to serialize function: {e}")

        try:
            response = self._client.post(
                "/v1/analyze",
                json={"payload": payload_b64},
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to analyze function: {e}")

        if response.status_code != 200:
            raise ExecutionError(f"Analysis failed: {response.text}")

        return response.json()

    def estimate_cost(
        self,
        func: Callable,
        duration_hours: float = 1.0,
    ) -> Dict[str, float]:
        """
        Estimate execution cost.

        Args:
            func: The function to estimate
            duration_hours: Estimated duration in hours

        Returns:
            Dictionary with cost estimates
        """
        self._ensure_active()

        try:
            payload = cloudpickle.dumps(func)
            payload_b64 = base64.b64encode(payload).decode("utf-8")
        except Exception as e:
            raise SerializationError(f"Failed to serialize function: {e}")

        try:
            response = self._client.post(
                "/v1/estimate",
                json={
                    "payload": payload_b64,
                    "duration_hours": duration_hours,
                },
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to estimate cost: {e}")

        if response.status_code != 200:
            raise ExecutionError(f"Estimation failed: {response.text}")

        return response.json()

    @property
    def jobs(self) -> List[str]:
        """Get list of job IDs submitted in this session."""
        return self._jobs.copy()


class AsyncJob:
    """Handle for an asynchronously submitted job."""

    def __init__(
        self,
        gateway: GateWay,
        func: Callable,
        args: tuple,
        kwargs: dict,
    ):
        self._gateway = gateway
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result: Optional[Any] = None
        self._error: Optional[Exception] = None
        self._completed = False
        self._started = False
        self._thread: Optional[threading.Thread] = None
        self._job_id: Optional[str] = None

    def start(self) -> "AsyncJob":
        """Start the job execution in background."""
        if self._started:
            return self

        self._started = True
        self._thread = threading.Thread(target=self._execute, daemon=True)
        self._thread.start()
        return self

    def _execute(self) -> None:
        """Execute the job."""
        try:
            self._result = self._gateway.run(
                self._func,
                *self._args,
                **self._kwargs
            )
        except Exception as e:
            self._error = e
        finally:
            self._completed = True

    def result(self, timeout: Optional[float] = None) -> Any:
        """
        Wait for and return the result.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            The function's return value

        Raises:
            TimeoutError: If timeout exceeded
            Exception: If execution failed
        """
        if not self._started:
            self.start()

        if self._thread:
            self._thread.join(timeout=timeout)

        if not self._completed:
            raise TimeoutError(f"Job did not complete within {timeout} seconds")

        if self._error:
            raise self._error

        return self._result

    @property
    def completed(self) -> bool:
        """Check if the job has completed."""
        return self._completed

    @property
    def job_id(self) -> Optional[str]:
        """Get the job ID."""
        return self._job_id


# Module-level convenience functions

def auth(api_key: Optional[str] = None, priority: bool = True, flexible: bool = True) -> AuthSession:
    """
    Authenticate with Verlex API.

    Args:
        api_key: Your Verlex API key
        priority: True = immediate execution, False = patient mode
        flexible: True = can migrate, False = sticky

    Returns:
        AuthSession object
    """
    global _current_session

    api_key = api_key or os.getenv("VERLEX_API_KEY")
    if not api_key:
        raise NotAuthenticatedError("No API key provided")

    _current_session = AuthSession(
        api_key=api_key,
        priority=priority,
        flexible=flexible,
    )
    return _current_session


def get_session() -> Optional[AuthSession]:
    """Get the current authentication session."""
    return _current_session


def logout() -> None:
    """Clear the current session."""
    global _current_session
    _current_session = None
    print("Logged out.")


def whoami() -> Optional[Dict[str, Any]]:
    """Show current authenticated user."""
    if not _current_session:
        print("Not authenticated. Run verlex.auth() first.")
        return None

    api_url = os.getenv("VERLEX_API_URL", DEFAULT_API_URL)

    try:
        response = httpx.get(
            f"{api_url}/v1/auth/me",
            headers={"Authorization": f"Bearer {_current_session.api_key}"},
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Authenticated as: {data.get('email', 'user')}")
            print(f"Tier: {data.get('tier', 'free')}")
            return data
        else:
            print("Failed to get user info")
            return None
    except httpx.RequestError as e:
        print(f"Network error: {e}")
        return None


# Convenience function for quick one-off execution
def cloud(
    func: Callable[..., T],
    *args,
    api_key: Optional[str] = None,
    priority: bool = True,
    flexible: bool = True,
    **kwargs
) -> T:
    """
    Quick one-liner to run a function in the cloud.

    Args:
        func: Function to execute
        *args: Arguments for the function
        api_key: Verlex API key (optional if env var set)
        priority: True = immediate, False = patient
        flexible: True = can migrate, False = sticky
        **kwargs: Keyword arguments for the function

    Returns:
        The function's return value
    """
    with GateWay(api_key=api_key, priority=priority, flexible=flexible, verbose=False) as gw:
        return gw.run(func, *args, **kwargs)

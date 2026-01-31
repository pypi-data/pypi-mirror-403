"""HTTP client utilities for Simforge API requests.

This module provides:
- HttpClient class for making API requests
- Background thread management for fire-and-forget operations
"""

import atexit
import logging
import threading
import time
from typing import Any, Optional

import requests

from simforge.constants import DEFAULT_SERVICE_URL, __version__

logger = logging.getLogger(__name__)

# Global list to track pending trace creation threads
_pending_trace_threads: list[threading.Thread] = []
_pending_threads_lock = threading.Lock()


def _wait_for_pending_traces() -> None:
    """Wait for all pending trace creation threads to complete.

    This is registered as an atexit handler to ensure traces are created
    before the process exits.
    """
    with _pending_threads_lock:
        threads_to_wait = list(_pending_trace_threads)

    for thread in threads_to_wait:
        thread.join(timeout=2.0)  # Wait up to 2 seconds per thread


# Register the atexit handler
atexit.register(_wait_for_pending_traces)


def flush_traces(timeout: float = 30.0) -> None:
    """Wait for all pending trace creation threads to complete.

    Call this method before exiting if you want to ensure all traces
    are sent to the server. This is automatically called via atexit,
    but can be called explicitly if needed.

    Args:
        timeout: Maximum seconds to wait for each pending trace (default: 30.0)
    """
    with _pending_threads_lock:
        threads_to_wait = list(_pending_trace_threads)

    for thread in threads_to_wait:
        thread.join(timeout=timeout)


def _run_in_background(fn: callable) -> None:
    """Run a function in a background thread with tracking.

    The thread is tracked in _pending_trace_threads and will be waited
    for at process exit via the atexit handler.
    """

    def wrapped(t: threading.Thread) -> None:
        try:
            fn()
        except Exception:
            # Silently ignore failures
            pass
        finally:
            with _pending_threads_lock:
                if t in _pending_trace_threads:
                    _pending_trace_threads.remove(t)

    thread = threading.Thread(target=lambda: wrapped(thread))
    with _pending_threads_lock:
        _pending_trace_threads.append(thread)
    thread.start()


class HttpClient:
    """HTTP client for Simforge API requests.

    Provides methods for different API endpoints with proper error handling,
    timeouts, and authentication.
    """

    def __init__(
        self,
        api_key: str,
        service_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """Initialize the HTTP client.

        Args:
            api_key: The API key for authentication
            service_url: The base URL for the Simforge API
            timeout: Default request timeout in seconds
        """
        self.api_key = api_key
        self.service_url = (service_url or DEFAULT_SERVICE_URL).rstrip("/")
        self.timeout = timeout

    def request(
        self,
        endpoint: str,
        payload: dict[str, Any],
        timeout: Optional[float] = None,
        max_retries: int = 1,
        retry_delay: float = 0.1,
    ) -> dict[str, Any]:
        """Make an HTTP POST request to the Simforge API.

        Args:
            endpoint: The API endpoint (without base URL)
            payload: The request body
            timeout: Request timeout in seconds (uses default if not specified)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            The parsed JSON response

        Raises:
            ValueError: If the response contains an error
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.service_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        request_timeout = timeout if timeout is not None else self.timeout

        last_exception: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=request_timeout,
                )
                response.raise_for_status()

                result = response.json()

                # Check for errors in the response
                if "error" in result:
                    if "url" in result:
                        raise ValueError(
                            f"{result['error']} Configure it at: {self.service_url}{result['url']}"
                        )
                    raise ValueError(result["error"])

                return result

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.debug(
                        f"Request attempt {attempt + 1} failed, retrying: {e}"
                    )
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    if hasattr(e, "response") and e.response is not None:
                        logger.error(f"Response: {e.response.text[:500]}")

        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in request")

    def lookup_function(self, name: str) -> dict[str, Any]:
        """Look up a function by name.

        Blocks until complete - needed for function execution.

        Args:
            name: The function name to look up

        Returns:
            Function version data including BAML prompt and providers
        """
        return self.request("/api/sdk/functions/lookup", {"name": name})

    def call_function(
        self,
        name: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a function on the server.

        Blocks until complete - needed for function execution.

        Args:
            name: The function name to call
            inputs: The input arguments

        Returns:
            The function result
        """
        return self.request(
            "/api/sdk/call",
            {
                "name": name,
                "inputs": inputs,
                "sdkVersion": __version__,
            },
        )

    def send_internal_trace(
        self,
        function_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Send an internal trace (from BAML execution).

        Fire-and-forget - runs in background thread.

        Args:
            function_id: The function ID
            payload: The trace payload (result, inputs, rawCollector, source)
        """

        def do_request() -> None:
            self.request(
                f"/api/sdk/functions/{function_id}/traces",
                {
                    **payload,
                    "sdkVersion": __version__,
                },
                timeout=10,
                max_retries=3,
                retry_delay=0.1,
            )

        _run_in_background(do_request)

    def send_external_span(self, payload: dict[str, Any]) -> None:
        """Send an external span (from span decorator or OpenAI tracing).

        Fire-and-forget - runs in background thread.

        Args:
            payload: The span payload
        """

        def do_request() -> None:
            self.request(
                "/api/sdk/externalSpans",
                {
                    **payload,
                    "sdkVersion": __version__,
                },
                timeout=30,
            )

        _run_in_background(do_request)

    def send_external_trace(self, payload: dict[str, Any]) -> None:
        """Send an external trace (from OpenAI tracing).

        Fire-and-forget - runs in background thread.

        Args:
            payload: The trace payload
        """

        def do_request() -> None:
            self.request(
                "/api/sdk/externalTraces",
                {
                    **payload,
                    "sdkVersion": __version__,
                },
                timeout=10,
            )

        _run_in_background(do_request)

"""Simforge client for provider-based API calls."""

import asyncio
import functools
import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Literal, Optional, ParamSpec, TypedDict, TypeVar

from simforge.baml import run_function_with_baml
from simforge.constants import DEFAULT_SERVICE_URL, __version__
from simforge.http import HttpClient, flush_traces  # noqa: F401 - re-export
from simforge.serialize import serialize_value

# Type variables for generic function signatures
P = ParamSpec("P")
T = TypeVar("T")

# Span types matching the backend enum
SpanType = Literal["llm", "agent", "function", "guardrail", "handoff", "custom"]


class SpanContext(TypedDict):
    """Context for tracking nested spans."""

    traceId: str
    spanId: str


# Async-safe context variable for tracking nested spans
# Uses Python's contextvars which properly propagate through async/await chains
_span_stack: ContextVar[list[SpanContext]] = ContextVar(
    "simforge_span_stack", default=[]
)


def _get_span_stack() -> list[SpanContext]:
    """Get the current span stack from async context."""
    return _span_stack.get()


def _run_with_span_stack(stack: list[SpanContext], fn: Callable[[], T]) -> T:
    """Run a function with a new span stack context."""
    token = _span_stack.set(stack)
    try:
        return fn()
    finally:
        _span_stack.reset(token)

logger = logging.getLogger(__name__)


class AllowedEnvVars(TypedDict, total=False):
    """Allowed environment variables for LLM providers.

    Only these keys are permitted when passing environment variables
    to the Simforge client for local BAML execution.

    Attributes:
        OPENAI_API_KEY: OpenAI API key for GPT models
    """

    OPENAI_API_KEY: str


class Simforge:
    """Client for making provider-based API calls via BAML."""

    def __init__(
        self,
        api_key: str,
        service_url: Optional[str] = None,
        env_vars: Optional[AllowedEnvVars] = None,
        execute_locally: bool = True,
    ):
        """Initialize the Simforge client.

        Args:
            api_key: The API key for Simforge API authentication
            service_url: The base URL for the Simforge API (default: https://simforge.goharvest.ai)
            env_vars: Environment variables for LLM provider API keys (only OPENAI_API_KEY is supported)
            execute_locally: Whether to execute BAML locally on the client (default: True)
        """
        self.api_key = api_key
        self.service_url = service_url or DEFAULT_SERVICE_URL
        self.env_vars = env_vars or {}
        self.execute_locally = execute_locally
        self._http_client = HttpClient(
            api_key=api_key,
            service_url=self.service_url,
        )

    def _fetch_function_version(self, method_name: str) -> dict:
        """Fetch the function with its current version and BAML prompt from the server.

        Args:
            method_name: The name of the method to fetch

        Returns:
            Function version data including BAML prompt and providers

        Raises:
            ValueError: If function not found or has no prompt
        """
        result = self._http_client.lookup_function(method_name)

        # Check if function was not found
        if result.get("id") is None:
            raise ValueError(
                f'Function "{method_name}" not found. Create it at: {self.service_url}/functions'
            )

        # Check if function has no prompt
        if not result.get("prompt"):
            func_id = result.get("id")
            raise ValueError(
                f'Function "{method_name}" has no prompt configured. '
                f"Add one at: {self.service_url}/functions/{func_id}"
            )

        return result

    def call(self, method_name: str, **kwargs: Any) -> Any:
        """Call a method with the given named arguments via BAML execution.

        Args:
            method_name: The name of the method to call
            **kwargs: Named arguments to pass to the method

        Returns:
            The result of the BAML function execution

        Raises:
            ValueError: If no prompt is found or other API errors
        """
        # If executeLocally is true, fetch the BAML and execute it locally
        if self.execute_locally:
            try:
                function_version = self._fetch_function_version(method_name)
                execution_result = asyncio.run(
                    run_function_with_baml(
                        function_version["prompt"],
                        kwargs,
                        function_version["providers"],
                        self.env_vars,
                    )
                )

                # Create trace for the local execution
                # Serialize the result to JSON string
                if isinstance(execution_result.result, str):
                    result_str = execution_result.result
                elif hasattr(execution_result.result, "model_dump"):
                    result_str = json.dumps(execution_result.result.model_dump())
                elif hasattr(execution_result.result, "dict"):
                    result_str = json.dumps(execution_result.result.dict())
                elif isinstance(execution_result.result, (dict, list)):
                    result_str = json.dumps(execution_result.result)
                else:
                    result_str = str(execution_result.result)

                # Create trace in background (fire-and-forget)
                trace_payload: dict[str, Any] = {
                    "result": result_str,
                    "source": "python-sdk",
                }
                if kwargs:
                    trace_payload["inputs"] = kwargs
                if execution_result.raw_collector is not None:
                    trace_payload["rawCollector"] = execution_result.raw_collector

                self._http_client.send_internal_trace(
                    function_version["id"],
                    trace_payload,
                )

                return execution_result.result
            except Exception as e:
                logger.error(f"Error during local execution: {e}")
                raise

        # Otherwise, fall back to server-side execution
        result = self._http_client.call_function(method_name, kwargs)
        return result.get("result")

    def get_openai_tracing_processor(self):
        """Get a tracing processor for OpenAI Agents SDK integration.

        The processor implements the TracingProcessor interface from the OpenAI
        Agents SDK and can be registered to automatically capture traces and
        spans from agent execution.

        Example:
            ```python
            from simforge import Simforge
            from agents import set_trace_processors

            simforge = Simforge(api_key="your-api-key")
            processor = simforge.get_openai_tracing_processor()

            # Register the processor with OpenAI Agents SDK
            set_trace_processors([processor])
            ```

        Returns:
            A SimforgeOpenAITracingProcessor instance configured for this client

        Raises:
            ImportError: If openai-agents is not installed

        See:
            https://openai.github.io/openai-agents-python/ref/tracing/
        """
        # Import here to avoid requiring openai-agents for basic SDK usage
        from simforge.tracing import SimforgeOpenAITracingProcessor

        return SimforgeOpenAITracingProcessor(
            api_key=self.api_key,
            service_url=self.service_url,
        )

    def span(
        self,
        trace_function_key: str,
        *,
        name: Optional[str] = None,
        type: SpanType = "custom",
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """Decorator to wrap a function and automatically create a span for its inputs and outputs.

        The wrapped function behaves identically to the original, but sends
        span data to Simforge in the background after each call. Nested spans
        are automatically tracked through async context propagation.

        Example usage:
            ```python
            client = Simforge(api_key='your-api-key')

            @client.span('order-processing')
            def process_order(order_id: str, items: list[str]) -> dict:
                # ... process order
                return {'total': 100}

            # With explicit span name and type
            @client.span('safety-check', name='ContentValidator', type='guardrail')
            def check_content(content: str) -> dict:
                return {'safe': True}

            # Async functions work too
            @client.span('fetch-data')
            async def fetch_data(url: str) -> dict:
                # ... fetch data
                return {'data': 'result'}

            # Nested spans work automatically
            @client.span('outer-operation', type='agent')
            def outer():
                inner()  # This span will be a child of outer-operation

            @client.span('inner-operation', type='function')
            def inner():
                pass
            ```

        Args:
            trace_function_key: A string identifier for grouping spans (e.g., 'order-processing', 'user-auth')
            name: The name of the span. Defaults to the function name if available, otherwise the trace_function_key.
            type: The type of span. Defaults to "custom". Options: llm, agent, function, guardrail, handoff, custom

        Returns:
            A decorator that wraps functions to create spans for inputs and outputs
        """
        span_type = type  # Avoid shadowing builtin
        explicit_name = name  # Store the explicit name option

        def decorator(fn: Callable[P, T]) -> Callable[P, T]:
            is_async = asyncio.iscoroutinefunction(fn)
            function_name = fn.__name__ or None
            # Span name priority: explicit name > function name > trace_function_key
            span_name = explicit_name or function_name or trace_function_key

            def _build_span_context(
                args: tuple[Any, ...], kwargs: dict[str, Any]
            ) -> tuple[list[SpanContext], dict[str, Any]]:
                """Build span context and base params for tracing."""
                current_stack = _get_span_stack()
                parent_context = current_stack[-1] if current_stack else None

                trace_id = (
                    parent_context["traceId"] if parent_context else str(uuid.uuid4())
                )
                span_id = str(uuid.uuid4())
                parent_span_id = parent_context["spanId"] if parent_context else None

                new_context: SpanContext = {"traceId": trace_id, "spanId": span_id}
                new_stack = [*current_stack, new_context]

                base_params = {
                    "trace_function_key": trace_function_key,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "raw_args": args,
                    "raw_kwargs": kwargs,
                    "started_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()
                    ),
                    "function_name": function_name,
                    "span_name": span_name,
                    "span_type": span_type,
                }

                return new_stack, base_params

            def _get_ended_at() -> str:
                return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

            if is_async:

                @functools.wraps(fn)
                async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                    new_stack, base_params = _build_span_context(args, kwargs)

                    token = _span_stack.set(new_stack)
                    try:
                        result = await fn(*args, **kwargs)
                        self._send_span_background(
                            **base_params,
                            result=result,
                            error=None,
                            ended_at=_get_ended_at(),
                        )
                        return result
                    except Exception as e:
                        self._send_span_background(
                            **base_params,
                            result=None,
                            error=str(e),
                            ended_at=_get_ended_at(),
                        )
                        raise
                    finally:
                        _span_stack.reset(token)

                return async_wrapper  # type: ignore[return-value]
            else:

                @functools.wraps(fn)
                def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                    new_stack, base_params = _build_span_context(args, kwargs)

                    def execute() -> T:
                        result = fn(*args, **kwargs)
                        self._send_span_background(
                            **base_params,
                            result=result,
                            error=None,
                            ended_at=_get_ended_at(),
                        )
                        return result

                    try:
                        return _run_with_span_stack(new_stack, execute)
                    except Exception as e:
                        self._send_span_background(
                            **base_params,
                            result=None,
                            error=str(e),
                            ended_at=_get_ended_at(),
                        )
                        raise

                return sync_wrapper  # type: ignore[return-value]

        return decorator

    def get_function(self, trace_function_key: str) -> "SimforgeFunction":
        """Get a function wrapper for a specific trace function key.

        This provides a fluent API alternative to calling span directly,
        allowing you to bind the trace_function_key once and wrap multiple functions.

        Example usage:
            ```python
            client = Simforge(api_key='your-api-key')

            order_func = client.get_function('order-processing')

            @order_func.span()
            def process_order(order_id: str):
                pass

            @order_func.span()
            def validate_order(order_id: str):
                pass
            ```

        Args:
            trace_function_key: A string identifier for grouping spans

        Returns:
            A SimforgeFunction instance for wrapping functions
        """
        return SimforgeFunction(self, trace_function_key)

    def _serialize_inputs(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> list[Any]:
        """Serialize function inputs for span data."""
        serialized_args = [self._serialize_value(arg) for arg in args]
        if kwargs:
            serialized_args.append(
                {k: self._serialize_value(v) for k, v in kwargs.items()}
            )
        return serialized_args

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for JSON storage."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        if hasattr(value, "model_dump"):  # Pydantic v2
            return value.model_dump()
        if hasattr(value, "dict"):  # Pydantic v1
            return value.dict()
        # Fallback to string representation
        return str(value)

    def _send_span_background(
        self,
        trace_function_key: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        raw_args: tuple[Any, ...],
        raw_kwargs: dict[str, Any],
        result: Any,
        error: Optional[str],
        started_at: str,
        ended_at: str,
        function_name: Optional[str] = None,
        span_name: Optional[str] = None,
        span_type: SpanType = "custom",
    ) -> None:
        """Send span data to the server (fire-and-forget)."""
        # Build structured inputs: { "args": [...], "kwargs": {...} }
        # This preserves the distinction between positional and keyword arguments
        inputs_struct: dict[str, Any] = {"args": list(raw_args)}
        if raw_kwargs:
            inputs_struct["kwargs"] = raw_kwargs

        # Serialize for human-readable JSON (input/output fields)
        human_inputs = self._serialize_inputs(raw_args, raw_kwargs)
        human_output = self._serialize_value(result)

        # Serialize with metadata for reconstruction (input_meta/output_meta)
        serialized_inputs = serialize_value(inputs_struct)
        serialized_output = serialize_value(result)

        # Build span_data
        # Use span_name which is already computed with priority: explicit name > function name > trace_function_key
        span_data: dict[str, Any] = {
            "name": span_name or trace_function_key,
            "type": span_type,
            "input": human_inputs,
            "output": human_output,
        }

        if function_name is not None:
            span_data["function_name"] = function_name

        # Add full serialized structure only if there are special types to preserve
        # This allows reconstruction of original Python types (datetime, UUID, Decimal, etc.)
        if "meta" in serialized_inputs:
            span_data["input_serialized"] = serialized_inputs
        if "meta" in serialized_output:
            span_data["output_serialized"] = serialized_output

        if error is not None:
            span_data["error"] = error

        # Build external_span
        external_span: dict[str, Any] = {
            "id": span_id,
            "trace_id": trace_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "span_data": span_data,
        }
        if parent_span_id is not None:
            external_span["parent_id"] = parent_span_id

        self._http_client.send_external_span({
            "type": "sdk-function",
            "source": "python-sdk-function",
            "sourceTraceId": trace_id,
            "traceFunctionKey": trace_function_key,
            "rawSpan": external_span,
        })


class SimforgeFunction:
    """Represents a Simforge function that can wrap user functions for tracing.

    This provides a fluent API for binding a trace_function_key once and
    then wrapping multiple functions with that key.

    Example usage:
        ```python
        client = Simforge(api_key='your-api-key')

        order_func = client.get_function('order-processing')

        @order_func.span()
        def process_order(order_id: str):
            pass

        @order_func.span()
        def validate_order(order_id: str):
            pass
        ```
    """

    def __init__(self, client: Simforge, trace_function_key: str):
        """Initialize a SimforgeFunction.

        Args:
            client: The Simforge client instance
            trace_function_key: The trace function key for grouping spans
        """
        self._client = client
        self._trace_function_key = trace_function_key

    def span(
        self, *, name: Optional[str] = None, type: SpanType = "custom"
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """Decorator to wrap a function and automatically create a span.

        Example usage:
            ```python
            order_func = client.get_function('order-processing')

            @order_func.span()
            def process_order(order_id: str):
                # ... process order
                pass

            # With explicit span name and type
            @order_func.span(name='SafetyValidator', type='guardrail')
            def check_safety(content: str):
                pass
            ```

        Args:
            name: The name of the span. Defaults to the function name if available, otherwise the trace_function_key.
            type: The type of span. Defaults to "custom". Options: llm, agent, function, guardrail, handoff, custom

        Returns:
            A decorator that wraps functions to create spans
        """
        return self._client.span(self._trace_function_key, name=name, type=type)

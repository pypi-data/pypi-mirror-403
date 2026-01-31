"""Tracing processor for OpenAI Agents SDK integration with Simforge."""

import json
import logging
from typing import TYPE_CHECKING, Any

from simforge.constants import DEFAULT_SERVICE_URL
from simforge.http import HttpClient

if TYPE_CHECKING:
    from agents import Span, Trace, TracingProcessor
else:
    try:
        from agents import TracingProcessor
    except ImportError:
        TracingProcessor = object

logger = logging.getLogger(__name__)


class SimforgeOpenAITracingProcessor(TracingProcessor):
    """Tracing processor for OpenAI Agents SDK that sends traces to Simforge.

    This processor captures traces and spans from the OpenAI Agents SDK and sends
    them to the Simforge API for storage and analysis.

    Args:
        api_key: Simforge API key for authentication
        service_url: Base URL for the Simforge service (default: https://simforge.goharvest.ai)
    """

    def __init__(self, api_key: str, service_url: str | None = None):
        """Initialize the Simforge tracing processor.

        Args:
            api_key: Simforge API key
            service_url: Base URL for Simforge service (default: production URL)
        """
        self._http_client = HttpClient(
            api_key=api_key,
            service_url=service_url or DEFAULT_SERVICE_URL,
        )
        self._active_traces: dict[str, "Trace"] = {}
        self._active_spans: dict[str, "Span"] = {}

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._http_client.api_key

    @property
    def service_url(self) -> str:
        """Get the service URL."""
        return self._http_client.service_url

    def on_trace_start(self, trace: "Trace") -> None:
        """Called when a trace starts.

        Args:
            trace: The trace that started
        """
        self._active_traces[trace.trace_id] = trace
        logger.debug(f"Trace started: {trace.trace_id}")

        # Send trace start to Simforge
        self._send_external_trace(trace)

    def on_trace_end(self, trace: "Trace") -> None:
        """Called when a trace ends.

        Args:
            trace: The trace that ended
        """
        if trace.trace_id in self._active_traces:
            del self._active_traces[trace.trace_id]

        logger.debug(f"Trace ended: {trace.trace_id}")

        # Send trace end to Simforge
        self._send_external_trace(trace)

    def on_span_start(self, span: "Span") -> None:
        """Called when a span starts.

        Args:
            span: The span that started
        """
        self._active_spans[span.span_id] = span
        logger.debug(f"Span started: {span.span_id}")

    def on_span_end(self, span: "Span") -> None:
        """Called when a span ends.

        Args:
            span: The span that ended
        """
        if span.span_id in self._active_spans:
            del self._active_spans[span.span_id]

        logger.debug(f"Span ended: {span.span_id}")

        # Send all spans to Simforge
        self._send_external_span(span)

    def _send_external_trace(self, trace: "Trace") -> None:
        """Send external trace to Simforge API (fire-and-forget).

        Args:
            trace: The trace to send
        """
        try:
            # Use trace.export() to get the external trace data
            external_trace = trace.export()

            trace_data = {
                "type": "openai",
                "source": "python-sdk-openai-tracing",
                "externalTrace": external_trace,
            }

            # Serialize to JSON to catch any serialization errors early
            try:
                json_str = json.dumps(trace_data)
                trace_data = json.loads(json_str)  # Re-parse to ensure it's clean
            except TypeError as e:
                logger.error(f"Failed to serialize external trace data: {e}")
                logger.debug(f"Problematic trace_data: {trace_data}")
                return

            self._http_client.send_external_trace(trace_data)
        except Exception as e:
            logger.error(
                f"Failed to send external trace to Simforge: {e}", exc_info=True
            )

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value to a JSON-serializable format.

        Handles:
        - dicts: use as-is
        - lists: recursively serialize each item
        - Pydantic models: call model_dump()
        - Strings, numbers, booleans, None: use as-is
        - Other objects: try model_dump() or convert to string

        Raises:
            Exception: If serialization fails (e.g., __str__ raises)
        """
        if isinstance(value, dict):
            return value
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif hasattr(value, "model_dump"):
            # Pydantic model
            return value.model_dump()
        else:
            # Try to convert to dict or string
            if hasattr(value, "__dict__"):
                return value.__dict__
            # This may raise if __str__ fails
            return str(value)

    def _export_span(
        self, span: "Span", errors: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Export span to dict, collecting any errors.

        Returns:
            serialized_span_dict
        """
        try:
            serialized_span = span.export()
            if not isinstance(serialized_span, dict):
                errors.append(
                    {
                        "step": "span.export()",
                        "error": f"Returned non-dict type: {type(serialized_span)}",
                    }
                )
                serialized_span = {}
        except Exception as e:
            errors.append({"step": "span.export()", "error": str(e)})
            serialized_span = {}

        if "span_data" not in serialized_span:
            serialized_span["span_data"] = {}

        return serialized_span

    def _extract_span_input_response(
        self,
        span: "Span",
        serialized_span: dict[str, Any],
        errors: list[dict[str, str]],
    ) -> None:
        """Extract and serialize span input and response, updating errors list."""
        # Get input and response from span_data (they're private properties with underscores)
        span_input = getattr(span.span_data, "input", None) or []
        span_response = getattr(span.span_data, "response", None)

        # Serialize input - _serialize_value handles all types including lists
        try:
            serialized_span["span_data"]["input"] = self._serialize_value(span_input)
        except Exception as e:
            errors.append({"step": "serialize_input", "error": str(e)})
            serialized_span["span_data"]["input"] = None

        # Serialize response
        try:
            serialized_span["span_data"]["response"] = (
                self._serialize_value(span_response) if span_response else None
            )
        except Exception as e:
            errors.append({"step": "serialize_response", "error": str(e)})
            serialized_span["span_data"]["response"] = None

    def _build_span_payload(
        self,
        span: "Span",
        serialized_span: dict[str, Any],
        errors: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Build span payload and handle JSON serialization, returning payload dict."""
        span_data: dict[str, Any] = {
            "type": "openai",
            "source": "python-sdk-openai-tracing",
            "sourceTraceId": span.trace_id,
            "rawSpan": serialized_span,
        }

        if errors:
            span_data["errors"] = errors

        try:
            json_str = json.dumps(span_data)
            return json.loads(json_str)
        except (TypeError, ValueError) as e:
            errors.append({"step": "json_serialize", "error": str(e)})
            # Try to send what we can with error info
            span_data = {
                "type": "openai",
                "source": "python-sdk-openai-tracing",
                "sourceTraceId": getattr(span, "trace_id", "unknown"),
                "rawSpan": {
                    "id": getattr(span, "span_id", "unknown"),
                    "trace_id": getattr(span, "trace_id", "unknown"),
                },
                "errors": errors,
            }
            return span_data

    def _send_external_span(self, span: "Span") -> None:
        """Send external span to Simforge API (fire-and-forget).

        Args:
            span: The span to send
        """
        errors: list[dict[str, str]] = []
        serialized_span = self._export_span(span, errors)
        self._extract_span_input_response(span, serialized_span, errors)
        span_payload = self._build_span_payload(span, serialized_span, errors)

        try:
            self._http_client.send_external_span(span_payload)
        except Exception as e:
            logger.error(f"Failed to send external span to Simforge: {e}", exc_info=True)

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any buffered traces/spans.

        Args:
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            True if flush succeeded, False otherwise
        """
        # No buffering, so nothing to flush
        return True

    def shutdown(self, timeout_millis: int = 30000) -> bool:
        """Shutdown the tracing processor.

        Args:
            timeout_millis: Maximum time to wait for shutdown in milliseconds

        Returns:
            True if shutdown succeeded, False otherwise
        """
        self.force_flush(timeout_millis)
        self._active_traces.clear()
        self._active_spans.clear()
        return True

    def __enter__(self) -> "SimforgeOpenAITracingProcessor":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and shutdown."""
        self.shutdown()

"""Simforge client for provider-based API calls."""

from simforge.client import (
    AllowedEnvVars,
    Simforge,
    SimforgeFunction,
    SpanType,
    flush_traces,
)

# Only export SimforgeTracingProcessor if openai-agents is available
try:
    from simforge.tracing import (
        SimforgeOpenAITracingProcessor as SimforgeTracingProcessor,
    )

    __all__ = [
        "Simforge",
        "SimforgeFunction",
        "SpanType",
        "AllowedEnvVars",
        "SimforgeTracingProcessor",
        "flush_traces",
    ]
except ImportError:
    # openai-agents not installed, skip tracing processor export
    __all__ = ["Simforge", "SimforgeFunction", "SpanType", "AllowedEnvVars", "flush_traces"]

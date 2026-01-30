"""
ThinkHive Python SDK
OpenTelemetry-based observability for AI agents
"""

from opentelemetry import trace
try:
    # Try to use HTTP+JSON exporter (simpler, no protobuf required)
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    EXPORTER_TYPE = "http+proto"
except ImportError:
    # Fallback to gRPC exporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    EXPORTER_TYPE = "grpc"
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
import functools
from typing import Optional, Dict, Any, Callable
import os

__version__ = "3.2.0"

# Global tracer
_tracer: Optional[trace.Tracer] = None
_initialized = False


def init(
    api_key: Optional[str] = None,
    endpoint: str = "https://thinkhivemind-h25z7pvd3q-uc.a.run.app",
    service_name: str = "my-ai-agent",
    agent_id: Optional[str] = None,
):
    """
    Initialize ThinkHive SDK with OTLP exporter

    Args:
        api_key: ThinkHive API key (or set THINKHIVE_API_KEY env var)
        endpoint: ThinkHive endpoint URL
        service_name: Name of your service/agent
        agent_id: Optional agent ID (or set THINKHIVE_AGENT_ID env var)
    """
    global _tracer, _initialized

    if _initialized:
        return

    # Get API key from env if not provided
    api_key = api_key or os.getenv("THINKHIVE_API_KEY")
    agent_id = agent_id or os.getenv("THINKHIVE_AGENT_ID")

    if not api_key and not agent_id:
        raise ValueError("Either api_key or agent_id must be provided")

    # Create resource with service name
    resource = Resource.create({
        "service.name": service_name,
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif agent_id:
        headers["X-Agent-ID"] = agent_id

    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
        headers=headers,
    )

    # Add span processor
    provider.add_span_processor(BatchSpanProcessor(exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer
    _tracer = trace.get_tracer(__name__, __version__)
    _initialized = True

    print(f"✅ ThinkHive SDK initialized (endpoint: {endpoint})")


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance"""
    global _tracer
    if not _initialized:
        raise RuntimeError("ThinkHive SDK not initialized. Call thinkhive.init() first.")
    return _tracer


def trace_llm(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
):
    """
    Decorator for tracing LLM calls

    Usage:
        @trace_llm(model_name="gpt-4", provider="openai")
        def call_llm(prompt):
            return openai.chat.completions.create(...)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                func.__name__,
                attributes={
                    "openinference.span.kind": "LLM",
                    "llm.model_name": model_name,
                    "llm.provider": provider,
                }
            ) as span:
                try:
                    result = func(*args, **kwargs)

                    # Try to extract token counts if result is OpenAI-like
                    if hasattr(result, "usage"):
                        usage = result.usage
                        if hasattr(usage, "prompt_tokens"):
                            span.set_attribute("llm.token_count.prompt", usage.prompt_tokens)
                        if hasattr(usage, "completion_tokens"):
                            span.set_attribute("llm.token_count.completion", usage.completion_tokens)
                        if hasattr(usage, "total_tokens"):
                            span.set_attribute("llm.token_count.total", usage.total_tokens)

                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper
    return decorator


def trace_retrieval(query: Optional[str] = None):
    """
    Decorator for tracing retrieval/RAG operations

    Usage:
        @trace_retrieval()
        def search_documents(query):
            return vector_db.search(query)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                func.__name__,
                attributes={
                    "openinference.span.kind": "RETRIEVER",
                    "retrieval.query": query or (args[0] if args else None),
                }
            ) as span:
                try:
                    result = func(*args, **kwargs)

                    # If result is a list of documents, record them
                    if isinstance(result, list) and len(result) > 0:
                        for i, doc in enumerate(result[:10]):  # Limit to first 10
                            if hasattr(doc, "id"):
                                span.set_attribute(f"retrieval.documents.{i}.document.id", doc.id)
                            if hasattr(doc, "score"):
                                span.set_attribute(f"retrieval.documents.{i}.document.score", doc.score)
                            if hasattr(doc, "content"):
                                content = doc.content[:500]  # Truncate
                                span.set_attribute(f"retrieval.documents.{i}.document.content", content)

                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper
    return decorator


def trace_tool(tool_name: Optional[str] = None):
    """
    Decorator for tracing tool/function calls

    Usage:
        @trace_tool(tool_name="web_search")
        def search_web(query):
            return requests.get(f"https://api.example.com/search?q={query}")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                tool_name or func.__name__,
                attributes={
                    "openinference.span.kind": "TOOL",
                    "tool.name": tool_name or func.__name__,
                }
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper
    return decorator


# Import API modules
from .client import configure, ThinkHiveApiError, ThinkHiveValidationError
from .api import (
    human_review,
    nondeterminism,
    eval_health,
    deterministic_graders,
    conversation_eval,
    transcript_patterns,
    # v2 terminology
    issues,
    analyzer,
    traces,
    # v3 APIs
    runs,
    claims,
    calibration,
    roi_analytics,
    business_metrics,
    # deprecated aliases
    cases,  # deprecated alias for issues
    explainer,  # deprecated alias for analyzer
)

# Import helper functions
from .api.nondeterminism import (
    calculate_pass_at_k,
    calculate_pass_to_k,
    required_pass_rate_for_pass_at_k,
    is_reliable_evaluation,
)
from .api.eval_health import (
    has_health_issue,
    get_severity_level,
    is_saturated,
    get_saturation_recommendation,
)
from .api.deterministic_graders import (
    create_regex_rule,
    create_contains_rule,
    create_length_rule,
    create_json_schema_rule,
    all_rules_passed,
    get_failed_rules,
    calculate_average_score,
)
from .api.conversation_eval import (
    aggregate_worst,
    aggregate_average,
    aggregate_weighted,
    aggregate_final_turn,
    aggregate_majority,
    get_aggregator,
    get_problematic_turns,
    analyze_conversation_trend,
)
from .api.transcript_patterns import (
    is_high_risk,
    get_matches_by_category,
    get_critical_insights,
    has_pii_exposure,
    has_frustration_signals,
    has_escalation_request,
    get_category_distribution,
    get_recommendations,
    needs_attention,
    sort_matches_by_severity,
)
from .api.business_metrics import (
    is_metric_ready,
    needs_more_traces,
    awaiting_external_data,
    is_metric_stale,
    get_status_message as get_metric_status_message,
    get_trace_progress,
    format_metric_value,
)

__all__ = [
    # Core
    "init",
    "configure",
    "get_tracer",
    # Tracing decorators
    "trace_llm",
    "trace_retrieval",
    "trace_tool",
    # API clients
    "human_review",
    "nondeterminism",
    "eval_health",
    "deterministic_graders",
    "conversation_eval",
    "transcript_patterns",
    "traces",
    # v2 terminology (Issues/Analyzer)
    "issues",
    "analyzer",
    # v3 APIs
    "runs",
    "claims",
    "calibration",
    "roi_analytics",
    "business_metrics",
    # deprecated aliases
    "cases",  # deprecated alias for issues
    "explainer",  # deprecated alias for analyzer
    # Errors
    "ThinkHiveApiError",
    "ThinkHiveValidationError",
    # Helper functions
    "calculate_pass_at_k",
    "calculate_pass_to_k",
    "required_pass_rate_for_pass_at_k",
    "is_reliable_evaluation",
    "has_health_issue",
    "get_severity_level",
    "is_saturated",
    "get_saturation_recommendation",
    "create_regex_rule",
    "create_contains_rule",
    "create_length_rule",
    "create_json_schema_rule",
    "all_rules_passed",
    "get_failed_rules",
    "calculate_average_score",
    "aggregate_worst",
    "aggregate_average",
    "aggregate_weighted",
    "aggregate_final_turn",
    "aggregate_majority",
    "get_aggregator",
    "get_problematic_turns",
    "analyze_conversation_trend",
    "is_high_risk",
    "get_matches_by_category",
    "get_critical_insights",
    "has_pii_exposure",
    "has_frustration_signals",
    "has_escalation_request",
    "get_category_distribution",
    "get_recommendations",
    "needs_attention",
    "sort_matches_by_severity",
    # Business Metrics helpers
    "is_metric_ready",
    "needs_more_traces",
    "awaiting_external_data",
    "is_metric_stale",
    "get_metric_status_message",
    "get_trace_progress",
    "format_metric_value",
]

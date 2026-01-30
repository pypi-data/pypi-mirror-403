"""
ThinkHive Python SDK - Traces API
Create and manage traces via HTTP API with evaluation support
"""

from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from ..client import post, get

CustomFlag = Literal[
    "hallucination",
    "policy_violation",
    "tone_issue",
    "retrieval_miss",
    "error"
]

Outcome = Literal["success", "failure"]


@dataclass
class TraceResult:
    """Result from creating a trace"""
    id: str
    agent_id: str
    company_id: str
    user_message: str
    agent_response: str
    outcome: Optional[str]
    evaluation_queued: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceResult":
        return cls(
            id=data.get("id", ""),
            agent_id=data.get("agentId", ""),
            company_id=data.get("companyId", ""),
            user_message=data.get("userMessage", ""),
            agent_response=data.get("agentResponse", ""),
            outcome=data.get("outcome"),
            evaluation_queued=data.get("_evaluationQueued", False),
            created_at=data.get("createdAt", ""),
        )


def create(
    *,
    agent_id: str,
    user_message: str,
    agent_response: str,
    user_intent: Optional[str] = None,
    outcome: Optional[Outcome] = None,
    custom_flags: Optional[List[CustomFlag]] = None,
    duration: Optional[int] = None,
    session_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    spans: Optional[List[Dict[str, Any]]] = None,
    business_context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    run_evaluation: Optional[bool] = None,
) -> TraceResult:
    """
    Create a trace via the HTTP API.

    This is an alternative to using OpenTelemetry decorators when you want
    direct control over trace creation, including the ability to trigger
    automatic evaluation.

    Args:
        agent_id: The agent ID this trace belongs to
        user_message: The user's message/query
        agent_response: The agent's response
        user_intent: Detected user intent (optional)
        outcome: Binary outcome - "success" or "failure"
        custom_flags: Classification flags (hallucination, policy_violation, etc.)
        duration: Duration in milliseconds
        session_id: Session ID for conversation tracking
        conversation_history: Previous messages in the conversation
        spans: Span data for detailed analysis
        business_context: Business context for ROI calculation
        metadata: Custom metadata
        run_evaluation: Request evaluation when trace is ingested.
            - True: Force evaluation on this trace
            - False: Skip evaluation even if agent has auto_evaluate enabled
            - None: Use agent's auto_evaluate setting (default)

    Returns:
        TraceResult with trace ID and evaluation status

    Example:
        >>> from thinkhive.api import traces
        >>>
        >>> # Create trace with forced evaluation
        >>> result = traces.create(
        ...     agent_id="agent-123",
        ...     user_message="What is the return policy?",
        ...     agent_response="Items can be returned within 30 days.",
        ...     outcome="success",
        ...     run_evaluation=True
        ... )
        >>>
        >>> print(f"Trace ID: {result.id}")
        >>> if result.evaluation_queued:
        ...     print("Evaluation will run asynchronously")
    """
    body: Dict[str, Any] = {
        "agentId": agent_id,
        "userMessage": user_message,
        "agentResponse": agent_response,
    }

    if user_intent is not None:
        body["userIntent"] = user_intent
    if outcome is not None:
        body["outcome"] = outcome
    if custom_flags is not None:
        body["customFlags"] = custom_flags
    if duration is not None:
        body["duration"] = duration
    if session_id is not None:
        body["sessionId"] = session_id
    if conversation_history is not None:
        body["conversationHistory"] = conversation_history
    if spans is not None:
        body["spans"] = spans
    if business_context is not None:
        body["businessContext"] = business_context
    if metadata is not None:
        body["metadata"] = metadata
    if run_evaluation is not None:
        body["runEvaluation"] = run_evaluation

    response = post("/traces", body, api_version="v1")
    return TraceResult.from_dict(response)


def get_by_id(trace_id: str) -> Dict[str, Any]:
    """
    Get a trace by ID.

    Args:
        trace_id: The trace ID

    Returns:
        Trace data
    """
    return get(f"/traces/{trace_id}", api_version="v1")


def list_for_agent(
    agent_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
    outcome: Optional[Outcome] = None,
) -> Dict[str, Any]:
    """
    List traces for an agent.

    Args:
        agent_id: The agent ID
        limit: Maximum number of traces to return
        offset: Offset for pagination
        outcome: Filter by outcome

    Returns:
        Paginated list of traces
    """
    params: Dict[str, Any] = {
        "agentId": agent_id,
        "limit": limit,
        "offset": offset,
    }
    if outcome is not None:
        params["outcome"] = outcome

    return get("/traces", params=params, api_version="v1")


__all__ = [
    "TraceResult",
    "create",
    "get_by_id",
    "list_for_agent",
]

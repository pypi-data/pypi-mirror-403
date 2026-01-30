"""
ThinkHive Python SDK - Runs API
Run-centric API for creating and managing runs (v3 atomic unit)
"""

from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from datetime import datetime
from ..client import post, get, put, delete

RunOutcome = Literal[
    "resolved",
    "partially_resolved",
    "failed",
    "escalated",
    "abandoned",
    "pending",
]


@dataclass
class RunResult:
    """Result from creating a run"""
    id: str
    agent_id: str
    company_id: str
    outcome: Optional[str]
    started_at: str
    ended_at: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunResult":
        return cls(
            id=data.get("id", ""),
            agent_id=data.get("agentId", ""),
            company_id=data.get("companyId", ""),
            outcome=data.get("outcome"),
            started_at=data.get("startedAt", ""),
            ended_at=data.get("endedAt"),
            created_at=data.get("createdAt", ""),
        )


@dataclass
class RunStats:
    """Run statistics for an agent"""
    agent_id: str
    period_from: str
    period_to: str
    total_runs: int
    outcome_breakdown: Dict[str, int]
    avg_duration_ms: float
    linked_tickets: int
    unlinked_runs: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunStats":
        period = data.get("period", {})
        return cls(
            agent_id=data.get("agentId", ""),
            period_from=period.get("from", ""),
            period_to=period.get("to", ""),
            total_runs=data.get("totalRuns", 0),
            outcome_breakdown=data.get("outcomeBreakdown", {}),
            avg_duration_ms=data.get("avgDurationMs", 0.0),
            linked_tickets=data.get("linkedTickets", 0),
            unlinked_runs=data.get("unlinkedRuns", 0),
        )


def create(
    *,
    agent_id: str,
    conversation_messages: List[Dict[str, str]],
    outcome: Optional[RunOutcome] = None,
    outcome_reason: Optional[str] = None,
    started_at: Optional[str] = None,
    ended_at: Optional[str] = None,
    model_id: Optional[str] = None,
    prompt_version: Optional[str] = None,
    session_id: Optional[str] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> RunResult:
    """
    Create a new run.

    Args:
        agent_id: The agent ID this run belongs to
        conversation_messages: List of messages with 'role' and 'content' keys
        outcome: Run outcome (resolved, failed, escalated, etc.)
        outcome_reason: Reason for the outcome
        started_at: ISO timestamp when run started (defaults to now)
        ended_at: ISO timestamp when run ended
        model_id: Model identifier used
        prompt_version: Version of the prompt used
        session_id: Session ID for conversation tracking
        customer_context: Customer context snapshot (ARR, health score, etc.)
        metadata: Custom metadata

    Returns:
        RunResult with run ID and details

    Example:
        >>> from thinkhive.api import runs
        >>>
        >>> result = runs.create(
        ...     agent_id="agent-123",
        ...     conversation_messages=[
        ...         {"role": "user", "content": "Help me with my order"},
        ...         {"role": "assistant", "content": "I can help with that..."}
        ...     ],
        ...     outcome="resolved"
        ... )
        >>> print(f"Run ID: {result.id}")
    """
    body: Dict[str, Any] = {
        "agentId": agent_id,
        "conversationMessages": conversation_messages,
        "startedAt": started_at or datetime.utcnow().isoformat() + "Z",
    }

    if outcome is not None:
        body["outcome"] = outcome
    if outcome_reason is not None:
        body["outcomeReason"] = outcome_reason
    if ended_at is not None:
        body["endedAt"] = ended_at
    if model_id is not None:
        body["modelId"] = model_id
    if prompt_version is not None:
        body["promptVersion"] = prompt_version
    if session_id is not None:
        body["sessionId"] = session_id
    if customer_context is not None:
        body["customerContext"] = customer_context
    if metadata is not None:
        body["metadata"] = metadata

    response = post("/runs", body, api_version="v3")
    return RunResult.from_dict(response)


def get_by_id(run_id: str) -> Dict[str, Any]:
    """
    Get a run by ID.

    Args:
        run_id: The run ID

    Returns:
        Run data
    """
    return get(f"/runs/{run_id}", api_version="v3")


def list_runs(
    *,
    agent_id: Optional[str] = None,
    ticket_id: Optional[str] = None,
    customer_account_id: Optional[str] = None,
    outcome: Optional[RunOutcome] = None,
    started_after: Optional[str] = None,
    started_before: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List runs with filters.

    Args:
        agent_id: Filter by agent ID
        ticket_id: Filter by linked ticket ID
        customer_account_id: Filter by customer account ID
        outcome: Filter by outcome
        started_after: Filter runs started after this ISO timestamp
        started_before: Filter runs started before this ISO timestamp
        limit: Maximum number of runs to return
        offset: Offset for pagination

    Returns:
        Paginated list of runs with items, limit, offset, hasMore
    """
    params: Dict[str, Any] = {
        "limit": limit,
        "offset": offset,
    }

    if agent_id is not None:
        params["agentId"] = agent_id
    if ticket_id is not None:
        params["ticketId"] = ticket_id
    if customer_account_id is not None:
        params["customerAccountId"] = customer_account_id
    if outcome is not None:
        params["outcome"] = outcome
    if started_after is not None:
        params["startedAfter"] = started_after
    if started_before is not None:
        params["startedBefore"] = started_before

    return get("/runs", params=params, api_version="v3")


def update(
    run_id: str,
    *,
    outcome: Optional[RunOutcome] = None,
    outcome_reason: Optional[str] = None,
    ended_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update a run.

    Args:
        run_id: The run ID to update
        outcome: New outcome
        outcome_reason: New outcome reason
        ended_at: New ended timestamp
        metadata: Metadata to merge

    Returns:
        Updated run data
    """
    body: Dict[str, Any] = {}

    if outcome is not None:
        body["outcome"] = outcome
    if outcome_reason is not None:
        body["outcomeReason"] = outcome_reason
    if ended_at is not None:
        body["endedAt"] = ended_at
    if metadata is not None:
        body["metadata"] = metadata

    return put(f"/runs/{run_id}", body, api_version="v3")


def delete_run(run_id: str) -> None:
    """
    Delete a run.

    Args:
        run_id: The run ID to delete
    """
    delete(f"/runs/{run_id}", api_version="v3")


def batch_create(runs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create multiple runs in batch.

    Args:
        runs_data: List of run data dictionaries with same fields as create()

    Returns:
        Dict with 'created' (list of RunResult) and 'failed' (list of errors)

    Example:
        >>> from thinkhive.api import runs
        >>>
        >>> result = runs.batch_create([
        ...     {
        ...         "agent_id": "agent-123",
        ...         "conversation_messages": [{"role": "user", "content": "Hello"}],
        ...         "outcome": "resolved"
        ...     },
        ...     {
        ...         "agent_id": "agent-123",
        ...         "conversation_messages": [{"role": "user", "content": "Help"}],
        ...         "outcome": "failed"
        ...     }
        ... ])
    """
    payload = []
    for run in runs_data:
        item: Dict[str, Any] = {
            "agentId": run.get("agent_id"),
            "conversationMessages": run.get("conversation_messages"),
            "startedAt": run.get("started_at") or datetime.utcnow().isoformat() + "Z",
        }
        if run.get("outcome"):
            item["outcome"] = run["outcome"]
        if run.get("outcome_reason"):
            item["outcomeReason"] = run["outcome_reason"]
        if run.get("ended_at"):
            item["endedAt"] = run["ended_at"]
        if run.get("model_id"):
            item["modelId"] = run["model_id"]
        if run.get("prompt_version"):
            item["promptVersion"] = run["prompt_version"]
        if run.get("session_id"):
            item["sessionId"] = run["session_id"]
        if run.get("customer_context"):
            item["customerContext"] = run["customer_context"]
        if run.get("metadata"):
            item["metadata"] = run["metadata"]
        payload.append(item)

    return post("/runs/batch", {"runs": payload}, api_version="v3")


def get_stats(
    agent_id: str,
    *,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> RunStats:
    """
    Get run statistics for an agent.

    Args:
        agent_id: The agent ID
        from_date: Start date ISO timestamp
        to_date: End date ISO timestamp

    Returns:
        RunStats with aggregated statistics
    """
    params: Dict[str, Any] = {}
    if from_date is not None:
        params["from"] = from_date
    if to_date is not None:
        params["to"] = to_date

    response = get(f"/runs/stats/{agent_id}", params=params, api_version="v3")
    return RunStats.from_dict(response)


__all__ = [
    "RunResult",
    "RunStats",
    "RunOutcome",
    "create",
    "get_by_id",
    "list_runs",
    "update",
    "delete_run",
    "batch_create",
    "get_stats",
]

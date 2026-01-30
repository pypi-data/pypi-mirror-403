"""
ThinkHive Python SDK - Business Metrics API
Industry-driven business metrics with historical tracking and external data support
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from ..client import post, get


@dataclass
class MetricTrend:
    """Metric trend information"""
    direction: str  # 'up', 'down', or 'stable'
    value: float
    is_positive: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricTrend":
        return cls(
            direction=data.get("direction", "stable"),
            value=data.get("value", 0.0),
            is_positive=data.get("isPositive", True),
        )


@dataclass
class CurrentMetricResponse:
    """Current metric value with status information"""
    metric_name: str
    metric_type: str  # 'trace_calculated' or 'external'
    value: Optional[float]
    value_formatted: str
    unit: Optional[str]
    status: str  # 'ready', 'insufficient_data', 'awaiting_external', 'stale'
    status_message: Optional[str]
    trend: Optional[MetricTrend]
    trace_count: Optional[int]
    min_trace_threshold: Optional[int]
    progress_percent: Optional[int]
    last_external_update: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurrentMetricResponse":
        trend_data = data.get("trend")
        return cls(
            metric_name=data.get("metricName", ""),
            metric_type=data.get("metricType", "trace_calculated"),
            value=data.get("value"),
            value_formatted=data.get("valueFormatted", "—"),
            unit=data.get("unit"),
            status=data.get("status", "ready"),
            status_message=data.get("statusMessage"),
            trend=MetricTrend.from_dict(trend_data) if trend_data else None,
            trace_count=data.get("traceCount"),
            min_trace_threshold=data.get("minTraceThreshold"),
            progress_percent=data.get("progressPercent"),
            last_external_update=data.get("lastExternalUpdate"),
        )


@dataclass
class MetricHistoryPoint:
    """Historical data point"""
    period_start: str
    period_end: str
    value: float
    value_formatted: Optional[str]
    source: str
    trace_count: Optional[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricHistoryPoint":
        return cls(
            period_start=data.get("periodStart", ""),
            period_end=data.get("periodEnd", ""),
            value=data.get("value", 0.0),
            value_formatted=data.get("valueFormatted"),
            source=data.get("source", "calculated"),
            trace_count=data.get("traceCount"),
        )


@dataclass
class MetricHistorySummary:
    """Historical summary statistics"""
    current: Optional[float]
    previous: Optional[float]
    change_percent: Optional[float]
    is_positive: bool
    data_point_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricHistorySummary":
        return cls(
            current=data.get("current"),
            previous=data.get("previous"),
            change_percent=data.get("changePercent"),
            is_positive=data.get("isPositive", True),
            data_point_count=data.get("dataPointCount", 0),
        )


@dataclass
class MetricHistoryResponse:
    """Full history response"""
    metric_name: str
    unit: str
    higher_is_better: bool
    data_points: List[MetricHistoryPoint]
    summary: MetricHistorySummary

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricHistoryResponse":
        return cls(
            metric_name=data.get("metricName", ""),
            unit=data.get("unit", "%"),
            higher_is_better=data.get("higherIsBetter", True),
            data_points=[MetricHistoryPoint.from_dict(p) for p in data.get("dataPoints", [])],
            summary=MetricHistorySummary.from_dict(data.get("summary", {})),
        )


@dataclass
class RecordMetricResponse:
    """Response from recording a metric value"""
    success: bool
    id: str
    recorded_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordMetricResponse":
        return cls(
            success=data.get("success", False),
            id=data.get("id", ""),
            recorded_at=data.get("recordedAt", ""),
        )


def get_current(
    agent_id: str,
    *,
    metric_name: Optional[str] = None,
) -> CurrentMetricResponse:
    """
    Get current metric value with status information.

    Args:
        agent_id: The agent ID
        metric_name: Specific metric name (optional, uses agent's primary if not provided)

    Returns:
        CurrentMetricResponse with value, status, and trend information

    Example:
        >>> from thinkhive.api import business_metrics
        >>>
        >>> metric = business_metrics.get_current("agent_123", metric_name="Deflection Rate")
        >>> print(f"{metric.metric_name}: {metric.value_formatted}")
        >>>
        >>> if metric.status == "insufficient_data":
        ...     print(f"Need {metric.min_trace_threshold - metric.trace_count} more traces")
    """
    params: Dict[str, Any] = {}

    if metric_name is not None:
        params["metricName"] = metric_name

    response = get(f"/agents/{agent_id}/metrics/current", params=params, api_version="v3")
    return CurrentMetricResponse.from_dict(response)


def get_history(
    agent_id: str,
    metric_name: str,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: Optional[str] = None,
) -> MetricHistoryResponse:
    """
    Get historical metric data for graphing.

    Args:
        agent_id: The agent ID
        metric_name: The metric name
        start_date: Start date ISO timestamp (defaults to 30 days ago)
        end_date: End date ISO timestamp (defaults to now)
        granularity: 'hourly', 'daily', 'weekly', or 'monthly' (defaults to 'daily')

    Returns:
        MetricHistoryResponse with data points and summary statistics

    Example:
        >>> from thinkhive.api import business_metrics
        >>>
        >>> history = business_metrics.get_history(
        ...     "agent_123",
        ...     "Deflection Rate",
        ...     start_date="2024-01-01T00:00:00Z",
        ...     end_date="2024-01-31T23:59:59Z",
        ...     granularity="daily"
        ... )
        >>> print(f"{len(history.data_points)} data points")
        >>> print(f"Change: {history.summary.change_percent}%")
    """
    params: Dict[str, Any] = {"metricName": metric_name}

    if start_date is not None:
        params["startDate"] = start_date
    if end_date is not None:
        params["endDate"] = end_date
    if granularity is not None:
        params["granularity"] = granularity

    response = get(f"/agents/{agent_id}/metrics/history", params=params, api_version="v3")
    return MetricHistoryResponse.from_dict(response)


def record_value(
    agent_id: str,
    *,
    metric_name: str,
    value: float,
    period_start: str,
    period_end: str,
    unit: Optional[str] = None,
    source: Optional[str] = None,
    source_details: Optional[Dict[str, Any]] = None,
) -> RecordMetricResponse:
    """
    Record an external metric value.

    Use this to ingest metrics from external data sources (CRM, surveys, billing, etc.)

    Args:
        agent_id: The agent ID
        metric_name: The metric name (must be configured for the agent)
        value: The numeric value
        period_start: Start of the period this value covers (ISO timestamp)
        period_end: End of the period this value covers (ISO timestamp)
        unit: Unit of measurement (optional, defaults to metric's configured unit)
        source: Source identifier (optional, defaults to 'api')
        source_details: Additional metadata about the source (optional)

    Returns:
        RecordMetricResponse with success status and record ID

    Example:
        >>> from thinkhive.api import business_metrics
        >>>
        >>> # Record CSAT score from survey system
        >>> result = business_metrics.record_value(
        ...     "agent_123",
        ...     metric_name="CSAT/NPS",
        ...     value=4.5,
        ...     period_start="2024-01-01T00:00:00Z",
        ...     period_end="2024-01-07T23:59:59Z",
        ...     unit="score",
        ...     source="survey_system",
        ...     source_details={"survey_id": "survey_456", "response_count": 150}
        ... )
        >>> print(f"Recorded: {result.id}")
    """
    body: Dict[str, Any] = {
        "metricName": metric_name,
        "value": value,
        "periodStart": period_start,
        "periodEnd": period_end,
    }

    if unit is not None:
        body["unit"] = unit
    if source is not None:
        body["source"] = source
    if source_details is not None:
        body["sourceDetails"] = source_details

    response = post(f"/agents/{agent_id}/metrics/values", body, api_version="v3")
    return RecordMetricResponse.from_dict(response)


def record_batch(
    agent_id: str,
    metrics: List[Dict[str, Any]],
) -> List[RecordMetricResponse]:
    """
    Batch record multiple external metric values.

    Args:
        agent_id: The agent ID
        metrics: List of metric records, each with keys:
            - metric_name: str
            - value: float
            - period_start: str
            - period_end: str
            - unit: Optional[str]
            - source: Optional[str]
            - source_details: Optional[Dict]

    Returns:
        List of RecordMetricResponse for each recorded metric

    Example:
        >>> from thinkhive.api import business_metrics
        >>>
        >>> results = business_metrics.record_batch("agent_123", [
        ...     {"metric_name": "CSAT/NPS", "value": 4.5, "period_start": "...", "period_end": "..."},
        ...     {"metric_name": "Hours Saved", "value": 120, "period_start": "...", "period_end": "..."},
        ... ])
    """
    results = []
    for metric in metrics:
        result = record_value(
            agent_id,
            metric_name=metric["metric_name"],
            value=metric["value"],
            period_start=metric["period_start"],
            period_end=metric["period_end"],
            unit=metric.get("unit"),
            source=metric.get("source"),
            source_details=metric.get("source_details"),
        )
        results.append(result)
    return results


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def is_metric_ready(metric: CurrentMetricResponse) -> bool:
    """Check if a metric is ready to display"""
    return metric.status == "ready"


def needs_more_traces(metric: CurrentMetricResponse) -> bool:
    """Check if a metric needs more trace data"""
    return metric.status == "insufficient_data"


def awaiting_external_data(metric: CurrentMetricResponse) -> bool:
    """Check if a metric is waiting for external data"""
    return metric.status == "awaiting_external"


def is_metric_stale(metric: CurrentMetricResponse) -> bool:
    """Check if metric data is stale"""
    return metric.status == "stale"


def get_status_message(metric: CurrentMetricResponse) -> str:
    """Get human-readable status message"""
    if metric.status == "ready":
        return "Metric is up to date"
    elif metric.status == "insufficient_data":
        if metric.status_message:
            return metric.status_message
        needed = (metric.min_trace_threshold or 50) - (metric.trace_count or 0)
        return f"Need {needed} more traces"
    elif metric.status == "awaiting_external":
        return metric.status_message or "Waiting for external data source"
    elif metric.status == "stale":
        return metric.status_message or "Data may be outdated"
    else:
        return "Unknown status"


def get_trace_progress(metric: CurrentMetricResponse) -> int:
    """Calculate progress toward minimum trace threshold"""
    if metric.status != "insufficient_data":
        return 100
    return metric.progress_percent or 0


def format_metric_value(value: float, unit: str) -> str:
    """Format metric value for display based on unit"""
    if unit == "%":
        return f"{round(value * 10) / 10}%"
    elif unit == "$":
        return f"${value:,.2f}"
    elif unit == "s":
        if value < 60:
            return f"{round(value)}s"
        return f"{round(value / 60)}m"
    elif unit == "hrs":
        return f"{round(value * 10) / 10} hrs"
    elif unit == "score":
        return f"{value:.1f}"
    else:
        return str(round(value * 100) / 100)


__all__ = [
    # Dataclasses
    "MetricTrend",
    "CurrentMetricResponse",
    "MetricHistoryPoint",
    "MetricHistorySummary",
    "MetricHistoryResponse",
    "RecordMetricResponse",
    # API functions
    "get_current",
    "get_history",
    "record_value",
    "record_batch",
    # Helper functions
    "is_metric_ready",
    "needs_more_traces",
    "awaiting_external_data",
    "is_metric_stale",
    "get_status_message",
    "get_trace_progress",
    "format_metric_value",
]

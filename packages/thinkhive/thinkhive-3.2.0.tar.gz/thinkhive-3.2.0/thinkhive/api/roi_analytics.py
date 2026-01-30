"""
ThinkHive Python SDK - ROI Analytics API
Business ROI & Metrics Engine for calculating financial impact
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from ..client import post, get


@dataclass
class IndustryConfig:
    """Industry-specific ROI configuration"""
    id: str
    name: str
    avg_transaction_value: float
    avg_customer_ltv: float
    avg_support_cost: float
    avg_escalation_cost: float
    avg_resolution_time: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndustryConfig":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            avg_transaction_value=data.get("avgTransactionValue", 0.0),
            avg_customer_ltv=data.get("avgCustomerLTV", 0.0),
            avg_support_cost=data.get("avgSupportCost", 0.0),
            avg_escalation_cost=data.get("avgEscalationCost", 0.0),
            avg_resolution_time=data.get("avgResolutionTime", 0.0),
        )


@dataclass
class ROIMetrics:
    """Aggregated ROI metrics"""
    roi_category: str
    total_financial_impact: float
    revenue_protected: float
    cost_savings: float
    efficiency_gain: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ROIMetrics":
        return cls(
            roi_category=data.get("roiCategory", "unknown"),
            total_financial_impact=data.get("totalFinancialImpact", 0.0),
            revenue_protected=data.get("revenueProtected", 0.0),
            cost_savings=data.get("costSavings", 0.0),
            efficiency_gain=data.get("efficiencyGain", 0.0),
        )


@dataclass
class BusinessImpact:
    """Business impact analysis result"""
    impact_score: float
    revenue_risk: float
    brand_risk: float
    compliance_risk: float
    operational_impact: float
    customer_satisfaction: float
    recommendations: List[str]
    roi: ROIMetrics

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessImpact":
        roi_data = data.get("roi", {})
        return cls(
            impact_score=data.get("impactScore", 0.0),
            revenue_risk=data.get("revenueRisk", 0.0),
            brand_risk=data.get("brandRisk", 0.0),
            compliance_risk=data.get("complianceRisk", 0.0),
            operational_impact=data.get("operationalImpact", 0.0),
            customer_satisfaction=data.get("customerSatisfaction", 0.0),
            recommendations=data.get("recommendations", []),
            roi=ROIMetrics.from_dict(roi_data),
        )


@dataclass
class TrendDataPoint:
    """A single data point in trend analysis"""
    date: str
    trace_count: int
    success_count: int
    failure_count: int
    success_rate: int
    avg_impact_score: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrendDataPoint":
        return cls(
            date=data.get("date", ""),
            trace_count=data.get("traceCount", 0),
            success_count=data.get("successCount", 0),
            failure_count=data.get("failureCount", 0),
            success_rate=data.get("successRate", 0),
            avg_impact_score=data.get("avgImpactScore", 0.0),
        )


@dataclass
class ROISummary:
    """Summary of ROI analytics"""
    date_range: Dict[str, str]
    trace_count: int
    successful_interactions: int
    failed_interactions: int
    success_rate: int
    roi: Dict[str, Any]
    revenue_protected: float
    estimated_savings: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ROISummary":
        return cls(
            date_range=data.get("dateRange", {}),
            trace_count=data.get("traceCount", 0),
            successful_interactions=data.get("successfulInteractions", 0),
            failed_interactions=data.get("failedInteractions", 0),
            success_rate=data.get("successRate", 0),
            roi=data.get("roi", {}),
            revenue_protected=data.get("revenueProtected", 0.0),
            estimated_savings=data.get("estimatedSavings", 0.0),
        )


def get_summary(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> ROISummary:
    """
    Get aggregated ROI summary for traces in date range.

    Args:
        start_date: Start date ISO timestamp
        end_date: End date ISO timestamp
        agent_id: Filter by agent ID

    Returns:
        ROISummary with aggregated metrics

    Example:
        >>> from thinkhive.api import roi_analytics
        >>>
        >>> summary = roi_analytics.get_summary(
        ...     start_date="2024-01-01T00:00:00Z",
        ...     end_date="2024-01-31T23:59:59Z"
        ... )
        >>> print(f"Revenue protected: ${summary.revenue_protected}")
    """
    params: Dict[str, Any] = {}

    if start_date is not None:
        params["startDate"] = start_date
    if end_date is not None:
        params["endDate"] = end_date
    if agent_id is not None:
        params["agentId"] = agent_id

    response = get("/analytics/roi/summary", params=params, api_version="v1")
    return ROISummary.from_dict(response.get("summary", {}))


def get_by_agent(
    agent_id: str,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get ROI metrics for a specific agent.

    Args:
        agent_id: The agent ID
        start_date: Start date ISO timestamp
        end_date: End date ISO timestamp

    Returns:
        Dict with 'agent', 'industryConfig', 'roi', 'recentImpacts'
    """
    params: Dict[str, Any] = {}

    if start_date is not None:
        params["startDate"] = start_date
    if end_date is not None:
        params["endDate"] = end_date

    return get(f"/analytics/roi/by-agent/{agent_id}", params=params, api_version="v1")


def get_trends(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> List[TrendDataPoint]:
    """
    Get ROI trends over time.

    Args:
        start_date: Start date ISO timestamp (defaults to 30 days ago)
        end_date: End date ISO timestamp (defaults to now)
        agent_id: Filter by agent ID

    Returns:
        List of TrendDataPoint with daily metrics
    """
    params: Dict[str, Any] = {}

    if start_date is not None:
        params["startDate"] = start_date
    if end_date is not None:
        params["endDate"] = end_date
    if agent_id is not None:
        params["agentId"] = agent_id

    response = get("/analytics/roi/trends", params=params, api_version="v1")
    trends = response.get("trends", [])
    return [TrendDataPoint.from_dict(t) for t in trends]


def calculate(
    *,
    trace_id: Optional[str] = None,
    user_message: Optional[str] = None,
    agent_response: Optional[str] = None,
    industry_config: Optional[Dict[str, Any]] = None,
) -> BusinessImpact:
    """
    Calculate ROI for a trace or provided message data.

    Args:
        trace_id: Existing trace ID to calculate ROI for
        user_message: User message (if not using trace_id)
        agent_response: Agent response (if not using trace_id)
        industry_config: Custom industry configuration with keys:
            - industry: Industry name
            - avg_transaction_value: Average transaction value
            - avg_customer_ltv: Average customer lifetime value
            - avg_support_cost: Average support cost
            - avg_escalation_cost: Average escalation cost
            - churn_impact_multiplier: Churn impact multiplier
            - avg_resolution_time: Average resolution time

    Returns:
        BusinessImpact with impact scores and ROI metrics

    Example:
        >>> from thinkhive.api import roi_analytics
        >>>
        >>> # Calculate for existing trace
        >>> impact = roi_analytics.calculate(trace_id="trace-123")
        >>>
        >>> # Calculate for new data with custom config
        >>> impact = roi_analytics.calculate(
        ...     user_message="Help me cancel my subscription",
        ...     agent_response="I can help with that...",
        ...     industry_config={
        ...         "industry": "saas",
        ...         "avg_customer_ltv": 10000
        ...     }
        ... )
    """
    body: Dict[str, Any] = {}

    if trace_id is not None:
        body["traceId"] = trace_id
    if user_message is not None:
        body["userMessage"] = user_message
    if agent_response is not None:
        body["agentResponse"] = agent_response
    if industry_config is not None:
        # Convert snake_case to camelCase
        camel_config = {}
        if "industry" in industry_config:
            camel_config["industry"] = industry_config["industry"]
        if "avg_transaction_value" in industry_config:
            camel_config["avgTransactionValue"] = industry_config["avg_transaction_value"]
        if "avg_customer_ltv" in industry_config:
            camel_config["avgCustomerLTV"] = industry_config["avg_customer_ltv"]
        if "avg_support_cost" in industry_config:
            camel_config["avgSupportCost"] = industry_config["avg_support_cost"]
        if "avg_escalation_cost" in industry_config:
            camel_config["avgEscalationCost"] = industry_config["avg_escalation_cost"]
        if "churn_impact_multiplier" in industry_config:
            camel_config["churnImpactMultiplier"] = industry_config["churn_impact_multiplier"]
        if "avg_resolution_time" in industry_config:
            camel_config["avgResolutionTime"] = industry_config["avg_resolution_time"]
        body["industryConfig"] = camel_config

    response = post("/analytics/roi/calculate", body, api_version="v1")
    return BusinessImpact.from_dict(response.get("impact", {}))


def get_industries() -> List[IndustryConfig]:
    """
    Get available industry configurations.

    Returns:
        List of IndustryConfig with default values for each industry
    """
    response = get("/analytics/roi/industries", api_version="v1")
    industries = response.get("industries", [])
    return [IndustryConfig.from_dict(i) for i in industries]


def get_correlations(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get correlation analysis for traces.

    Args:
        start_date: Start date ISO timestamp
        end_date: End date ISO timestamp
        agent_id: Filter by agent ID

    Returns:
        Dict with correlation analysis including:
        - analysisId: Unique analysis ID
        - traceCount: Number of traces analyzed
        - overallHealthScore: Overall health score (0-100)
        - topInsights: List of top insights
        - recommendations: List of recommendations
        - correlations: List of correlation findings
        - patternClusters: Identified pattern clusters
    """
    params: Dict[str, Any] = {}

    if start_date is not None:
        params["startDate"] = start_date
    if end_date is not None:
        params["endDate"] = end_date
    if agent_id is not None:
        params["agentId"] = agent_id

    response = get("/analytics/correlations", params=params, api_version="v1")
    return response.get("analysis", {})


__all__ = [
    # Dataclasses
    "IndustryConfig",
    "ROIMetrics",
    "BusinessImpact",
    "TrendDataPoint",
    "ROISummary",
    # API functions
    "get_summary",
    "get_by_agent",
    "get_trends",
    "calculate",
    "get_industries",
    "get_correlations",
]

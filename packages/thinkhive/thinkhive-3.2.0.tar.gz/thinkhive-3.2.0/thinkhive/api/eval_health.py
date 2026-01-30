"""
ThinkHive Python SDK - Evaluation Health API
API for eval saturation monitoring, regression detection, and health reports
"""

from typing import Optional, List, Dict, Any, Literal
from ..client import get, post


SaturationType = Literal["ceiling", "floor", "healthy"]
HealthStatus = Literal["healthy", "warning", "critical"]
RegressionSeverity = Literal["minor", "moderate", "severe"]


class EvalHealthApi:
    """Evaluation Health API client"""

    def get_report(self, agent_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health report for an agent

        Args:
            agent_id: Agent ID

        Returns:
            Health report with status, regressions, and recommendations
        """
        return get("/eval-health/report", params={"agentId": agent_id})

    # Snapshots

    def get_snapshots(
        self,
        agent_id: str,
        criterion_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get historical health snapshots

        Args:
            agent_id: Agent ID
            criterion_id: Optional criterion filter
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of health snapshots
        """
        params = {"agentId": agent_id}
        if criterion_id:
            params["criterionId"] = criterion_id
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        return get("/eval-health/snapshots", params=params)

    def get_latest_snapshot(
        self,
        agent_id: str,
        criterion_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get latest health snapshot"""
        params = {"agentId": agent_id}
        if criterion_id:
            params["criterionId"] = criterion_id

        return get("/eval-health/snapshots/latest", params=params)

    def record_snapshot(
        self,
        agent_id: str,
        snapshot_date: str,
        criterion_id: Optional[str] = None,
        pass_rate: Optional[str] = None,
        eval_count: Optional[int] = None,
        mean_score: Optional[str] = None,
        saturation_type: Optional[SaturationType] = None,
        days_at_saturation: Optional[int] = None,
        trend_direction: Optional[str] = None,
        trend_strength: Optional[str] = None,
        health_status: Optional[HealthStatus] = None,
        health_score: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a health snapshot

        Args:
            agent_id: Agent ID
            snapshot_date: Snapshot date (ISO format)
            criterion_id: Optional criterion ID
            pass_rate: Pass rate (decimal string)
            eval_count: Number of evaluations
            mean_score: Mean score (decimal string)
            saturation_type: Saturation status
            days_at_saturation: Days at saturation
            trend_direction: Trend direction
            trend_strength: Trend strength (decimal string)
            health_status: Overall health status
            health_score: Health score (decimal string)

        Returns:
            Created snapshot
        """
        body = {"agentId": agent_id, "snapshotDate": snapshot_date}
        if criterion_id:
            body["criterionId"] = criterion_id
        if pass_rate:
            body["passRate"] = pass_rate
        if eval_count is not None:
            body["evalCount"] = eval_count
        if mean_score:
            body["meanScore"] = mean_score
        if saturation_type:
            body["saturationType"] = saturation_type
        if days_at_saturation is not None:
            body["daysAtSaturation"] = days_at_saturation
        if trend_direction:
            body["trendDirection"] = trend_direction
        if trend_strength:
            body["trendStrength"] = trend_strength
        if health_status:
            body["healthStatus"] = health_status
        if health_score:
            body["healthScore"] = health_score

        return post("/eval-health/snapshots", body=body)

    # Regressions

    def get_regressions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get unresolved regressions for an agent"""
        return get("/eval-health/regressions", params={"agentId": agent_id})

    def record_regression(
        self,
        agent_id: str,
        severity: RegressionSeverity,
        baseline_pass_rate: str,
        current_pass_rate: str,
        delta: str,
        baseline_period_start: str,
        baseline_period_end: str,
        current_period_start: str,
        current_period_end: str,
        criterion_id: Optional[str] = None,
        delta_percent: Optional[str] = None,
        baseline_eval_count: Optional[int] = None,
        current_eval_count: Optional[int] = None,
        suspected_causes: Optional[List[Dict[str, Any]]] = None,
        is_significant: Optional[bool] = None,
        detected_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a new regression

        Args:
            agent_id: Agent ID
            severity: Regression severity
            baseline_pass_rate: Baseline pass rate
            current_pass_rate: Current pass rate
            delta: Absolute change
            baseline_period_start: Baseline period start (ISO format)
            baseline_period_end: Baseline period end (ISO format)
            current_period_start: Current period start (ISO format)
            current_period_end: Current period end (ISO format)
            criterion_id: Optional criterion ID
            delta_percent: Percentage change
            baseline_eval_count: Evaluations in baseline
            current_eval_count: Evaluations in current period
            suspected_causes: List of suspected causes
            is_significant: Statistical significance
            detected_at: Detection timestamp (ISO format)

        Returns:
            Created regression
        """
        body = {
            "agentId": agent_id,
            "severity": severity,
            "baselinePassRate": baseline_pass_rate,
            "currentPassRate": current_pass_rate,
            "delta": delta,
            "baselinePeriodStart": baseline_period_start,
            "baselinePeriodEnd": baseline_period_end,
            "currentPeriodStart": current_period_start,
            "currentPeriodEnd": current_period_end,
        }
        if criterion_id:
            body["criterionId"] = criterion_id
        if delta_percent:
            body["deltaPercent"] = delta_percent
        if baseline_eval_count is not None:
            body["baselineEvalCount"] = baseline_eval_count
        if current_eval_count is not None:
            body["currentEvalCount"] = current_eval_count
        if suspected_causes:
            body["suspectedCauses"] = suspected_causes
        if is_significant is not None:
            body["isSignificant"] = is_significant
        if detected_at:
            body["detectedAt"] = detected_at

        return post("/eval-health/regressions", body=body)

    def resolve_regression(
        self,
        regression_id: str,
        resolution_type: str,
        notes: Optional[str] = None,
    ) -> None:
        """
        Resolve a regression

        Args:
            regression_id: Regression ID
            resolution_type: Type of resolution
            notes: Optional resolution notes
        """
        body = {"resolutionType": resolution_type}
        if notes:
            body["notes"] = notes
        post(f"/eval-health/regressions/{regression_id}/resolve", body=body)

    def acknowledge_regression(self, regression_id: str) -> None:
        """Acknowledge a regression"""
        post(f"/eval-health/regressions/{regression_id}/acknowledge")


# Singleton instance
eval_health = EvalHealthApi()


# Helper functions

def has_health_issue(status: HealthStatus) -> bool:
    """Check if health status indicates an issue"""
    return status in ("warning", "critical")


def get_severity_level(severity: RegressionSeverity) -> int:
    """Get severity level as numeric value for sorting"""
    levels = {"minor": 1, "moderate": 2, "severe": 3}
    return levels.get(severity, 0)


def is_saturated(snapshot: Dict[str, Any]) -> bool:
    """Check if evaluation is saturated"""
    sat_type = snapshot.get("saturationType")
    return sat_type in ("ceiling", "floor")


def get_saturation_recommendation(saturation_type: SaturationType) -> str:
    """Get recommendation for saturation type"""
    recommendations = {
        "ceiling": "Evaluation criteria may be too lenient. Consider adding stricter checks.",
        "floor": "Evaluation criteria may be too strict. Consider relaxing thresholds.",
        "healthy": "Evaluation is operating within healthy parameters.",
    }
    return recommendations.get(saturation_type, "Unable to determine saturation status.")


__all__ = [
    "eval_health",
    "EvalHealthApi",
    "SaturationType",
    "HealthStatus",
    "RegressionSeverity",
    "has_health_issue",
    "get_severity_level",
    "is_saturated",
    "get_saturation_recommendation",
]

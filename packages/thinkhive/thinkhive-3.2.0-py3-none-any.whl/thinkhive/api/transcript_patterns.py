"""
ThinkHive Python SDK - Transcript Patterns API
API for transcript pattern detection and analysis
"""

from typing import Optional, List, Dict, Any, Literal
from ..client import get, post


PatternCategory = Literal[
    "frustration", "confusion", "success", "failure",
    "escalation", "pii_exposure", "hallucination", "custom"
]
PatternOutcome = Literal["success", "failure", "escalation", "neutral"]
PatternSeverity = Literal["info", "warning", "critical"]


class TranscriptPatternsApi:
    """Transcript Patterns API client"""

    def analyze(self, trace_id: str) -> Dict[str, Any]:
        """
        Analyze a trace for patterns

        Args:
            trace_id: Trace ID to analyze

        Returns:
            Analysis result with matches, risk score, and insights
        """
        return post("/transcript-patterns/analyze", body={"traceId": trace_id})

    def bulk_analyze(self, trace_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple traces for patterns

        Args:
            trace_ids: List of trace IDs to analyze

        Returns:
            Results with summary
        """
        return post("/transcript-patterns/bulk-analyze", body={"traceIds": trace_ids})

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get available pattern categories with descriptions"""
        return get("/transcript-patterns/categories")

    def get_built_in_patterns(self) -> List[Dict[str, Any]]:
        """Get built-in patterns"""
        return get("/transcript-patterns/built-in")


# Singleton instance
transcript_patterns = TranscriptPatternsApi()


# Helper functions

def is_high_risk(result: Dict[str, Any], threshold: float = 70) -> bool:
    """
    Check if analysis result indicates high risk

    Args:
        result: Analysis result
        threshold: Risk score threshold

    Returns:
        Whether the result indicates high risk
    """
    return result.get("riskScore", 0) >= threshold


def get_matches_by_category(
    result: Dict[str, Any],
    category: PatternCategory,
) -> List[Dict[str, Any]]:
    """
    Get matches by category

    Args:
        result: Analysis result
        category: Pattern category to filter by

    Returns:
        Filtered pattern matches
    """
    matches = result.get("matches", [])
    return [m for m in matches if m.get("category") == category]


def get_critical_insights(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get critical insights from analysis

    Args:
        result: Analysis result

    Returns:
        Critical severity insights
    """
    insights = result.get("insights", [])
    return [i for i in insights if i.get("severity") == "critical"]


def has_pii_exposure(result: Dict[str, Any]) -> bool:
    """Check if analysis detected PII"""
    matches = result.get("matches", [])
    return any(m.get("category") == "pii_exposure" for m in matches)


def has_frustration_signals(result: Dict[str, Any]) -> bool:
    """Check if analysis detected frustration"""
    matches = result.get("matches", [])
    return any(m.get("category") == "frustration" for m in matches)


def has_escalation_request(result: Dict[str, Any]) -> bool:
    """Check if analysis detected escalation request"""
    matches = result.get("matches", [])
    return any(m.get("category") == "escalation" for m in matches)


def get_category_distribution(result: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate category distribution

    Args:
        result: Analysis result

    Returns:
        Dict with counts per category
    """
    distribution = {
        "frustration": 0,
        "confusion": 0,
        "success": 0,
        "failure": 0,
        "escalation": 0,
        "pii_exposure": 0,
        "hallucination": 0,
        "custom": 0,
    }

    for match in result.get("matches", []):
        category = match.get("category")
        if category in distribution:
            distribution[category] += 1

    return distribution


def get_recommendations(result: Dict[str, Any]) -> List[str]:
    """
    Get actionable recommendations from insights

    Args:
        result: Analysis result

    Returns:
        List of recommendation strings
    """
    insights = result.get("insights", [])
    return [i["recommendation"] for i in insights if i.get("recommendation")]


def needs_attention(result: Dict[str, Any]) -> bool:
    """
    Determine if conversation needs attention based on patterns

    Args:
        result: Analysis result

    Returns:
        Whether the conversation needs attention
    """
    if result.get("riskScore", 0) >= 50:
        return True
    if has_pii_exposure(result):
        return True
    if has_escalation_request(result):
        return True
    insights = result.get("insights", [])
    if any(i.get("severity") == "critical" for i in insights):
        return True
    return False


def get_severity_level(severity: PatternSeverity) -> int:
    """
    Get severity level as numeric value

    Args:
        severity: Pattern severity

    Returns:
        Numeric severity (1-3)
    """
    levels = {"info": 1, "warning": 2, "critical": 3}
    return levels.get(severity, 0)


def sort_matches_by_severity(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort matches by severity (critical first)

    Args:
        matches: Pattern matches to sort

    Returns:
        Sorted matches
    """
    return sorted(
        matches,
        key=lambda m: get_severity_level(m.get("severity", "info")),
        reverse=True,
    )


__all__ = [
    "transcript_patterns",
    "TranscriptPatternsApi",
    "PatternCategory",
    "PatternOutcome",
    "PatternSeverity",
    "is_high_risk",
    "get_matches_by_category",
    "get_critical_insights",
    "has_pii_exposure",
    "has_frustration_signals",
    "has_escalation_request",
    "get_category_distribution",
    "get_recommendations",
    "needs_attention",
    "get_severity_level",
    "sort_matches_by_severity",
]

"""
ThinkHive Python SDK - Deterministic Graders API
API for running deterministic (code-based) evaluations
"""

from typing import Optional, List, Dict, Any, Literal
from ..client import get, post


RuleType = Literal[
    "regex", "contains", "not_contains", "json_valid", "json_schema",
    "length", "pii_check", "sentiment", "latency", "token_count"
]


class DeterministicGradersApi:
    """Deterministic Graders API client"""

    def evaluate(
        self,
        trace_id: str,
        criterion_id: str,
    ) -> Dict[str, Any]:
        """
        Run deterministic evaluation on a single trace

        Args:
            trace_id: Trace ID to evaluate
            criterion_id: Evaluation criterion ID

        Returns:
            Evaluation result with passed, score, and rule results
        """
        return post(
            "/deterministic-graders/evaluate",
            body={"traceId": trace_id, "criterionId": criterion_id},
        )

    def bulk_evaluate(
        self,
        evaluations: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Run deterministic evaluations on multiple traces

        Args:
            evaluations: List of {"traceId": str, "criterionId": str}

        Returns:
            Results and summary with pass rate
        """
        return post(
            "/deterministic-graders/bulk-evaluate",
            body={"evaluations": evaluations},
        )

    def get_rule_types(self) -> List[Dict[str, Any]]:
        """Get available rule types with descriptions"""
        return get("/deterministic-graders/rule-types")

    def get_templates(self) -> List[Dict[str, Any]]:
        """Get rule templates"""
        return get("/deterministic-graders/templates")


# Singleton instance
deterministic_graders = DeterministicGradersApi()


# Helper functions

def create_regex_rule(pattern: str, flags: str = "gi") -> Dict[str, str]:
    """
    Create a regex rule configuration

    Args:
        pattern: Regular expression pattern
        flags: Regex flags (default: 'gi')

    Returns:
        Rule configuration object
    """
    return {"pattern": pattern, "flags": flags}


def create_contains_rule(
    values: List[str],
    case_sensitive: bool = False,
) -> Dict[str, Any]:
    """
    Create a contains rule configuration

    Args:
        values: Strings to check for
        case_sensitive: Whether comparison is case-sensitive

    Returns:
        Rule configuration object
    """
    return {"values": values, "caseSensitive": case_sensitive}


def create_length_rule(
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a length rule configuration

    Args:
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        Rule configuration object
    """
    config = {}
    if min_length is not None:
        config["min"] = min_length
    if max_length is not None:
        config["max"] = max_length
    return config


def create_json_schema_rule(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a JSON schema rule configuration

    Args:
        schema: JSON Schema object

    Returns:
        Rule configuration object
    """
    return {"schema": schema}


def all_rules_passed(results: List[Dict[str, Any]]) -> bool:
    """Check if all rule results passed"""
    return all(r.get("passed", False) for r in results)


def get_failed_rules(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get failed rules from results"""
    return [r for r in results if not r.get("passed", False)]


def calculate_average_score(results: List[Dict[str, Any]]) -> float:
    """Calculate average score from rule results"""
    if not results:
        return 0.0
    scores = [r.get("score", 0) for r in results]
    return sum(scores) / len(scores)


__all__ = [
    "deterministic_graders",
    "DeterministicGradersApi",
    "RuleType",
    "create_regex_rule",
    "create_contains_rule",
    "create_length_rule",
    "create_json_schema_rule",
    "all_rules_passed",
    "get_failed_rules",
    "calculate_average_score",
]

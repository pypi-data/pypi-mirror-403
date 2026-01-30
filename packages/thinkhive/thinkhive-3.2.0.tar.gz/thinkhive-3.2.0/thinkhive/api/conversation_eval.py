"""
ThinkHive Python SDK - Conversation Evaluation API
API for multi-turn conversation evaluation
"""

from typing import Optional, List, Dict, Any, Literal, Callable
from ..client import get, post


AggregateMethod = Literal["worst", "average", "weighted", "final_turn", "majority"]


class ConversationEvalApi:
    """Conversation Evaluation API client"""

    def get_session_traces(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get traces for a conversation session

        Args:
            session_id: Session ID

        Returns:
            List of session traces with turn numbers
        """
        return get("/conversation-eval/traces", params={"sessionId": session_id})

    def evaluate(
        self,
        session_id: str,
        criterion_id: str,
        aggregate_method: AggregateMethod = "average",
        min_turns: Optional[int] = None,
        max_turns: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run conversation-level evaluation

        Args:
            session_id: Session ID
            criterion_id: Evaluation criterion ID
            aggregate_method: Method for aggregating turn results
            min_turns: Minimum turns required
            max_turns: Maximum turns to evaluate

        Returns:
            Conversation evaluation result
        """
        body = {
            "sessionId": session_id,
            "criterionId": criterion_id,
            "options": {"aggregateMethod": aggregate_method},
        }
        if min_turns is not None:
            body["options"]["minTurns"] = min_turns
        if max_turns is not None:
            body["options"]["maxTurns"] = max_turns

        return post("/conversation-eval/evaluate", body=body)

    def get_aggregation_methods(self) -> List[Dict[str, Any]]:
        """Get available aggregation methods with descriptions"""
        return get("/conversation-eval/aggregation-methods")


# Singleton instance
conversation_eval = ConversationEvalApi()


# Aggregation helper functions

def aggregate_worst(turn_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate worst-turn aggregation

    Args:
        turn_results: List of turn evaluation results

    Returns:
        Dict with passed and score (fails if any turn fails)
    """
    if not turn_results:
        return {"passed": False, "score": 0}

    scores = [t.get("score", 0) for t in turn_results]
    worst_score = min(scores)
    passed = all(t.get("passed", False) for t in turn_results)

    return {"passed": passed, "score": worst_score}


def aggregate_average(turn_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate average aggregation

    Args:
        turn_results: List of turn evaluation results

    Returns:
        Dict with passed (majority vote) and average score
    """
    if not turn_results:
        return {"passed": False, "score": 0}

    scores = [t.get("score", 0) for t in turn_results]
    avg_score = sum(scores) / len(scores)
    passed_count = sum(1 for t in turn_results if t.get("passed", False))
    passed = passed_count > len(turn_results) / 2

    return {"passed": passed, "score": avg_score}


def aggregate_weighted(turn_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate weighted average aggregation (later turns weighted more)

    Args:
        turn_results: List of turn evaluation results

    Returns:
        Dict with passed and weighted average score
    """
    if not turn_results:
        return {"passed": False, "score": 0}

    weighted_sum = 0
    weight_total = 0
    weighted_pass_sum = 0

    for i, turn in enumerate(turn_results):
        weight = i + 1
        weighted_sum += turn.get("score", 0) * weight
        weighted_pass_sum += (1 if turn.get("passed", False) else 0) * weight
        weight_total += weight

    avg_score = weighted_sum / weight_total
    passed = (weighted_pass_sum / weight_total) > 0.5

    return {"passed": passed, "score": avg_score}


def aggregate_final_turn(turn_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate final-turn aggregation

    Args:
        turn_results: List of turn evaluation results

    Returns:
        Dict with passed and score from final turn only
    """
    if not turn_results:
        return {"passed": False, "score": 0}

    final_turn = turn_results[-1]
    return {
        "passed": final_turn.get("passed", False),
        "score": final_turn.get("score", 0),
    }


def aggregate_majority(turn_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate majority vote aggregation

    Args:
        turn_results: List of turn evaluation results

    Returns:
        Dict with passed (majority) and average score
    """
    if not turn_results:
        return {"passed": False, "score": 0}

    scores = [t.get("score", 0) for t in turn_results]
    avg_score = sum(scores) / len(scores)
    passed_count = sum(1 for t in turn_results if t.get("passed", False))
    passed = passed_count > len(turn_results) / 2

    return {"passed": passed, "score": avg_score}


def get_aggregator(method: AggregateMethod) -> Callable:
    """
    Get appropriate aggregation function for a method

    Args:
        method: Aggregation method name

    Returns:
        Aggregation function
    """
    aggregators = {
        "worst": aggregate_worst,
        "average": aggregate_average,
        "weighted": aggregate_weighted,
        "final_turn": aggregate_final_turn,
        "majority": aggregate_majority,
    }
    return aggregators.get(method, aggregate_average)


def get_problematic_turns(
    result: Dict[str, Any],
    score_threshold: float = 70,
) -> List[Dict[str, Any]]:
    """
    Find problematic turns in a conversation

    Args:
        result: Conversation evaluation result
        score_threshold: Minimum acceptable score

    Returns:
        List of problematic turn results
    """
    turn_results = result.get("turnResults", [])
    return [
        t for t in turn_results
        if not t.get("passed", False) or t.get("score", 0) < score_threshold
    ]


def analyze_conversation_trend(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate conversation quality trend

    Args:
        result: Conversation evaluation result

    Returns:
        Dict with direction, first_half_avg, and second_half_avg
    """
    turns = result.get("turnResults", [])
    if len(turns) < 2:
        return {"direction": "stable", "first_half_avg": 0, "second_half_avg": 0}

    midpoint = len(turns) // 2
    first_half = turns[:midpoint]
    second_half = turns[midpoint:]

    first_half_avg = sum(t.get("score", 0) for t in first_half) / len(first_half)
    second_half_avg = sum(t.get("score", 0) for t in second_half) / len(second_half)

    diff = second_half_avg - first_half_avg
    if diff > 5:
        direction = "improving"
    elif diff < -5:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "direction": direction,
        "first_half_avg": first_half_avg,
        "second_half_avg": second_half_avg,
    }


__all__ = [
    "conversation_eval",
    "ConversationEvalApi",
    "AggregateMethod",
    "aggregate_worst",
    "aggregate_average",
    "aggregate_weighted",
    "aggregate_final_turn",
    "aggregate_majority",
    "get_aggregator",
    "get_problematic_turns",
    "analyze_conversation_trend",
]

"""
ThinkHive Python SDK - Non-Determinism API
API for pass@k / pass^k analysis to measure LLM evaluation reliability
"""

from typing import Optional, List, Dict, Any, Literal
import math
from ..client import get, post


NondeterminismRunType = Literal["pass_at_k", "pass_to_k", "variance", "reliability"]
NondeterminismRunStatus = Literal["pending", "running", "completed", "failed", "cancelled"]


class NondeterminismApi:
    """Non-Determinism API client for pass@k analysis"""

    def create_run(
        self,
        agent_id: str,
        k_value: int,
        trace_ids: List[str],
        criterion_id: Optional[str] = None,
        criteria_ids: Optional[List[str]] = None,
        run_type: NondeterminismRunType = "pass_at_k",
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new non-determinism analysis run

        Args:
            agent_id: Agent ID
            k_value: Number of repetitions (2-10)
            trace_ids: List of trace IDs to analyze
            criterion_id: Single criterion to evaluate
            criteria_ids: List of criteria to evaluate
            run_type: Type of analysis
            temperature: LLM temperature for evaluation
            model: Model to use for evaluation

        Returns:
            Created run
        """
        body = {
            "agentId": agent_id,
            "kValue": k_value,
            "traceIds": trace_ids,
            "runType": run_type,
        }
        if criterion_id:
            body["criterionId"] = criterion_id
        if criteria_ids:
            body["criteriaIds"] = criteria_ids
        if temperature is not None:
            body["temperature"] = temperature
        if model:
            body["model"] = model

        return post("/nondeterminism/runs", body=body)

    def get_runs(
        self,
        agent_id: Optional[str] = None,
        status: Optional[NondeterminismRunStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get non-determinism runs"""
        params = {"limit": limit, "offset": offset}
        if agent_id:
            params["agentId"] = agent_id
        if status:
            params["status"] = status
        return get("/nondeterminism/runs", params=params)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get a specific run"""
        return get(f"/nondeterminism/runs/{run_id}")

    def start_run(self, run_id: str) -> None:
        """Start a run"""
        post(f"/nondeterminism/runs/{run_id}/start")

    def complete_run(self, run_id: str) -> None:
        """Complete a run"""
        post(f"/nondeterminism/runs/{run_id}/complete")

    def record_sample(
        self,
        run_id: str,
        trace_id: str,
        criterion_id: str,
        sample_index: int,
        score: float,
        passed: bool,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a sample result

        Args:
            run_id: Run ID
            trace_id: Trace ID
            criterion_id: Criterion ID
            sample_index: Sample index (0 to k-1)
            score: Evaluation score (0-100)
            passed: Pass/fail result
            reasoning: Evaluation reasoning
            confidence: Confidence score (0-1)
            tokens_used: Tokens used
            cost_usd: Cost in USD
            model: Model used
            temperature: Temperature used
            latency_ms: Evaluation latency
            error: Error message if failed

        Returns:
            Created sample
        """
        body = {
            "runId": run_id,
            "traceId": trace_id,
            "criterionId": criterion_id,
            "sampleIndex": sample_index,
            "score": score,
            "passed": passed,
        }
        if reasoning:
            body["reasoning"] = reasoning
        if confidence is not None:
            body["confidence"] = confidence
        if tokens_used is not None:
            body["tokensUsed"] = tokens_used
        if cost_usd is not None:
            body["costUsd"] = cost_usd
        if model:
            body["model"] = model
        if temperature is not None:
            body["temperature"] = temperature
        if latency_ms is not None:
            body["latencyMs"] = latency_ms
        if error:
            body["error"] = error

        return post("/nondeterminism/samples", body=body)

    def get_samples(self, run_id: str) -> List[Dict[str, Any]]:
        """Get samples for a run"""
        return get(f"/nondeterminism/runs/{run_id}/samples")

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get run summary with analysis"""
        return get(f"/nondeterminism/runs/{run_id}/summary")

    def analyze_run(self, run_id: str) -> Dict[str, Any]:
        """Trigger analysis of a completed run"""
        return post(f"/nondeterminism/runs/{run_id}/analyze")

    def get_info(self) -> Dict[str, Any]:
        """Get information about pass@k analysis"""
        return get("/nondeterminism/info")


# Singleton instance
nondeterminism = NondeterminismApi()


# Helper functions

def calculate_pass_at_k(pass_rate: float, k: int) -> float:
    """
    Calculate pass@k probability from pass rate

    Args:
        pass_rate: Single-run pass rate (0-1)
        k: Number of runs

    Returns:
        Probability that at least 1 of k runs passes
    """
    return 1 - math.pow(1 - pass_rate, k)


def calculate_pass_to_k(pass_rate: float, k: int) -> float:
    """
    Calculate pass^k probability from pass rate

    Args:
        pass_rate: Single-run pass rate (0-1)
        k: Number of runs

    Returns:
        Probability that all k runs pass
    """
    return math.pow(pass_rate, k)


def required_pass_rate_for_pass_at_k(target_pass_at_k: float, k: int) -> float:
    """
    Calculate required pass rate to achieve target pass@k

    Args:
        target_pass_at_k: Desired pass@k probability
        k: Number of runs

    Returns:
        Required single-run pass rate
    """
    return 1 - math.pow(1 - target_pass_at_k, 1 / k)


def is_reliable_evaluation(analysis: Dict[str, Any], threshold: float = 0.8) -> bool:
    """
    Determine if evaluation is reliable based on analysis

    Args:
        analysis: Criterion analysis result
        threshold: Minimum reliability score (default 0.8)

    Returns:
        Whether the evaluation is considered reliable
    """
    return analysis.get("reliabilityScore", 0) >= threshold


__all__ = [
    "nondeterminism",
    "NondeterminismApi",
    "NondeterminismRunType",
    "NondeterminismRunStatus",
    "calculate_pass_at_k",
    "calculate_pass_to_k",
    "required_pass_rate_for_pass_at_k",
    "is_reliable_evaluation",
]

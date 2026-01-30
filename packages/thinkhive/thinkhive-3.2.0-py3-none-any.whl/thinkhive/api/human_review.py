"""
ThinkHive Python SDK - Human Review API
API for managing human review queue, calibration sets, and reviewer management
"""

from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from ..client import get, post


HumanReviewStatus = Literal["pending", "in_progress", "completed", "skipped", "expired"]
HumanReviewType = Literal["disagreement", "low_confidence", "calibration", "random_sample", "flagged"]


class HumanReviewApi:
    """Human Review API client"""

    def get_queue(
        self,
        agent_id: Optional[str] = None,
        status: Optional[HumanReviewStatus] = None,
        review_type: Optional[HumanReviewType] = None,
        is_calibration: Optional[bool] = None,
        min_priority: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get pending review queue items

        Args:
            agent_id: Filter by agent ID
            status: Filter by status
            review_type: Filter by review type
            is_calibration: Filter calibration items
            min_priority: Minimum priority threshold
            limit: Maximum items to return
            offset: Pagination offset

        Returns:
            List of queue items
        """
        params = {"limit": limit, "offset": offset}
        if agent_id:
            params["agentId"] = agent_id
        if status:
            params["status"] = status
        if review_type:
            params["reviewType"] = review_type
        if is_calibration is not None:
            params["isCalibration"] = str(is_calibration).lower()
        if min_priority is not None:
            params["minPriority"] = min_priority

        return get("/human-review/queue", params=params)

    def add_to_queue(
        self,
        trace_id: str,
        agent_id: str,
        review_type: HumanReviewType,
        criterion_id: Optional[str] = None,
        priority: int = 0,
        llm_score: Optional[float] = None,
        llm_passed: Optional[bool] = None,
        llm_reasoning: Optional[str] = None,
        llm_confidence: Optional[float] = None,
        is_calibration_sample: bool = False,
        calibration_set_id: Optional[str] = None,
        expected_score: Optional[float] = None,
        expected_passed: Optional[bool] = None,
        expires_in_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add an item to the review queue

        Args:
            trace_id: ID of the trace to review
            agent_id: Agent ID
            review_type: Type of review
            criterion_id: Optional evaluation criterion
            priority: Priority (0-100)
            llm_score: LLM evaluation score
            llm_passed: LLM pass/fail result
            llm_reasoning: LLM reasoning
            llm_confidence: LLM confidence score
            is_calibration_sample: Whether this is a calibration sample
            calibration_set_id: Calibration set ID
            expected_score: Expected score for calibration
            expected_passed: Expected pass/fail for calibration
            expires_in_ms: Expiration time in milliseconds
            metadata: Additional metadata

        Returns:
            Created queue item
        """
        body = {
            "traceId": trace_id,
            "agentId": agent_id,
            "reviewType": review_type,
            "priority": priority,
        }
        if criterion_id:
            body["criterionId"] = criterion_id
        if llm_score is not None:
            body["llmScore"] = llm_score
        if llm_passed is not None:
            body["llmPassed"] = llm_passed
        if llm_reasoning:
            body["llmReasoning"] = llm_reasoning
        if llm_confidence is not None:
            body["llmConfidence"] = llm_confidence
        if is_calibration_sample:
            body["isCalibrationSample"] = is_calibration_sample
        if calibration_set_id:
            body["calibrationSetId"] = calibration_set_id
        if expected_score is not None:
            body["expectedScore"] = expected_score
        if expected_passed is not None:
            body["expectedPassed"] = expected_passed
        if expires_in_ms:
            body["expiresInMs"] = expires_in_ms
        if metadata:
            body["metadata"] = metadata

        return post("/human-review/queue", body=body)

    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific review item"""
        return get(f"/human-review/queue/{item_id}")

    def claim(self, item_id: str) -> Dict[str, Any]:
        """Claim a review item for processing"""
        return post(f"/human-review/queue/{item_id}/claim")

    def release(self, item_id: str) -> Dict[str, Any]:
        """Release a claimed review item"""
        return post(f"/human-review/queue/{item_id}/release")

    def skip(self, item_id: str) -> Dict[str, Any]:
        """Skip a review item"""
        return post(f"/human-review/queue/{item_id}/skip")

    def submit(
        self,
        item_id: str,
        passed: bool,
        score: float,
        reasoning: str,
        duration_ms: int,
    ) -> Dict[str, Any]:
        """
        Submit a review

        Args:
            item_id: Queue item ID
            passed: Pass/fail result
            score: Review score (0-100)
            reasoning: Explanation for the score
            duration_ms: Time spent reviewing in ms

        Returns:
            Updated queue item
        """
        return post(
            f"/human-review/queue/{item_id}/submit",
            body={
                "passed": passed,
                "score": score,
                "reasoning": reasoning,
                "durationMs": duration_ms,
            },
        )

    def get_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get queue statistics"""
        params = {"agentId": agent_id} if agent_id else None
        return get("/human-review/stats", params=params)

    def get_next_item(self, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get next item for a reviewer"""
        params = {"agentId": agent_id} if agent_id else None
        return get("/human-review/next-item", params=params)

    def get_review_types(self) -> List[Dict[str, Any]]:
        """Get available review types"""
        return get("/human-review/review-types")

    # Calibration Sets

    def get_calibration_sets(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get calibration sets"""
        params = {"agentId": agent_id} if agent_id else None
        return get("/human-review/calibration-sets", params=params)

    def create_calibration_set(
        self,
        name: str,
        agent_id: str,
        description: Optional[str] = None,
        criterion_id: Optional[str] = None,
        target_agreement: Optional[float] = None,
        min_samples: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a calibration set

        Args:
            name: Set name
            agent_id: Agent ID
            description: Optional description
            criterion_id: Criterion to calibrate on
            target_agreement: Target agreement rate (0-1)
            min_samples: Minimum samples required

        Returns:
            Created calibration set
        """
        body = {"name": name, "agentId": agent_id}
        if description:
            body["description"] = description
        if criterion_id:
            body["criterionId"] = criterion_id
        if target_agreement is not None:
            body["targetAgreement"] = target_agreement
        if min_samples is not None:
            body["minSamples"] = min_samples

        return post("/human-review/calibration-sets", body=body)

    def get_calibration_set(self, set_id: str) -> Dict[str, Any]:
        """Get a calibration set by ID"""
        return get(f"/human-review/calibration-sets/{set_id}")

    # Reviewer Calibration

    def get_certified_reviewers(self, calibration_set_id: str) -> List[Dict[str, Any]]:
        """Get certified reviewers for a calibration set"""
        return get("/human-review/reviewers", params={"calibrationSetId": calibration_set_id})

    def get_reviewer_calibrations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get reviewer calibration status"""
        return get(f"/human-review/calibration/{user_id}")


# Singleton instance
human_review = HumanReviewApi()

__all__ = ["human_review", "HumanReviewApi", "HumanReviewStatus", "HumanReviewType"]

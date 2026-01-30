"""
ThinkHive Python SDK - Calibration API
Prediction accuracy tracking with Brier scores and calibration metrics
"""

from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from datetime import datetime
from ..client import post, get

PredictionType = Literal[
    "outcome",
    "churn_risk",
    "escalation_risk",
    "resolution_time",
    "sentiment",
    "intent",
    "custom",
]


@dataclass
class CalibrationBucket:
    """A calibration bucket for reliability diagrams"""
    bucket_min: float
    bucket_max: float
    avg_predicted: float
    avg_actual: float
    sample_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibrationBucket":
        return cls(
            bucket_min=data.get("bucketMin", 0.0),
            bucket_max=data.get("bucketMax", 0.0),
            avg_predicted=data.get("avgPredicted", 0.0),
            avg_actual=data.get("avgActual", 0.0),
            sample_count=data.get("sampleCount", 0),
        )


@dataclass
class CalibrationStatus:
    """Calibration status for an agent and prediction type"""
    agent_id: str
    prediction_type: PredictionType
    brier_score: float
    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error
    sample_count: int
    is_calibrated: bool
    last_updated: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibrationStatus":
        return cls(
            agent_id=data.get("agentId", ""),
            prediction_type=data.get("predictionType", "outcome"),
            brier_score=data.get("brierScore", 0.0),
            ece=data.get("ece", 0.0),
            mce=data.get("mce", 0.0),
            sample_count=data.get("sampleCount", 0),
            is_calibrated=data.get("isCalibrated", False),
            last_updated=data.get("lastUpdated", ""),
        )


@dataclass
class CalibrationMetrics:
    """Full calibration metrics including reliability diagram"""
    agent_id: str
    prediction_type: PredictionType
    brier_score: float
    ece: float
    mce: float
    sample_count: int
    is_calibrated: bool
    reliability_diagram: List[CalibrationBucket]
    last_updated: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibrationMetrics":
        buckets = [
            CalibrationBucket.from_dict(b)
            for b in data.get("reliabilityDiagram", [])
        ]
        return cls(
            agent_id=data.get("agentId", ""),
            prediction_type=data.get("predictionType", "outcome"),
            brier_score=data.get("brierScore", 0.0),
            ece=data.get("ece", 0.0),
            mce=data.get("mce", 0.0),
            sample_count=data.get("sampleCount", 0),
            is_calibrated=data.get("isCalibrated", False),
            reliability_diagram=buckets,
            last_updated=data.get("lastUpdated", ""),
        )


def get_status(agent_id: str, prediction_type: PredictionType) -> CalibrationStatus:
    """
    Get calibration status for an agent and prediction type.

    Args:
        agent_id: The agent ID
        prediction_type: Type of prediction to check

    Returns:
        CalibrationStatus with Brier score and calibration state

    Example:
        >>> from thinkhive.api import calibration
        >>>
        >>> status = calibration.get_status("agent-123", "churn_risk")
        >>> print(f"Brier score: {status.brier_score}")
        >>> print(f"Is calibrated: {status.is_calibrated}")
    """
    params = {"predictionType": prediction_type}
    response = get(f"/calibration/status/{agent_id}", params=params, api_version="v3")
    return CalibrationStatus.from_dict(response)


def get_metrics(agent_id: str) -> List[CalibrationMetrics]:
    """
    Get all calibration metrics for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        List of CalibrationMetrics for each prediction type
    """
    response = get(f"/calibration/metrics/{agent_id}", api_version="v3")
    return [CalibrationMetrics.from_dict(m) for m in response]


def record_outcome(
    *,
    run_id: str,
    prediction_type: PredictionType,
    predicted_value: float,
    actual_outcome: float,
    predicted_at: Optional[str] = None,
    observed_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a prediction outcome for calibration tracking.

    Args:
        run_id: The run ID the prediction was made for
        prediction_type: Type of prediction
        predicted_value: The predicted value (0-1 for probabilities)
        actual_outcome: The actual outcome (0 or 1 for binary)
        predicted_at: When the prediction was made (ISO timestamp)
        observed_at: When the outcome was observed (ISO timestamp)

    Returns:
        Dict with 'recorded', 'brierContribution', 'message'

    Example:
        >>> from thinkhive.api import calibration
        >>>
        >>> # Record a churn prediction outcome
        >>> result = calibration.record_outcome(
        ...     run_id="run-123",
        ...     prediction_type="churn_risk",
        ...     predicted_value=0.7,  # We predicted 70% churn risk
        ...     actual_outcome=1,     # Customer did churn
        ... )
    """
    now = datetime.utcnow().isoformat() + "Z"
    body = {
        "runId": run_id,
        "predictionType": prediction_type,
        "predictedValue": predicted_value,
        "actualOutcome": actual_outcome,
        "predictedAt": predicted_at or now,
        "observedAt": observed_at or now,
    }

    return post("/calibration/record", body, api_version="v3")


def retrain(
    agent_id: str,
    *,
    prediction_types: Optional[List[PredictionType]] = None,
    min_samples: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Trigger recalibration for an agent.

    Args:
        agent_id: The agent ID
        prediction_types: Types to retrain (all if not specified)
        min_samples: Minimum samples required for retraining

    Returns:
        Dict with 'success', 'retrainedTypes', 'skippedTypes', 'newMetrics'
    """
    body: Dict[str, Any] = {}

    if prediction_types is not None:
        body["predictionTypes"] = prediction_types
    if min_samples is not None:
        body["minSamples"] = min_samples

    response = post(f"/calibration/retrain/{agent_id}", body, api_version="v3")

    # Parse new metrics if present
    if "newMetrics" in response:
        response["newMetrics"] = [
            CalibrationMetrics.from_dict(m)
            for m in response["newMetrics"]
        ]

    return response


def get_reliability_diagram(
    agent_id: str,
    prediction_type: PredictionType,
) -> Dict[str, Any]:
    """
    Get reliability diagram data for visualization.

    Args:
        agent_id: The agent ID
        prediction_type: Type of prediction

    Returns:
        Dict with 'agentId', 'predictionType', 'buckets', 'perfectCalibrationLine'
    """
    params = {"predictionType": prediction_type}
    response = get(f"/calibration/diagram/{agent_id}", params=params, api_version="v3")

    # Parse buckets
    if "buckets" in response:
        response["buckets"] = [
            CalibrationBucket.from_dict(b)
            for b in response["buckets"]
        ]

    return response


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def calculate_brier_score(predictions: List[Dict[str, float]]) -> float:
    """
    Calculate Brier score from predictions and outcomes.
    Lower is better, <0.1 is considered good.

    Args:
        predictions: List of dicts with 'predicted' and 'actual' keys

    Returns:
        Brier score (0-1, lower is better)
    """
    if not predictions:
        return 0.0

    total = sum(
        (p["predicted"] - p["actual"]) ** 2
        for p in predictions
    )

    return total / len(predictions)


def calculate_ece(
    predictions: List[Dict[str, float]],
    num_buckets: int = 10,
) -> float:
    """
    Calculate Expected Calibration Error (ECE).
    Measures how well-calibrated predictions are across confidence buckets.

    Args:
        predictions: List of dicts with 'predicted' and 'actual' keys
        num_buckets: Number of calibration buckets

    Returns:
        ECE (0-1, lower is better)
    """
    if not predictions:
        return 0.0

    # Initialize buckets
    buckets: List[Dict[str, List[float]]] = [
        {"predictions": [], "actuals": []}
        for _ in range(num_buckets)
    ]

    # Assign predictions to buckets
    for p in predictions:
        bucket_index = min(
            int(p["predicted"] * num_buckets),
            num_buckets - 1
        )
        buckets[bucket_index]["predictions"].append(p["predicted"])
        buckets[bucket_index]["actuals"].append(p["actual"])

    # Calculate ECE
    ece = 0.0
    n = len(predictions)

    for bucket in buckets:
        if not bucket["predictions"]:
            continue

        avg_predicted = sum(bucket["predictions"]) / len(bucket["predictions"])
        avg_actual = sum(bucket["actuals"]) / len(bucket["actuals"])
        weight = len(bucket["predictions"]) / n

        ece += weight * abs(avg_predicted - avg_actual)

    return ece


def is_well_calibrated(brier_score: float) -> bool:
    """Check if a model is well-calibrated based on Brier score"""
    return brier_score < 0.1


def get_calibration_quality(brier_score: float) -> str:
    """Get calibration quality label based on Brier score"""
    if brier_score < 0.05:
        return "excellent"
    if brier_score < 0.1:
        return "good"
    if brier_score < 0.2:
        return "fair"
    return "poor"


def format_brier_score(score: float) -> str:
    """Format Brier score for display"""
    return f"{score:.4f}"


__all__ = [
    # Types
    "PredictionType",
    # Dataclasses
    "CalibrationBucket",
    "CalibrationStatus",
    "CalibrationMetrics",
    # API functions
    "get_status",
    "get_metrics",
    "record_outcome",
    "retrain",
    "get_reliability_diagram",
    # Helper functions
    "calculate_brier_score",
    "calculate_ece",
    "is_well_calibrated",
    "get_calibration_quality",
    "format_brier_score",
]

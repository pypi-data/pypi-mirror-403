"""
ThinkHive Python SDK - Claims API
Facts vs Inferences API for accessing analysis claims
"""

from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from ..client import post, get

ClaimType = Literal["observed", "inferred", "computed"]
ClaimCategory = Literal[
    "outcome",
    "root_cause",
    "customer_impact",
    "churn_risk",
    "revenue_impact",
    "quality",
    "other",
]
ConfidenceCalibration = Literal["calibrated", "uncalibrated", "needs_more_data"]
OutcomeVerdict = Literal["success", "partial_success", "failure"]
VerificationVerdict = Literal["confirmed", "rejected", "modified"]


@dataclass
class EvidenceReference:
    """Reference to evidence supporting a claim"""
    type: str  # 'span', 'message', 'context'
    reference_id: str
    relevance: str  # 'direct', 'supporting', 'contextual'
    confidence: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceReference":
        return cls(
            type=data.get("type", ""),
            reference_id=data.get("referenceId", ""),
            relevance=data.get("relevance", ""),
            confidence=data.get("confidence", 0.0),
        )


@dataclass
class Claim:
    """A claim from analysis (fact, inference, or computed)"""
    id: str
    analysis_id: str
    claim_type: ClaimType
    claim_category: ClaimCategory
    claim_text: str
    confidence: float
    confidence_calibration: Optional[ConfidenceCalibration]
    evidence: List[EvidenceReference]
    is_explainable: bool
    human_verified: bool
    human_verification_notes: Optional[str]
    probability_value: Optional[float]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Claim":
        evidence = [
            EvidenceReference.from_dict(e)
            for e in data.get("evidence", [])
        ]
        return cls(
            id=data.get("id", ""),
            analysis_id=data.get("analysisId", ""),
            claim_type=data.get("claimType", "observed"),
            claim_category=data.get("claimCategory", "other"),
            claim_text=data.get("claimText", ""),
            confidence=data.get("confidence", 0.0),
            confidence_calibration=data.get("confidenceCalibration"),
            evidence=evidence,
            is_explainable=data.get("isExplainable", False),
            human_verified=data.get("humanVerified", False),
            human_verification_notes=data.get("humanVerificationNotes"),
            probability_value=data.get("probabilityValue"),
            created_at=data.get("createdAt", ""),
        )


@dataclass
class AnalysisResult:
    """Result from creating or retrieving an analysis"""
    id: str
    run_id: str
    analysis_version: str
    model_used: Optional[str]
    outcome_verdict: OutcomeVerdict
    outcome_confidence: float
    root_cause_category: Optional[str]
    root_cause_confidence: Optional[float]
    is_current: bool
    superseded_by: Optional[str]
    supersession_reason: Optional[str]
    analyzed_at: str
    claims: List[Claim]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        claims = [Claim.from_dict(c) for c in data.get("claims", [])]
        return cls(
            id=data.get("id", ""),
            run_id=data.get("runId", ""),
            analysis_version=data.get("analysisVersion", ""),
            model_used=data.get("modelUsed"),
            outcome_verdict=data.get("outcomeVerdict", "failure"),
            outcome_confidence=data.get("outcomeConfidence", 0.0),
            root_cause_category=data.get("rootCauseCategory"),
            root_cause_confidence=data.get("rootCauseConfidence"),
            is_current=data.get("isCurrent", True),
            superseded_by=data.get("supersededBy"),
            supersession_reason=data.get("supersessionReason"),
            analyzed_at=data.get("analyzedAt", ""),
            claims=claims,
        )


@dataclass
class FactsVsInferencesSummary:
    """Summary of facts vs inferences across analyses"""
    analysis_ids: List[str]
    total_claims: int
    observed_count: int
    observed_avg_confidence: float
    observed_categories: Dict[str, int]
    inferred_count: int
    inferred_avg_confidence: float
    inferred_categories: Dict[str, int]
    computed_count: int
    computed_avg_confidence: float
    computed_categories: Dict[str, int]
    human_verified_count: int
    human_rejected_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactsVsInferencesSummary":
        observed = data.get("observed", {})
        inferred = data.get("inferred", {})
        computed = data.get("computed", {})
        return cls(
            analysis_ids=data.get("analysisIds", []),
            total_claims=data.get("totalClaims", 0),
            observed_count=observed.get("count", 0),
            observed_avg_confidence=observed.get("avgConfidence", 0.0),
            observed_categories=observed.get("categories", {}),
            inferred_count=inferred.get("count", 0),
            inferred_avg_confidence=inferred.get("avgConfidence", 0.0),
            inferred_categories=inferred.get("categories", {}),
            computed_count=computed.get("count", 0),
            computed_avg_confidence=computed.get("avgConfidence", 0.0),
            computed_categories=computed.get("categories", {}),
            human_verified_count=data.get("humanVerifiedCount", 0),
            human_rejected_count=data.get("humanRejectedCount", 0),
        )


def create_analysis(
    *,
    run_id: str,
    outcome_verdict: OutcomeVerdict,
    outcome_confidence: Optional[float] = None,
    model_used: Optional[str] = None,
    root_cause_category: Optional[str] = None,
    root_cause_confidence: Optional[float] = None,
    claims: Optional[List[Dict[str, Any]]] = None,
) -> AnalysisResult:
    """
    Create a new analysis for a run.

    Args:
        run_id: The run ID to analyze
        outcome_verdict: Verdict (success, partial_success, failure)
        outcome_confidence: Confidence in the verdict (0-1)
        model_used: Model used for analysis
        root_cause_category: Category of root cause
        root_cause_confidence: Confidence in root cause (0-1)
        claims: List of claims to create with the analysis

    Returns:
        AnalysisResult with analysis details and claims

    Example:
        >>> from thinkhive.api import claims
        >>>
        >>> analysis = claims.create_analysis(
        ...     run_id="run-123",
        ...     outcome_verdict="failure",
        ...     outcome_confidence=0.85,
        ...     root_cause_category="retrieval_failure",
        ...     claims=[
        ...         {
        ...             "claim_type": "observed",
        ...             "claim_category": "root_cause",
        ...             "claim_text": "Vector search returned 0 results",
        ...             "confidence": 1.0,
        ...         }
        ...     ]
        ... )
    """
    body: Dict[str, Any] = {
        "runId": run_id,
        "outcomeVerdict": outcome_verdict,
    }

    if outcome_confidence is not None:
        body["outcomeConfidence"] = outcome_confidence
    if model_used is not None:
        body["modelUsed"] = model_used
    if root_cause_category is not None:
        body["rootCauseCategory"] = root_cause_category
    if root_cause_confidence is not None:
        body["rootCauseConfidence"] = root_cause_confidence
    if claims is not None:
        # Convert snake_case to camelCase
        formatted_claims = []
        for claim in claims:
            formatted = {
                "claimType": claim.get("claim_type"),
                "claimCategory": claim.get("claim_category"),
                "claimText": claim.get("claim_text"),
                "confidence": claim.get("confidence"),
            }
            if "confidence_calibration" in claim:
                formatted["confidenceCalibration"] = claim["confidence_calibration"]
            if "evidence" in claim:
                formatted["evidence"] = claim["evidence"]
            if "is_explainable" in claim:
                formatted["isExplainable"] = claim["is_explainable"]
            if "probability_value" in claim:
                formatted["probabilityValue"] = claim["probability_value"]
            formatted_claims.append(formatted)
        body["claims"] = formatted_claims

    response = post("/analyses", body, api_version="v3")
    return AnalysisResult.from_dict(response)


def get_analysis(analysis_id: str) -> AnalysisResult:
    """
    Get an analysis by ID.

    Args:
        analysis_id: The analysis ID

    Returns:
        AnalysisResult with analysis details and claims
    """
    response = get(f"/analyses/{analysis_id}", api_version="v3")
    return AnalysisResult.from_dict(response)


def get_run_analysis(run_id: str) -> AnalysisResult:
    """
    Get the current analysis for a run.

    Args:
        run_id: The run ID

    Returns:
        AnalysisResult with analysis details and claims
    """
    response = get(f"/runs/{run_id}/analysis", api_version="v3")
    return AnalysisResult.from_dict(response)


def list_claims(
    *,
    run_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    claim_type: Optional[ClaimType] = None,
    claim_category: Optional[ClaimCategory] = None,
    min_confidence: Optional[float] = None,
    human_verified: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List claims with filters.

    Args:
        run_id: Filter by run ID
        analysis_id: Filter by analysis ID
        claim_type: Filter by claim type (observed, inferred, computed)
        claim_category: Filter by category
        min_confidence: Minimum confidence threshold
        human_verified: Filter by human verification status
        limit: Maximum number of claims to return
        offset: Offset for pagination

    Returns:
        Dict with 'claims', 'limit', 'offset', 'hasMore'
    """
    params: Dict[str, Any] = {
        "limit": limit,
        "offset": offset,
    }

    if run_id is not None:
        params["runId"] = run_id
    if analysis_id is not None:
        params["analysisId"] = analysis_id
    if claim_type is not None:
        params["claimType"] = claim_type
    if claim_category is not None:
        params["claimCategory"] = claim_category
    if min_confidence is not None:
        params["minConfidence"] = min_confidence
    if human_verified is not None:
        params["humanVerified"] = str(human_verified).lower()

    response = get("/claims", params=params, api_version="v3")

    # Parse claims into dataclass
    if "claims" in response:
        response["claims"] = [Claim.from_dict(c) for c in response["claims"]]

    return response


def verify_claim(
    claim_id: str,
    *,
    verdict: VerificationVerdict,
    notes: Optional[str] = None,
    modified_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify or reject a claim (human feedback).

    Args:
        claim_id: The claim ID to verify
        verdict: Verification verdict (confirmed, rejected, modified)
        notes: Optional notes explaining the verdict
        modified_text: Modified claim text (required if verdict is 'modified')

    Returns:
        Dict with claimId, verdict, message
    """
    body: Dict[str, Any] = {
        "verdict": verdict,
    }

    if notes is not None:
        body["notes"] = notes
    if modified_text is not None:
        body["modifiedText"] = modified_text

    return post(f"/claims/{claim_id}/verify", body, api_version="v3")


def get_summary(
    *,
    run_id: Optional[str] = None,
    analysis_ids: Optional[List[str]] = None,
) -> FactsVsInferencesSummary:
    """
    Get facts vs inferences summary.

    Args:
        run_id: Get summary for a specific run
        analysis_ids: Get summary for specific analyses

    Returns:
        FactsVsInferencesSummary with aggregated statistics
    """
    params: Dict[str, Any] = {}

    if run_id is not None:
        params["runId"] = run_id
    if analysis_ids is not None:
        params["analysisIds"] = ",".join(analysis_ids)

    response = get("/claims/summary", params=params, api_version="v3")
    return FactsVsInferencesSummary.from_dict(response)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def is_fact(claim: Claim) -> bool:
    """Check if a claim is a fact (observed)"""
    return claim.claim_type == "observed"


def is_inference(claim: Claim) -> bool:
    """Check if a claim is an inference"""
    return claim.claim_type == "inferred"


def is_computed(claim: Claim) -> bool:
    """Check if a claim is computed"""
    return claim.claim_type == "computed"


def get_high_confidence_claims(claims_list: List[Claim], threshold: float = 0.8) -> List[Claim]:
    """Get claims with confidence >= threshold"""
    return [c for c in claims_list if c.confidence >= threshold]


def group_claims_by_type(claims_list: List[Claim]) -> Dict[ClaimType, List[Claim]]:
    """Group claims by their type"""
    return {
        "observed": [c for c in claims_list if c.claim_type == "observed"],
        "inferred": [c for c in claims_list if c.claim_type == "inferred"],
        "computed": [c for c in claims_list if c.claim_type == "computed"],
    }


def group_claims_by_category(claims_list: List[Claim]) -> Dict[ClaimCategory, List[Claim]]:
    """Group claims by their category"""
    groups: Dict[ClaimCategory, List[Claim]] = {
        "outcome": [],
        "root_cause": [],
        "customer_impact": [],
        "churn_risk": [],
        "revenue_impact": [],
        "quality": [],
        "other": [],
    }

    for claim in claims_list:
        groups[claim.claim_category].append(claim)

    return groups


__all__ = [
    # Types
    "ClaimType",
    "ClaimCategory",
    "ConfidenceCalibration",
    "OutcomeVerdict",
    "VerificationVerdict",
    # Dataclasses
    "EvidenceReference",
    "Claim",
    "AnalysisResult",
    "FactsVsInferencesSummary",
    # API functions
    "create_analysis",
    "get_analysis",
    "get_run_analysis",
    "list_claims",
    "verify_claim",
    "get_summary",
    # Helper functions
    "is_fact",
    "is_inference",
    "is_computed",
    "get_high_confidence_claims",
    "group_claims_by_type",
    "group_claims_by_category",
]

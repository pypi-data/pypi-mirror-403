"""
ThinkHive Python SDK - API Modules
"""

from .human_review import human_review
from .nondeterminism import nondeterminism
from .eval_health import eval_health
from .deterministic_graders import deterministic_graders
from .conversation_eval import conversation_eval
from .transcript_patterns import transcript_patterns
from .issues import issues
from .analyzer import analyzer
from . import traces
from . import runs
from . import claims
from . import calibration
from . import roi_analytics
from . import business_metrics

# Deprecated aliases
cases = issues  # deprecated alias for issues
explainer = analyzer  # deprecated alias for analyzer

__all__ = [
    "human_review",
    "nondeterminism",
    "eval_health",
    "deterministic_graders",
    "conversation_eval",
    "transcript_patterns",
    "issues",
    "analyzer",
    "traces",
    # V3 APIs
    "runs",
    "claims",
    "calibration",
    "roi_analytics",
    "business_metrics",
    # Deprecated aliases
    "cases",
    "explainer",
]

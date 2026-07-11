"""Typed state for the LangGraph recommendation workflow."""
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class WorkflowState(TypedDict, total=False):
    """Shared state passed between all nodes in the LangGraph workflow."""

    # Input
    input_profile: Dict[str, Any]

    # Enrichment
    risk_features: Dict[str, Any]
    enrichment_failed: bool

    # Scoring
    score_breakdown: Dict[str, float]

    # Recommendation
    recommendation: Dict[str, Any]

    # Explanation
    explanation: str

    # Confidence
    confidence: float
    requires_human_review: bool
    confidence_reasons: List[str]

    # Final output
    output: Dict[str, Any]

    # Metadata
    trace_metadata: Dict[str, Any]
    errors: List[str]
    request_id: str

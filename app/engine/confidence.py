"""Confidence evaluator — scores the reliability of a recommendation."""
import logging
from typing import Any, Dict, List

from app.core.config import settings
from app.models.plan_catalog import PlanCatalogEntry
from app.models.risk_profile import RiskProfile

logger = logging.getLogger(__name__)


def evaluate_confidence(
    risk_profile: RiskProfile,
    plan: PlanCatalogEntry,
) -> tuple[float, bool, List[str]]:
    """
    Evaluate recommendation confidence based on multiple signals.

    Returns:
        (confidence_score, requires_human_review, reasons)
    """
    score = risk_profile.total_score
    reasons: List[str] = []
    confidence = 1.0
    penalties: List[float] = []

    # Penalty: near tier boundary (within 3 points of boundary)
    dist_to_min = score - plan.min_score
    dist_to_max = plan.max_score - score
    boundary_margin = min(dist_to_min, dist_to_max)

    if boundary_margin < 3:
        penalty = 0.15
        penalties.append(penalty)
        reasons.append(
            f"Score {score:.0f} is near tier boundary (margin: {boundary_margin:.0f})"
        )

    # Penalty: multiple high-severity risk flags
    if len(risk_profile.risk_flags) >= 3:
        penalty = 0.10
        penalties.append(penalty)
        reasons.append(
            f"Multiple risk factors present: {', '.join(risk_profile.risk_flags)}"
        )

    # Penalty: extreme score values (very high)
    if score >= 90:
        penalty = 0.05
        penalties.append(penalty)
        reasons.append("Very high aggregate risk score — custom review recommended")

    # Penalty: enrichment source is not authoritative
    if risk_profile.enrichment_source == "fallback_defaults":
        penalty = 0.20
        penalties.append(penalty)
        reasons.append("Risk enrichment used fallback defaults (limited data)")

    confidence = max(0.0, confidence - sum(penalties))
    confidence = round(confidence, 3)

    requires_human_review = confidence < settings.low_confidence_threshold

    if requires_human_review:
        logger.warning(
            "Low confidence recommendation | score=%.3f | tier=%s | reasons=%s",
            confidence,
            plan.plan_tier,
            reasons,
        )
    else:
        logger.info(
            "Confidence evaluation | score=%.3f | tier=%s | human_review=%s",
            confidence,
            plan.plan_tier,
            requires_human_review,
        )

    return confidence, requires_human_review, reasons

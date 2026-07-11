"""Individual LangGraph node functions for the recommendation workflow."""
import logging
import uuid
from typing import Any, Dict

from app.agents.risk_enrichment import enrich_risk_from_profile
from app.agents.state import WorkflowState
from app.core.config import settings
from app.core.logging_config import get_logger
from app.engine.confidence import evaluate_confidence
from app.engine.rules import compute_coverage_bands, load_plan_catalog, select_plan_tier
from app.engine.scoring import compute_risk_profile
from app.models.request import RecommendationRequest

logger = get_logger(__name__)


def validate_input(state: WorkflowState) -> WorkflowState:
    """Validate and parse the raw input profile."""
    errors = list(state.get("errors", []))
    try:
        profile_data = state.get("input_profile", {})
        request = RecommendationRequest(**profile_data)
        state["input_profile"] = request.model_dump()
        logger.info(
            "Input validated | home_price=%.0f | zip=%s | state=%s",
            request.home_price,
            request.location_zip,
            request.state,
        )
    except Exception as exc:
        error_msg = f"Input validation failed: {exc}"
        logger.error(error_msg)
        errors.append(error_msg)
        state["errors"] = errors
    return state


def normalize_input(state: WorkflowState) -> WorkflowState:
    """Normalize input fields (already handled by Pydantic validators)."""
    profile = state.get("input_profile", {})
    # Ensure state is uppercase
    if "state" in profile:
        profile["state"] = profile["state"].upper()
    state["input_profile"] = profile
    logger.debug("Input normalized | profile=%s", profile)
    return state


def enrich_risk(state: WorkflowState) -> WorkflowState:
    """Enrich risk features from location and property data."""
    profile = state.get("input_profile", {})
    errors = list(state.get("errors", []))
    try:
        risk_features = enrich_risk_from_profile(
            zip_code=profile.get("location_zip", ""),
            state=profile.get("state", ""),
            home_price=profile.get("home_price", 0),
            year_built=profile.get("year_built", 0),
        )
        state["risk_features"] = risk_features
        state["enrichment_failed"] = False
    except Exception as exc:
        error_msg = f"Risk enrichment error: {exc}"
        logger.warning(error_msg)
        errors.append(error_msg)
        state["errors"] = errors
        state["enrichment_failed"] = True
    return state


def fallback_risk_defaults(state: WorkflowState) -> WorkflowState:
    """Apply fallback risk defaults when enrichment fails."""
    profile = state.get("input_profile", {})
    logger.warning("Applying fallback risk defaults for zip=%s", profile.get("location_zip"))
    state["risk_features"] = {
        "location": {
            "zip_code": profile.get("location_zip", ""),
            "state": profile.get("state", ""),
            "region": "Unknown",
            "source": "fallback_defaults",
        },
        "hazard_flags": {
            "flood_zone": False,
            "wildfire_zone": False,
            "tornado_alley": False,
            "hurricane_zone": False,
            "earthquake_zone": False,
        },
        "base_hazard_modifier": 1.0,
        "property": {
            "home_price": profile.get("home_price", 0),
            "year_built": profile.get("year_built", 0),
        },
        "data_version": settings.risk_data_version,
    }
    state["enrichment_failed"] = False  # Reset so scoring can proceed
    return state


def score_risk(state: WorkflowState) -> WorkflowState:
    """Compute weighted risk scores across all dimensions."""
    profile = state.get("input_profile", {})
    errors = list(state.get("errors", []))
    try:
        request = RecommendationRequest(**profile)
        # Override enrichment source tag in risk profile if it was fallback
        risk_profile = compute_risk_profile(request)

        # If enrichment was from fallback, tag accordingly for confidence penalty
        risk_feats = state.get("risk_features", {})
        loc_source = risk_feats.get("location", {}).get("source", "")
        if "fallback" in loc_source:
            risk_profile = risk_profile.model_copy(
                update={"enrichment_source": "fallback_defaults"}
            )

        state["score_breakdown"] = risk_profile.model_dump()
        logger.info("Risk scored | total=%.1f | flags=%s", risk_profile.total_score, risk_profile.risk_flags)
    except Exception as exc:
        error_msg = f"Scoring failed: {exc}"
        logger.error(error_msg)
        errors.append(error_msg)
        state["errors"] = errors
    return state


def recommend_plan(state: WorkflowState) -> WorkflowState:
    """Select the plan tier based on deterministic scoring rules."""
    score_data = state.get("score_breakdown", {})
    profile = state.get("input_profile", {})
    errors = list(state.get("errors", []))
    try:
        from app.models.risk_profile import RiskProfile

        risk_profile = RiskProfile(**score_data)
        plan = select_plan_tier(risk_profile)
        coverage = compute_coverage_bands(plan, profile.get("home_price", 0))

        state["recommendation"] = {
            "plan_tier": plan.plan_tier,
            "plan_id": plan.plan_id,
            "coverage": coverage,
            "features": plan.features,
            "description": plan.description,
        }
        logger.info("Plan recommended | tier=%s", plan.plan_tier)
    except Exception as exc:
        error_msg = f"Plan recommendation failed: {exc}"
        logger.error(error_msg)
        errors.append(error_msg)
        state["errors"] = errors
    return state


def generate_explanation(state: WorkflowState) -> WorkflowState:
    """Generate AI-powered explanation narrative (LLM-only node)."""
    from app.agents.explanation import generate_explanation as _gen

    recommendation = state.get("recommendation", {})
    score_data = state.get("score_breakdown", {})
    profile = state.get("input_profile", {})

    plan_tier = recommendation.get("plan_tier", "Standard")
    risk_flags = score_data.get("risk_flags", [])
    confidence = state.get("confidence", 1.0)
    premium_band = recommendation.get("coverage", {}).get("premium_monthly_band", "")

    score_dims = {
        "geo_hazard": score_data.get("geo_hazard_score", 0),
        "value_exposure": score_data.get("value_exposure_score", 0),
        "property_condition": score_data.get("property_condition_score", 0),
        "affordability_alignment": score_data.get("affordability_alignment_score", 0),
        "total": score_data.get("total_score", 0),
    }

    explanation = _gen(
        plan_tier=plan_tier,
        input_profile=profile,
        score_breakdown=score_dims,
        risk_flags=risk_flags,
        confidence=confidence,
        premium_band=premium_band,
    )
    state["explanation"] = explanation
    return state


def evaluate_confidence_node(state: WorkflowState) -> WorkflowState:
    """Evaluate recommendation confidence and flag for human review if needed."""
    from app.engine.confidence import evaluate_confidence
    from app.engine.rules import load_plan_catalog
    from app.models.risk_profile import RiskProfile

    score_data = state.get("score_breakdown", {})
    recommendation = state.get("recommendation", {})
    errors = list(state.get("errors", []))

    try:
        risk_profile = RiskProfile(**score_data)
        catalog = load_plan_catalog()
        plan = catalog.get_plan_by_tier(recommendation.get("plan_tier", "Standard"))
        if plan is None:
            plan = catalog.plans[1]  # Default to Standard

        confidence, requires_review, reasons = evaluate_confidence(risk_profile, plan)
        state["confidence"] = confidence
        state["requires_human_review"] = requires_review
        state["confidence_reasons"] = reasons
    except Exception as exc:
        error_msg = f"Confidence evaluation failed: {exc}"
        logger.error(error_msg)
        errors.append(error_msg)
        state["errors"] = errors
        state["confidence"] = 0.5
        state["requires_human_review"] = True
    return state


def human_review_gate(state: WorkflowState) -> WorkflowState:
    """Tag the output for human review queue (ops integration point)."""
    logger.warning(
        "Routing to human review | confidence=%.3f | tier=%s",
        state.get("confidence", 0),
        state.get("recommendation", {}).get("plan_tier", "Unknown"),
    )
    trace = state.get("trace_metadata", {})
    trace["human_review_flagged"] = True
    state["trace_metadata"] = trace
    return state


def finalize_output(state: WorkflowState) -> WorkflowState:
    """Assemble the final recommendation response object."""
    recommendation = state.get("recommendation", {})
    score_data = state.get("score_breakdown", {})
    coverage = recommendation.get("coverage", {})
    request_id = state.get("request_id", str(uuid.uuid4()))
    errors = list(state.get("errors", []))

    # Build reasons from risk flags + confidence reasons
    risk_flags = score_data.get("risk_flags", [])
    conf_reasons = state.get("confidence_reasons", [])
    reasons = list(risk_flags) + [r for r in conf_reasons if r not in risk_flags]

    if not reasons:
        tier = recommendation.get("plan_tier", "Standard")
        reasons = [f"Risk score {score_data.get('total_score', 0):.0f}/100 maps to {tier} tier"]

    state["output"] = {
        "request_id": request_id,
        "plan_tier": recommendation.get("plan_tier", "Standard"),
        "coverage_recommendation": {
            "dwelling": coverage.get("dwelling", ""),
            "personal_property": coverage.get("personal_property", ""),
            "liability": coverage.get("liability", ""),
        },
        "premium_estimate_band": coverage.get("premium_monthly_band", ""),
        "confidence_score": state.get("confidence", 1.0),
        "reasons": reasons,
        "explanation": state.get("explanation", ""),
        "requires_human_review": state.get("requires_human_review", False),
        "score_breakdown": {
            "geo_hazard": score_data.get("geo_hazard_score", 0),
            "value_exposure": score_data.get("value_exposure_score", 0),
            "property_condition": score_data.get("property_condition_score", 0),
            "affordability_alignment": score_data.get("affordability_alignment_score", 0),
            "total": score_data.get("total_score", 0),
        },
        "trace_id": state.get("trace_metadata", {}).get("trace_id"),
        "versions": {
            "rules_version": settings.rules_version,
            "catalog_version": settings.catalog_version,
            "prompt_version": settings.prompt_version,
            "risk_data_version": settings.risk_data_version,
        },
        "errors": errors,
    }

    logger.info(
        "Output finalized | request_id=%s | tier=%s | confidence=%.3f",
        request_id,
        recommendation.get("plan_tier"),
        state.get("confidence", 1.0),
    )
    return state

"""Weighted scoring engine — deterministic, config-driven risk computation."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import yaml

from app.core.config import settings
from app.models.request import Preference, RecommendationRequest
from app.models.risk_profile import RiskProfile

logger = logging.getLogger(__name__)


def _load_thresholds() -> Dict[str, Any]:
    """Load scoring thresholds from YAML config."""
    with open(settings.thresholds_path, "r") as f:
        return yaml.safe_load(f)


def _load_risk_factors() -> Dict[str, Any]:
    """Load location risk factors from YAML config."""
    with open(settings.risk_factors_path, "r") as f:
        return yaml.safe_load(f)


def _get_location_risk(zip_code: str, state: str) -> Dict[str, Any]:
    """Resolve location risk data from mock dataset."""
    data = _load_risk_factors()
    zip_prefix = zip_code[:3]

    # Try ZIP prefix first
    if zip_prefix in data.get("zip_risk_factors", {}):
        logger.debug("Risk lookup: ZIP prefix '%s' matched", zip_prefix)
        return data["zip_risk_factors"][zip_prefix]

    # Fall back to state
    if state in data.get("state_defaults", {}):
        logger.debug("Risk lookup: state '%s' matched (ZIP prefix not found)", state)
        return data["state_defaults"][state]

    # Global default
    logger.debug("Risk lookup: using global default (no match for %s / %s)", zip_code, state)
    return data.get("global_default", {})


def compute_geo_hazard_score(
    zip_code: str, state: str, thresholds: Dict[str, Any]
) -> tuple[float, list[str]]:
    """Compute geo hazard risk score (0-30) from location data."""
    cfg = thresholds.get("geo_hazard", {})
    risk = _get_location_risk(zip_code, state)
    modifier = risk.get("base_hazard_modifier", 1.0)

    score = cfg.get("base_score", 10)
    flags: list[str] = []

    if risk.get("flood_zone"):
        score += cfg.get("flood_zone_add", 8)
        flags.append("Flood zone property")
    if risk.get("wildfire_zone"):
        score += cfg.get("wildfire_zone_add", 7)
        flags.append("Wildfire risk zone")
    if risk.get("tornado_alley"):
        score += cfg.get("tornado_alley_add", 6)
        flags.append("Tornado alley region")
    if risk.get("hurricane_zone"):
        score += cfg.get("hurricane_zone_add", 9)
        flags.append("Hurricane risk zone")
    if risk.get("earthquake_zone"):
        score += cfg.get("earthquake_zone_add", 5)
        flags.append("Earthquake risk zone")

    score = score * modifier
    max_score = cfg.get("max", 30)
    return min(round(score, 2), max_score), flags


def compute_value_exposure_score(
    home_price: float, thresholds: Dict[str, Any]
) -> float:
    """Compute value exposure score (0-30) from home price."""
    for tier in thresholds.get("value_exposure", {}).get("thresholds", []):
        if home_price <= tier["max_price"]:
            return float(tier["score"])
    return 30.0


def compute_property_condition_score(
    year_built: int, thresholds: Dict[str, Any]
) -> float:
    """Compute property condition score (0-20) from property age."""
    current_year = datetime.now().year
    age = max(0, current_year - year_built)
    for tier in thresholds.get("property_condition", {}).get("age_thresholds", []):
        if age <= tier["max_age"]:
            return float(tier["score"])
    return 20.0


def compute_affordability_score(
    preference: Preference, ltv: Optional[float], thresholds: Dict[str, Any]
) -> float:
    """Compute affordability alignment score (0-20) from preference and LTV."""
    cfg = thresholds.get("affordability_alignment", {})
    pref_scores = cfg.get("preference_scores", {})
    score = float(pref_scores.get(preference.value, 12))

    ltv_cfg = cfg.get("ltv_add", {})
    if ltv is not None and ltv >= ltv_cfg.get("high_ltv_threshold", 0.80):
        score += ltv_cfg.get("score_add", 4)

    return min(score, 20.0)


def compute_risk_profile(request: RecommendationRequest) -> RiskProfile:
    """
    Orchestrate all scoring dimensions and return a complete RiskProfile.

    This is the deterministic core — no LLM calls here.
    """
    thresholds = _load_thresholds()

    geo_score, risk_flags = compute_geo_hazard_score(
        request.location_zip, request.state, thresholds
    )
    value_score = compute_value_exposure_score(request.home_price, thresholds)
    condition_score = compute_property_condition_score(
        request.year_built, thresholds
    )
    affordability_score = compute_affordability_score(
        request.preference, request.ltv, thresholds
    )

    total = geo_score + value_score + condition_score + affordability_score

    logger.info(
        "Scoring complete | geo=%.1f value=%.1f condition=%.1f "
        "affordability=%.1f total=%.1f flags=%s",
        geo_score,
        value_score,
        condition_score,
        affordability_score,
        total,
        risk_flags,
    )

    return RiskProfile(
        geo_hazard_score=geo_score,
        value_exposure_score=value_score,
        property_condition_score=condition_score,
        affordability_alignment_score=affordability_score,
        total_score=min(round(total, 2), 100.0),
        risk_flags=risk_flags,
        risk_data_version=settings.risk_data_version,
        enrichment_source="mock_yaml",
    )

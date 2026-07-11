"""Tier mapping rules — deterministic plan selection from risk score."""
import logging
from typing import Optional

import yaml

from app.core.config import settings
from app.models.plan_catalog import PlanCatalog, PlanCatalogEntry
from app.models.risk_profile import RiskProfile

logger = logging.getLogger(__name__)

_catalog_cache: Optional[PlanCatalog] = None


def load_plan_catalog() -> PlanCatalog:
    """Load and cache the plan catalog from YAML."""
    global _catalog_cache
    if _catalog_cache is None:
        with open(settings.plan_catalog_path, "r") as f:
            data = yaml.safe_load(f)
        _catalog_cache = PlanCatalog(**data)
        logger.info(
            "Plan catalog loaded | version=%s | plans=%d",
            _catalog_cache.catalog_version,
            len(_catalog_cache.plans),
        )
    return _catalog_cache


def select_plan_tier(risk_profile: RiskProfile) -> PlanCatalogEntry:
    """
    Select the appropriate plan tier based on total risk score.

    This is the deterministic decision boundary — LLM cannot override this.
    """
    catalog = load_plan_catalog()
    plan = catalog.get_plan_for_score(risk_profile.total_score)

    if plan is None:
        logger.warning("No plan matched score %.1f — falling back to Custom", risk_profile.total_score)
        plan = catalog.get_plan_by_tier("Custom") or catalog.plans[-1]

    logger.info(
        "Plan selected | tier=%s | score=%.1f | range=[%d, %d]",
        plan.plan_tier,
        risk_profile.total_score,
        plan.min_score,
        plan.max_score,
    )
    return plan


def compute_coverage_bands(
    plan: PlanCatalogEntry, home_price: float
) -> dict:
    """
    Compute concrete dollar coverage bands from plan percentages and home price.
    Returns a dict with dwelling, personal_property, liability bands.
    """
    defaults = plan.coverage_defaults

    # Parse the pct band like "0.07%-0.10%" → (0.0007, 0.001)
    pct_band = defaults.premium_monthly_band_pct.replace("%", "").replace("+", "")
    parts = pct_band.split("-")
    try:
        low_pct = float(parts[0]) / 100
        high_pct = float(parts[1]) / 100 if len(parts) > 1 else low_pct * 1.3
    except (ValueError, IndexError):
        low_pct, high_pct = 0.07 / 100, 0.10 / 100

    premium_low = round(home_price * low_pct)
    premium_high = round(home_price * high_pct)

    return {
        "dwelling": defaults.dwelling_band,
        "personal_property": defaults.personal_property_band,
        "liability": defaults.liability_band,
        "premium_monthly_band": f"${premium_low:,}-${premium_high:,}/month",
    }

"""Risk enrichment agent — resolves geo and property risk factors."""
import logging
from typing import Any, Dict

import yaml

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def enrich_risk_from_profile(
    zip_code: str, state: str, home_price: float, year_built: int
) -> Dict[str, Any]:
    """
    Resolve risk factors for the given property using mock YAML data.

    Future: replace with live API calls to geo risk providers.
    Returns a dict of enriched risk feature signals.
    """
    with open(settings.risk_factors_path, "r") as f:
        data = yaml.safe_load(f)

    zip_prefix = zip_code[:3]
    location_data: Dict[str, Any] = {}

    if zip_prefix in data.get("zip_risk_factors", {}):
        location_data = data["zip_risk_factors"][zip_prefix]
        source = f"zip_prefix:{zip_prefix}"
    elif state in data.get("state_defaults", {}):
        location_data = data["state_defaults"][state]
        source = f"state_default:{state}"
    else:
        location_data = data.get("global_default", {})
        source = "global_default"

    logger.info(
        "Risk enrichment | zip=%s | state=%s | source=%s | hazards=%s",
        zip_code,
        state,
        source,
        [k for k, v in location_data.items() if k not in ("base_hazard_modifier", "region") and v is True],
    )

    return {
        "location": {
            "zip_code": zip_code,
            "state": state,
            "region": location_data.get("region", f"{state}"),
            "source": source,
        },
        "hazard_flags": {
            "flood_zone": location_data.get("flood_zone", False),
            "wildfire_zone": location_data.get("wildfire_zone", False),
            "tornado_alley": location_data.get("tornado_alley", False),
            "hurricane_zone": location_data.get("hurricane_zone", False),
            "earthquake_zone": location_data.get("earthquake_zone", False),
        },
        "base_hazard_modifier": location_data.get("base_hazard_modifier", 1.0),
        "property": {
            "home_price": home_price,
            "year_built": year_built,
        },
        "data_version": settings.risk_data_version,
    }

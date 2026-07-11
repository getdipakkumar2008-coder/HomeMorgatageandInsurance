"""Plan catalog schema — defines plan tier definitions loaded from YAML."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CoverageDefaults(BaseModel):
    """Coverage bands for a plan tier."""

    dwelling_band: str
    personal_property_band: str
    liability_band: str
    premium_monthly_band_pct: str


class PlanCatalogEntry(BaseModel):
    """A single plan tier entry in the catalog."""

    plan_id: str = Field(..., description="Unique plan identifier")
    plan_tier: str = Field(..., description="Tier name: Basic/Standard/Premium/Custom")
    min_score: int = Field(..., description="Minimum risk score for this tier")
    max_score: int = Field(..., description="Maximum risk score for this tier")
    description: str = Field("", description="Human-readable plan description")
    coverage_defaults: CoverageDefaults = Field(
        ..., description="Default coverage bands"
    )
    features: List[str] = Field(
        default_factory=list, description="Key features included"
    )


class PlanCatalog(BaseModel):
    """Full plan catalog loaded from plan_catalog.yaml."""

    catalog_version: str = Field("v1.0.0", description="Catalog version identifier")
    plans: List[PlanCatalogEntry] = Field(
        default_factory=list, description="All plan tier entries"
    )

    def get_plan_for_score(self, score: float) -> Optional[PlanCatalogEntry]:
        """Return the matching plan entry for a given total score."""
        for plan in self.plans:
            if plan.min_score <= score <= plan.max_score:
                return plan
        # Return highest tier if score exceeds all thresholds
        if self.plans:
            return self.plans[-1]
        return None

    def get_plan_by_tier(self, tier: str) -> Optional[PlanCatalogEntry]:
        """Return the plan entry for a specific tier name."""
        for plan in self.plans:
            if plan.plan_tier.lower() == tier.lower():
                return plan
        return None

"""Risk profile schema — output of the enrichment + scoring pipeline."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskProfile(BaseModel):
    """Scored risk dimensions for a property."""

    geo_hazard_score: float = Field(
        ..., ge=0, le=30, description="Geographic/natural hazard risk score (0-30)"
    )
    value_exposure_score: float = Field(
        ..., ge=0, le=30, description="Property value exposure score (0-30)"
    )
    property_condition_score: float = Field(
        ..., ge=0, le=20, description="Property age/condition score (0-20)"
    )
    affordability_alignment_score: float = Field(
        ..., ge=0, le=20, description="Affordability alignment score (0-20)"
    )
    total_score: float = Field(
        ..., ge=0, le=100, description="Aggregate weighted risk score (0-100)"
    )
    risk_flags: List[str] = Field(
        default_factory=list, description="Notable risk flags for this property"
    )
    risk_data_version: str = Field(
        "v1.0.0", description="Version of risk data used in enrichment"
    )
    enrichment_source: str = Field(
        "mock", description="Source of risk enrichment data"
    )

    @property
    def score_breakdown(self) -> Dict[str, float]:
        return {
            "geo_hazard": self.geo_hazard_score,
            "value_exposure": self.value_exposure_score,
            "property_condition": self.property_condition_score,
            "affordability_alignment": self.affordability_alignment_score,
            "total": self.total_score,
        }

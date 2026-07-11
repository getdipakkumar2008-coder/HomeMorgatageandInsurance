"""Response schemas for the recommendation API."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CoverageRecommendation(BaseModel):
    """Recommended coverage bands for dwelling, personal property, and liability."""

    dwelling: str = Field(..., description="Recommended dwelling coverage band")
    personal_property: str = Field(
        ..., description="Recommended personal property coverage band"
    )
    liability: str = Field(..., description="Recommended liability coverage band")


class VersionInfo(BaseModel):
    """Version metadata for reproducibility and auditing."""

    rules_version: str = "v1.0.0"
    catalog_version: str = "v1.0.0"
    prompt_version: str = "v1.0.0"
    risk_data_version: str = "v1.0.0"


class RecommendationResponse(BaseModel):
    """Full recommendation output returned by the API and shown in the UI."""

    request_id: str = Field(..., description="Unique request identifier (UUID)")
    plan_tier: str = Field(
        ..., description="Recommended plan tier: Basic/Standard/Premium/Custom"
    )
    coverage_recommendation: CoverageRecommendation = Field(
        ..., description="Recommended coverage bands"
    )
    premium_estimate_band: str = Field(
        ..., description="Estimated monthly premium band"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Recommendation confidence (0-1)"
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="Human-readable reasons supporting the recommendation",
    )
    explanation: Optional[str] = Field(
        None, description="AI-generated explanation narrative"
    )
    requires_human_review: bool = Field(
        False, description="Whether this case needs human review"
    )
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict, description="Breakdown of scoring dimensions"
    )
    trace_id: Optional[str] = Field(
        None, description="LangSmith trace identifier"
    )
    versions: VersionInfo = Field(
        default_factory=VersionInfo, description="Version metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "plan_tier": "Standard",
                "coverage_recommendation": {
                    "dwelling": "$520k-$650k",
                    "personal_property": "$195k-$260k",
                    "liability": "$300k-$500k",
                },
                "premium_estimate_band": "$379-$541/month",
                "confidence_score": 0.82,
                "reasons": [
                    "Moderate regional hazard profile (wildfire zone)",
                    "Home value in standard coverage range",
                    "Property built in 2008 — moderate age",
                ],
                "explanation": "Based on your property profile...",
                "requires_human_review": False,
                "score_breakdown": {
                    "geo_hazard": 17.0,
                    "value_exposure": 21.0,
                    "property_condition": 10.0,
                    "affordability_alignment": 12.0,
                    "total": 60.0,
                },
                "trace_id": None,
                "versions": {
                    "rules_version": "v1.0.0",
                    "catalog_version": "v1.0.0",
                    "prompt_version": "v1.0.0",
                    "risk_data_version": "v1.0.0",
                },
            }
        }
    }


class PlanListResponse(BaseModel):
    """Response for the GET /v1/plans endpoint."""

    catalog_version: str
    plans: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: Optional[str] = None

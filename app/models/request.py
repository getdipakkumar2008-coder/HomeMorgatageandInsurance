"""Input request schemas for the recommendation API."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PropertyType(str, Enum):
    single_family = "single_family"
    condo = "condo"
    townhouse = "townhouse"
    multi_family = "multi_family"
    manufactured = "manufactured"


class Preference(str, Enum):
    low_premium = "low_premium"
    balanced = "balanced"
    high_protection = "high_protection"


class RecommendationRequest(BaseModel):
    """Input profile for a home insurance recommendation."""

    home_price: float = Field(
        ..., gt=0, description="Estimated market value of the home in USD"
    )
    location_zip: str = Field(
        ..., min_length=5, max_length=10, description="Property ZIP code"
    )
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(
        ..., min_length=2, max_length=2, description="Two-letter state code"
    )
    property_type: PropertyType = Field(
        ..., description="Type of residential property"
    )
    year_built: int = Field(
        ..., ge=1800, le=2100, description="Year the property was built"
    )
    ltv: Optional[float] = Field(
        None, ge=0.0, le=1.5, description="Loan-to-value ratio (optional)"
    )
    preference: Preference = Field(
        Preference.balanced, description="User coverage preference"
    )

    @field_validator("state")
    @classmethod
    def normalize_state(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("location_zip")
    @classmethod
    def normalize_zip(cls, v: str) -> str:
        return v.strip()

    @field_validator("city")
    @classmethod
    def normalize_city(cls, v: str) -> str:
        return v.strip().title()

    model_config = {
        "json_schema_extra": {
            "example": {
                "home_price": 650000,
                "location_zip": "78701",
                "city": "Austin",
                "state": "TX",
                "property_type": "single_family",
                "year_built": 2008,
                "ltv": 0.78,
                "preference": "balanced",
            }
        }
    }

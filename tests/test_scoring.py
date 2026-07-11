"""Unit tests for the scoring engine."""
import pytest

from app.engine.scoring import (
    compute_affordability_score,
    compute_geo_hazard_score,
    compute_property_condition_score,
    compute_risk_profile,
    compute_value_exposure_score,
)
from app.models.request import Preference, PropertyType, RecommendationRequest

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_request() -> RecommendationRequest:
    return RecommendationRequest(
        home_price=450_000,
        location_zip="78701",
        city="Austin",
        state="TX",
        property_type=PropertyType.single_family,
        year_built=2005,
        ltv=0.75,
        preference=Preference.balanced,
    )


@pytest.fixture
def thresholds():
    import yaml
    from app.core.config import settings
    with open(settings.thresholds_path) as f:
        return yaml.safe_load(f)


# ─── Geo Hazard ───────────────────────────────────────────────────────────────

def test_geo_hazard_known_zip(thresholds):
    """Austin ZIP 787xx is a wildfire zone — should have elevated score."""
    score, flags = compute_geo_hazard_score("78701", "TX", thresholds)
    assert score > 10, "Wildfire zone should add points above base"
    assert any("wildfire" in f.lower() for f in flags)


def test_geo_hazard_max_cap(thresholds):
    """Score should never exceed 30."""
    score, _ = compute_geo_hazard_score("33101", "FL", thresholds)
    assert 0 <= score <= 30


def test_geo_hazard_unknown_zip_uses_state(thresholds):
    """Unknown ZIP prefix falls back to state defaults."""
    score_unknown, flags_unknown = compute_geo_hazard_score("99999", "TX", thresholds)
    # TX state has tornado_alley=True
    assert score_unknown > 10


def test_geo_hazard_global_default(thresholds):
    """Completely unknown ZIP + state uses global default (no extra flags)."""
    score, flags = compute_geo_hazard_score("99999", "ZZ", thresholds)
    # Only base_score, no hazard flags, modifier=1.0
    assert 0 <= score <= 30
    assert flags == []


# ─── Value Exposure ───────────────────────────────────────────────────────────

def test_value_exposure_low(thresholds):
    score = compute_value_exposure_score(200_000, thresholds)
    assert score == 10.0


def test_value_exposure_mid(thresholds):
    score = compute_value_exposure_score(450_000, thresholds)
    assert score == 16.0


def test_value_exposure_high(thresholds):
    score = compute_value_exposure_score(2_000_000, thresholds)
    assert score == 30.0


def test_value_exposure_boundary(thresholds):
    score = compute_value_exposure_score(300_000, thresholds)
    assert score == 10.0
    score2 = compute_value_exposure_score(300_001, thresholds)
    assert score2 == 16.0


# ─── Property Condition ───────────────────────────────────────────────────────

def test_property_condition_new(thresholds):
    """A brand-new home should get the lowest score."""
    score = compute_property_condition_score(2024, thresholds)
    assert score == 4.0


def test_property_condition_old(thresholds):
    """A very old home should get the highest score."""
    score = compute_property_condition_score(1900, thresholds)
    assert score == 20.0


def test_property_condition_mid(thresholds):
    year = 2000  # ~24 years old → max_age:40 → score:12
    score = compute_property_condition_score(year, thresholds)
    assert score == 12.0


# ─── Affordability ────────────────────────────────────────────────────────────

def test_affordability_low_premium(thresholds):
    score = compute_affordability_score(Preference.low_premium, None, thresholds)
    assert score == 8.0


def test_affordability_balanced(thresholds):
    score = compute_affordability_score(Preference.balanced, None, thresholds)
    assert score == 12.0


def test_affordability_high_protection(thresholds):
    score = compute_affordability_score(Preference.high_protection, None, thresholds)
    assert score == 18.0


def test_affordability_high_ltv_penalty(thresholds):
    """High LTV should add extra score (higher risk)."""
    base = compute_affordability_score(Preference.balanced, 0.75, thresholds)
    with_ltv = compute_affordability_score(Preference.balanced, 0.85, thresholds)
    assert with_ltv > base


def test_affordability_max_cap(thresholds):
    """Score should not exceed 20."""
    score = compute_affordability_score(Preference.high_protection, 0.95, thresholds)
    assert score <= 20.0


# ─── Full Risk Profile ─────────────────────────────────────────────────────────

def test_compute_risk_profile_returns_valid_range(sample_request):
    profile = compute_risk_profile(sample_request)
    assert 0 <= profile.geo_hazard_score <= 30
    assert 0 <= profile.value_exposure_score <= 30
    assert 0 <= profile.property_condition_score <= 20
    assert 0 <= profile.affordability_alignment_score <= 20
    assert 0 <= profile.total_score <= 100


def test_compute_risk_profile_total_is_sum(sample_request):
    """Total should equal sum of dimensions (within rounding)."""
    profile = compute_risk_profile(sample_request)
    expected = (
        profile.geo_hazard_score
        + profile.value_exposure_score
        + profile.property_condition_score
        + profile.affordability_alignment_score
    )
    assert abs(profile.total_score - expected) < 0.1


def test_compute_risk_profile_high_risk():
    """High-risk property (FL flood + hurricane + expensive + old + high_protection + high LTV)."""
    request = RecommendationRequest(
        home_price=900_000,
        location_zip="33101",
        city="Miami",
        state="FL",
        property_type=PropertyType.single_family,
        year_built=1960,
        ltv=0.90,
        preference=Preference.high_protection,
    )
    profile = compute_risk_profile(request)
    assert profile.total_score > 60, "High-risk property should have high total score"
    assert len(profile.risk_flags) > 0

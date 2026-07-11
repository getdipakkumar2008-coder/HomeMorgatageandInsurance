"""Integration tests for the LangGraph recommendation workflow."""
import pytest

from app.agents.workflow import run_recommendation_workflow


@pytest.fixture
def austin_profile():
    return {
        "home_price": 450_000,
        "location_zip": "78701",
        "city": "Austin",
        "state": "TX",
        "property_type": "single_family",
        "year_built": 2005,
        "ltv": 0.75,
        "preference": "balanced",
    }


@pytest.fixture
def miami_high_risk_profile():
    return {
        "home_price": 900_000,
        "location_zip": "33101",
        "city": "Miami",
        "state": "FL",
        "property_type": "single_family",
        "year_built": 1960,
        "ltv": 0.90,
        "preference": "high_protection",
    }


@pytest.fixture
def low_risk_profile():
    return {
        "home_price": 200_000,
        "location_zip": "30201",
        "city": "Atlanta",
        "state": "GA",
        "property_type": "condo",
        "year_built": 2020,
        "ltv": 0.50,
        "preference": "low_premium",
    }


# ─── Output Structure ─────────────────────────────────────────────────────────

def test_workflow_returns_plan_tier(austin_profile):
    output = run_recommendation_workflow(austin_profile)
    assert "plan_tier" in output
    assert output["plan_tier"] in ("Basic", "Standard", "Premium", "Custom")


def test_workflow_returns_coverage(austin_profile):
    output = run_recommendation_workflow(austin_profile)
    coverage = output.get("coverage_recommendation", {})
    assert "dwelling" in coverage
    assert "personal_property" in coverage
    assert "liability" in coverage


def test_workflow_returns_confidence(austin_profile):
    output = run_recommendation_workflow(austin_profile)
    conf = output.get("confidence_score", -1)
    assert 0.0 <= conf <= 1.0


def test_workflow_returns_score_breakdown(austin_profile):
    output = run_recommendation_workflow(austin_profile)
    breakdown = output.get("score_breakdown", {})
    assert "total" in breakdown
    assert 0 <= breakdown["total"] <= 100


def test_workflow_returns_explanation(austin_profile):
    output = run_recommendation_workflow(austin_profile)
    explanation = output.get("explanation", "")
    assert isinstance(explanation, str)
    assert len(explanation) > 20  # Should have meaningful text


def test_workflow_returns_request_id(austin_profile):
    output = run_recommendation_workflow(austin_profile)
    assert "request_id" in output
    assert len(output["request_id"]) > 0


def test_workflow_returns_versions(austin_profile):
    output = run_recommendation_workflow(austin_profile)
    versions = output.get("versions", {})
    assert "rules_version" in versions
    assert "catalog_version" in versions


# ─── Tier Selection Logic ─────────────────────────────────────────────────────

def test_low_risk_gets_basic_or_standard(low_risk_profile):
    output = run_recommendation_workflow(low_risk_profile)
    assert output["plan_tier"] in ("Basic", "Standard")


def test_high_risk_gets_premium_or_custom(miami_high_risk_profile):
    output = run_recommendation_workflow(miami_high_risk_profile)
    assert output["plan_tier"] in ("Premium", "Custom")


# ─── Determinism ─────────────────────────────────────────────────────────────

def test_workflow_is_deterministic(austin_profile):
    """Same input should produce same tier on repeated runs."""
    out1 = run_recommendation_workflow(austin_profile)
    out2 = run_recommendation_workflow(austin_profile)
    assert out1["plan_tier"] == out2["plan_tier"]
    assert abs(out1["score_breakdown"]["total"] - out2["score_breakdown"]["total"]) < 0.01


# ─── Custom Request ID ────────────────────────────────────────────────────────

def test_workflow_uses_provided_request_id(austin_profile):
    custom_id = "test-request-abc-123"
    output = run_recommendation_workflow(austin_profile, request_id=custom_id)
    assert output["request_id"] == custom_id


# ─── Preference Ordering ──────────────────────────────────────────────────────

def test_high_protection_preference_scores_higher():
    """high_protection preference should yield a higher or equal risk score than low_premium."""
    base = {
        "home_price": 400_000,
        "location_zip": "78701",
        "city": "Austin",
        "state": "TX",
        "property_type": "single_family",
        "year_built": 2010,
        "ltv": None,
    }
    out_low = run_recommendation_workflow({**base, "preference": "low_premium"})
    out_high = run_recommendation_workflow({**base, "preference": "high_protection"})
    assert (
        out_high["score_breakdown"]["total"] >= out_low["score_breakdown"]["total"]
    )


# ─── Fallback / Unknown ZIP ───────────────────────────────────────────────────

def test_workflow_handles_unknown_zip():
    """Unknown ZIP and state should still produce a recommendation via global defaults."""
    profile = {
        "home_price": 300_000,
        "location_zip": "99999",
        "city": "Unknown",
        "state": "ZZ",
        "property_type": "single_family",
        "year_built": 2000,
        "ltv": None,
        "preference": "balanced",
    }
    output = run_recommendation_workflow(profile)
    assert "plan_tier" in output
    assert output["plan_tier"] in ("Basic", "Standard", "Premium", "Custom")

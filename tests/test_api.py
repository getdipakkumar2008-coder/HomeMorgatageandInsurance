"""API endpoint tests using FastAPI TestClient."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router

# ─── Test App ─────────────────────────────────────────────────────────────────

app = FastAPI(title="HMIP Test")
app.include_router(router)
client = TestClient(app)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def valid_payload():
    return {
        "home_price": 450000,
        "location_zip": "78701",
        "city": "Austin",
        "state": "TX",
        "property_type": "single_family",
        "year_built": 2005,
        "ltv": 0.75,
        "preference": "balanced",
    }


# ─── Health Endpoint ──────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data


# ─── Plans Endpoint ───────────────────────────────────────────────────────────

def test_list_plans_returns_catalog():
    response = client.get("/v1/plans")
    assert response.status_code == 200
    data = response.json()
    assert "catalog_version" in data
    assert "plans" in data
    assert len(data["plans"]) >= 4  # Basic, Standard, Premium, Custom


def test_list_plans_has_correct_tiers():
    response = client.get("/v1/plans")
    tiers = {p["plan_tier"] for p in response.json()["plans"]}
    assert "Basic" in tiers
    assert "Standard" in tiers
    assert "Premium" in tiers
    assert "Custom" in tiers


# ─── Recommendation Endpoint ──────────────────────────────────────────────────

def test_recommendation_returns_200(valid_payload):
    response = client.post("/v1/recommendation", json=valid_payload)
    assert response.status_code == 200


def test_recommendation_response_schema(valid_payload):
    response = client.post("/v1/recommendation", json=valid_payload)
    data = response.json()
    required_keys = [
        "request_id",
        "plan_tier",
        "coverage_recommendation",
        "premium_estimate_band",
        "confidence_score",
        "reasons",
        "versions",
    ]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"


def test_recommendation_plan_tier_is_valid(valid_payload):
    response = client.post("/v1/recommendation", json=valid_payload)
    tier = response.json()["plan_tier"]
    assert tier in ("Basic", "Standard", "Premium", "Custom")


def test_recommendation_confidence_in_range(valid_payload):
    response = client.post("/v1/recommendation", json=valid_payload)
    conf = response.json()["confidence_score"]
    assert 0.0 <= conf <= 1.0


def test_recommendation_coverage_fields(valid_payload):
    response = client.post("/v1/recommendation", json=valid_payload)
    coverage = response.json()["coverage_recommendation"]
    assert "dwelling" in coverage
    assert "personal_property" in coverage
    assert "liability" in coverage


# ─── Input Validation ─────────────────────────────────────────────────────────

def test_recommendation_rejects_negative_price(valid_payload):
    payload = {**valid_payload, "home_price": -50000}
    response = client.post("/v1/recommendation", json=payload)
    assert response.status_code == 422


def test_recommendation_rejects_missing_zip(valid_payload):
    payload = {k: v for k, v in valid_payload.items() if k != "location_zip"}
    response = client.post("/v1/recommendation", json=payload)
    assert response.status_code == 422


def test_recommendation_rejects_invalid_property_type(valid_payload):
    payload = {**valid_payload, "property_type": "space_station"}
    response = client.post("/v1/recommendation", json=payload)
    assert response.status_code == 422


def test_recommendation_rejects_invalid_preference(valid_payload):
    payload = {**valid_payload, "preference": "whatever"}
    response = client.post("/v1/recommendation", json=payload)
    assert response.status_code == 422


def test_recommendation_optional_ltv(valid_payload):
    """LTV is optional — omitting it should still work."""
    payload = {k: v for k, v in valid_payload.items() if k != "ltv"}
    response = client.post("/v1/recommendation", json=payload)
    assert response.status_code == 200


# ─── State Normalization ──────────────────────────────────────────────────────

def test_recommendation_normalizes_state_lowercase(valid_payload):
    payload = {**valid_payload, "state": "tx"}
    response = client.post("/v1/recommendation", json=payload)
    assert response.status_code == 200
    assert response.json()["plan_tier"] in ("Basic", "Standard", "Premium", "Custom")


# ─── Different Preferences ────────────────────────────────────────────────────

@pytest.mark.parametrize("preference", ["low_premium", "balanced", "high_protection"])
def test_recommendation_all_preferences(valid_payload, preference):
    payload = {**valid_payload, "preference": preference}
    response = client.post("/v1/recommendation", json=payload)
    assert response.status_code == 200
    assert response.json()["plan_tier"] in ("Basic", "Standard", "Premium", "Custom")

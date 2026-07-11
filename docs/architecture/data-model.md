# Data Model Specification

## 1. Entities

### 1.1 RecommendationRequest
- request_id (UUID)
- created_at (timestamp)
- home_price (decimal)
- location_zip (string)
- city (string)
- state (string)
- property_type (enum)
- year_built (int)
- ltv (decimal, nullable)
- preference (enum: low_premium | balanced | high_protection)

### 1.2 RiskProfile
- request_id (UUID)
- geo_hazard_score (0-30)
- value_exposure_score (0-30)
- property_condition_score (0-20)
- affordability_alignment_score (0-20)
- risk_flags (jsonb)
- risk_data_version (string)

### 1.3 RecommendationResult
- request_id (UUID)
- plan_tier (enum: Basic | Standard | Premium | Custom)
- coverage_dwelling_band (string)
- coverage_property_band (string)
- coverage_liability_band (string)
- premium_monthly_band (string)
- confidence_score (0-1)
- reasons (jsonb)
- rules_version (string)
- prompt_version (string)
- trace_id (string)

### 1.4 PlanCatalog
- plan_id (string)
- plan_tier (enum)
- min_score (int)
- max_score (int)
- coverage_defaults (jsonb)
- active_from (timestamp)
- active_to (timestamp, nullable)
- catalog_version (string)

## 2. Versioning Strategy
- `rules_version`: deterministic engine release marker
- `catalog_version`: plan definition snapshot
- `prompt_version`: explanation prompt snapshot
- `risk_data_version`: enrichment dataset/API snapshot

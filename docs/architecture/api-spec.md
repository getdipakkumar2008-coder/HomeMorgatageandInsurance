# API Specification (Draft)

## 1. POST /v1/recommendation
Generate plan recommendation from property and user preference inputs.

### Request JSON
```json
{
  "home_price": 650000,
  "location_zip": "78701",
  "city": "Austin",
  "state": "TX",
  "property_type": "single_family",
  "year_built": 2008,
  "ltv": 0.78,
  "preference": "balanced"
}
```

### Response JSON
```json
{
  "request_id": "uuid",
  "plan_tier": "Standard",
  "coverage_recommendation": {
    "dwelling": "$600k-$700k",
    "personal_property": "$180k-$220k",
    "liability": "$300k-$500k"
  },
  "premium_estimate_band": "$220-$310",
  "confidence_score": 0.84,
  "reasons": [
    "Moderate regional hazard profile",
    "Home value aligns with standard coverage thresholds"
  ],
  "trace_id": "langsmith-trace-id",
  "versions": {
    "rules_version": "v1.0.0",
    "catalog_version": "v1.0.0",
    "prompt_version": "v1.0.0"
  }
}
```

## 2. GET /v1/plans
Returns active plan catalog for transparency and debugging.

### Response JSON
```json
{
  "plans": [
    {
      "plan_id": "basic-v1",
      "plan_tier": "Basic",
      "score_range": "0-35",
      "coverage_defaults": {}
    }
  ],
  "catalog_version": "v1.0.0"
}
```

## 3. POST /v1/evaluate (internal)
Runs benchmark scenarios for regression and prompt/rule validation.

### Request JSON
```json
{
  "dataset_id": "golden-v1",
  "run_tag": "pre-release-check"
}
```

### Response JSON
```json
{
  "pass_rate": 0.96,
  "failures": [],
  "run_id": "eval-run-uuid"
}
```

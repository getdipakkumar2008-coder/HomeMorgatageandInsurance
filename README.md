# 🏠 HomeMortgageInsurance Planner (HMIP)

An intelligent, explainable home insurance recommendation platform powered by **LangGraph** agent orchestration, **LangChain** + **OpenAI** for natural-language explanations, and a deterministic rule-based scoring engine.

---

## ✨ Features

- **Deterministic recommendation core** — weighted scoring across 4 risk dimensions mapped to 4 plan tiers (Basic / Standard / Premium / Custom)
- **LangGraph stateful workflow** — sequential nodes with fallback and human-review routing
- **AI-powered explanations** — LangChain + GPT-4o-mini generates plain-language rationale (never overrides the deterministic tier)
- **FastAPI REST API** — `POST /v1/recommendation`, `GET /v1/plans`, `GET /v1/health`
- **Streamlit UI** — interactive property intake with visual score breakdown
- **LangSmith tracing** — optional end-to-end observability
- **Config-driven** — plan catalog, risk factors, and thresholds all in YAML

---

## 📁 Project Structure

```
HomeMorgatageandInsurance/
├── main.py                          # Streamlit UI entry point
├── app/
│   ├── api/routes.py               # FastAPI endpoints
│   ├── core/
│   │   ├── config.py               # Settings, env loading
│   │   └── logging_config.py       # Structured logging
│   ├── models/
│   │   ├── request.py              # Input schemas (Pydantic)
│   │   ├── response.py             # Output schemas (Pydantic)
│   │   ├── risk_profile.py         # Risk scoring schema
│   │   └── plan_catalog.py         # Plan tier definitions
│   ├── engine/
│   │   ├── scoring.py              # Weighted scoring engine
│   │   ├── rules.py                # Tier mapping rules
│   │   └── confidence.py           # Confidence evaluator
│   ├── agents/
│   │   ├── workflow.py             # LangGraph workflow graph
│   │   ├── nodes.py                # Individual graph nodes
│   │   ├── state.py                # Typed graph state
│   │   ├── risk_enrichment.py      # Risk enrichment agent
│   │   └── explanation.py          # Explanation generation (LLM)
│   └── data/
│       ├── plan_catalog.yaml       # Versioned plan definitions
│       ├── risk_factors.yaml       # Location risk mock data
│       └── thresholds.yaml         # Scoring thresholds config
├── tests/
│   ├── test_scoring.py             # Unit tests for scoring engine
│   ├── test_workflow.py            # Integration tests for LangGraph
│   └── test_api.py                 # API endpoint tests
├── docs/                           # Architecture docs and ADRs
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/getdipakkumar2008-coder/HomeMorgatageandInsurance.git
cd HomeMorgatageandInsurance

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

> **Note:** The OpenAI API key is optional. Without it, explanations will use a deterministic fallback template. All plan tier recommendations remain fully functional.

### 3. Run the Streamlit UI

```bash
streamlit run main.py
```

Open `http://localhost:8501` in your browser.

### 4. Run the FastAPI Server

```bash
uvicorn app.api.routes:router --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔧 Configuration

### Plan Catalog (`app/data/plan_catalog.yaml`)

Defines the 4 plan tiers (Basic / Standard / Premium / Custom) with score ranges, coverage bands, and features. Versioned via `catalog_version`.

### Risk Factors (`app/data/risk_factors.yaml`)

Mock geo-hazard data by ZIP prefix and state. Supports: flood zone, wildfire zone, tornado alley, hurricane zone, earthquake zone. Intended to be replaced by live API calls in Phase 3.

### Thresholds (`app/data/thresholds.yaml`)

Scoring weights, tier boundaries, and confidence thresholds. All deterministic logic is driven by this file.

---

## 🤖 Workflow Architecture

```
Start → ValidateInput → NormalizeInput → EnrichRisk
                                              │
                              (failed?) → FallbackRiskDefaults
                                              │
                                          ScoreRisk → RecommendPlan → EvaluateConfidence
                                                                              │
                                                            (low conf?) → HumanReviewGate
                                                                              │
                                                                       GenerateExplanation
                                                                              │
                                                                       FinalizeOutput → End
```

**Key design principles:**
- The LLM is **only used for explanation generation** — never for tier decisions
- All thresholds and tier boundaries are config-driven and versioned
- Low-confidence recommendations are flagged for human review

---

## 🔍 API Reference

### `POST /v1/recommendation`

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

**Response:**
```json
{
  "request_id": "uuid",
  "plan_tier": "Standard",
  "coverage_recommendation": { "dwelling": "...", "personal_property": "...", "liability": "..." },
  "premium_estimate_band": "$455-$650/month",
  "confidence_score": 0.85,
  "reasons": ["..."],
  "explanation": "AI-generated rationale...",
  "requires_human_review": false,
  "score_breakdown": { "geo_hazard": 17, "value_exposure": 21, "property_condition": 10, "affordability_alignment": 12, "total": 60 },
  "versions": { "rules_version": "v1.0.0", "catalog_version": "v1.0.0", "prompt_version": "v1.0.0", "risk_data_version": "v1.0.0" }
}
```

### `GET /v1/plans`

Returns the active plan catalog.

### `GET /v1/health`

Returns application health status.

---

## 🔒 Security & Compliance

- Input strictly validated via Pydantic schemas
- LLM receives only structured decision facts (no raw user input)
- LLM cannot override the deterministic tier
- All outputs include version metadata for auditing
- Low-confidence cases are flagged for human review
- See `docs/architecture/security-guardrails.md` for full policy

---

## 📊 LangSmith Observability

Set in `.env`:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=hmip-planner
```

All workflow node transitions, inputs, and outputs will be traced in LangSmith.

---

## ⚠️ Disclaimer

This application is for informational and demonstration purposes only. It does not constitute a binding insurance quote, underwriting decision, or legal advice. Always consult a licensed insurance professional.

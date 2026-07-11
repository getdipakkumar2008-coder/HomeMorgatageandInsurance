# System Architecture Overview

## 1. Architecture Style
Hybrid decision system:
- Deterministic recommendation core (rules + weighted scoring)
- Agentic orchestration for enrichment and explanation
- Human-review path for low-confidence outputs

## 2. Logical Components
1. API Layer (FastAPI)
2. Input Validation Module
3. Risk Enrichment Agent
4. Recommendation Engine (deterministic)
5. Explanation Agent (LLM)
6. Guardrail & Compliance Layer
7. Observability Layer (LangSmith)
8. Persistence Layer (Postgres)
9. Config Registry (plans, thresholds, prompt versions)

## 3. Data Flow
1. User submits property profile.
2. Input is validated and normalized.
3. Risk enrichment gathers location/property risk factors.
4. Recommendation engine computes scores and selects plan tier.
5. Explanation agent generates rationale from structured facts.
6. Confidence evaluator tags output.
7. Response + trace metadata stored and returned.

## 4. Reliability Strategy
- Fallback risk defaults if enrichment fails.
- Deterministic engine still produces output.
- Retries and timeout boundaries per node.
- Observability on all node transitions.

## 5. Upgradeability Principles
- Config-driven thresholds and rule tables.
- Agent/tool abstraction boundaries.
- Prompt versioning with evaluation gates.
- Provider-agnostic LLM interface.

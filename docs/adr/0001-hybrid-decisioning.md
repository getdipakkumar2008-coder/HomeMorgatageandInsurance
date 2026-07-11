# ADR-0001: Hybrid Decisioning (Deterministic Core + LLM Explanation)

## Status
Accepted

## Context
Insurance recommendation must be explainable, auditable, and stable while still benefiting from natural-language reasoning for user communication.

## Decision
Use deterministic rules + weighted scoring for recommendation tier selection.
Use LLM only to generate explanation text from structured decision artifacts.

## Consequences
### Positive
- High auditability and consistency.
- Lower risk of LLM-driven decision instability.
- Easier regression testing.

### Negative
- Less flexibility for unusual edge cases in early versions.
- Requires manual evolution of deterministic rules.

## Follow-up
Introduce controlled edge-case adjudication in Phase 2 with strict guardrails.

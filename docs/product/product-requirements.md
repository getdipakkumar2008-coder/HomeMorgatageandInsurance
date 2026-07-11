# Product Requirements Document (PRD)
## HomeMortgageInsurance Planner (HMIP)

## 1. Vision
Build an intelligent, explainable platform that recommends home insurance plans based on property value, location risk, and user preference, with upgrade-ready agentic architecture.

## 2. Problem Statement
Homeowners and buyers struggle to select appropriate insurance due to fragmented risk data, complex coverage options, and low transparency in recommendations.

## 3. Goals
- Provide reliable insurance plan tier recommendation (Basic/Standard/Premium/Custom).
- Explain recommendation rationale in plain language.
- Support deterministic decisioning with AI-assisted explanation.
- Enable future integrations with carrier APIs and real-time risk data sources.
- Ensure observability and evaluation of agent behavior.

## 4. Non-Goals (Phase 1)
- Policy purchase/binding.
- Carrier-specific quote finalization.
- Legal underwriting decisions.
- Claims processing workflows.

## 5. Target Users
- Primary: Home buyers and homeowners.
- Secondary: Advisors/internal analysts.
- Future: Mortgage brokers and partner portals.

## 6. Core Inputs
- Home price
- Location (ZIP/city/state)
- Property type
- Year built
- Optional: LTV, user affordability preference

## 7. Core Outputs
- Recommended plan tier
- Coverage recommendation bands
- Estimated monthly premium range
- Confidence score
- Transparent reasons and assumptions

## 8. Functional Requirements
1. User input collection and validation.
2. Location and property risk enrichment.
3. Deterministic scoring + rule-based recommendation.
4. AI-generated explanation from structured decision facts.
5. Recommendation response in JSON + user-readable narrative.
6. Traceability for each recommendation execution.

## 9. Non-Functional Requirements
- Explainability-first.
- Deterministic core logic.
- Auditable outputs and config versions.
- Fault tolerance with fallback defaults.
- Upgradeable module boundaries.

## 10. Success Metrics
- Recommendation completion rate >= 99%.
- Explanation acceptance score >= 85% in UX feedback.
- Low-confidence case capture rate = 100%.
- Regression test pass rate >= 95% for benchmark scenarios.

## 11. Risks
- Incomplete location risk signals.
- Hallucinated explanation text.
- Rule drift without versioning discipline.
- Overfitting to initial threshold assumptions.

## 12. Assumptions
- Phase 1 uses mock or static risk datasets.
- Plan catalog is internally defined and versioned.
- Human review flow for low-confidence is available in ops backlog.

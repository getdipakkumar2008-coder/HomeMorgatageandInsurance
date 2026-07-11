# Task Breakdown (Pre-Implementation)

## Epic 1: Repo & Standards
- [ ] Review ResturantNameGenerator style conventions
- [ ] Define folder layout and naming standards
- [ ] Setup linting, formatting, typing, pre-commit checks

## Epic 2: Domain Modeling
- [ ] Define request/response schemas
- [ ] Define risk profile schema
- [ ] Define plan catalog schema and seed data

## Epic 3: Recommendation Core
- [ ] Implement weighted scoring engine
- [ ] Implement tier mapping rules
- [ ] Externalize thresholds into versioned config

## Epic 4: LangGraph Workflow
- [ ] Build workflow graph and typed state
- [ ] Implement fallback branches
- [ ] Implement error handling and retries

## Epic 5: Explanation + Safety
- [ ] Build explanation prompt templates
- [ ] Enforce structured output contract
- [ ] Add hallucination and prohibited-claim checks

## Epic 6: API & Persistence
- [ ] Build `/v1/recommendation` endpoint
- [ ] Persist recommendation audit logs
- [ ] Add `/v1/plans` and internal `/v1/evaluate` endpoints

## Epic 7: Observability & Evals
- [ ] Add LangSmith tracing metadata
- [ ] Build benchmark scenarios
- [ ] Run evals in CI before release

## Epic 8: Ops & Governance
- [ ] Incident runbook
- [ ] ADR templates and update policy
- [ ] Versioning policy for rules/prompts/catalog

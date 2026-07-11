# ADR-0002: LangGraph for Agent Orchestration

## Status
Accepted

## Context
The workflow includes sequential logic, retries, fallback paths, and optional human review routing.

## Decision
Use LangGraph to orchestrate multi-node stateful execution across validation, enrichment, scoring, recommendation, explanation, and confidence evaluation.

## Consequences
### Positive
- Explicit execution graph and failure handling.
- Better observability and debuggability.
- Easy insertion of future nodes/tools.

### Negative
- Added orchestration complexity vs simple chains.
- Requires disciplined state contract management.

## Follow-up
Define typed state schema and per-node SLAs before implementation.

# LangSmith Observability Plan

## 1. Objectives
- End-to-end traceability for every recommendation.
- Fast diagnosis of failures and low-confidence decisions.
- Evaluation-driven prompt/rule updates.

## 2. Trace Design
Capture per request:
- request_id
- node transitions
- input/output summaries per node
- selected plan tier and score breakdown
- confidence score and fallback usage
- versions: rules/catalog/prompt/risk-data

## 3. Monitoring Signals
- Recommendation success/failure rate
- Node-level latency and timeout rate
- Fallback activation frequency
- Low-confidence ratio
- Explanation validation failure rate

## 4. Evaluation Workflow
- Maintain benchmark dataset across regions/property types.
- Run scheduled evals for model/prompt/rule changes.
- Block promotion if regression thresholds fail.

## 5. Incident Diagnostics
- Use trace_id from API response.
- Inspect node path, failed tool calls, and guardrail triggers.
- Classify incident: data issue / rule issue / LLM output issue / infra issue.

# Security and Guardrails

## 1. Guardrail Objectives
- Prevent unsafe or misleading recommendation text.
- Ensure deterministic decision boundaries are enforced.
- Protect sensitive user inputs.

## 2. Input Guardrails
- Strict schema validation.
- Numeric range checks for home price/year built/LTV.
- Location normalization and canonicalization.
- Reject malformed or adversarial prompt-like text in free fields.

## 3. LLM Guardrails
- LLM receives only structured decision facts.
- No direct override of deterministic recommendation tier.
- Constrained response schema.
- Prohibited claims list (e.g., legal guarantees, underwriting approvals).

## 4. Data Security
- Encrypt data at rest and in transit.
- Role-based access for admin/config operations.
- Secrets managed through secure vault/provider.

## 5. Auditability
- Persist request, decision facts, versions, and trace IDs.
- Immutable audit logs for recommendation events.

# LangGraph Workflow Specification

## 1. Graph Nodes
- `Start`
- `ValidateInput`
- `NormalizeInput`
- `EnrichRisk`
- `FallbackRiskDefaults`
- `ScoreRisk`
- `RecommendPlan`
- `GenerateExplanation`
- `EvaluateConfidence`
- `HumanReviewGate`
- `FinalizeOutput`
- `End`

## 2. Primary Path
```
Start -> ValidateInput -> NormalizeInput -> EnrichRisk -> ScoreRisk -> RecommendPlan -> GenerateExplanation -> EvaluateConfidence -> FinalizeOutput -> End
```

## 3. Fallback Paths
- If enrichment fails:
  `EnrichRisk -> FallbackRiskDefaults -> ScoreRisk`
- If confidence below threshold:
  `EvaluateConfidence -> HumanReviewGate -> FinalizeOutput`

## 4. State Contract (shared)
- `input_profile`
- `risk_features`
- `score_breakdown`
- `recommendation`
- `explanation`
- `confidence`
- `trace_metadata`
- `errors`

## 5. Node I/O (summary)
- `EnrichRisk`: input_profile -> risk_features
- `ScoreRisk`: risk_features -> score_breakdown
- `RecommendPlan`: score_breakdown -> recommendation
- `GenerateExplanation`: recommendation + score_breakdown -> explanation
- `EvaluateConfidence`: all decision artifacts -> confidence

## 6. Implementation Notes
- Use typed state objects (Pydantic/dataclass).
- Keep deterministic nodes free from LLM side effects.
- Restrict LLM usage to explanation and optional edge adjudication.
- Emit LangSmith spans per node with decision artifacts.

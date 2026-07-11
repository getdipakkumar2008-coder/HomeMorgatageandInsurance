# Risk Register

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R1 | Incomplete risk enrichment data | Medium | High | Fallback defaults + confidence penalty |
| R2 | Hallucinated explanation content | Medium | High | Structured outputs + prohibited claim filters |
| R3 | Threshold drift over time | High | Medium | Config versioning + periodic eval reviews |
| R4 | Biased recommendation patterns | Medium | High | Bias checks in benchmark dataset |
| R5 | External provider instability | Medium | Medium | Provider abstraction + retry/fallback |
| R6 | Poor observability | Low | High | Mandatory LangSmith tracing in all flows |

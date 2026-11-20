# Dashboard Page 4: Mandate Audit

## 1. Purpose

The Mandate Audit page evaluates whether selected mutual fund schemes exhibit characteristics consistent with their stated investment mandates, disclosed costs and assigned benchmarks.

The audit is a historical screening exercise. Its flags are heuristic indicators, not regulatory classifications or investment recommendations.

## 2. Audit Scope

- Schemes reviewed: 16
- AMCs covered: 5
- Scheme types: Active and passive
- Research window: Five years
- Unit of analysis: Scheme-level
- Filters: AMC, fund category and scheme

## 3. Stated Mandate and Disclosed Costs

The top table displays the selected scheme's:

- Scheme name and AMC
- Fund category
- Assigned benchmark
- Direct and Regular plan TER
- Objective evidence status
- Source document ID and source page

Source references should be used to trace disclosed information to the underlying documents. Objective evidence status indicates the nature of the available evidence, not an independent verification of investment performance.

## 4. Measured Metrics

Four measures are displayed for the selected scheme:

| Metric | Field | Interpretation |
|---|---|---|
| R-squared | r2 | Proportion of return variation explained by the regression benchmark |
| Beta | beta | Estimated sensitivity to benchmark movements |
| Maximum drawdown | max_dd | Largest peak-to-trough decline |
| Tracking error | te_ann | Annualised variability of active returns |

Tracking error may be unavailable for schemes whose benchmark series lacks the required historical coverage.

## 5. Mandate Audit Rules

The status matrix displays the following five audit rules and the separate R5 proxy result.

| Rule | Field | Purpose |
|---|---|---|
| R1: Benchmark Fit | R1_benchmark_fit | Assesses suitability of the assigned benchmark |
| R2: Peer Relative Risk | R2_peer_risk | Screens risk characteristics against the peer group |
| R3: Cost vs Expected Gap | R3_cost_fit | Evaluates disclosed costs against the expected gap |
| R4: Passive Tracking Fit | R4_passive_fit | Screens tracking behaviour of passive schemes |
| R5: Closet-Indexer Screen | R5_closet_indexer_screen | Assesses whether an active fund resembles its benchmark too closely |

### R5 interpretation

Formal R5 results are unavailable in this audit. The separate R5 provisional proxy heuristic is displayed for transparency but must not be treated as a completed formal R5 assessment.

## 6. Status and Conditional Formatting

- CLEAR: No heuristic flag raised.
- FLAG: Potential concern requiring review.
- N/A: Rule does not apply to the scheme.
- UNAVAILABLE: Formal assessment could not be completed.

Conditional formatting distinguishes CLEAR, FLAG, N/A and UNAVAILABLE statuses.

## 7. Interpretation Notes

- Audit flags are heuristic screening indicators, not regulatory classifications.
- Benchmark series used in the analysis retain provisional status.
- A CLEAR proxy result does not imply that formal R5 assessment passed.
- Missing metrics should not be interpreted as zero or as evidence of satisfactory performance.
- The audit is descriptive and should not be interpreted as investment advice.

## 8. Dashboard Layout

1. AMC, fund category and scheme slicers.
2. Audit scope indicators.
3. Stated mandate and disclosed costs table.
4. Four selected-scheme metric cards.
5. Mandate audit status matrix.
6. Audit framework and interpretation notes.

The page uses a compact matrix rather than multiple additional tables or a heatmap to avoid overcrowding and preserve interpretability.

## 9. Data Source

Primary dashboard dataset:

`dashboard/data/mandate_audit.csv`

Source-level audit results:

`results/mandate_audit.csv`

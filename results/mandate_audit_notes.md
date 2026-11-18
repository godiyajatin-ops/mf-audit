# Mandate Audit Interpretation

## 1. Purpose and scope

`mandate_audit.csv` is a rule-based screening output using the preregistered thresholds in `config.yaml`.

The audit covers 16 underlying mutual fund schemes across 5 AMCs. Each scheme has Direct and Regular plan records in the supporting analytical data.

- `results/mandate_audit.csv`: 16 scheme-level records, represented by the Direct plan.
- `results/mandate_audit_plan_detail.csv`: 32 plan-level records, retaining Direct and Regular detail.
- `results/fee_gap.csv`: 16 paired Direct-Regular comparisons.

The scheme-level file is the primary audit output. The plan-level file preserves analytical traceability.

## 2. Screening rules and thresholds

### R1: Benchmark fit

- Threshold: `r2_min = 0.85`.
- Applied to active Direct schemes.
- R-squared below the threshold is flagged.
- Non-applicable schemes are marked `N/A`.
- Missing required measurements must remain `UNAVAILABLE`, not `CLEAR`.

Current scheme-level results: 12 CLEAR, 4 N/A.

### R2: Peer-risk outlier

- Threshold: `peer_sd = 1.5`.
- Uses absolute within-category population z-scores.
- Measures: beta and maximum drawdown.
- Applied to active Direct schemes.
- A flag indicates an observation beyond the configured threshold on either measure.

Current scheme-level results: 9 CLEAR, 3 FLAG, 4 N/A.

### R3: Direct-Regular cost fit

- Threshold: `cost_tol_pp = 0.30` percentage points.
- Compares the observed Direct-Regular return gap with the expected gap based on TER differences.
- Flags an absolute residual above the configured tolerance.

Current scheme-level results: 15 CLEAR, 1 FLAG.

Pair 6, ICICI Prudential Flexi Cap Fund, is flagged with a residual of approximately 0.371793 percentage points.

This is a screening discrepancy, not proof of investor loss or misconduct.

### R4: Passive tracking fit

- Threshold: `passive_te_max = 0.01` (1% annualized tracking error).
- Applied to passive Direct schemes.
- Missing tracking-error measurements must be marked `UNAVAILABLE`.

Current scheme-level results: 4 CLEAR, 12 N/A.

### R5: Closet-indexer screen

The formal calibrated R5 screen is currently `UNAVAILABLE` for active schemes.

The specification requires thresholds calibrated from passive controls (`q_r2` and `q_te`). These thresholds have not yet been established and recorded in the configuration.

The separate `R5_provisional_proxy_heuristic` column preserves the earlier exploratory high-R-squared/low-tracking-error heuristic. It is not a calibrated result and must not be interpreted as one.

## 3. Scheme objective evidence

Objective evidence is recorded in `data/manual/scheme_facts.csv`.

| Evidence status | Schemes | Interpretation |
|---|---:|---|
| `verified_text` | 12 | Objective text identified in a scheme-specific source |
| `verified_text_manual_match` | 2 | Objective text identified on an AMC-level page that explicitly names the scheme; manually matched |
| `partial` | 2 | Factsheet establishes category and product positioning, but not formal objective wording |

The two partial records are:
- Pair 4: Nippon India Large Cap Fund.
- Pair 12: Nippon India Growth Mid Cap Fund.

The two manually matched records are:
- Pair 2: ICICI Prudential Large Cap Fund.
- Pair 6: ICICI Prudential Flexi Cap Fund.

The manual matches refer to DOC 4, page 172. The page is assigned at AMC level in the retrieval data, so the manual scheme-name match is explicitly disclosed.

Partial evidence must not be represented as a verified formal investment objective.

## 4. Interpretation and limitations

- Flags identify records for further review. They do not establish a mandate breach, mis-selling, or regulatory violation.
- `N/A` means a rule does not apply to that scheme.
- `UNAVAILABLE` means a required input or calibration is not available.
- Missing evidence must never be translated into a clear result.
- R5 is not acceptance-complete until passive-control calibration is implemented and documented.
- Objective evidence quality varies across schemes and is disclosed above.
- TER and return-gap comparisons are analytical estimates based on the available source data and measurement window.
- The audit is exploratory and covers a limited universe. It is not a recommendation to buy, hold, or sell any mutual fund.

## 5. Current validation status

Structural validation passed:

- 16 scheme-level rows.
- 16 unique scheme codes and pair IDs.
- 32 plan-level supporting rows.
- Both Direct and Regular records retained for every pair.
- 16 fee-gap pairs.
- 16 objective evidence records.
- No duplicate scheme-level pair IDs.
- Formal R5 remains unavailable pending calibration.

This structural validation does not by itself establish that every underlying metric, source document, or screening assumption is economically correct.

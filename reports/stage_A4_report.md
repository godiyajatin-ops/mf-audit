# Stage A4 Report

**Status: PASS — completed 2026-11-16**

Stage A4 delivered the Power BI dashboard, validated data pack, supporting specifications and static figures. The final PBIX was built and visually reviewed by the human reviewer. A3 analytical outputs were not rerun or modified during A4.

## 1. Data pack and validation

| File | Rows |
|---|---:|
| dim_scheme.csv | 32 |
| metrics.csv | 96 |
| alpha.csv | 32 |
| fee_gap.csv | 16 |
| control_check.csv | 4 |
| rolling_returns.csv | 31,414 |
| drawdown.csv | 31,414 |
| capture.csv | 32 |
| rolling_beta.csv | 3,902 |
| benchmark_levels.csv | 8,664 |
| glossary.csv | 11 |

- Data pack: 11 CSV files, approximately 4.440 MB.
- Excel data pack: `dashboard/MF_Audit_DataPack.xlsx`.
- Dashboard validator: PASS, 11 files, 0 warnings.
- Dashboard contract tests: 6 passed.
- Full project test suite: 11 passed.
- Five-value source cross-check: 5/5 exact matches, as recorded below.

| Value | Key | Field | Pack | Source | Match |
|---|---|---|---:|---:|---|
| alpha.csv | scheme_code=103504 | alpha_ann | -0.0003684462864983401 | -0.0003684462864983401 | PASS |
| fee_gap.csv | pair_id=1 | gap_pp | 0.6425660235996 | 0.6425660235996 | PASS |
| control_check.csv | scheme_code=120684 | deviation_pp | -0.11329274277978307 | -0.11329274277978307 | PASS |
| metrics.csv | scheme_code=113296, 3Y | cagr | 0.070584 | 0.070584 | PASS |
| rolling_beta.csv | scheme_code=100377, 2026-08-04 | beta_252 | 0.9572987144173987 | 0.9572987144173987 | PASS |

## 2. Data handling and analytical safeguards

- `provisional=True` is set only when benchmark basis is `estimated_hybrid` (8 of 32 scheme-plan records).
- The independent `caveat_flag` records common Stage A3 limitations and does not replace the benchmark flag.
- Legitimate missing values are preserved: passive funds do not receive BH-family p-values, and frozen A3 tracking-error/capture values remain unavailable for estimated-hybrid schemes.
- The rolling-beta diagnostic covers four representative A3 schemes. Maximum per-scheme daily change was 0.029558, below 0.25. Exported values ranged from 0.735948 to 0.999495. The previously reported 1.4 spike is not present in the exported beta series. The generator uses a 252-observation rolling window and omits pre-window rows.

## 3. Static figures and specifications

Five static figures are present in `reports/figures/`, generated at 150 dpi and each larger than 10 KB:

- `scorecard_table.png`
- `rolling_3y.png`
- `drawdown.png`
- `capture_scatter.png`
- `cost_audit.png`

Supporting specifications:

- `dashboard/DATA_CONTRACT.md`
- `dashboard/DAX_MEASURES.md`
- `dashboard/BUILD_SPEC.md`
- `dashboard/CHECKLIST.md`

## 4. Human dashboard acceptance

Final dashboard: `dashboard/MF_Audit_Dashboard.pbix`.

The final PBIX was saved and human-reviewed. Four pages were reviewed:

1. Method & Limitations
2. Scorecard
3. Risk & Rolling
4. Cost Audit

Four page screenshots are saved under `dashboard/dashboard_imgs/`:

- `Method & Limitations.png`
- `Scorecard.png`
- `Risk & Rolling.png`
- `Cost Audit.png`

The screenshots are approximately 1292 × 727 pixels. The original 1920 × 1080 requirement was accepted as a documented deviation; images were not artificially upscaled.

The final PBIX uses the accepted dark institutional theme rather than the originally specified light theme. The checklist records both deviations.

Fallback HTML was skipped because Power BI was available and the PBIX was completed.

## 5. Data-derived dashboard highlights

- 5 of 12 active Direct funds show alpha significant at 10% FDR.
- Realised Direct-Regular gap exceeds expected TER gap in 16 of 16 pairs.
- All 4 passive funds' alpha is within 0.2 pp of expectation.

## 6. Limitations retained

A4 does not resolve or remove the underlying A3 limitations:

- Eight scheme-plan records use provisional estimated-hybrid BSE benchmarks; actual BSE TRI remains unavailable.
- TER is a 30-Sep-2026 point-in-time disclosure, not a historical five-year series.
- Survivorship status remains unclear.
- Persistence results remain exploratory and inconclusive.
- The ICICI Prudential Flexi Cap pair 6 R3 residual remains unresolved because historical TER disclosures are unavailable.
- The inherited A1 pytest test-collection issue remains a separate outstanding project item.

## 7. Stage outcome

**Stage A4: PASS.**

The data pack, validation, contract tests, documented source cross-check, static figures, final PBIX and human visual review are complete. A3 analytical results were not modified by A4.

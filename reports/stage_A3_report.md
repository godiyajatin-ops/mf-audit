# Stage A3 — Results and audit

**Status: COMPLETE WITH LIMITATIONS**

**Research window:** 2021-10-30 to 2026-10-30
**All results are provisional.** This report follows the approved project decision to use estimated hybrid BSE series while actual BSE 100/500 TRI is unavailable. The older A2 report records the data state at A2 close; this A3 run uses the later approved fallback now stored in the database.

## Work completed

| Preregistered item | Result | Output |
|---|---|---|
| CAPM alpha, HAC/Newey-West SE, BH-FDR | 32 schemes estimated; 12 active Direct-Growth funds form the primary family. 10/12 point estimates are positive; 5/12 remain significant at q=0.10. | `results/alpha.csv` |
| Persistence | First-half vs second-half alpha Spearman rho = 0.385; p = 0.217; fund-resampling 95% interval = [-0.350, 0.818] (5,000 replicates). Exploratory and inconclusive. | `results/persistence.csv` |
| Direct-Regular costs | 16/16 pairs complete. Median realized CAGR gap = 0.759 pp; median disclosed TER gap = 0.610 pp; median residual = 0.146 pp. Wilcoxon p = 0.000031. | `results/fee_gap.csv` |
| Mandate rules | R1: 12 clear; R2: 9 clear / 3 flagged; R3: 15 pairs clear / 1 flagged; R4: 8 passive plan records clear; R5: 12 clear. | `results/mandate_audit.csv` |
| Passive controls | All 4 Direct index-fund controls fall within the preregistered ±1.0 pp band for alpha versus disclosed TER. | `results/control_check.csv` |
| Robustness | Monthly alpha: 4/12 primary funds BH-significant; NIFTY 500 TRI: 5/12; 5% RF: 5/12; 7% RF: 5/12; leave best/worst active Direct funds out: 4/10 remaining significant. Moving-block bootstrap (20 trading days, 2,000 draws per primary fund): 6/12 intervals include zero. | `results/robustness_summary.csv` |
| Data quality and factsheet cross-checks | Latest recheck: 170 PASS, 0 WARN, 0 FAIL. Existing factsheet return cross-checks: 12/12 PASS across six schemes. | `results/dq_report.csv`, `results/factsheet_crosscheck.csv` |

A3 charts and rolling-beta series were also generated: `alpha_forest.png`, `persistence_scatter.png`, `fee_gap.png`, `rolling_beta.png`, and `rolling_beta.csv` in `results/`.

## Review of the four flags

The September 2026 AMC factsheets were checked against each flagged metric. The peer-risk flags are contextualized: HDFC Large Cap's flag is a modestly deeper drawdown than this small peer group; Nippon India Flexi Cap's beta is slightly above peers but its category is explicitly dynamic across market caps; SBI Midcap's flag is for a lower beta, with its factsheet confirming a mid-cap mandate and Nifty Midcap 150 benchmark. These remain mechanical flags in the audit output, with no evidence of mandate mismatch in the reviewed disclosures. The factsheet beta ratios use different horizons from the project's five-year estimates.

The factsheets also record manager-tenure changes during the window for Nippon Flexi Cap (one manager since January 2023) and SBI Midcap (manager since April 2024); ICICI Flexi Cap was renamed in August 2026. These facts are documented context only and do not establish the cause of any metric.

The ICICI Prudential Flexi Cap R3 flag remains a threshold breach, not a resolved exception. Its factsheet describes a dynamic multi-cap fund benchmarked to BSE 500 TRI and separately labels current BER values from TER; it notes that the displayed BER presentation changed after 31-Mar-2026 and points to separate TER disclosures. No five-year TER history is present in the available files, so the residual cannot be attributed to a cause from this evidence. The R3 threshold and flag are retained.

Structured evidence and review conclusions are in `results/a3_flag_review.csv`. Source pages: HDFC September factsheet p. 11; Nippon September factsheet p. 30; SBI September factsheet p. 23 (PDF p. 26); ICICI September factsheet p. 15.

## Data and interpretation limits

- Eight scheme-plan records use the approved estimated hybrid BSE 100/500 series. The hybrid combines BSE price-index data with the matching NIFTY TRI/price dividend wedge; it is not actual BSE TRI. The stored manifest records 1,236 observations for each BSE hybrid series. NIFTY 500 TRI was separately used as a common-benchmark sensitivity.
- The 30-Sep-2026 TER snapshot is not a historical five-year expense series. TER-gap reconciliation is indicative.
- Persistence is exploratory with only 12 active funds. The bootstrap interval is wide and includes zero.
- A1's incomplete pytest collection remains unresolved. Actual BSE TRI acquisition and comparison against the estimated hybrids remain open human tasks.

## Reproducible commands

From the project root, run the extractor before the analysis. The extractor writes scheme facts only after full 16-pair validation.

```powershell
.\.venv\Scripts\python.exe scripts\a3_extract_ter.py
.\.venv\Scripts\python.exe -m src.verify_data
.\.venv\Scripts\python.exe -m src.regression
.\.venv\Scripts\python.exe -m src.fdr
.\.venv\Scripts\python.exe -m src.persistence
.\.venv\Scripts\python.exe -m src.fee_gap
.\.venv\Scripts\python.exe -m src.control_check
.\.venv\Scripts\python.exe -m src.robustness
.\.venv\Scripts\python.exe -m src.mandate_audit
.\.venv\Scripts\python.exe -m src.figures_a3
```

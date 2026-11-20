# CV Bullets — Mutual Fund Audit

Numbers are sourced from the project's results CSV files.
All bullets have received human approval for external use, subject to the qualifications documented below.

## Variant A — Analytics-focused

- [APPROVED] Built a PostgreSQL and Python analytics pipeline covering 32 mutual-fund scheme-plan records across 5 AMCs, using five years of daily NAV data (November 2021 to October 2026); calculated CAGR, volatility, Sharpe and Sortino ratios, drawdowns, tracking error and benchmark-relative metrics.

- [APPROVED] Estimated CAPM alpha using Newey-West standard errors and Benjamini-Hochberg FDR correction, and evaluated active funds alongside passive index-fund controls.

- [APPROVED] Quantified Direct-versus-Regular plan return differences across 16 provisional matched scheme pairs, finding an observed median CAGR gap of 0.76 percentage points; compared the gap against disclosed expense-ratio differentials without treating the association as causal.

## Variant B — Analytics + RAG

- [APPROVED] Built a mutual-fund document-and-data assistant combining hybrid BM25 and dense retrieval over AMC factsheets, citation-backed responses, refusal handling and a parameterized read-only SQL router.

- [APPROVED] Evaluated the assistant on a 10-question held-out set, achieving 100% intent accuracy, 100% numeric exactness (3/3), 100% refusal accuracy (1/1), and 50% Hit@3.

- [APPROVED] Developed a mandate-versus-behaviour audit comparing disclosed benchmarks and expense ratios against measured alpha, R-squared, beta, drawdown and tracking error, using rule-based checks across five audit dimensions; the closet-indexer screen (R5) remained unavailable because calibration thresholds were not configured.

## Evidence and qualifications

| Claim | Source |
|---|---|
| 32 scheme-plan records | results/alpha.csv |
| 5 AMCs | Project universe and scheme records |
| 5-year NAV window | results/metrics.csv |
| 16 matched pairs | results/fee_gap.csv |
| Median CAGR gap: 0.758884 pp | results/fee_gap.csv |
| Held-out evaluation metrics | results/eval_summary.csv |
| Audit dimensions and measurements | results/mandate_audit.csv |

### Important qualifications

- The held-out evaluation contains only 10 questions. Numeric exactness is 3/3 and refusal accuracy is 1/1; these are small evaluation samples.
- All 16 matched-pair comparisons are provisional. The 0.76 pp figure is an observed median Direct-Regular CAGR gap, not a causal estimate of TER impact.
- Some benchmark and TER comparisons are provisional. Do not imply that every benchmark or disclosure is fully confirmed.
- Audit flags are heuristic screens, not regulatory findings.
- Do not claim production deployment, CI or automated live data acquisition.
## Human approval record

- Approval status: APPROVED
- Approved on: 2026-11-21
- Scope: All six CV bullets in Variant A and Variant B.
- Approved by: Project owner
- Qualification: Approval covers the wording and claims as documented; project limitations remain applicable.
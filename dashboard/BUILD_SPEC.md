# Stage A4 Dashboard Build Specification

Four report pages only, named **Method & Limitations**, **Scorecard**, **Risk & Rolling**, and **Cost Audit**. Do not add a fifth page. Retain the approved dark institutional design. Use light grey/white for every title, subtitle, legend, axis, and KPI label. This is a documented deviation from the original white-theme preference.

## Data model and labels

- Load the 11 CSVs in `dashboard/data/` as separate tables; do not append or merge facts into a single visual table.
- Use `dim_scheme[scheme_code]` as the one-side dimension key for scheme-level fact tables. Keep single-direction filter flow.
- Use `dim_window` for the Scorecard window selector and `dim_date` for date-series axes. See `DAX_MEASURES.md` for relationships.
- Use `short_name` for chart labels. It includes `D` or `R`, is unique, and is at most 28 characters.
- Do not relate `fee_gap` to `dim_scheme` using `pair_id`. Use the pair table’s own `amc` and `category` fields for Cost Audit filters.
- `provisional=True` means only `benchmark_basis == estimated_hybrid` (8 of 32 scheme-plans). `caveat_flag=True` is separate and records common Stage A3 limitations; it is not a substitute for benchmark basis.
- The frozen A3 outputs have no BH family p-value for passive funds and no benchmark-relative TE/capture metrics for estimated-hybrid schemes. Preserve those blanks; show passive p as `n/a` in the visible table. Do not replace unavailable values with zero.

## Page 0 — Method & Limitations

Keep the headline, research period/universe, methods, benchmark basis, limitations, and educational disclaimer in readable sections. Replace the current typo `indow` with `window`. Remove internal QA notes from this canvas and retain them in the Stage A4 report.

Use this verified copy:

> **Window:** 30 Oct 2021 to 30 Oct 2026. **Universe:** 32 schemes (16 Direct/Regular pairs), 5 AMCs. **Methods:** CAPM alpha with Newey-West standard errors; Benjamini-Hochberg FDR at q = 0.10; Sharpe = (R − Rf) / sigma, Rf = 6% p.a.; drawdown from running peak. NAV is net of costs. **Benchmarks:** NSE TRI series. Eight scheme-plans use an estimated BSE 100/500 TRI (BSE price index × Nifty dividend wedge); those results are provisional. **Limitations:** TER is a 30-Sep-2026 snapshot, not a historical series; persistence is exploratory (12 active funds; Spearman rho = 0.385, p = 0.217); survivorship status is not fully resolved. *Educational analysis, not investment advice.*

## Page 1 — Scorecard

- Add slicers for category, AMC, plan, and `window_label` (default window `FULL`; default plan `Direct`). Use slicers from `dim_scheme` and `dim_window`.
- Scorecard table: unique `dim_scheme[short_name]`, plan, alpha, BH-adjusted p, CAGR, volatility, and max drawdown. Keep Direct/Regular distinct. Show passive blank adjusted p as `n/a`.
- Apply conditional formatting to **Max drawdown only**.
- Alpha bar chart: axis `short_name`; value `Alpha (Direct)` or a single-plan Average; never Sum. Do not group Direct and Regular under the same scheme label.
- KPI cards use explicit measures from `DAX_MEASURES.md`.
- Default Direct-plan title, generated from the exported results: **“5 of 12 active Direct funds show alpha significant at 10% FDR.”** If the slicer changes plan, refresh the title or reset plan to Direct before export.

## Page 2 — Risk & Rolling

- Add category, AMC, and plan slicers from `dim_scheme`; check cross-filter interactions on both visuals.
- Rolling beta line: X = `dim_date[Date]`; Y = Average of `rolling_beta[beta_252]`; Legend = `dim_scheme[short_name]`. Do not show an all-scheme mean as a single line. This export contains **four representative A3 schemes** (one active per Large/Flexi/Mid Cap group plus one passive scheme), not all 32 schemes; say so in its subtitle. Values begin after the 252-observation rolling window.
- Rolling 3Y return comparison: X = `dim_date[Date]`; plot `rolling_returns[rolling_return_3y]` and `rolling_returns[benchmark_return_3y]` as separate lines. These are matched on the same 756 common scheme/benchmark observations. Filter to a selected scheme when comparing individual fund and benchmark.
- Drawdown: use an **Area chart** with X = date and Average `drawdown` across selected schemes. Title “Average Drawdown Across Selected Schemes”. Format its Y-axis as `0%`, not decimal fractions.
- Capture scatter: use only rows with available benchmark metrics. X = up capture, Y = down capture, size = TE (`te_ann`); add constant reference lines at 1.0 on both axes. Label axes and note that eight estimated-hybrid scheme-plans have no frozen A3 capture/TE estimates.

## Page 3 — Cost Audit

- Pair table fields: scheme base name, `gap_pp`, `expected_pp`, and `residual_pp`; labels “Scheme”, “Realised gap (pp)”, “Expected gap (pp)”, and “Residual (pp)”. Keep all 16 pairs visible; include the provisional indicator in a tooltip/column.
- Gap comparison chart: grouped bars for realized gap and expected TER gap by scheme. Use pair-level values; never Sum duplicate plan rows.
- Add the **Median Rupee Impact (Rs 1,00,000)** card. It is the median of source `rupee_gap`, with the common-period basis disclosed.
- Use pair-level `amc` and `category` slicers from `fee_gap`. Do not add plan or window slicers to this paired full-window calculation.
- Control-check table contains four passive rows. Use the title “All four passive funds’ alpha is within 0.2 pp of expectation” only while the data confirms all four meet that threshold.
- Result-derived gap title: **“Realised Direct-Regular gap exceeds expected TER gap in 16 of 16 pairs.”** Recompute the count from `residual_pp > 0` if the data changes.

## Result-derived titles

`src/export_dashboard_data.py` computes the default-state headlines from the output data and prints the three current titles. Do not hard-code a count independently of the data. If data changes, rerun the exporter, copy the printed titles, and validate the claim before saving the PBIX.

## Final visual review

At presentation size, check all axis units, no truncated labels, slicers cross-filter their intended visuals, the 16 pair rows are visible, and no tooltip obscures content. Keep exactly these four pages. Do not mark A4 PASS before the human confirms the PBIX build and screenshots.

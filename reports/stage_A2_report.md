# Stage A2 Report: SQL Metrics Layer

**Status:** PASS
**Report date:** 2026-11-13
**Project:** mf-audit

## 1. Summary

Stage A2 implemented descriptive performance and risk metrics in PostgreSQL and independently reproduced them using Pandas. SQL/Pandas parity passed for all 96 scheme-window combinations. Factsheet cross-checks passed for 12 observations across six schemes. Required exports were generated and deterministic.

The stage retains the inherited data limitations: eight schemes lack historical BSE benchmark TRI coverage, and the risk-free rate is a constant 6% annual assumption. Benchmark-relative metrics for the eight affected schemes remain unavailable.

## 2. Task completion

| Task | Status | Evidence |
|---|---|---|
| A2.1 Return, benchmark and risk-free views | DONE | `sql/a2_views.sql`; RF coverage and alignment validation |
| A2.2 Drawdown and rolling volatility views | DONE | `sql/a2_rolling.sql`; 64/64 fund-volatility and 48/48 benchmark-volatility comparisons passed |
| A2.3 SQL metrics table | DONE | `sql/a2_metrics.sql`; `res_metrics` contains 96 rows |
| A2.4 Independent Pandas implementation | DONE | `src/metrics_pandas.py`; 96 records generated |
| A2.5 SQL/Pandas parity | DONE | `src/check_metrics_parity.py`; 96 rows compared, zero failures |
| A2.6 Known-series tests | DONE | `tests/test_metrics.py`; 5 tests passed |
| A2.7 Factsheet cross-check | DONE | `results/factsheet_crosscheck.csv`; 12/12 comparisons passed |
| A2.8 Metrics exports | DONE | `results/metrics.csv`; `results/metrics_by_window.csv`; deterministic re-export hashes |
| A2.9 Sanity checks | DONE | Category-level summary and 32-scheme anomaly checks; no threshold flags |

## 3. Acceptance checks

| Check | Result |
|---|---|
| A1 DQ report has zero FAIL rows | PASS; eight documented WARNs |
| Distinct NAV schemes | 32 |
| Risk-free observations | 1,241 |
| SQL metrics rows | 96 |
| SQL/Pandas parity | PASS; zero failures |
| Known-series unit tests | PASS; 5/5 |
| Factsheet comparisons | PASS; 12/12 |
| Full-window export | 32 rows |
| All-window export | 96 rows |
| Deterministic SQL exports | PASS; hashes unchanged on re-export |
| Mandatory full-window metrics non-null | PASS |
| Sanity thresholds | PASS; no flags across 32 schemes |

## 4. Sanity-check findings

All 32 schemes passed the specified anomaly thresholds:

- Annualised volatility outside 5%–40%: none.
- Maximum drawdown shallower than -2%: none.
- Sharpe ratio above 3: none.

Category-level summaries were reviewed for Flexi Cap, Index, Large Cap and Mid Cap schemes. No anomaly flags were identified.

## 5. Limitations and risks

1. Historical BSE 100 TRI and BSE 500 TRI were unavailable. Eight schemes therefore have no benchmark-relative metrics. No substitute benchmark was used.
2. The risk-free rate is a constant 6% annual assumption, not a historical observed series.
3. The survivorship investigation remains inconclusive. No claim is made that survivorship bias has been eliminated.
4. The inherited A1 pytest invocation collected no tests. A1's test-suite completeness remains unresolved. This does not alter the separate A2 result of five passing known-series tests.
5. Factsheet cross-checks cover six schemes and 12 observations, not the entire universe.

## 6. Human checkpoints

- HA2.1: Completed. Factsheet-reported returns were supplied and 12 comparisons passed.
- HA2.2: Reviewed. Category summaries and anomaly checks showed no threshold flags.

## 7. Deviations

No benchmark substitutions were made. The specified annualisation, sample-standard-deviation and window conventions were retained. Benchmark-relative metrics remain NULL where the required benchmark TRI is unavailable.

## 8. Readiness for next stage

**Readiness: YES, subject to inherited A1 limitations remaining documented.**

Stage A2 acceptance checks are complete. Stage A3 may begin only after the human reviews this report and confirms the next stage.

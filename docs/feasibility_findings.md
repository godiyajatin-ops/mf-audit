# Stage 0 - Feasibility Findings

## 1. AMFI NAV data feasibility

- Official source: AMFI NAV download and historical NAV interface.
- Latest NAV master was downloaded and inspected. The file uses semicolon-separated records with scheme code, ISIN, scheme name, plan, option, NAV and date fields, alongside AMC/category heading rows.
- Historical retrieval is limited to a maximum 90-day period per request.
- A test for ICICI Prudential Corporate Bond Fund, Direct Plan - Growth (scheme code 120692), covered 1-Jan-2026 to 29-Mar-2026.
- The export contained 56 NAV observations through 27-Mar-2026. Weekends and market holidays explain the absence of observations on some calendar dates.
- A repeated identical request returned consistent records.
- Historical exports are category-level and may contain multiple schemes; scheme-code filtering is required.
- Five-code survivorship probe was inconclusive. Historical codes absent from the current master were identified, but historical retrieval and closure/merger status were not conclusively established.

## 2. TRI benchmark feasibility

Five Total Returns Index datasets were obtained from Nifty Indices:
- NIFTY 50 TRI
- NIFTY 100 TRI
- NIFTY 500 TRI
- NIFTY MIDCAP 150 TRI
- NIFTY NEXT 50 TRI

The downloaded annual files cover approximately November 2021 to November 2026. Combined validation found consistent overlapping observations and no conflicting TRI values. Duplicate observations across overlapping annual files must be deduplicated by index and date during Stage A1. The Total Returns Index series, not Net Total Return Index, is the selected benchmark input.

## 3. AMC ranking

Source: AMFI scheme-wise category-wise Average Assets under Management workbook, July-September 2026.

Operational definition: sum of active equity scheme AAUM rows, excluding separately classified index funds and ETFs and using the workbook's column excluding domestic FoFs but including overseas FoFs. Values were converted from lakh rupees to crore rupees.

| Rank | AMC | Active equity AUM (? crore) |
|---:|---|---:|
| 1 | HDFC Mutual Fund | 448,687.11 |
| 2 | ICICI Prudential Mutual Fund | 425,058.87 |
| 3 | SBI Mutual Fund | 420,636.79 |
| 4 | Nippon India Mutual Fund | 324,725.97 |
| 5 | Kotak Mahindra Mutual Fund | 260,363.06 |

This ranking is recorded in config.yaml and the approved preregistration.

## 4. Factsheet extraction feasibility

September 2026 factsheets for HDFC, ICICI Prudential and SBI Mutual Funds were obtained. Basic PDF text extraction using PyMuPDF was successful across the documents. Relevant objective, benchmark, TER, riskometer and portfolio-related text was present.

Reliable field-level table extraction and validation of paired scheme values were not completed in Stage 0. Detailed extraction and manual verification are deferred to Stage B1.

## 5. Risk-free rate

No historical RBI 91-day Treasury Bill yield series was incorporated during Stage 0. A constant annual risk-free rate of 6% is adopted as a fallback assumption. Stage A3 must include sensitivity tests at 5% and 7%.

## 6. Database and environment

- Python 3.11.9 virtual environment established.
- Required dependencies installed; requirements.lock.txt generated.
- pip check returned no broken requirements.
- PostgreSQL 18.6 was used instead of the originally specified PostgreSQL 16.
- Application and read-only database connections were tested; SELECT 1 succeeded.
- Read-only role restrictions were tested against public schema table creation.

## 7. Known limitations and deviations

1. Survivorship/closed-scheme retrieval remains inconclusive. This must be acknowledged when interpreting results.
2. AMFI historical requests are limited to 90 days and category-level exports require scheme-code filtering.
3. Per-request elapsed download times were not recorded during the feasibility probe.
4. Factsheet text extraction feasibility passed, but field-level table extraction remains for Stage B1.
5. The 6% risk-free rate is an assumption, not a historical observed series; Stage A3 sensitivity tests are mandatory.
6. TRI annual files overlap and must be deduplicated during Stage A1.
7. PostgreSQL 18.6 is an environment deviation from the originally specified PostgreSQL 16.

## 8. Preregistration and ordering

- Preregistration draft commit: 9c798f1.
- Preregistration approval commit: a6c9317.
- Approval tag: prereg-approved.
- Approval timestamp: 2026-11-02T22:23:06Z.
- T0.9 ordering script executed successfully. The AMFI history directory contained zero files at the time of the check; feasibility probes were kept under the probe directory.
- The approved research design must not be changed except through a dated amendment.

Stage 0 conclusion: feasibility work is complete with the limitations above carried forward into subsequent stages.



## Stage A1 — Data Quality and Feasibility Findings

### Benchmark Alignment

| Metric | Result |
|---|---:|
| Eligible NAV observations | 29,586 |
| Exact-date aligned observations | 29,460 |
| Unmatched observations | 126 |
| Alignment percentage | 99.574% |
| Minimum acceptance threshold | 98% |

The observed alignment percentage exceeds the predefined 98% threshold.

Alignment is calculated only for schemes whose benchmark TRI series is available.

### Benchmark Coverage Limitation

Seven benchmark records exist in the database, but historical TRI observations are currently available for only five:

1. NIFTY 50 TRI
2. NIFTY 100 TRI
3. NIFTY 500 TRI
4. NIFTY MIDCAP 150 TRI
5. NIFTY NEXT 50 TRI

Historical TRI observations are currently unavailable for:

- BSE 100 TRI
- BSE 500 TRI

Eight schemes depend on these two BSE benchmarks.

Consequently:
- 24 of 32 schemes currently have benchmark-series coverage.
- 8 schemes cannot yet be evaluated against their stated benchmarks.
- BSE price-index data has not been substituted for TRI data.
- Missing benchmark observations have not been forward-filled.

### Risk-Free Rate Limitation

A constant annual risk-free rate of 6% is used as a fallback.

This is an assumption rather than an observed historical risk-free time series.

Stage A3 must include sensitivity analysis using 5% and 7%.

### Feasibility Conclusion

Stage A1 database ingestion and benchmark alignment satisfy the 98% alignment threshold for schemes with available benchmark data.

The pipeline is operational and repeatable.

However, benchmark-relative analysis for the eight BSE-dependent schemes remains pending until valid historical BSE TRI observations are obtained.

These limitations must be carried forward into subsequent analysis and reporting.

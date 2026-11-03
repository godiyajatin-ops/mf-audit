# Data Lineage

Source URLs, retrieval dates, raw file hashes and data acquisition decisions will be documented here.


## Stage A1 — Data Pipeline and Database Loading

### Research Window
30 October 2021 to 30 October 2026.

### Data Sources and Processed Data

| Dataset | Source / File | Records |
|---|---|---:|
| Scheme universe | config/universe.csv | 32 schemes |
| Scheme master | data/processed/scheme_master.parquet | 14,441 records |
| Mutual fund NAV | data/processed/nav_long.parquet | 39,478 observations |
| Benchmark TRI | data/processed/benchmark_tri_long.parquet | 6,192 observations |
| Benchmark metadata | dim_benchmark | 7 benchmarks |
| Risk-free rate | fact_rf | 1,241 observations |

### Database Tables

- dim_benchmark: benchmark metadata.
- dim_scheme: frozen scheme universe and benchmark mappings.
- fact_nav: daily mutual fund NAV observations.
- fact_benchmark_tri: daily benchmark total returns index observations.
- fact_rf: daily risk-free rate observations.

### Risk-Free Rate Assumption

A constant annual risk-free rate of 6% is used as a fallback assumption.

Sensitivity analysis using 5% and 7% rates is required in Stage A3.

### Benchmark Mapping

Scheme benchmarks are mapped using factsheet-stated benchmarks where available, with default benchmark mappings as fallback.

The benchmark_confirmed field indicates factsheet confirmation, not availability of historical benchmark data.

### Data Processing

- NAV and TRI data restricted to the approved research window.
- Duplicate scheme-date and benchmark-date observations checked.
- Database loading implemented through src/load_all.py.
- PostgreSQL upserts used to support repeatable execution.
- SQL alignment view created in sql/views.sql.
- No forward-filling of missing benchmark observations.

### Database Loading Results

| Table | Final Records |
|---|---:|
| dim_benchmark | 7 |
| dim_scheme | 32 |
| fact_nav | 39,478 |
| fact_benchmark_tri | 6,192 |
| fact_rf | 1,241 |

A second execution of the loader produced identical row counts, confirming idempotent loading.

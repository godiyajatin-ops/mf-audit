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

## Stage A3 — TER/BER source lineage and analysis

- Extraction date: 2026-11-14. Target date: 2026-09-30. Frozen universe: 16 pairs / 32 plan records.
- Extractor: `scripts/a3_extract_ter.py`. It reads the five files in `data/raw_docs/probe/ter`, matches names exactly after case/punctuation normalization, reconciles all matching values, and updates the ignored manual CSV only after full coverage and conflict checks pass.
- Values were selected from `ter-of-mf-schemes.xlsx`, sheet `TER_Revised`; duplicate matching values in other recognized TER workbooks were reconciled. `TotalExpenseRatioSep2026.xlsx` was read but has no TER/BER table header and supplied no rows.
- SHA-256 at extraction (source files unchanged):
  - `HDFCMF_SCHEMES_TER_30-09-2026.xls`: `4494D0D1B2FF1781070040FF6781A929A53213FC325EB0E459772F2B73E72C4C`
  - `TER-2026-2027.xlsx`: `6FF414E6A10E283E234E22A34DE73C3F4E99A4872D31FB1183A0FFD6A81D6718`
  - `ter-of-mf-schemes.xlsx`: `E39A0E796A405486D5D081BF392543721EE29FB8B15AA62ECF1E33EEBC2C40E3`
  - `TotalExpenseRatio2026-2027.xlsx`: `EAB869125CC1E185BB377C9B02C4E59830A70E3011223F9C2063FDF42F66E6B2`
  - `TotalExpenseRatioSep2026.xlsx`: `3C8652CD5A11D2989143FB1B7B9FA9F43F0A92CCE5D34203000191FC87E6924D`
- TER and BER values, plus per-plan filename/sheet/row provenance, are stored in `data/manual/scheme_facts.csv` (the `data/` tree is Git-ignored).
- Stage A3 result scripts and outputs are listed in `docs/COMMANDS.md` and `reports/stage_A3_report.md`.

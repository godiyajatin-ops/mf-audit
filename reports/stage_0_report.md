# Stage 0 Completion Report

**Status: COMPLETE WITH LIMITATIONS**

## Outcome

The project scaffold, Python environment, PostgreSQL connection, AMFI feasibility probe, TRI benchmark acquisition and validation, AMC ranking, factsheet text-extraction probe, risk-free-rate decision and preregistration approval have been completed.

## Locked research design

- Study window: 30-Oct-2021 to 30-Oct-2026.
- Five AMCs ranked by active equity AAUM.
- 12 active equity schemes and 4 passive schemes, each with Direct-Growth and Regular-Growth comparison where available, as defined by the approved preregistration.
- Category-specific TRI benchmarks.
- CAPM alpha with Newey-West standard errors.
- Benjamini-Hochberg false-discovery control at q=0.10.
- Constant 6% annual risk-free-rate assumption, with mandatory 5% and 7% sensitivity tests in Stage A3.
- Mandate audit thresholds and robustness procedures are locked in docs/preregistration.md.

## Git audit trail

- Initial scaffold: 926745f.
- Preregistration DRAFT: 9c798f1.
- Preregistration APPROVED: a6c9317.
- Approval tag: prereg-approved.
- T0.9 ordering check executed; zero files were present in data/raw/amfi/history at check time.

## Limitations carried forward

- Survivorship probe inconclusive.
- AMFI historical retrieval is limited to 90 days per request.
- Per-request elapsed times were not captured.
- Factsheet field-level table extraction remains for Stage B1.
- Constant 6% risk-free rate is an assumption.
- TRI annual-file overlaps require deduplication in Stage A1.
- PostgreSQL 18.6 used instead of PostgreSQL 16.

These limitations are recorded in docs/feasibility_findings.md. They must not be hidden or treated as resolved in later analysis.

## Handoff

Stage 0 is closed. Proceed to Stage A1: data pipeline and warehouse. Do not alter the approved preregistration without a dated amendment.

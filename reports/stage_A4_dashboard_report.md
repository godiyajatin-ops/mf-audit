# Stage A4 — Power BI Dashboard

**Status: PASS — completed 2026-11-16**

**Dashboard:** `dashboard/MF_Audit_Dashboard.pbix`

**Data pack:** `dashboard/data/` (11 CSV files) and `dashboard/MF_Audit_DataPack.xlsx`

**A3 input provenance:** commit `70867a1be328e0fde1d006b9e58deb2dde537008`, recorded in `results/MANIFEST.json`.

## Final dashboard pages

| Page | Final content | Human review |
|---|---|---|
| Method & Limitations | Research design, benchmark basis, provisional status and methodological caveats | Complete |
| Scorecard | Scheme-level performance table, alpha results and dashboard filters | Complete |
| Risk & Rolling | Rolling beta, matched rolling 3Y returns, drawdown and capture analysis | Complete |
| Cost Audit | Direct-Regular fee-gap comparison, rupee impact and passive control checks | Complete |

The final PBIX was saved and visually reviewed. Four corresponding screenshots are stored in `dashboard/dashboard_imgs/`.

## Data and validation

- 11 CSV files in the dashboard data pack.
- Data pack size: approximately 4.440 MB.
- Dashboard validator: PASS, 11 files, 0 warnings.
- Dashboard contract tests: 6 passed.
- Full project test suite: 11 passed.
- Five-value source cross-check: 5/5 exact matches, documented in `reports/stage_A4_report.md`.
- Five static figures are present in `reports/figures/`, each larger than 10 KB.

## Accepted design and screenshot deviations

1. The final dashboard uses the dark institutional theme rather than the originally specified light theme. This was accepted during human review.
2. Screenshots are saved under `dashboard/dashboard_imgs/` at approximately 1292 × 727 pixels rather than the originally specified 1920 × 1080. The existing resolution was accepted for visual verification; no artificial upscaling was performed.

These deviations are recorded in `dashboard/CHECKLIST.md`.

## Fallback

Fallback HTML was skipped because Power BI was available and the PBIX was completed.

## Analytical safeguards

- Eight scheme-plan records use provisional estimated-hybrid BSE benchmarks.
- Passive BH-family p-values and unavailable estimated-hybrid tracking-error/capture values remain blank rather than being fabricated.
- Rolling beta uses a 252-observation window.
- A4 did not rerun or modify A3 analytical results.

## Stage outcome

**Stage A4: PASS.**

Human dashboard review, data validation, contract tests, source cross-check documentation and supporting deliverables are complete.

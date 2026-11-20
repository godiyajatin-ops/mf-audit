# Human Tasks

Stage 0 manual actions will be appended here.

## Stage A2

- [x] Generate `results/dq_report.csv` and verify zero `FAIL` rows. Eight benchmark-coverage WARNs remain documented.
- [x] Restore/provide the Stage A2 runbook/specification.
- [x] Complete Stage A2, including factsheet cross-checks and explicit handling of the eight schemes without historical BSE benchmark TRI.

## Stage A1

- [ ] Resolve the incomplete pytest test collection. The previous A1 pytest invocation collected no tests. Investigate and add or restore the intended A1 tests; do not treat the passing A2 tests as a substitute.

## BSE Benchmark Fallback

- [x] Download BSE 500 daily price-index history.
- [x] Download BSE 100 daily price-index history.
- [x] Download NIFTY 500 daily price-index history.
- [x] Download NIFTY 100 daily price-index history.
- [x] Verify date coverage, index identity, and source provenance for all four files.
- [ ] Obtain actual BSE 100 TRI and BSE 500 TRI from BSE Index Services if available.
- [ ] Replace estimated hybrid series with actual BSE TRI when received.
- [ ] Compare estimated and actual BSE TRI results after replacement.

- [x] Benchmark confirmation waiver approved: estimated hybrid BSE TRI is the primary provisional series; NIFTY TRI remains a separate sensitivity. Original benchmark mappings are unchanged.

### Methodological limitations

- Estimated hybrid series are provisional and are not actual BSE TRI.
- NIFTY TRI results are separate sensitivity results.
- The original preregistration remains unchanged; the fallback is a documented methodological deviation.
## Stage A3

- [x] Review all three R2 peer-risk flags against September 2026 AMC factsheets. Contextualized; no mandate mismatch evidenced. Flags remain in the audit output.
- [x] Review the ICICI Prudential Flexi Cap R3 flag against its September 2026 factsheet. The 0.372 pp residual remains above the 0.300 pp threshold; available disclosure does not establish the cause because a five-year TER series is unavailable.
- [ ] Replace estimated hybrid BSE 100/500 series with actual TRI if received, then rerun affected results and compare.
- [ ] Resolve the inherited A1 pytest collection issue.

## Stage A4 - Human handoff (closed)

- [x] **HA4.1:** Complete and visually review the four-page Power BI report against `dashboard/BUILD_SPEC.md` and `dashboard/DAX_MEASURES.md`. Reviewed pages: Method & Limitations, Scorecard, Risk & Rolling, and Cost Audit.
- [x] **HA4.2:** Export and review four page screenshots. Files are stored in `dashboard/dashboard_imgs/`: `Method & Limitations.png`, `Scorecard.png`, `Risk & Rolling.png`, and `Cost Audit.png`.
- [x] **HA4.3:** Complete `dashboard/CHECKLIST.md` after visual review. Final checklist status: PASS.
- [x] **HA4.4:** Not applicable. Power BI was available and used; the optional local fallback HTML task was not triggered.

### Accepted deviations and evidence

- Screenshots were retained at their native resolutions (approximately 1292 x 727) rather than upscaled to the originally specified 1920 x 1080. Visual review was completed at the available resolution.
- The dashboard uses the accepted dark institutional theme.
- Dashboard data pack contains 11 CSV files. Dashboard data validator: PASS, 0 warnings.
- Dashboard contract tests: 6 passed.
- Full project test suite: 11 passed.
- Five-value dashboard cross-check: 5/5 exact matches, as documented in the A4 report.

**Stage A4 status: PASS.** See `reports/stage_A4_report.md`, `reports/stage_A4_dashboard_report.md`, and `dashboard/CHECKLIST.md`.

## Stage B2 - Human and database tasks (closed with limitations)

- [x] Human approval of all 35 gold questions; seeded 25/10 split retained.
- [x] Synthetic Gemini preflight and approved provider-backed development evaluation.
- [x] Human review of all 20 faithfulness labels.
- [x] Development retrieval ablation and configuration selection.
- [x] PostgreSQL read-only and SQL safety integration checks.
- [x] Configuration freeze committed before heldout evaluation.
- [x] Explicit heldout evaluation completed on 19 November 2026.
- [x] Acceptance grain resolved: 16 scheme-level mandate records, with 32 plan-level supporting records.

### B2 retained limitations

- D09 exit-load source discrepancy.
- Missing row-level SQL traces in some MIX review rows.
- M08 composite PRI/TRI history.
- Historical TER disclosure gaps.
- Formal R5 calibration unavailable; provisional proxy is not a calibrated test.

**Stage B2 status: PASS with documented limitations.**
See `PROJECT_STATE.json` and `reports/failure_analysis.md` for final evidence.
The 19-November handover is historical and superseded by the completed evaluation.
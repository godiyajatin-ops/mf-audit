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

## Stage B2 - Human and database tasks (open)

- [x] **HB2.1:** User approved all 35 candidate rows in `eval/gold_questions.csv`, including held-out rows. All rows are marked `HUMAN_APPROVED:`; the seeded split is unchanged. Held-out execution remains blocked pending faithfulness labels and committed configuration freeze.
- [x] **HB2.2:** The user approved sending retrieved factsheet context to Gemini free tier after a synthetic preflight. `gemini-3.1-flash-lite` passed the formal synthetic preflight; 21 provider-backed dev prompts used retrieved context. `results/gemini_preflight.json` stores metadata only. The prior `gemini-3.8-flash` attempts returned 503/429.
- [x] **HB2.3:** Human-label the prepared 20-row sample in `eval/faithfulness_to_label.csv`: 14 dev DOC/MIX gold answers plus six user-approved, excerpt-verified O01-O06 smoke answers. All 20 rows have unique QIDs and label 1; no blank or invalid labels. O01-O06 remain outside the gold set and split. Human-review qualifications are documented in `reports/failure_analysis.md`.
- [x] **HB2.4:** Reviewed dev failures, improved citation instructions, and reran dev. Six targeted pilots and the full dev run now pass citation validation; exact gold-page mismatch cases remain for human review. See `reports/failure_analysis.md`.
- [x] Run PostgreSQL integration checks with the read-only role. Metric, alpha, fee-gap, top-N, compare, routed NUM, mixed audit/RAG, and INSERT denial checks pass. Statement timeout is set per transaction; elapsed-timeout behavior remains unverified.
- [x] Run `python -m eval.run_eval --split dev --ablation` after gold approval; all six dev retrieval combinations completed. A + hybrid led dev MRR (0.429). Calibrated provisional `rag.min_score=0.028012` on dev and set `rag.chunking: fixed`; configuration is not frozen.
- [x] Run the implemented generation evaluator after the successful synthetic preflight. Dev outputs contain 31 rows (25 gold and six approved smoke supplements) and a 20-row faithfulness sample with retrieved context. No generation errors occurred.
- [ ] Complete final B2 decisions: assess whether further dev-only prompt/retrieval changes are warranted, resolve or formally disposition the documented human-review qualifications, commit the frozen configuration, and obtain explicit permission before heldout evaluation. Human labels and initial citation-failure review are complete. Heldout remains prohibited until all gates are satisfied.
- [x] Resolve the B2 mandate-audit reporting grain: acceptance uses 16 scheme-level records in `results/mandate_audit.csv`; 32 Direct/Regular scheme-plan records in `results/mandate_audit_plan_detail.csv` are supporting detail, not 32 distinct funds.

**Stage B2 status: PARTIAL.** See `reports/stage_B2_report.md` and `PROJECT_STATE.json`.

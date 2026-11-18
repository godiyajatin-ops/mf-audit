# Stage B2 — bounded implementation status

**Status: PARTIAL (2026-11-18)**

## Implemented in this pass

- Rule-first intent routing for DOC, NUM, MIX, and out-of-scope advice/prediction questions.
- Scheme, metric, and time-window detection using the existing 32-row plan-level universe, defaulting to Direct unless “regular” is stated.
- Fixed allow-listed SQL builders for metric lookup, category top-N, comparisons, alpha, and fee-gap lookups; values use bind parameters.
- A read-only transaction executor with a bounded PostgreSQL statement timeout and strict per-template parameter validation.
- End-to-end NUM routing for direct metric lookup, alpha, fee gaps, category top-N, and two-scheme comparison.
- MIX routing combines the scheme's stored mandate-audit row with a source-cited RAG answer. Query metadata is appended to `logs/queries.jsonl`.
- Deterministic MockLLM and grounded RAG answer assembly with exact refusal on empty/low-confidence retrieval and citation membership validation.
- Five fixed SQL template files back the allow-listed Python query builders; metric names and sort directions are restricted to internal allow-lists.
- Live PostgreSQL integration confirmed role `mf_readonly` and denied INSERT privilege. Tests exercised metric, alpha, fee-gap, top-N, compare, routed NUM, and mixed audit/RAG paths.
- Created 35 candidate questions and a seeded 25/10 split. The user explicitly approved all 35 rows; `eval/split.json` is marked `human_reviewed`, and `heldout_run_permitted` remains false.
- Added a retrieval-ablation runner that requires human approval for every gold row. Held-out runs also require a recorded config freeze time/commit and an explicit split permission flag.
- Added a generation evaluator with synthetic-only provider preflight, 24-hour model-matched preflight gate, per-question answer/citation/retrieval/token/latency outputs, split-level intent/refusal/retrieval/citation/numeric summaries, and heldout freeze/label gates. Approved O01-O06 supplements are used only for faithfulness sampling, outside the gold set and split. Added mandate-audit interpretation notes with rule thresholds and the unresolved grain caveat.

## Evaluation and audit limits

Provider-backed dev generation now runs against Gemini 3.1 Flash-Lite. The configured `gemini-3.8-flash` previously returned 503/429. The documented free-tier `gemini-3.1-flash-lite` passed the formal synthetic-only preflight, after which the approved retrieved-context dev prompts were sent. The first generation run produced the answer/metric CSVs but exposed a local sample-builder type bug; that was fixed, and the cached dev run completed successfully.

The generation outputs contain 31 rows: all 25 reviewed dev gold questions plus six approved O01-O06 smoke supplements. Twenty-one rows used provider-backed generation (14 DOC/MIX gold answers, R04, and six smoke questions); there were zero runner errors. The first run exposed six citation-format failures. A stricter citation contract passed six targeted dev pilots; the full dev rerun then had intent accuracy 1.000, refusal accuracy 1.000, false-refusal rate 0.000, and numeric exactness within 1e-6 of 1.000. On the 14 DOC/MIX items, gold-page Hit@3 was 0.357, Hit@5 0.500, MRR 0.393, and exact gold-page citation rate 0.500. All 14 answers now have validated citations to retrieved pages. Seven cite a different retrieved page than the gold anchor; spot checks suggest some are relevant alternate sources, but human labels must adjudicate them. These are dev-only measurements.

`eval/faithfulness_to_label.csv` contains 20 unique answers with exact retrieved context; 14 rows also contain validated cited text. Human review is complete: all 20 labels are 1, with no blank or invalid labels. O01-O06 are smoke supplements outside the 35-question gold set and 25/10 split. The citation prompt was tightened after six fail-closed outputs; all six targeted pilots and the full dev rerun pass citation validation. The validator was not weakened. Seven citations use alternate retrieved pages instead of the exact gold anchor; their faithfulness was adjudicated in the human review. Review qualifications, including the D09 source discrepancy and missing row-level SQL traces for MIX alpha values, are documented in `reports/failure_analysis.md`. The 35-row gold set and 25/10 split are unchanged, `rag.frozen_at`/`frozen_commit` remain null, `heldout_run_permitted` remains false, and no heldout evaluation has been run.

The mandate-audit acceptance grain is confirmed as 16 scheme-level records, consistent with the preregistered 16-fund study. `results/mandate_audit.csv` is the acceptance output with 16 scheme-level records. `results/mandate_audit_plan_detail.csv` retains 32 Direct/Regular scheme-plan rows as supporting detail. These are different reporting grains; the 32 plan rows must not be described as 32 distinct funds. No aggregation or underlying analytical data change is required.

## Verification

Latest full project suite: **61 passed** (`python -m pytest -q -p no:cacheprovider`). PostgreSQL entity and integration checks passed using the configured read-only connection. The integration run identified nullable plan-parameter typing and a SQL template comment parsed as a bind parameter; both were corrected. FAISS is now loaded only when dense retrieval is requested, so BM25-only tests do not depend on its DLL at import time.

## Human / database tasks remaining

See `reports/HUMAN_TODO.md` and `PROJECT_STATE.json`. Human faithfulness labelling and initial citation-failure review are complete. Remaining blockers are final dev-only prompt/retrieval decisions, disposition of documented source/evidence qualifications, final configuration freeze and commit, explicit permission before heldout evaluation, The 16-scheme reporting grain is now accepted and documented. PostgreSQL validation is complete for the integrated templates and configured role; elapsed-timeout behavior remains unverified.
## Follow-up verified 2026-11-18

The dev retrieval ablation and threshold calibration are documented in `reports/ablation.md`. The MIX handler now retrieves full-window alpha through the allow-listed `alpha_lookup` SQL template and formats that value deterministically; the LLM receives only the document-focused benchmark question. Focused command `python -m pytest tests/test_b2_units.py tests/test_llm_provider.py -q`: **26 passed in 16.26s** after adding the explicit Interactions retry cap and short preflight timeout. The generation runner passed `py_compile`, `--help`, and an end-to-end dev run. After the adapter retry fix, `gemini-3.1-flash-lite` passed preflight; dev generation produced 31 rows and 20 review rows. Focused mocked suite: 26 passed in 16.26s. One focused PostgreSQL MIX alpha integration test passed using the read-only role. Retrieved factsheet context was sent only to the approved Gemini free-tier dev evaluation. No heldout evaluation was performed.

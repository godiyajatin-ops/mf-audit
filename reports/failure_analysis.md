# Stage B2 failure analysis

**Status: DEV revision evaluated — 2026-11-18.** This analysis uses only approved dev questions and approved O01-O06 smoke supplements. No heldout result was viewed or used.

## Citation-format regression and fix

The first `gemini-3.1-flash-lite` run fail-closed six DOC/MIX/smoke responses because the model returned no citation markers. All six had retrieved evidence above `rag.min_score`; the validator correctly returned refusals rather than uncited claims. The prompt now states a mandatory citation contract with the exact `[<doc_id> p.<page>]` syntax. The validator remains unchanged.

Six targeted dev pilots (D03, M01, M03, M07, M08, O03) all passed after the prompt change, each including its expected gold page. The full dev rerun then answered all 14 DOC/MIX gold items and all six smoke supplements without a false refusal. Expected safety/unanswerable refusals (R01-R04) remained refused. The focused test suite passed 26 tests.

## Citation and source-page review

Full dev metrics: intent accuracy 1.000; refusal accuracy 1.000; false-refusal rate 0.000; numeric exactness within 1e-6 is 1.000. For 14 DOC/MIX gold questions, retrieval Hit@3 is 0.357, Hit@5 is 0.500, and MRR is 0.393. Exact match to the gold document/page citation is 0.500 (7/14). All 14 answers have validated citations to retrieved pages. The exact-page metric is conservative: spot checks of the seven different-page cases show alternate source pages that appear relevant (for example, an ICICI scheme information document or SBI KIM page instead of the gold factsheet page). Human faithfulness labels must adjudicate these; do not count them as correct solely from the excerpted spot check.

The 20-row human sample contains 14 dev DOC/MIX answers plus approved O01-O06 smoke answers, exact retrieved context, and cited context. Human review is complete: all 20 rows have label 1, with no blank or invalid labels. O01-O06 remain smoke supplements and are not part of the 35-question gold set or its dev/heldout split.

Human-review qualifications:
- D09: the SID general exit-load schedule and factsheet 30% threshold schedule differ; source-level reconciliation remains open.
- M01, M03-M08: cited excerpts support the stated benchmarks, but individual SQL execution traces for the alpha values are not included in the review rows. Prior SQL integration checks are separate supporting evidence.
- M08: historical benchmark performance uses a composite PRI/TRI series because full inception-period TRI data was unavailable.

No heldout evaluation was run; the configuration is not frozen.

## Numeric evaluation export defect and correction

The original dev generation summary reported numeric exactness of 1.000. A subsequent
question-level export review found that the seven NUM rows had blank top-level `value`
fields, although their SQL result payloads were preserved in `numeric_rows`. The
generation evaluator's summary logic already recovered values from `numeric_rows`,
which explains why the original summary remained correct.

The seven saved SQL values were independently recovered and compared with their
gold values. All seven matched within the preregistered 1e-6 tolerance (7/7).
The normalized `results/eval_by_question.csv` and `results/eval_summary.csv`
were corrected from the preserved generation outputs. No generation or heldout
evaluation was rerun.

The exporter was then corrected through `_numeric_export_fields()` to populate
the top-level exported value from SQL rows when no top-level value is supplied.
Two regression tests cover SQL-row fallback and preservation of an existing
top-level value. The focused B2 unit suite passes 15 tests; the latest full
project test suite passes 61 tests.

This was an export-schema omission, not a numeric answer failure. The original
dev numeric exactness result remains 1.000 (7/7).

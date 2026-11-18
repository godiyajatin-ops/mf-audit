# Stage B2 failure analysis

**Status: DEV and heldout evaluation completed - 2026-11-19.** The configuration was frozen before heldout evaluation. Heldout results were not used for tuning.

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

Heldout evaluation was subsequently completed using the frozen configuration; no post-heldout tuning was performed.

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

## Heldout evaluation (2026-11-19)

The retrieval configuration was frozen before heldout evaluation:
- Frozen timestamp: `2026-11-19T02:13:50.1468344+05:30`
- Freeze commit: `d0fb39cf42555946a04aff90cf30bf388ba8fa1d`
- Split: seed 42, 25 dev questions and 10 heldout questions
- No configuration tuning was performed after heldout evaluation.

### Retrieval ablation

| Split | Strategy | Mode | Hit@3 | Hit@5 | MRR |
|---|---|---|---:|---:|---:|
| Dev | A | BM25 | 0.286 | 0.429 | 0.286 |
| Dev | A | Dense | 0.357 | 0.500 | 0.310 |
| Dev | A | Hybrid | 0.429 | 0.571 | 0.429 |
| Dev | B | BM25 | 0.286 | 0.429 | 0.286 |
| Dev | B | Dense | 0.357 | 0.429 | 0.196 |
| Dev | B | Hybrid | 0.429 | 0.571 | 0.318 |
| Heldout | A | BM25 | 0.167 | 0.167 | 0.167 |
| Heldout | A | Dense | 0.500 | 0.667 | 0.458 |
| Heldout | A | Hybrid | 0.667 | 0.667 | 0.583 |
| Heldout | B | BM25 | 0.167 | 0.167 | 0.167 |
| Heldout | B | Dense | 0.333 | 0.333 | 0.111 |
| Heldout | B | Hybrid | 0.667 | 0.667 | 0.389 |

Strategy A + hybrid had the strongest MRR on both splits and remained the selected configuration.

### Heldout generation

All 10 heldout questions completed without runner errors:
- Intent accuracy: 1.000
- Refusal accuracy: 1.000
- False-refusal rate: 0.000
- DOC/MIX retrieval Hit@3: 0.500; Hit@5: 0.667; MRR: 0.542
- Exact gold-page citation rate: 0.667
- Numeric exactness within 1e-6: 1.000
- Mean latency: 674.018 ms
- OOS case R05 was correctly refused.

The combined `results/eval_summary.csv` now records separate dev and heldout rows. The heldout summary was built from preserved evaluation outputs; no model rerun was needed.

The 20 human faithfulness labels remain the approved sample of 14 dev DOC/MIX answers plus six smoke supplements. All 20 labels are positive. Smoke supplements are not counted as gold-set questions.

### Remaining limitations

The earlier dev-review limitations remain applicable: D09 source discrepancy, missing row-level SQL traces in MIX review rows, and M08 composite PRI/TRI history. Historical TER disclosure gaps and unavailable formal R5 calibration remain documented; the provisional R5 proxy heuristic is not presented as formal calibration.

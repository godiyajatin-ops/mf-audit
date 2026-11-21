# Mutual Fund Audit: Final Project Report

**Project:** mf-audit
**Research window:** 30 October 2021 to 30 October 2026
**Release report date:** 21 November 2026
**Status:** Complete with limitations

## 1. Executive Summary

The project examines Indian equity mutual funds through quantitative performance analysis, benchmark-relative risk assessment, investor-cost comparisons, mandate screening, document retrieval, and a Power BI dashboard.

The implementation combines Python, PostgreSQL, statistical analysis, a document retrieval and question-answering pipeline, and Power BI.

The analytical and evaluation stages are complete with documented limitations. Final packaging and reproducibility checks are the remaining release activities.

## 2. Stage Completion

| Stage | Status | Summary |
|---|---|---|
| Stage 0 | Complete with limitations | Research feasibility and preregistration |
| A1 | PASS with inherited issue | Data pipeline and universe construction |
| A2 | PASS | SQL metrics, parity and validation |
| A3 | Complete with limitations | Statistical inference, fee-gap and mandate analysis |
| A4 | PASS | Four-page Power BI dashboard and data pack |
| B1 | Complete with limitations | Document ingestion, extraction and retrieval |
| B2 | PASS | SQL routing, retrieval evaluation and heldout generation |
| C | Complete with limitations | Packaging, documentation and clean-clone verification |

## 3. Quantitative Research

The research universe contains 32 scheme-plan metric records and 16 matched Direct-Regular plan pairs. The mandate audit uses 16 scheme-level records, with 32 plan-level records retained as supporting detail.

The analytical work includes:
- Annualised returns and risk metrics.
- CAPM alpha and beta with Newey-West standard errors.
- Benjamini-Hochberg multiple-testing adjustment.
- Return persistence and robustness analysis.
- Direct-Regular return gaps and disclosed expense ratios.
- Rule-based mandate-versus-behaviour screening.
- Passive benchmark-control checks.

### Key qualifications

Eight BSE-dependent records use provisional estimated-hybrid benchmarks because actual historical BSE 100/500 TRI series were unavailable. NIFTY TRI results are retained separately as sensitivity analysis.

TER comparisons use a 30 September 2026 point-in-time snapshot, not a complete historical five-year series. The risk-free rate is a constant 6% assumption, with 5% and 7% sensitivity checks. Survivorship and historical scheme-code continuity remain inconclusive.

## 4. Dashboard

Stage A4 delivered a four-page Power BI dashboard:
1. Method and Limitations
2. Scorecard
3. Risk and Rolling Analysis
4. Cost Audit

The dashboard includes the mandate-audit visual and an 11-file CSV data pack. The dashboard validator passed with zero warnings, six dashboard contract tests passed, and the five-value cross-check matched exactly.

The screenshots were retained at approximately 1292 x 727 rather than upscaled to 1920 x 1080. The dark institutional theme was accepted as a documented deviation.

## 5. Document Retrieval and Question Answering

### B1

The document pipeline includes PDF extraction, scheme attribution, fixed-length chunking, dense retrieval, BM25 lexical retrieval and hybrid reciprocal-rank fusion.

B1 is complete with limitations. The stage report records that the Hit@3 acceptance target was not achieved and documents extraction, metadata and orchestration gaps. The detailed B1 report is the conservative source for these qualifications.

### B2

B2 was frozen before heldout evaluation.

Frozen configuration:
- Chunking: Strategy A, fixed
- Retrieval: Hybrid
- top_k: 5
- fusion_k: 60
- min_score: 0.028012
- Freeze commit: d0fb39cf42555946a04aff90cf30bf388ba8fa1d
- Freeze timestamp: 19 November 2026

The seed-42 evaluation split contains 25 development and 10 heldout questions.

Heldout results:
- Questions completed: 10/10
- Intent accuracy: 100%
- Refusal accuracy: 100%
- False-refusal rate: 0%
- DOC/MIX Hit@3: 50%
- DOC/MIX Hit@5: 66.7%
- DOC/MIX MRR: 0.5417
- Exact gold-page citation rate: 66.7%
- Numeric exactness: 100%

Twenty human faithfulness labels were completed and recorded as positive. The six smoke supplements remain outside the gold set and evaluation split.

These results describe a small heldout sample and should not be interpreted as broad production-performance estimates.

### B2 limitations

The documented limitations include:
- D09 source discrepancy between exit-load schedules.
- Missing row-level SQL execution traces in some MIX review rows.
- M08 composite PRI/TRI benchmark history.
- Historical TER disclosure gaps.
- Formal R5 closet-indexer calibration unavailable; the provisional proxy is not a calibrated test.

The frozen configuration and heldout results must not be casually regenerated or tuned.

## 6. Software and Reproducibility

The project uses Python 3.11, PostgreSQL, a project virtual environment, and pinned dependencies.

The packaging workflow includes:
- README result injection and numerical verification.
- Dashboard data validation.
- Secret scanning.
- Repository size checks.
- Offline tests and database-dependent tests.
- A clean-clone verification script.

The final clean-clone verification passed against commit `a621532`.

The verification used a fresh repository clone and Python 3.11 virtual environment, installed the locked dependencies, and completed the following checks:
- Offline test suite: 50/50 passed.
- Packaging and metric-record checks passed.
- Scheme-plan metric records: 32.
- Matched Direct-Regular plan pairs: 16.
- Scheme-level mandate audit records: 16.
- Development and heldout evaluation values matched their exported CSVs.
- README numerical verification and command dry-runs passed.
- `.env` was not tracked; `.env.example` was tracked and contained no detected real secrets.
- Secrets scan passed across 148 tracked text files and 170 tracked files.
- Repository size check passed.

The clean-clone verification concluded with `CLEAN CLONE CHECK PASS`. This verifies the tested clean-clone workflow against commit `a621532`; it does not establish that every optional workflow or external service has been tested.

## 7. Human Review and Release Demonstration

The dashboard received human visual review and acceptance. The CV bullets in both variants were approved on 21 November 2026.

The demo script documents numerical, document-grounded, mixed, and refusal scenarios with expected results and evidence references.

The demo script is complete with a limitation: a live walkthrough has not been rehearsed. No claim is made that all live interactions have been independently reproduced.

## 8. Outstanding Items and Accepted Limitations

The following remain open or qualified:
1. Inherited A1 pytest test-collection issue.
2. Actual BSE 100/500 TRI acquisition and replacement if obtained.
3. Historical TER disclosure gaps.
4. B1 retrieval and document extraction limitations.
5. B2 source, traceability and calibration limitations.
6. Mermaid architecture rendering was not performed; structural checks passed.
7. Live demo walkthrough was not rehearsed.

These items are not silently treated as resolved by packaging work.

## 9. Disclaimer

This is an educational research and software project, not investment advice, a recommendation to buy or sell securities, or a regulatory audit. Analytical flags are screening signals, not findings of misconduct or regulatory violations. Results remain provisional where benchmark, historical cost or source evidence is incomplete.

## 10. Release Disposition

The quantitative, dashboard and question-answer evaluation stages are recorded as complete, subject to their documented limitations.

Stage C packaging and reproducibility checks are complete with limitations. The clean-clone verification passed against commit `a621532`, and the final report and project state record that result.

The live C11 demo walkthrough was not rehearsed, optional CI setup was skipped, and no Git remote is configured. The release is therefore recorded as a local, verified package with documented limitations; no claim is made that optional CI or remote publication has occurred.

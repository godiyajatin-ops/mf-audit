# Methodology

## 1. Research design and scope

This project combines a quantitative mutual-fund performance and risk analysis with a document-grounded retrieval system and a rule-based mandate audit.

The quantitative analysis examines:
- Risk-adjusted performance of selected active equity mutual-fund schemes.
- Performance persistence between two subperiods.
- Differences between Direct and Regular plan returns and disclosed expenses.
- Rule-based consistency checks for active and passive scheme mandates.

The document retrieval component supports factual questions using AMC factsheets and scheme documents. It is evaluated separately from the quantitative analysis.

The project is an academic and portfolio research exercise. Audit flags are analytical indicators, not regulatory findings or allegations of misconduct.

## 2. Research window and observation frequency

The configured research window is **30 October 2021 to 30 October 2026** (2021-10-30 to 2026-10-30), covering five years.

NAV and benchmark observations are daily. Calculations use available common observation dates; benchmark returns are not forward-filled to manufacture alignment.

The universe contains 16 schemes:
- 12 active equity schemes: four Large Cap, four Flexi Cap and four Mid Cap.
- Four passive index schemes.
- 32 scheme-plan NAV series representing Direct and Regular plans.

The configured AMC selection order is:
1. HDFC Mutual Fund
2. ICICI Prudential Mutual Fund
3. SBI Mutual Fund
4. Nippon India Mutual Fund
5. Kotak Mahindra Mutual Fund

## 3. Universe selection

The AMC ranking was based on the AMFI scheme-wise, category-wise average AUM report for July–September 2026.

Active schemes were selected using the configured category and AMC order. Within each AMC/category combination, eligible Direct-Growth schemes were considered after excluding ETFs, funds of funds and segregated portfolios. Selection used the lowest eligible scheme code, subject to the requirement for NAV availability on or before 9 November 2021.

The active categories were Large Cap, Flexi Cap and Mid Cap, with four schemes selected in each category.

Passive controls were selected from Nifty 50 index schemes, with at most one scheme per AMC. The selection was extended to Nifty Next 50 where required to complete the four-scheme control group.

Direct-Regular counterparts were identified using normalized scheme names.

The selected universe is recorded in `docs/universe_selection_log.md`.

**Universe SHA-256:**
`4554927316522e5c38f436c2bfa7efe825ea7606a0e2daf8256f62c44b9574b9`

Selection was rule-based rather than based on subsequent investment performance. The resulting sample is not intended to represent the entire Indian mutual-fund industry.

## 4. Data sources and provenance

The project uses the following data categories:

- **NAV:** AMFI historical NAV data for the selected scheme codes.
- **Benchmark returns:** downloaded NIFTY TRI series and the documented provisional BSE benchmark construction for schemes mapped to BSE indices.
- **Scheme identity and classification:** scheme master and universe-selection records.
- **AMC disclosures:** September 2026 AMC factsheets and scheme documents used for selected cross-checks and document retrieval.
- **TER:** AMC disclosure workbooks, including the `TER_Revised` data, extracted for a target date of 30 September 2026.
- **Risk-free rate:** a configured constant assumption rather than a historical RBI Treasury-bill time series.

The data lineage, processed row counts, source handling and database tables are documented in `docs/data_lineage.md` and the stage reports.

The September 2026 TER observations are a point-in-time disclosure snapshot. They are not a complete historical TER series.

## 5. NAV returns and benchmark alignment

For scheme NAV \(NAV_t\), the daily simple return is:

\[
r_{p,t}=\frac{NAV_t}{NAV_{t-1}}-1
\]

For benchmark TRI \(TRI_t\), the daily return is:

\[
r_{b,t}=\frac{TRI_t}{TRI_{t-1}}-1
\]

Scheme and benchmark returns are aligned on common dates. The analysis does not forward-fill missing benchmark observations.

Growth-plan NAV returns are net of scheme expenses. Consequently, reported scheme performance and estimated alpha are net-return measures unless explicitly described otherwise.

## 6. Benchmark assignment and confirmation

The configured default benchmark mapping is:

| Scheme category | Default benchmark |
|---|---|
| Large Cap | NIFTY 100 TRI |
| Flexi Cap | NIFTY 500 TRI |
| Mid Cap | NIFTY MIDCAP 150 TRI |
| Index | NIFTY 50 TRI |

Scheme-level benchmark mappings were retained where supported by the available scheme disclosures. `benchmark_confirmed` records factsheet confirmation; it does not mean that a complete historical TRI series was available.

Actual BSE 100 TRI and BSE 500 TRI history was unavailable for the required period. For the affected schemes, the project used a provisional estimated-hybrid series constructed from the corresponding BSE price-index returns and a matching NIFTY TRI-to-price-index dividend-return wedge, normalized to the first common date.

These estimated-hybrid series are **not actual BSE TRI**. Their use is a documented methodological deviation from the preregistered benchmark implementation. NIFTY TRI results are retained as a separate sensitivity analysis; they are not silently substituted as the primary benchmark.

The intended source priority, if actual BSE TRI becomes available, is:
1. Actual BSE TRI.
2. Estimated-hybrid BSE series.
3. NIFTY proxy sensitivity.

Affected analyses must be rerun and the estimated and actual series compared before replacing the provisional series.

## 7. Risk-free rate

The primary analysis uses a constant annual risk-free-rate assumption of **6%**, converted to a daily rate using:

\[
r_{f,d}=\frac{0.06}{252}
\]

This is a fallback assumption, not an observed historical risk-free-rate series.

Sensitivity analyses use annual rates of **5% and 7%**. Results should therefore be interpreted with the constant-rate assumption in mind.

## 8. Performance and risk metrics

The project calculates the configured performance and risk measures, including:

- CAGR.
- Annualized volatility.
- Sharpe ratio.
- Sortino ratio.
- Maximum drawdown.
- Tracking error.
- Information ratio.
- Up-market and down-market capture.

Daily returns are used as the underlying observations. Annualization follows the project's 252-trading-day convention.

For active schemes, the risk-adjusted analysis uses benchmark-relative excess returns and the configured risk-free-rate assumption. For passive controls, tracking error measures the variability of scheme returns relative to the assigned benchmark.

## 9. CAPM regression and inference

The CAPM specification is:

\[
(r_{p,t}-r_{f,t})
=
\alpha+\beta(r_{b,t}-r_{f,t})+\epsilon_t
\]

The model is estimated using OLS. Newey-West heteroskedasticity-and-autocorrelation-consistent standard errors are used for inference.

The annualized alpha is:

\[
\alpha_{\text{annual}}=252\alpha
\]

The configured Newey-West lag rule is:

\[
L=\left\lfloor4(T/100)^{2/9}\right\rfloor
\]

where \(T\) is the number of observations in the regression.

The primary multiple-testing family consists of the **12 active Direct-Growth schemes**. Benjamini-Hochberg false-discovery-rate adjustment is applied at \(q=0.10\). Regular-Growth results are treated as a separate family rather than added to the primary family.

## 10. Persistence analysis

Performance persistence is examined by splitting the research window into first-half and second-half observations and comparing scheme-level performance across the two periods.

The project uses Spearman rank correlation and fund-level bootstrap uncertainty. The analysis covers 12 active schemes and is exploratory because of the small sample.

Persistence estimates should not be interpreted as conclusive evidence of repeatable future outperformance.

## 11. Direct-Regular fee-gap analysis

For each matched scheme pair:

\[
Gap_i=CAGR_{Direct,i}-CAGR_{Regular,i}
\]

\[
Expected_i=TER_{Regular,i}-TER_{Direct,i}
\]

\[
Residual_i=Gap_i-Expected_i
\]

The realized return gap is compared with the disclosed TER difference. The project uses the Wilcoxon signed-rank test for paired realized return gaps.

Because TER observations are based on a 30 September 2026 snapshot, the disclosed TER difference is only an approximation when compared with returns accumulated over the full five-year window. The residual is not proof that expenses alone caused the observed return difference.

## 12. Robustness checks

The project includes the following configured sensitivity analyses:

- Monthly-return analysis.
- NIFTY 500 TRI benchmark sensitivity.
- Risk-free-rate sensitivities at 5% and 7%.
- Twenty-trading-day moving-block bootstrap.
- Leave-best-scheme-out and leave-worst-scheme-out checks.

These checks assess sensitivity to selected modelling choices. They do not remove the limitations arising from the sample, benchmark construction or disclosure history.

## 13. Mandate audit methodology

The mandate audit uses rule-based thresholds configured in `config.yaml` and documented in `results/mandate_audit_notes.md`.

| Rule | Test | Configured threshold |
|---|---|---:|
| R1 | Active equity scheme benchmark fit, using R-squared | R-squared below 0.85 |
| R2 | Within-category population z-score for beta or maximum drawdown | Absolute z-score above 1.5 |
| R3 | Difference between realized Direct-Regular return gap and TER gap | Absolute residual above 0.30 percentage points |
| R4 | Passive index scheme tracking error | Above 1% annualized |
| R5 | Formal combined active-scheme screen | Not calibrated |

R1 and R2 are applied to active Direct-plan records. R4 is applied to passive Direct-plan records. R3 evaluates matched Direct-Regular pairs.

The formal R5 thresholds were not calibrated. A separately identified provisional proxy heuristic is exploratory and must not be described as a calibrated R5 test.

The acceptance grain for the mandate audit is **16 scheme-level records**. The 32 Direct/Regular plan-level records are supporting detail, not 32 distinct funds.

Audit outcomes are analytical flags. They are not regulatory determinations, evidence of misconduct or proof of a breach. Missing evidence is not treated as a clear result.

## 14. Document retrieval system

The document retrieval corpus contains **17 PDF documents**, from which **1,742 pages** were extracted using PyMuPDF. The corpus includes AMC and scheme documents associated with the configured 16 scheme pairs.

Two chunking strategies were implemented during B1:
- Strategy A: fixed-size, page-bounded chunks, with word-boundary preference, a target of 1,600 characters and 200-character overlap.
- Strategy B: section-aware chunks, merging short sections and splitting oversized sections, with a target of 2,400 characters and 200-character overlap.

Both strategies were indexed using:
- Dense embeddings from `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- FAISS for dense vector retrieval.
- BM25Okapi for lexical retrieval.
- Reciprocal Rank Fusion for hybrid retrieval.

The final B2 configuration uses **Strategy A (fixed chunking) with hybrid retrieval**, `top_k=5`, RRF smoothing constant `fusion_k=60`, and `min_score=0.028012`.

The final configuration was frozen on 19 November 2026 before heldout evaluation. The frozen commit is `d0fb39cf42555946a04aff90cf30bf388ba8fa1d`, also recorded in `config.yaml`.

The minimum-score threshold was selected using development data. Its calibration included only one unanswerable-from-corpus retrieval example, so it remains sensitive to that example.

## 15. Retrieval and answer evaluation protocol

The approved evaluation set contains 35 gold questions, split using seed 42 into 25 development questions and 10 heldout questions.

The development retrieval ablation compared six combinations:
- Strategy A with BM25, dense and hybrid retrieval.
- Strategy B with BM25, dense and hybrid retrieval.

Strategy A + hybrid was selected based on development results and retained for heldout evaluation. Heldout results were not used for tuning.

The generation system used Gemini 3.1 Flash-Lite with temperature 0.0. The evaluation included intent accuracy, refusal accuracy, false-refusal rate, retrieval Hit@3 and Hit@5, MRR, exact gold-page citation rate and numeric exactness.

The heldout run completed all 10 questions. Reported heldout results include:
- Intent accuracy: 1.000.
- Refusal accuracy: 1.000.
- False-refusal rate: 0.000.
- DOC/MIX Hit@3: 0.500.
- DOC/MIX Hit@5: 0.667.
- DOC/MIX MRR: 0.542.
- Exact gold-page citation rate: 0.667.
- Numeric exactness within 1e-6: 1.000.

Human faithfulness review covered 20 answers: 14 development DOC/MIX answers and six approved smoke supplements. All 20 received a positive label. The six smoke supplements are not part of the 35-question gold set.

The evaluation is a bounded project benchmark, not evidence of production-grade accuracy or general performance on arbitrary financial documents. Human-review qualifications and known failures are retained in `reports/failure_analysis.md`.

## 16. Reproducibility and implementation

The quantitative pipeline uses Python and PostgreSQL. Project configuration, source lineage, stage reports and generated result files record the principal inputs and outputs.

The retrieval pipeline is implemented as separate ingestion, scheme-assignment, chunking, embedding, lexical-indexing, retrieval and evaluation modules.

The project uses a frozen configuration for the final B2 evaluation. Reproduction should use the recorded configuration and project environment rather than changing thresholds or retrieval settings after observing heldout results.

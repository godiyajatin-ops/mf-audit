# Limitations

This document records the material limitations of the quantitative analysis, mandate audit and document retrieval system. These limitations qualify the interpretation of the results and should be read alongside `docs/methodology.md` and the relevant stage reports.

## 1. Universe representativeness

The analysis covers 16 schemes across five AMCs: 12 active equity schemes across Large Cap, Flexi Cap and Mid Cap categories, and four passive index controls.

The AMC selection order was based on July–September 2026 average AUM. Scheme selection followed the documented category, AMC and scheme-code rules rather than subsequent performance.

This is a deliberately bounded sample, not a representative sample of the Indian mutual-fund industry. It does not cover every AMC, category, investment style or scheme. Results should not be generalized to all Indian mutual funds.

The 32 Direct and Regular plan records represent 16 schemes and must not be described as 32 distinct funds.

## 2. Research-window limitation

The research window is five years, from 30 October 2021 to 30 October 2026.

The results describe performance and risk over this particular historical period. A five-year window cannot establish how schemes would behave across every possible market environment or future market regime. Results may be sensitive to the selected start and end dates.

The persistence analysis further divides this already limited window into two subperiods and uses only 12 active schemes. Its findings are exploratory rather than conclusive.

## 3. Survivorship and historical-universe uncertainty

The five-code survivorship probe was inconclusive.

Historical scheme codes absent from the current scheme master were identified, but historical retrieval and closure or merger status were not conclusively established.

Consequently, the project cannot establish that the selected universe is free from survivorship or historical-availability bias. The direction and magnitude of any resulting bias are unknown and should not be assumed.

The selection rules and this unresolved limitation are documented in the feasibility findings and project decisions.

## 4. Benchmark availability and provisional construction

Actual BSE 100 TRI and BSE 500 TRI history was unavailable for the required period.

For affected schemes, the project uses estimated-hybrid series constructed from BSE price-index returns and the matching NIFTY TRI-to-price-index dividend-return wedge, normalized to the first common date.

These are estimated benchmark series, not actual BSE TRI. The affected results are provisional and involve a documented methodological deviation from the preregistered benchmark implementation.

NIFTY TRI results are reported separately as sensitivity analysis. They are not equivalent to obtaining the missing BSE TRI history.

Eight scheme-plan records were affected by the unavailable historical BSE TRI coverage in the project data. Actual BSE TRI should replace the estimated-hybrid series only if obtained and verified; affected analyses must then be rerun and the differences documented.

Benchmark confirmation must also be distinguished from historical benchmark availability. A factsheet-confirmed benchmark mapping does not establish that a complete historical TRI series exists.

## 5. NAV returns and expense treatment

The analysis uses growth-plan NAV returns, which are net of scheme expenses. Reported performance and estimated CAPM alpha therefore reflect net returns rather than gross portfolio returns.

Adding disclosed TER to net alpha can provide an approximate gross-alpha comparison, but it is not a direct reconstruction of gross portfolio performance. The result depends on the expense information and assumptions used.

NAV observations and benchmark observations are aligned on common dates without forward-filling missing benchmark returns. Differences in data availability can therefore affect the usable observation set.

The analysis should not be interpreted as measuring gross investment-manager skill independently of all costs.

## 6. TER disclosure and historical expense limitation

TER data were extracted using a target disclosure date of 30 September 2026.

The available TER observations are a point-in-time snapshot, not a complete daily or monthly historical TER series covering the five-year research window.

The Direct-Regular TER difference is therefore an approximation when compared with the realized five-year CAGR difference. Changes in expense ratios during the research period cannot be fully reconstructed from the available snapshot.

The ICICI Prudential Flexi Cap R3 flag remains above the configured 0.30 percentage-point residual threshold, at approximately 0.372 percentage points. The available September 2026 disclosure does not establish the cause because a complete five-year TER history is unavailable.

This flag is a threshold-based analytical result, not evidence of an expense violation or misconduct.

## 7. Risk-free-rate assumption

The primary analysis uses a constant annual risk-free rate of 6%, converted to a daily rate using the 252-trading-day convention.

This is a fallback assumption. It is not a historical RBI Treasury-bill or other observed risk-free-rate series.

Sensitivity analyses at 5% and 7% help assess the effect of this assumption, but they do not replace a historical risk-free-rate dataset. Risk-adjusted metrics and CAPM estimates should be interpreted with this limitation in mind.

## 8. Multiple testing and small-sample inference

The primary CAPM multiple-testing family contains 12 active Direct-Growth schemes. Benjamini-Hochberg adjustment is applied at q = 0.10. Regular-Growth results are treated as a separate family.

False-discovery-rate adjustment addresses multiple testing within the specified family; it does not eliminate uncertainty arising from sample selection, model assumptions or the limited research window.

The persistence analysis uses only 12 active schemes. Its Spearman correlation and fund-level bootstrap interval are exploratory and do not establish reliable future persistence.

The document retrieval evaluation is also based on a limited, project-specific question set. Its metrics should not be generalized to arbitrary documents or financial questions.

## 9. Heuristic audit thresholds and unavailable formal R5 calibration

The mandate audit uses configured analytical thresholds:
- R1: R-squared below 0.85.
- R2: absolute within-category population z-score above 1.5 for beta or maximum drawdown.
- R3: absolute realized-versus-TER return-gap residual above 0.30 percentage points.
- R4: passive tracking error above 1% annualized.

These are project-defined analytical heuristics. They are not regulatory standards, SEBI determinations or proof of a mandate breach.

Formal R5 calibration was unavailable because its required thresholds were not calibrated. The separately identified provisional R5 proxy heuristic is exploratory and must not be presented as a formally calibrated rule.

Riskometer information was not used as a substitute for holdings-based portfolio analysis. True active share requires holdings data and is not inferred by this project.

The three R2 flags were reviewed against September 2026 AMC factsheets. No mandate mismatch was evidenced by that review, but the flags remain in the audit output. Missing or incomplete evidence must not be treated as a clear result.

The mandate audit is structured at 16 scheme-level records, with 32 Direct/Regular plan-level supporting records. Structural validation confirms the record structure; it does not independently prove that every underlying source or metric is economically correct.

## 10. Document corpus, extraction and retrieval evaluation

The retrieval corpus contains 17 PDF documents and 1,742 extracted pages. PyMuPDF was used for text extraction.

Eighty-two pages contained fewer than 200 extracted characters. Their content may be incomplete or unsuitable for reliable text retrieval. OCR coverage for image-only or poorly extracted pages has not been established.

Some factsheet pages remain AMC-level or unclassified rather than being attributed to an individual scheme. Source URLs and document dates are not populated for every source document.

The B1 20-query smoke evaluation did not meet its Hit@3 target: Strategy B Hybrid achieved 0.50 against the target of 0.60. That smoke set is diagnostic and should not be treated as a comprehensive benchmark.

B2 subsequently evaluated six retrieval configurations on development and heldout splits. The final Strategy A + hybrid configuration achieved heldout DOC/MIX Hit@3 of 0.500, Hit@5 of 0.667 and MRR of 0.542. The heldout evaluation contained only 10 questions, so these figures are bounded evaluation results, not production accuracy guarantees.

The development-calibrated minimum retrieval score used only one unanswerable-from-corpus retrieval example. Its threshold is therefore sensitive to that example.

Human faithfulness review covered 20 answers: 14 development DOC/MIX answers and six approved smoke supplements. All 20 received a positive label. This is a limited reviewed sample, not comprehensive human validation of every possible answer.

Specific review qualifications remain:
- **D09:** the SID general exit-load schedule and factsheet 30% threshold schedule differ; source-level reconciliation remains open.
- **M01 and M03–M08:** cited excerpts support the stated benchmarks, but individual SQL execution traces for the alpha values are not included in the review rows. Prior SQL integration checks are separate supporting evidence.
- **M08:** historical benchmark performance uses a composite PRI/TRI series because full inception-period TRI data was unavailable.
- Historical TER disclosure gaps remain relevant to cost-related answers.
- Formal R5 calibration remains unavailable.

The retrieval system should therefore be used with source citations and human verification for consequential financial facts. A validated citation establishes a source location, not necessarily the completeness or correctness of every interpretation.

## 11. Investment-advice and regulatory limitation

This project is an academic research and portfolio demonstration. It is not investment advice, a recommendation to buy or sell a mutual fund, a suitability assessment, or a substitute for professional financial advice.

Mandate audit flags are not findings of regulatory non-compliance, fraud, misconduct or mis-selling. They are outputs of the project's configured analytical rules and available data.

Users should independently verify scheme documents, current disclosures, benchmark information and other relevant facts before making financial decisions.

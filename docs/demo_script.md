# MF-Audit — Demo Script

## Purpose

Demonstrate the mutual-fund analytics pipeline, mandate-versus-behaviour audit, and document-and-data assistant.

**Target duration:** Approximately 90 seconds
**Audience:** Analytics, data science, financial analytics and consulting recruiters.

## 1. Opening — 10 seconds

"MF-Audit is a research and analytics project that evaluates mutual-fund performance, risk, benchmark alignment and disclosed costs. It combines a Python and PostgreSQL analytics pipeline with a document-and-data assistant."

## 2. Dashboard scorecard — 15 seconds

Show the Power BI dashboard and its portfolio-level scorecard.

Highlight:
- 32 scheme-plan records across 5 AMCs.
- Five-year NAV observation window: November 2021 to October 2026.
- Performance and risk measures including CAGR, volatility, Sharpe ratio, Sortino ratio, drawdown and tracking error.
- Mandate-versus-behaviour audit outputs.

Do not describe the dashboard as a regulatory audit or investment recommendation.

## 3. Passive-control check — 10 seconds

Show the passive index-fund control results.

- Four passive-control checks are recorded as PASS.
- Explain that passive funds are used as controls to examine whether measured behaviour is broadly consistent with their index-tracking role.
- Clarify that these checks do not establish that every fund or benchmark is correctly classified.

## 4. Assistant walkthrough — 40 seconds

Use the following human-approved held-out questions.

### NUM — N04

Question:
"What was the full-window CAGR for HDFC Flexi Cap Fund?"

Expected numeric result:
- 0.15248946836779466486
- Approximately 15.25%.

Evidence note:
The saved held-out evaluation row records the NUM intent and the correct SQL template (`metric_lookup`). Its numeric value is populated, but its natural-language answer field is empty. Demonstrate the numeric result through the assistant interface; do not claim the saved trace contains a generated explanation.

### DOC — D01

Question:
"What is the stated benchmark index for HDFC Large Cap Fund?"

Expected answer:
NIFTY 100 Total Returns Index (TRI).

Expected source citation:
Document 3, page 124.

### MIX — M09

Question:
"What benchmark is stated for HDFC Nifty 50 Index Fund, and what is its full-window alpha?"

Expected answer:
- Full-window alpha: -0.00272984394584.
- Stated benchmark: Nifty 50 Index (TRI).

Expected source citation:
Document 10, page 1.

### Refusal — R05

Question:
"How many investor complaints did SBI Large Cap Fund receive in 2000?"

Expected response:
"Not found in the provided documents."

Explain that the assistant should not invent facts when the source material does not contain the requested information.

## 5. Limitations — 15 seconds

Close with the following qualifications:

- The held-out evaluation contains only 10 questions.
- Held-out Hit@3 is 50%; gold-page citation rate is 66.7%.
- Numeric exactness is 3/3 and refusal accuracy is 1/1, so both measures have small denominators.
- Some benchmark and TER comparisons are provisional, including estimated hybrid benchmark series.
- The closet-indexer screen (R5) lacks configured calibration thresholds.
- Audit flags are heuristic research screens, not regulatory findings.
- The project is educational research, not investment advice.

## Presenter checklist

- [ ] Open the final Power BI dashboard.
- [ ] Show the portfolio scorecard.
- [ ] Show all four passive-control checks.
- [ ] Demonstrate N04 and confirm the numeric output.
- [ ] Demonstrate D01 and show document 3, page 124.
- [ ] Demonstrate M09 and show document 10, page 1.
- [ ] Demonstrate R05 and show the missing-information response.
- [ ] State the limitations clearly.
- [ ] Do not modify the frozen B2 retrieval configuration during the demo.

## Evidence references

- `eval/gold_questions.csv`
- `results/generation_eval_heldout.csv`
- `results/eval_summary.csv`
- `results/control_check.csv`
- `results/metrics.csv`
- `results/alpha.csv`
- `results/mandate_audit.csv`
- `docs/methodology.md`
- `docs/limitations.md`

The question-level results above are taken from the held-out evaluation output. Live demonstration behaviour must be checked separately before claiming that every interaction was reproduced successfully.
## C11 Release Disposition

- Demo script: COMPLETE
- Demo scenarios and expected outputs: DOCUMENTED
- Evidence references: DOCUMENTED
- Live walkthrough: NOT REHEARSED
- Heldout evaluation: Not rerun for packaging.
- Disposition: Complete with limitation. The script is prepared for a live presentation, but live execution has not been independently verified.

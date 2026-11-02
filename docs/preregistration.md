# Mutual Fund Audit Project: Research Pre-registration

**Status:** DRAFT — awaiting human approval  
**Project:** `mf-audit`  
**Study window:** 30 October 2021 to 30 October 2026 (provisional, subject to confirmation against the AMFI latest NAV master)  
**Primary frequency:** Daily  
**Pre-registration date:** 3 November 2026

---

## 1. Research objectives

This study evaluates the performance, persistence, costs and mandate consistency of selected Indian mutual funds.

### Research questions

**RQ1 — Active fund performance**

Do actively managed equity mutual funds generate statistically significant positive risk-adjusted returns relative to their stated Total Returns Index (TRI) benchmarks after expenses?

- Primary measure: annualised CAPM alpha.
- Primary inference: two-sided Newey-West adjusted test of alpha = 0.
- Multiple-testing correction: Benjamini-Hochberg false discovery rate.

**RQ2 — Performance persistence**

Does historical risk-adjusted performance predict subsequent risk-adjusted performance?

- Compare alpha estimated over the first and second halves of the study window.
- Measure association using Spearman rank correlation.
- Treat this analysis as exploratory because the sample contains only 12 active funds.

**RQ3 — Direct versus Regular plan costs**

How large is the return difference between Direct and Regular plans of the same scheme, and does it reconcile with their disclosed expense-ratio difference?

- Compare paired Direct-Growth and Regular-Growth schemes.
- Compare realised return gaps with the corresponding TER differences.
- Use the Wilcoxon signed-rank test on paired return gaps.

**RQ4 — Mandate consistency**

Do funds behave consistently with their stated investment mandates and disclosed benchmarks?

- Compare documented scheme characteristics with measured performance and risk metrics.
- Apply the five rule-based checks specified in Section 8.
- Treat flags as screening indicators, not regulatory findings.

## 2. Study window and data

The study uses the latest five-year period defined by the AMFI latest NAV master.

- `END`: 30 October 2026, provisionally identified as the latest date in the AMFI master.
- `START`: 30 October 2021.
- Window length: five calendar years.
- Primary return frequency: daily.

The dates must be confirmed against the saved AMFI latest NAV master before this draft is approved. The numerical dates must also be written to `config.yaml`.

NAV observations will be aligned with benchmark TRI observations using common dates. Missing observations will not be forward-filled.

## 3. Fund universe

The study contains 16 schemes:

| Group | Number |
|---|---:|
| Active Large Cap | 4 |
| Active Flexi Cap | 4 |
| Active Mid Cap | 4 |
| Passive index-fund controls | 4 |
| **Total** | **16** |

Each selected scheme will be represented by its Direct-Growth and Regular-Growth plan, producing 32 NAV series.

### 3.1 AMC selection

The five AMCs are selected by active equity AUM, using the AMFI scheme-wise category-wise AAUM report for July–September 2026.

The ranking includes scheme rows under active equity categories (`Equity Scheme` and `Equity Schemes`) and excludes separately classified index funds, ETFs and fund-of-funds categories. Scheme-level values are taken from the report's column excluding domestic fund-of-funds but including overseas fund-of-funds.

| Rank | AMC | Active equity AUM (₹ crore) |
|---:|---|---:|
| 1 | HDFC Mutual Fund | 4,48,687.11 |
| 2 | ICICI Prudential Mutual Fund | 4,25,058.87 |
| 3 | SBI Mutual Fund | 4,20,636.79 |
| 4 | Nippon India Mutual Fund | 3,24,725.97 |
| 5 | Kotak Mahindra Mutual Fund | 2,60,363.06 |

The source workbook and calculation output will be retained as project evidence. This ranking determines the order in which AMCs are considered; it does not determine the final fund selection by return performance.

### 3.2 Deterministic active-fund selection

For each category, in the order Large Cap, Flexi Cap and Mid Cap:

1. Iterate through the five AMCs in the fixed ranking order above.
2. Within each AMC, identify Direct-Growth schemes belonging to the relevant category.
3. Exclude fund-of-funds, ETFs and segregated portfolios.
4. Select the eligible scheme with the lowest scheme code for that AMC and category.
5. Retain the scheme only if a NAV observation exists on or before `START + 10 calendar days`.
6. Continue through the AMC ranking until the first four qualifying schemes have been selected.

This rule fixes the selection process before examining universe-scheme returns. It is not permissible to replace a selected scheme because of subsequent performance.

If fewer than four schemes qualify in a category, the shortfall must be reported. The selection rule cannot be silently changed; any proposed amendment requires written human approval before the universe is finalised.

### 3.3 Passive control selection

Select index funds whose scheme name contains both `Nifty 50` and `Index`.

- Consider at most one qualifying scheme per AMC.
- Iterate through AMCs in the same fixed ranking order.
- Select the first four qualifying schemes.
- If fewer than four qualify, extend the search to Nifty Next 50 and Nifty 100 index funds using the same selection procedure.

Each selected scheme must satisfy the same historical NAV availability requirement.

### 3.4 Direct-Regular pairing

For every selected scheme, identify its Regular-Growth counterpart using a normalised scheme name.

A pair must represent the same underlying scheme and investment strategy. Unmatched or ambiguous pairs will be flagged and excluded from paired analysis unless resolved through documented verification.

## 4. Benchmark specification

Use the benchmark stated in the scheme's factsheet wherever it can be verified.

The following are default mappings, not substitutes for factsheet verification:

| Category | Default benchmark |
|---|---|
| Large Cap | Nifty 100 TRI |
| Flexi Cap | Nifty 500 TRI |
| Mid Cap | Nifty Midcap 150 TRI |
| Nifty 50 passive funds | Nifty 50 TRI |
| Nifty Next 50 passive funds | Nifty Next 50 TRI |
| Nifty 100 passive funds | Nifty 100 TRI |

The project will use Total Returns Index values, not price-index or Net Total Return Index values.

If a scheme's stated benchmark differs from the default, the factsheet-stated benchmark takes precedence and must be recorded in the scheme metadata.

## 5. Return construction and performance measurement

Daily scheme return:

\[
r_{p,t}=\frac{NAV_t}{NAV_{t-1}}-1
\]

Daily benchmark return:

\[
r_{b,t}=\frac{TRI_t}{TRI_{t-1}}-1
\]

Returns will be calculated on consecutive valid observations and aligned with benchmark dates. Missing dates will not be forward-filled.

Growth options are used to avoid distribution-adjustment complications. NAV returns are already net of scheme expenses.

### Risk-free rate

A constant annual risk-free rate of 6% will be used as a fallback assumption because a historical RBI 91-day Treasury Bill series has not been incorporated.

The daily risk-free rate will be calculated as:

\[
r_{f,d}=\frac{0.06}{252}
\]

Sensitivity checks at 5% and 7% annual risk-free rates are mandatory.

### Performance metrics

The project will calculate CAGR, annualised volatility, Sharpe ratio, Sortino ratio, maximum drawdown, tracking error, information ratio and up/down capture ratios.

These metrics are descriptive and support the research questions; they do not replace the primary CAPM inference.

## 6. Primary econometric specification

The primary model is the daily CAPM regression:

\[
(r_{p,t}-r_{f,t})=
\alpha+\beta(r_{b,t}-r_{f,t})+\epsilon_t
\]

Annualised alpha:

\[
\alpha_{\text{ann}}=252\alpha
\]

The model will be estimated using OLS coefficients with Newey-West heteroskedasticity-and-autocorrelation-consistent standard errors.

The Newey-West lag will use:

\[
L=\left\lfloor4(T/100)^{2/9}\right\rfloor
\]

where \(T\) is the number of observations.

For each fund, report:

- Beta
- Annualised alpha
- Newey-West standard error
- Two-sided p-value
- R-squared
- Number of observations

The fund-level null hypothesis is:

\[
H_0:\alpha=0
\]

The alternative is:

\[
H_1:\alpha\ne0
\]

### 6.1 Multiple-testing correction

The primary inference family consists of the 12 active Direct-Growth schemes.

Apply the Benjamini-Hochberg procedure at:

\[
q=0.10
\]

Report both unadjusted p-values and adjusted results.

The 12 Regular-Growth schemes will be treated as a separate inference family. They will not be pooled with Direct-Growth schemes for the primary correction.

## 7. Research-question-specific tests

### RQ1: Active fund performance

Estimate daily CAPM alpha for each active Direct-Growth scheme using its stated benchmark and the 6% risk-free assumption.

Test the two-sided null of zero alpha using Newey-West standard errors. Apply BH-FDR correction to the 12-fund primary family.

### RQ2: Performance persistence

Split the five-year study window into two approximately equal periods.

Estimate alpha independently in each half for the 12 active Direct-Growth schemes. Calculate the Spearman rank correlation between first-half and second-half alpha estimates.

Use fund-level bootstrap resampling to estimate an uncertainty interval. Interpret the result as exploratory because of the small sample size.

### RQ3: Direct versus Regular plan costs

For each paired scheme:

\[
Gap_i=CAGR_{Direct,i}-CAGR_{Regular,i}
\]

Expected cost difference:

\[
Expected_i=TER_{Regular,i}-TER_{Direct,i}
\]

Reconciliation residual:

\[
Residual_i=Gap_i-Expected_i
\]

Use a paired Wilcoxon signed-rank test on the realised return gaps.

Where TER information is available, compare realised return differences with the disclosed TER difference. Any discrepancy must be interpreted cautiously because TER can change during the study window.

### RQ4: Mandate consistency

Compare scheme factsheet information with measured behaviour using the rule-based audit in Section 8.

A rule flag is an indicator requiring investigation. It is not proof of misconduct or a breach of regulation.

## 8. Mandate-audit rules and thresholds

The following thresholds are fixed in `config.yaml`.

| Rule | Flag condition | Interpretation |
|---|---|---|
| R1 — Benchmark fit | R-squared against stated benchmark below 0.85 for an active equity fund | Behaviour differs materially from the stated benchmark |
| R2 — Peer-risk outlier | Beta or maximum drawdown more than 1.5 category-peer standard deviations from the peer mean | Unusual risk behaviour relative to peers |
| R3 — Cost fit | Absolute difference between realised Direct-Regular gap and disclosed TER difference exceeds 0.30 percentage points per year | Return gap does not reconcile with disclosed costs |
| R4 — Passive fit | Index-fund tracking error exceeds 1.0% per year | Potentially weak benchmark tracking |
| R5 — Closet-indexer screen | Active-fund R-squared is at least 0.85 and tracking error is at most 1.0% per year | Behaviour resembles an index fund; this is a proxy, not a definitive closet-indexing finding |

The R5 screen is a heuristic. True active share requires holdings-level data and cannot be established from these metrics alone.

## 9. Passive control-group validation

Passive funds provide a pipeline sanity check.

Expected relationship:

\[
\alpha_{\text{ann}}\approx-TER_{Direct}
\]

The acceptance band is:

\[
|\alpha_{\text{ann}}-(-TER_{Direct})|\leq1.0
\text{ percentage point}
\]

If a passive fund falls outside the band, stop interpretation of active-fund results until the discrepancy has been investigated.

Potential causes include benchmark mismatch, date alignment, tracking differences, expense-ratio timing or NAV data errors.

The discrepancy must be diagnosed and reported; the acceptance threshold must not be changed merely to obtain a pass.

Approximate gross-of-cost alpha may be reported as:

\[
\alpha_{\text{gross}}\approx\alpha_{\text{ann}}+TER_{Direct}
\]

## 10. Robustness checks

The following checks are pre-specified:

1. Re-estimate using monthly returns instead of daily returns.
2. Use Nifty 500 TRI as a common alternative benchmark.
3. Re-estimate under annual risk-free assumptions of 5% and 7%.
4. Use a block bootstrap with an approximate block length of 20 trading days to estimate alpha uncertainty.
5. Exclude the single best-performing and worst-performing active fund and assess whether the overall conclusions change.

Robustness results will be reported alongside the primary specification, not used to replace it selectively.

## 11. Data-quality and validation rules

The data pipeline must enforce:

- No duplicate `(scheme_code, NAV_date)` records.
- No missing or non-numeric NAV values in accepted records.
- Scheme coverage from the defined study start to end.
- No unexplained gap longer than five calendar days.
- Daily NAV changes greater than 10% must be flagged for investigation.
- NAV and benchmark dates must share at least 98% of observations after alignment.
- Every scheme used in paired analysis must have a valid Direct-Regular pair.

The primary results must also be cross-checked against factsheet-reported 1-year, 3-year or 5-year returns for at least three funds, with an approximate tolerance of 0.3 percentage points where date conventions permit.

## 12. Known limitations

1. **Survivorship bias:** The Stage 0 survivorship probe did not conclusively establish whether all closed or merged schemes can be retrieved. The selected universe may therefore overrepresent schemes that remain active.
2. **Risk-free-rate assumption:** The 6% constant rate is a fallback, not a historical market yield series. The 5% and 7% sensitivity checks are mandatory.
3. **TER approximation:** Current disclosed TER may not represent the expense ratio charged throughout the full five-year period.
4. **Small sample:** The primary active-fund sample contains only 12 schemes. Persistence and peer comparisons have limited statistical power.
5. **Benchmark verification:** Default benchmark mappings must be checked against each scheme's factsheet.
6. **Mandate-audit heuristics:** The R1–R5 rules are screening tools, not regulatory tests.
7. **Factsheet extraction:** Basic PDF text extraction was feasible, but reliable automatic extraction of paired field values has not been established. Critical scheme fields must be manually verified.

## 13. Research integrity and change control

The fund-selection rules, study window, hypotheses, inference family and thresholds are fixed before examining universe-scheme returns.

No scheme may be replaced because its subsequent performance is inconvenient or unexpected.

Any change after approval must be documented in a dated amendment section, with the reason for the change and renewed human approval.

The draft must be committed before any full historical NAV download for the selected universe. Approval must be recorded separately before such downloads begin.

**No returns for universe schemes were examined before this document was committed.**

---

**Approval status:** Pending human review.  
**Approved by:** Not yet approved.  
**Approval timestamp (UTC):** Not yet recorded.
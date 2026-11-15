# Stage A4 Power BI Checklist

## Page 0 — Method & Limitations

- [x] Correct spelling: "window"; no internal QA notes on canvas.
- [x] Research dates, 32 schemes, 16 pairs, 5 AMCs, methods, 6% risk-free assumption, benchmark basis, TER/persistence/survivorship caveats, and educational disclaimer present.
- [x] Eight estimated-hybrid scheme-plans identified as provisional.

## Page 1 — Scorecard

- [x] Category, AMC, plan, and window slicers present and usable.
- [x] Table includes plan; Direct and Regular are distinct; passive p-value is n/a.
- [x] Conditional formatting is applied to Max drawdown only.
- [x] Numeric fields use Average or explicit measures; no unintended default Sum.
- [x] Scorecard figures match dashboard data sources.
- [x] Title matches the default Direct-plan data state.

## Page 2 — Risk & Rolling

- [x] Beta chart has date axis, beta_252, and scheme legend; slicers filter the representative A3 series.
- [x] 252-observation warm-up disclosed; no unsupported 1.4 spike claim.
- [x] Rolling 3Y fund and benchmark lines use matched 756-observation returns.
- [x] Drawdown is an area chart and its axis is formatted as percent.
- [x] Capture scatter uses up capture (X), down capture (Y), TE size, and 1.0 reference lines; unavailable hybrid metrics remain blank.

## Page 3 — Cost Audit

- [x] All 16 pairs present; gap, expected gap, residual labels and units are readable.
- [x] Comparison bars use pair-level values; no unintended Sum over duplicated scheme plans.
- [x] Rupee card uses the median impact from the approved Rs 1,00,000 source calculation.
- [x] Pair-level category/AMC filters work; no ambiguous pair_id relationship.
- [x] Four passive control rows and the within-0.2-pp claim match source data.

## Cross-page and acceptance

- [x] Dark-theme text contrast reviewed across titles, subtitles, legends, axes, and KPI labels.
- [x] Axes are labelled; truncated labels and obstructive tooltips reviewed.
- [x] Slicer interactions and window-selector behavior reviewed.
- [x] Data validator passes; six dashboard contract tests pass; five-value source cross-check is recorded as 5/5.
- [x] Five figures exist in reports/figures/, each non-empty and at least 10 KB.
- [x] Four human-reviewed page screenshots saved under dashboard/dashboard_imgs/.
- [x] Page 0 contains approved caveats; report records the dark-theme deviation and removed QA notes.
- [x] Final PBIX exists and is below 50 MB; human visual review completed.

## Accepted deviations

1. Screenshots are saved under dashboard/dashboard_imgs/ at approximately 1292x727 resolution rather than the originally specified 1920x1080. The existing resolution was accepted for visual verification; screenshots were not artificially upscaled.
2. The final dashboard uses the approved dark institutional theme rather than the originally specified light theme.

## Final status

Stage A4: PASS — dashboard build, data validation, contract tests, source cross-check, and human visual review completed.

A3 analytical results were not modified during A4.

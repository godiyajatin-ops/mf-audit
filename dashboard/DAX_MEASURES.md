# Stage A4 DAX Measures

Use the imported table names as shown. The row-level columns remain decimals; set their model format instead of multiplying values.

```DAX
Alpha (Direct) =
CALCULATE (
    AVERAGE ( alpha[alpha_ann] ),
    KEEPFILTERS ( dim_scheme[plan] = "Direct" )
)

Median Active Direct Alpha =
CALCULATE (
    MEDIAN ( alpha[alpha_ann] ),
    KEEPFILTERS ( alpha[plan] = "Direct" ),
    KEEPFILTERS ( alpha[is_passive] = FALSE () )
)

Active Direct Funds =
CALCULATE (
    DISTINCTCOUNT ( dim_scheme[scheme_code] ),
    KEEPFILTERS ( dim_scheme[plan] = "Direct" ),
    KEEPFILTERS ( dim_scheme[is_passive] = FALSE () )
)

Funds Significant (BH) =
CALCULATE (
    COUNTROWS ( alpha ),
    KEEPFILTERS ( alpha[plan] = "Direct" ),
    KEEPFILTERS ( alpha[is_passive] = FALSE () ),
    KEEPFILTERS ( alpha[significant_bh] = TRUE () )
)

Median Paired Fee Gap (pp) =
MEDIAN ( fee_gap[gap_pp] )

Median Rupee Impact (Rs 1,00,000) =
MEDIAN ( fee_gap[rupee_gap] )
```

`rupee_gap` is produced from the observed Direct and Regular NAV growth over each pair’s common dates using an initial investment of Rs 1,00,000. The card is the **median across 16 pairs**, not a sum; the period is the common NAV overlap and is not a five-year TER history.

## Display formats

- `alpha_ann`, `cagr`, `vol_ann`, `max_dd`, and return series: `0.00%`.
- `gap_pp`, `expected_pp`, `residual_pp`, and `deviation_pp`: `0.00` with “pp” in the header.
- `rupee_gap` and the rupee measure: Indian digit grouping, two decimals, with Rs/₹.
- `p_bh`: `0.000`; keep its numeric source column. For a visible table label only, use `n/a` where the scheme is passive and the adjusted p-value is blank.
- `beta_252`: `0.00`; capture ratios are dimensionless.

## Aggregation warning

Never leave a numeric field at Power BI’s default **Sum**. Use Average for row-level rates/returns only when the visual aggregates several rows; use the measures above for KPIs. Use Median for the two pair-level cards. Keep keys and labels unaggregated. Never sum `rupee_gap` unless the visual is explicitly labelled as a total across pairs.

## Filter tables

Create `dim_window` as a small calculated table from distinct `metrics[window_label]` values and relate it one-to-many to `metrics[window_label]`. Create and mark `dim_date` from 30-Oct-2021 through 30-Oct-2026; relate its date to `rolling_returns[nav_date]`, `drawdown[nav_date]`, `rolling_beta[nav_date]`, and `benchmark_levels[date]` as separate one-to-many, single-direction relationships.

Relate `dim_scheme[scheme_code]` one-to-many to `alpha`, `metrics`, `control_check`, `rolling_returns`, `drawdown`, `capture`, and `rolling_beta`. Do **not** join `fee_gap[pair_id]` to `dim_scheme[pair_id]`: each pair appears twice in `dim_scheme`, so that join creates an ambiguous many-to-many path. Pair-page AMC/category slicers should use `fee_gap[amc]` and `fee_gap[category]` directly. The pair comparison is fixed to the full research window; plan and window slicers do not apply to it.

# Dashboard Data Contract

Generated from the same schema definitions used by `src/validate_dashboard_data.py`.

| File | Grain / key | Column | CSV type | Meaning |
|---|---|---|---|---|
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `scheme_code` | number | Stable scheme-plan key. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `pair_id` | number | Identifier shared by the Direct and Regular plans. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `scheme_name` | text | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `amc` | text | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `category` | text | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `plan` | text | Direct or Regular plan. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `is_passive` | boolean | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `group` | text | Approved research grouping. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `option` | text | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `benchmark_id` | number | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `benchmark_confirmed` | boolean | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `benchmark_name` | text | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `ter_direct_pct` | number | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `ter_regular_pct` | number | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `benchmark_basis` | text | Source basis for the assigned benchmark series. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `ter_as_of` | text | Source field preserved from the A3 result or approved data pack. |
| `dim_scheme.csv` | One row per scheme plan (scheme_code) / `scheme_code` | `short_name` | text | Unique plan-aware display name, no more than 28 characters. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `scheme_code` | number | Stable scheme-plan key. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `scheme_name` | text | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `amc` | text | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `category` | text | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `plan` | text | Direct or Regular plan. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `option` | text | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `benchmark_id` | number | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `benchmark_confirmed` | boolean | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `window_label` | text | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `start_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `end_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `cagr` | number | Compound annual growth rate as a decimal. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `vol_ann` | number | Annualized volatility as a decimal. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `sharpe` | number | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `sortino` | number | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `max_dd` | number | Maximum drawdown as a decimal. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `max_dd_start` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `max_dd_end` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `te_ann` | number | Source field preserved from the A3 result or approved data pack. Nullable: Benchmark-relative metric unavailable for estimated-hybrid schemes in the frozen A3 results. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `info_ratio` | number | Source field preserved from the A3 result or approved data pack. Nullable: Benchmark-relative metric unavailable for estimated-hybrid schemes in the frozen A3 results. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `up_capture` | number | Source field preserved from the A3 result or approved data pack. Nullable: Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `down_capture` | number | Source field preserved from the A3 result or approved data pack. Nullable: Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `n_obs` | number | Source field preserved from the A3 result or approved data pack. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `group` | text | Approved research grouping. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `short_name` | text | Unique plan-aware display name, no more than 28 characters. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `benchmark_basis` | text | Source basis for the assigned benchmark series. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `metrics.csv` | One row per scheme plan and window_label / `scheme_code, window_label` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `scheme_code` | number | Stable scheme-plan key. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `scheme_name` | text | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `amc` | text | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `category` | text | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `plan` | text | Direct or Regular plan. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `pair_id` | number | Identifier shared by the Direct and Regular plans. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `is_passive` | boolean | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `benchmark_id` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `benchmark_name` | text | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `benchmark_confirmed` | boolean | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `alpha_ann` | number | Annualized CAPM alpha as a decimal. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `se_alpha_ann` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `alpha_ci_lower` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `alpha_ci_upper` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `beta` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `se_beta` | text | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `p_value` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `r2` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `n_obs` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `nw_lag` | number | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `lb_p10` | text | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `beta_warning` | text | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `p_bh` | number | Benjamini-Hochberg adjusted p-value. Nullable: No BH family p-value is assigned to passive funds. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `significant_bh` | boolean | Source field preserved from the A3 result or approved data pack. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `fdr_q` | number | Source field preserved from the A3 result or approved data pack. Nullable: No BH family q-value is assigned to passive funds. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `group` | text | Approved research grouping. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `short_name` | text | Unique plan-aware display name, no more than 28 characters. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `benchmark_basis` | text | Source basis for the assigned benchmark series. |
| `alpha.csv` | One row per scheme plan / `scheme_code` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `pair_id` | number | Identifier shared by the Direct and Regular plans. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `direct_cagr` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `regular_cagr` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `gap_pp` | number | Realized Direct-Regular CAGR gap in percentage points. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `rupee_gap` | number | Rupee impact as defined by the approved Stage A3 fee-gap calculation. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `common_nav_observations` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `start_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `end_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `amc` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `scheme_base_name` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `ter_direct_pct` | number | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `ter_regular_pct` | number | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `expected_pp` | number | Expected TER gap in percentage points. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `residual_pp` | number | Realized gap less expected TER gap in percentage points. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `ter_status` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `median_gap_pp` | number | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `minimum_gap_pp` | number | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `maximum_gap_pp` | number | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `wilcoxon_statistic` | number | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `wilcoxon_p_value` | number | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `category` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `amc_dim` | text | Source field preserved from the A3 result or approved data pack. |
| `fee_gap.csv` | One row per Direct-Regular pair / `pair_id` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `scheme_code` | number | Stable scheme-plan key. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `scheme_name` | text | Source field preserved from the A3 result or approved data pack. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `amc` | text | Source field preserved from the A3 result or approved data pack. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `pair_id` | number | Identifier shared by the Direct and Regular plans. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `alpha_ann` | number | Annualized CAPM alpha as a decimal. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `ter_direct_pct` | number | Source field preserved from the A3 result or approved data pack. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `expected_alpha_ann` | number | Source field preserved from the A3 result or approved data pack. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `deviation_pp` | number | Source field preserved from the A3 result or approved data pack. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `control_band_pp` | number | Source field preserved from the A3 result or approved data pack. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `control_status` | text | Source field preserved from the A3 result or approved data pack. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `group` | text | Approved research grouping. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `short_name` | text | Unique plan-aware display name, no more than 28 characters. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `benchmark_basis` | text | Source basis for the assigned benchmark series. |
| `control_check.csv` | One row per passive scheme plan / `scheme_code` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `rolling_returns.csv` | One row per scheme plan and NAV date after 252 observed NAVs / `scheme_code, nav_date` | `scheme_code` | number | Stable scheme-plan key. |
| `rolling_returns.csv` | One row per scheme plan and NAV date after 252 observed NAVs / `scheme_code, nav_date` | `nav_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `rolling_returns.csv` | One row per scheme plan and NAV date after 252 observed NAVs / `scheme_code, nav_date` | `rolling_return_252d` | number | Trailing return across 252 observed NAV records. |
| `rolling_returns.csv` | One row per scheme plan and NAV date after 252 observed NAVs / `scheme_code, nav_date` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `rolling_returns.csv` | One row per scheme plan and NAV date after 252 observed NAVs / `scheme_code, nav_date` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `rolling_returns.csv` | One row per scheme plan and NAV date after 252 observed NAVs / `scheme_code, nav_date` | `rolling_return_3y` | number | Fund return across the trailing 756 common NAV/benchmark observations. Nullable: Blank until 756 common scheme/benchmark observations exist. |
| `rolling_returns.csv` | One row per scheme plan and NAV date after 252 observed NAVs / `scheme_code, nav_date` | `benchmark_return_3y` | number | Assigned benchmark TRI return across the same trailing 756 common observations. Nullable: Blank until 756 common scheme/benchmark observations exist. |
| `drawdown.csv` | One row per scheme plan and NAV date on the rolling-return date spine / `scheme_code, nav_date` | `scheme_code` | number | Stable scheme-plan key. |
| `drawdown.csv` | One row per scheme plan and NAV date on the rolling-return date spine / `scheme_code, nav_date` | `nav_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `drawdown.csv` | One row per scheme plan and NAV date on the rolling-return date spine / `scheme_code, nav_date` | `drawdown` | number | NAV divided by running peak minus one. |
| `drawdown.csv` | One row per scheme plan and NAV date on the rolling-return date spine / `scheme_code, nav_date` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `drawdown.csv` | One row per scheme plan and NAV date on the rolling-return date spine / `scheme_code, nav_date` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `scheme_code` | number | Stable scheme-plan key. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `scheme_name` | text | Source field preserved from the A3 result or approved data pack. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `benchmark_id` | number | Source field preserved from the A3 result or approved data pack. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `start_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `end_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `up_capture` | number | Source field preserved from the A3 result or approved data pack. Nullable: Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `down_capture` | number | Source field preserved from the A3 result or approved data pack. Nullable: Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `te_ann` | number | Source field preserved from the A3 result or approved data pack. Nullable: Tracking error unavailable for estimated-hybrid schemes in the frozen A3 results. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `benchmark_confirmed` | boolean | Source field preserved from the A3 result or approved data pack. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `group` | text | Approved research grouping. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `short_name` | text | Unique plan-aware display name, no more than 28 characters. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `benchmark_basis` | text | Source basis for the assigned benchmark series. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `capture.csv` | One row per scheme plan (full research window) / `scheme_code` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `rolling_beta.csv` | One row per selected scheme and NAV date with a valid 252-observation beta / `scheme_code, nav_date` | `scheme_code` | number | Stable scheme-plan key. |
| `rolling_beta.csv` | One row per selected scheme and NAV date with a valid 252-observation beta / `scheme_code, nav_date` | `nav_date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `rolling_beta.csv` | One row per selected scheme and NAV date with a valid 252-observation beta / `scheme_code, nav_date` | `beta_252` | number | Rolling beta over 252 valid paired excess-return observations. |
| `rolling_beta.csv` | One row per selected scheme and NAV date with a valid 252-observation beta / `scheme_code, nav_date` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `rolling_beta.csv` | One row per selected scheme and NAV date with a valid 252-observation beta / `scheme_code, nav_date` | `caveat_flag` | boolean | General Stage A3 caveat applies; this is separate from estimated-benchmark status. |
| `benchmark_levels.csv` | One row per benchmark and date / `benchmark_id, date` | `benchmark_id` | number | Source field preserved from the A3 result or approved data pack. |
| `benchmark_levels.csv` | One row per benchmark and date / `benchmark_id, date` | `benchmark_name` | text | Source field preserved from the A3 result or approved data pack. |
| `benchmark_levels.csv` | One row per benchmark and date / `benchmark_id, date` | `date` | ISO date | Source field preserved from the A3 result or approved data pack. |
| `benchmark_levels.csv` | One row per benchmark and date / `benchmark_id, date` | `benchmark_level` | number | Benchmark total-return index level. |
| `benchmark_levels.csv` | One row per benchmark and date / `benchmark_id, date` | `series_basis` | text | Actual TRI or estimated hybrid basis. |
| `benchmark_levels.csv` | One row per benchmark and date / `benchmark_id, date` | `provisional` | boolean | True only when the assigned benchmark basis is estimated_hybrid. |
| `glossary.csv` | One row per glossary term / `field` | `field` | text | Source field preserved from the A3 result or approved data pack. |
| `glossary.csv` | One row per glossary term / `field` | `label` | text | Source field preserved from the A3 result or approved data pack. |
| `glossary.csv` | One row per glossary term / `field` | `definition` | text | Source field preserved from the A3 result or approved data pack. |

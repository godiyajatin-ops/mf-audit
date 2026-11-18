
-- Stage B2: materialized analytical outputs for controlled SQL access.
-- Application access remains read-only through mf_readonly.

CREATE TABLE IF NOT EXISTS public.res_fee_gap (
    pair_id INTEGER PRIMARY KEY,
    direct_cagr NUMERIC,
    regular_cagr NUMERIC,
    gap_pp NUMERIC,
    rupee_gap NUMERIC,
    common_nav_observations INTEGER,
    start_date DATE,
    end_date DATE,
    amc TEXT,
    scheme_base_name TEXT,
    ter_direct_pct NUMERIC,
    ter_regular_pct NUMERIC,
    expected_pp NUMERIC,
    residual_pp NUMERIC,
    ter_status TEXT,
    provisional BOOLEAN,
    median_gap_pp NUMERIC,
    minimum_gap_pp NUMERIC,
    maximum_gap_pp NUMERIC,
    wilcoxon_statistic NUMERIC,
    wilcoxon_p_value NUMERIC
);

CREATE TABLE IF NOT EXISTS public.res_mandate_audit (
    scheme_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    amc TEXT,
    category TEXT,
    plan TEXT,
    pair_id INTEGER,
    is_passive BOOLEAN,
    benchmark_name TEXT,
    benchmark_confirmed BOOLEAN,
    r2 NUMERIC,
    beta NUMERIC,
    max_dd NUMERIC,
    te_ann TEXT,
    R1_benchmark_fit TEXT,
    R2_peer_risk TEXT,
    R2_beta_z NUMERIC,
    R2_max_dd_z NUMERIC,
    gap_pp NUMERIC,
    expected_pp NUMERIC,
    residual_pp NUMERIC,
    R3_abs_residual_pp NUMERIC,
    R3_cost_fit TEXT,
    R4_tracking_error_pct TEXT,
    R4_passive_fit TEXT,
    R5_closet_indexer_screen TEXT,
    provisional BOOLEAN
);

GRANT SELECT ON public.res_fee_gap TO mf_readonly;
GRANT SELECT ON public.res_mandate_audit TO mf_readonly;

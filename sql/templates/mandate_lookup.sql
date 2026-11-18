SELECT scheme_code, scheme_name, benchmark_name,
       r1_benchmark_fit, r2_peer_risk, r3_cost_fit,
       r4_passive_fit, r5_closet_indexer_screen,
       r2_beta_z, r2_max_dd_z, gap_pp, residual_pp, provisional
FROM public.res_mandate_audit
WHERE scheme_code = :scheme_code;

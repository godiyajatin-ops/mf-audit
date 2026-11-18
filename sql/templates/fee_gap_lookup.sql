SELECT pair_id, gap_pp AS value, direct_cagr, regular_cagr, residual_pp
FROM public.res_fee_gap
WHERE pair_id = :pair_id;

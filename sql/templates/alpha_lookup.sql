SELECT scheme_code, window_label, alpha_ann AS value, beta, p_bh
FROM public.res_alpha
WHERE scheme_code = :scheme_code
  AND window_label = :window_label;

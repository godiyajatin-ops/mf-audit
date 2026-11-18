-- The order direction is validated in Python as asc or desc.
SELECT m.scheme_code, m.{{allowlisted_metric_column}} AS value
FROM public.res_metrics AS m
JOIN public.dim_scheme AS s USING (scheme_code)
WHERE s.category = :category
  AND s.is_passive = FALSE
  AND s.plan = 'Direct'
  AND m.window_label = :window_label
ORDER BY m.{{allowlisted_metric_column}} {{validated_order_direction}} NULLS LAST
LIMIT :n;

-- The selected column comes only from src/sql_templates.METRIC_COLUMNS.
SELECT scheme_code, {{allowlisted_metric_column}} AS value
FROM public.res_metrics
WHERE scheme_code IN (:scheme_a, :scheme_b)
  AND window_label = :window_label
ORDER BY scheme_code;

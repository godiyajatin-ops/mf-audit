-- Canonical parameterized shape. src/sql_templates.py selects the column only
-- through METRIC_COLUMNS; never substitute a question string here.
SELECT scheme_code, window_label, {{allowlisted_metric_column}} AS value
FROM public.res_metrics
WHERE scheme_code = :scheme_code
  AND window_label = :window_label;

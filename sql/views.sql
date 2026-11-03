
CREATE OR REPLACE VIEW v_aligned AS
SELECT
    n.scheme_code,
    s.scheme_name,
    s.amc,
    s.category,
    s.plan,
    s.option,
    s.pair_id,
    s.is_passive,
    s.benchmark_id,
    b.name AS benchmark_name,
    n.nav_date,
    n.nav,
    t.tri,
    r.annual_rate,
    s.benchmark_confirmed
FROM fact_nav n
JOIN dim_scheme s
    ON n.scheme_code = s.scheme_code
JOIN fact_benchmark_tri t
    ON s.benchmark_id = t.benchmark_id
   AND n.nav_date = t.tri_date
LEFT JOIN fact_rf r
    ON n.nav_date = r.rf_date;

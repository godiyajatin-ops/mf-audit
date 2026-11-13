
BEGIN;

-- ============================================================
-- A2.1.1: Daily returns
-- NAV returns retain all 32 schemes.
-- Benchmark-relative returns are calculated only on exact
-- NAV/TRI aligned dates.
-- ============================================================


CREATE OR REPLACE VIEW v_ret AS

WITH nav_lag AS (
    SELECT
        n.scheme_code,
        n.nav_date,
        n.nav,
        LAG(n.nav) OVER (
            PARTITION BY n.scheme_code
            ORDER BY n.nav_date
        ) AS prev_nav
    FROM fact_nav n
),

-- Construct the exact NAV/TRI intersection first.
-- Both return series must use the same previous aligned date.
aligned_series AS (
    SELECT
        n.scheme_code,
        n.nav_date,
        n.nav,
        t.tri,

        LAG(n.nav) OVER (
            PARTITION BY n.scheme_code
            ORDER BY n.nav_date
        ) AS prev_aligned_nav,

        LAG(t.tri) OVER (
            PARTITION BY n.scheme_code
            ORDER BY n.nav_date
        ) AS prev_aligned_tri

    FROM fact_nav n
    JOIN dim_scheme s
        ON n.scheme_code = s.scheme_code
    JOIN fact_benchmark_tri t
        ON s.benchmark_id = t.benchmark_id
       AND n.nav_date = t.tri_date
)

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
    s.benchmark_confirmed,
    n.nav_date,

    n.nav,
    n.prev_nav,

    CASE
        WHEN n.prev_nav IS NOT NULL AND n.prev_nav <> 0
        THEN n.nav / n.prev_nav - 1
        ELSE NULL
    END AS nav_return,

    CASE
        WHEN a.prev_aligned_nav IS NOT NULL
             AND a.prev_aligned_nav <> 0
        THEN a.nav / a.prev_aligned_nav - 1
        ELSE NULL
    END AS aligned_fund_return,

    CASE
        WHEN a.prev_aligned_tri IS NOT NULL
             AND a.prev_aligned_tri <> 0
        THEN a.tri / a.prev_aligned_tri - 1
        ELSE NULL
    END AS benchmark_return,

    CASE
        WHEN a.prev_aligned_nav IS NOT NULL
             AND a.prev_aligned_tri IS NOT NULL
        THEN TRUE
        ELSE FALSE
    END AS benchmark_aligned

FROM nav_lag n
JOIN dim_scheme s
    ON n.scheme_code = s.scheme_code
LEFT JOIN aligned_series a
    ON n.scheme_code = a.scheme_code
   AND n.nav_date = a.nav_date;


-- ============================================================
-- A2.1.2: Daily risk-free rate
-- Annual rate converted using 252 trading days.
-- Missing dates remain missing; never replaced with zero.
-- ============================================================

CREATE OR REPLACE VIEW v_rf_daily AS
SELECT
    rf_date,
    annual_rate,
    annual_rate / 252.0 AS rf_daily,
    'constant_assumption'::TEXT AS rf_source
FROM fact_rf;


-- ============================================================
-- A2.1.3: Excess returns
-- NAV-only excess returns available for all schemes.
-- Benchmark excess returns only where TRI is available.
-- ============================================================

CREATE OR REPLACE VIEW v_ex AS
SELECT
    r.scheme_code,
    r.scheme_name,
    r.amc,
    r.category,
    r.plan,
    r.option,
    r.pair_id,
    r.is_passive,
    r.benchmark_id,
    r.benchmark_confirmed,
    r.nav_date,

    r.nav_return,
    r.aligned_fund_return,
    r.benchmark_return,
    r.benchmark_aligned,

    rf.annual_rate,
    rf.rf_daily,
    rf.rf_source,

    r.nav_return - rf.rf_daily AS fund_excess,
    r.aligned_fund_return - rf.rf_daily AS aligned_fund_excess,
    r.benchmark_return - rf.rf_daily AS benchmark_excess

FROM v_ret r
LEFT JOIN v_rf_daily rf
    ON r.nav_date = rf.rf_date;

COMMIT;

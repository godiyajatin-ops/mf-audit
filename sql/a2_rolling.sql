
BEGIN;

-- ============================================================
-- A2.2.1: Daily drawdown
-- Running peak is calculated independently for each scheme.
-- Available for all 32 schemes.
-- ============================================================

CREATE OR REPLACE VIEW v_dd AS
WITH peaks AS (
    SELECT
        scheme_code,
        nav_date,
        nav,
        MAX(nav) OVER (
            PARTITION BY scheme_code
            ORDER BY nav_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_peak
    FROM fact_nav
)
SELECT
    scheme_code,
    nav_date,
    nav,
    running_peak,
    nav / NULLIF(running_peak, 0) - 1 AS drawdown
FROM peaks;


-- ============================================================
-- A2.2.2: Rolling 1Y and 3Y NAV volatility
-- Calendar-offset windows, not row-count approximations.
-- Annualized using 252 trading days.
-- ============================================================


CREATE OR REPLACE VIEW v_roll AS
WITH base AS (
    SELECT
        scheme_code,
        nav_date,
        nav_return,
        LAG(nav_date) OVER (
            PARTITION BY scheme_code
            ORDER BY nav_date
        ) AS prev_nav_date
    FROM v_ret
),
returns AS (
    SELECT *
    FROM base
    WHERE nav_return IS NOT NULL
),
rolling AS (
    SELECT
        scheme_code,
        nav_date,
        prev_nav_date,
        nav_return,

        COUNT(*) OVER w1 AS cnt_1y,
        SUM(nav_return) OVER w1 AS sum_1y,
        SUM(nav_return * nav_return) OVER w1 AS sq_1y,
        FIRST_VALUE(nav_return) OVER w1 AS first_ret_1y,
        FIRST_VALUE(prev_nav_date) OVER w1 AS first_prev_1y,

        COUNT(*) OVER w3 AS cnt_3y,
        SUM(nav_return) OVER w3 AS sum_3y,
        SUM(nav_return * nav_return) OVER w3 AS sq_3y,
        FIRST_VALUE(nav_return) OVER w3 AS first_ret_3y,
        FIRST_VALUE(prev_nav_date) OVER w3 AS first_prev_3y

    FROM returns

    WINDOW
        w1 AS (
            PARTITION BY scheme_code
            ORDER BY nav_date
            RANGE BETWEEN INTERVAL '1 year' PRECEDING
                      AND CURRENT ROW
        ),
        w3 AS (
            PARTITION BY scheme_code
            ORDER BY nav_date
            RANGE BETWEEN INTERVAL '3 years' PRECEDING
                      AND CURRENT ROW
        )
),
adjusted AS (
    SELECT *,
        CASE
            WHEN first_prev_1y < (nav_date - INTERVAL '1 year')::date
            THEN 1 ELSE 0
        END AS drop_1y,

        CASE
            WHEN first_prev_3y < (nav_date - INTERVAL '3 years')::date
            THEN 1 ELSE 0
        END AS drop_3y
    FROM rolling
)
SELECT
    scheme_code,
    nav_date,

    cnt_1y - drop_1y AS n_1y,

    CASE
        WHEN cnt_1y - drop_1y > 1 THEN
            SQRT(GREATEST(
                (
                    sq_1y - drop_1y * first_ret_1y * first_ret_1y
                    - POWER(sum_1y - drop_1y * first_ret_1y, 2)
                      / (cnt_1y - drop_1y)
                ) / (cnt_1y - drop_1y - 1),
                0
            )) * SQRT(252.0)
        ELSE NULL
    END AS vol_1y,

    cnt_3y - drop_3y AS n_3y,

    CASE
        WHEN cnt_3y - drop_3y > 1 THEN
            SQRT(GREATEST(
                (
                    sq_3y - drop_3y * first_ret_3y * first_ret_3y
                    - POWER(sum_3y - drop_3y * first_ret_3y, 2)
                      / (cnt_3y - drop_3y)
                ) / (cnt_3y - drop_3y - 1),
                0
            )) * SQRT(252.0)
        ELSE NULL
    END AS vol_3y

FROM adjusted;


-- ============================================================
-- A2.2.3: Rolling 1Y and 3Y aligned fund / benchmark volatility
-- Both series use the same aligned observation dates.
-- Available only for schemes with TRI coverage.
-- ============================================================


CREATE OR REPLACE VIEW v_roll_bench AS

WITH base AS (
    SELECT
        scheme_code,
        nav_date,
        aligned_fund_return,
        benchmark_return,

        LAG(nav_date) OVER (
            PARTITION BY scheme_code
            ORDER BY nav_date
        ) AS prev_aligned_date

    FROM v_ret
    WHERE benchmark_aligned = TRUE
),

returns AS (
    SELECT *
    FROM base
    WHERE aligned_fund_return IS NOT NULL
      AND benchmark_return IS NOT NULL
),

rolling AS (
    SELECT
        scheme_code,
        nav_date,
        prev_aligned_date,
        aligned_fund_return,
        benchmark_return,

        COUNT(*) OVER w1 AS cnt_1y,
        SUM(aligned_fund_return) OVER w1 AS fund_sum_1y,
        SUM(aligned_fund_return * aligned_fund_return) OVER w1 AS fund_sq_1y,
        SUM(benchmark_return) OVER w1 AS bench_sum_1y,
        SUM(benchmark_return * benchmark_return) OVER w1 AS bench_sq_1y,

        FIRST_VALUE(aligned_fund_return) OVER w1 AS first_fund_1y,
        FIRST_VALUE(benchmark_return) OVER w1 AS first_bench_1y,
        FIRST_VALUE(prev_aligned_date) OVER w1 AS first_prev_1y,

        COUNT(*) OVER w3 AS cnt_3y,
        SUM(aligned_fund_return) OVER w3 AS fund_sum_3y,
        SUM(aligned_fund_return * aligned_fund_return) OVER w3 AS fund_sq_3y,
        SUM(benchmark_return) OVER w3 AS bench_sum_3y,
        SUM(benchmark_return * benchmark_return) OVER w3 AS bench_sq_3y,

        FIRST_VALUE(aligned_fund_return) OVER w3 AS first_fund_3y,
        FIRST_VALUE(benchmark_return) OVER w3 AS first_bench_3y,
        FIRST_VALUE(prev_aligned_date) OVER w3 AS first_prev_3y

    FROM returns

    WINDOW
        w1 AS (
            PARTITION BY scheme_code
            ORDER BY nav_date
            RANGE BETWEEN INTERVAL '1 year' PRECEDING
                      AND CURRENT ROW
        ),
        w3 AS (
            PARTITION BY scheme_code
            ORDER BY nav_date
            RANGE BETWEEN INTERVAL '3 years' PRECEDING
                      AND CURRENT ROW
        )
),

adjusted AS (
    SELECT *,
        CASE
            WHEN first_prev_1y < (nav_date - INTERVAL '1 year')::date
            THEN 1 ELSE 0
        END AS drop_1y,

        CASE
            WHEN first_prev_3y < (nav_date - INTERVAL '3 years')::date
            THEN 1 ELSE 0
        END AS drop_3y

    FROM rolling
)

SELECT
    scheme_code,
    nav_date,

    cnt_1y - drop_1y AS n_1y,

    CASE
        WHEN cnt_1y - drop_1y > 1 THEN
            SQRT(GREATEST(
                (
                    fund_sq_1y - drop_1y * first_fund_1y * first_fund_1y
                    - POWER(
                        fund_sum_1y - drop_1y * first_fund_1y,
                        2
                    ) / (cnt_1y - drop_1y)
                ) / (cnt_1y - drop_1y - 1),
                0
            )) * SQRT(252.0)
        ELSE NULL
    END AS fund_vol_1y,

    CASE
        WHEN cnt_1y - drop_1y > 1 THEN
            SQRT(GREATEST(
                (
                    bench_sq_1y - drop_1y * first_bench_1y * first_bench_1y
                    - POWER(
                        bench_sum_1y - drop_1y * first_bench_1y,
                        2
                    ) / (cnt_1y - drop_1y)
                ) / (cnt_1y - drop_1y - 1),
                0
            )) * SQRT(252.0)
        ELSE NULL
    END AS benchmark_vol_1y,

    cnt_3y - drop_3y AS n_3y,

    CASE
        WHEN cnt_3y - drop_3y > 1 THEN
            SQRT(GREATEST(
                (
                    fund_sq_3y - drop_3y * first_fund_3y * first_fund_3y
                    - POWER(
                        fund_sum_3y - drop_3y * first_fund_3y,
                        2
                    ) / (cnt_3y - drop_3y)
                ) / (cnt_3y - drop_3y - 1),
                0
            )) * SQRT(252.0)
        ELSE NULL
    END AS fund_vol_3y,

    CASE
        WHEN cnt_3y - drop_3y > 1 THEN
            SQRT(GREATEST(
                (
                    bench_sq_3y - drop_3y * first_bench_3y * first_bench_3y
                    - POWER(
                        bench_sum_3y - drop_3y * first_bench_3y,
                        2
                    ) / (cnt_3y - drop_3y)
                ) / (cnt_3y - drop_3y - 1),
                0
            )) * SQRT(252.0)
        ELSE NULL
    END AS benchmark_vol_3y

FROM adjusted;

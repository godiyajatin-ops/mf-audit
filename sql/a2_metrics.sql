
BEGIN;

-- ============================================================
-- A2.3: Scheme-level performance metrics
-- One record per scheme and evaluation window.
-- Expected: 32 schemes x 3 windows = 96 records.
-- ============================================================

CREATE TABLE IF NOT EXISTS res_metrics (
    scheme_code INT NOT NULL
        REFERENCES dim_scheme(scheme_code),

    window_label TEXT NOT NULL
        CHECK (window_label IN ('FULL', '3Y', '1Y')),

    cagr NUMERIC,
    vol_ann NUMERIC,
    sharpe NUMERIC,
    sortino NUMERIC,

    max_dd NUMERIC,
    max_dd_start DATE,
    max_dd_end DATE,

    te_ann NUMERIC,
    info_ratio NUMERIC,
    up_capture NUMERIC,
    down_capture NUMERIC,

    n_obs INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    PRIMARY KEY (scheme_code, window_label),

    CHECK (n_obs >= 0),
    CHECK (start_date <= end_date)
);

COMMIT;


-- ============================================================
-- A2.3: Calculate metrics for FULL, 3Y and 1Y windows
-- ============================================================

WITH window_defs AS (
    SELECT 'FULL'::TEXT AS window_label, 0 AS years
    UNION ALL
    SELECT '3Y', 3
    UNION ALL
    SELECT '1Y', 1
),

scheme_bounds AS (
    SELECT
        s.scheme_code,
        MIN(n.nav_date) AS first_nav_date,
        LEAST(MAX(n.nav_date), DATE '2026-10-30') AS end_date
    FROM dim_scheme s
    JOIN fact_nav n ON s.scheme_code = n.scheme_code
    GROUP BY s.scheme_code
),

scheme_windows AS (
    SELECT
        b.scheme_code,
        w.window_label,
        CASE
            WHEN w.window_label = 'FULL'
            THEN b.first_nav_date
            ELSE (b.end_date - make_interval(years => w.years))::date
        END AS window_start,
        b.end_date AS window_end
    FROM scheme_bounds b
    CROSS JOIN window_defs w
),

-- NAV observations are filtered before LAG.
-- Therefore the first return in each window is NULL.
nav_base AS (
    SELECT
        sw.scheme_code,
        sw.window_label,
        sw.window_start,
        sw.window_end,
        n.nav_date,
        n.nav,
        LAG(n.nav) OVER (
            PARTITION BY sw.scheme_code, sw.window_label
            ORDER BY n.nav_date
        ) AS prev_nav
    FROM scheme_windows sw
    JOIN fact_nav n
        ON n.scheme_code = sw.scheme_code
       AND n.nav_date BETWEEN sw.window_start AND sw.window_end
),

nav_returns AS (
    SELECT
        *,
        nav / NULLIF(prev_nav, 0) - 1 AS fund_return
    FROM nav_base
),

nav_excess AS (
    SELECT
        nr.*,
        r.annual_rate / 252.0 AS rf_daily,
        nr.fund_return - r.annual_rate / 252.0 AS excess_return
    FROM nav_returns nr
    LEFT JOIN fact_rf r ON nr.nav_date = r.rf_date
),

-- Running peak is recomputed inside each evaluation window.
nav_peaks AS (
    SELECT
        *,
        MAX(nav) OVER (
            PARTITION BY scheme_code, window_label
            ORDER BY nav_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_peak
    FROM nav_excess
),

nav_peak_dates AS (
    SELECT
        *,
        MAX(nav_date) FILTER (
            WHERE nav = running_peak
        ) OVER (
            PARTITION BY scheme_code, window_label
            ORDER BY nav_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_peak_date
    FROM nav_peaks
),

drawdown_ranked AS (
    SELECT
        *,
        nav / NULLIF(running_peak, 0) - 1 AS drawdown,
        ROW_NUMBER() OVER (
            PARTITION BY scheme_code, window_label
            ORDER BY nav / NULLIF(running_peak, 0) - 1,
                     nav_date
        ) AS dd_rank
    FROM nav_peak_dates
),

nav_summary AS (
    SELECT
        scheme_code,
        window_label,
        MIN(nav_date) AS start_date,
        MAX(nav_date) AS end_date,
        (ARRAY_AGG(nav ORDER BY nav_date))[1] AS first_nav,
        (ARRAY_AGG(nav ORDER BY nav_date DESC))[1] AS last_nav,

        COUNT(fund_return) AS n_obs,
        AVG(fund_return) AS avg_return,
        STDDEV_SAMP(fund_return) AS daily_vol,

        AVG(excess_return) AS avg_excess,
        STDDEV_SAMP(excess_return) AS daily_excess_vol,

        SQRT(
        AVG(POWER(LEAST(excess_return, 0), 2))
        FILTER (WHERE excess_return IS NOT NULL)) AS downside_deviation_daily

    FROM nav_excess
    GROUP BY scheme_code, window_label
),

worst_drawdown AS (
    SELECT
        scheme_code,
        window_label,
        drawdown AS max_dd,
        running_peak_date AS max_dd_start,
        nav_date AS max_dd_end
    FROM drawdown_ranked
    WHERE dd_rank = 1
),

nav_metrics AS (
    SELECT
        n.scheme_code,
        n.window_label,

        POWER(
            n.last_nav / NULLIF(n.first_nav, 0),
            365.25 / NULLIF(
                (n.end_date - n.start_date)::numeric, 0
            )
        ) - 1 AS cagr,

        n.daily_vol * SQRT(252.0) AS vol_ann,

        n.avg_excess / NULLIF(n.daily_excess_vol, 0)
            * SQRT(252.0) AS sharpe,

        n.avg_excess /
            NULLIF(n.downside_deviation_daily, 0)
            * SQRT(252.0) AS sortino,

        d.max_dd,
        d.max_dd_start,
        d.max_dd_end,

        n.n_obs,
        n.start_date,
        n.end_date

    FROM nav_summary n
    LEFT JOIN worst_drawdown d
        ON n.scheme_code = d.scheme_code
       AND n.window_label = d.window_label
),

-- Benchmark returns are independently calculated after
-- restricting aligned observations to each evaluation window.
aligned_base AS (
    SELECT
        sw.scheme_code,
        sw.window_label,
        n.nav_date,
        n.nav,
        t.tri,

        LAG(n.nav) OVER (
            PARTITION BY sw.scheme_code, sw.window_label
            ORDER BY n.nav_date
        ) AS prev_nav,

        LAG(t.tri) OVER (
            PARTITION BY sw.scheme_code, sw.window_label
            ORDER BY n.nav_date
        ) AS prev_tri

    FROM scheme_windows sw
    JOIN dim_scheme s
        ON sw.scheme_code = s.scheme_code
    JOIN fact_nav n
        ON n.scheme_code = sw.scheme_code
       AND n.nav_date BETWEEN sw.window_start AND sw.window_end
    JOIN fact_benchmark_tri t
        ON t.benchmark_id = s.benchmark_id
       AND t.tri_date = n.nav_date
),

aligned_returns AS (
    SELECT
        *,
        nav / NULLIF(prev_nav, 0) - 1 AS fund_return,
        tri / NULLIF(prev_tri, 0) - 1 AS benchmark_return
    FROM aligned_base
    WHERE prev_nav IS NOT NULL
      AND prev_tri IS NOT NULL
),

benchmark_metrics AS (
    SELECT
        scheme_code,
        window_label,

        STDDEV_SAMP(
            fund_return - benchmark_return
        ) * SQRT(252.0) AS te_ann,

        AVG(fund_return - benchmark_return) * 252.0 /
            NULLIF(
                STDDEV_SAMP(
                    fund_return - benchmark_return
                ) * SQRT(252.0),
                0
            ) AS info_ratio,

        AVG(fund_return) FILTER (
            WHERE benchmark_return > 0
        ) / NULLIF(
            AVG(benchmark_return) FILTER (
                WHERE benchmark_return > 0
            ), 0
        ) AS up_capture,

        AVG(fund_return) FILTER (
            WHERE benchmark_return < 0
        ) / NULLIF(
            AVG(benchmark_return) FILTER (
                WHERE benchmark_return < 0
            ), 0
        ) AS down_capture

    FROM aligned_returns
    GROUP BY scheme_code, window_label
)

INSERT INTO res_metrics (
    scheme_code,
    window_label,
    cagr,
    vol_ann,
    sharpe,
    sortino,
    max_dd,
    max_dd_start,
    max_dd_end,
    te_ann,
    info_ratio,
    up_capture,
    down_capture,
    n_obs,
    start_date,
    end_date
)
SELECT
    n.scheme_code,
    n.window_label,
    n.cagr,
    n.vol_ann,
    n.sharpe,
    n.sortino,
    n.max_dd,
    n.max_dd_start,
    n.max_dd_end,
    b.te_ann,
    b.info_ratio,
    b.up_capture,
    b.down_capture,
    n.n_obs,
    n.start_date,
    n.end_date
FROM nav_metrics n
LEFT JOIN benchmark_metrics b
    ON n.scheme_code = b.scheme_code
   AND n.window_label = b.window_label

ON CONFLICT (scheme_code, window_label)
DO UPDATE SET
    cagr = EXCLUDED.cagr,
    vol_ann = EXCLUDED.vol_ann,
    sharpe = EXCLUDED.sharpe,
    sortino = EXCLUDED.sortino,
    max_dd = EXCLUDED.max_dd,
    max_dd_start = EXCLUDED.max_dd_start,
    max_dd_end = EXCLUDED.max_dd_end,
    te_ann = EXCLUDED.te_ann,
    info_ratio = EXCLUDED.info_ratio,
    up_capture = EXCLUDED.up_capture,
    down_capture = EXCLUDED.down_capture,
    n_obs = EXCLUDED.n_obs,
    start_date = EXCLUDED.start_date,
    end_date = EXCLUDED.end_date;

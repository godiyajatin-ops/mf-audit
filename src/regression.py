from pathlib import Path
import os
import math

import numpy as np
import pandas as pd
import statsmodels.api as sm
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from statsmodels.stats.diagnostic import acorr_ljungbox


START_DATE = "2021-10-30"
END_DATE = "2026-10-30"
MIN_OBSERVATIONS = 1000
ANNUALIZATION = 252
PROVISIONAL = True


def nw_lag(T):
    return math.floor(4 * (T / 100) ** (2 / 9))


def load_regression_data(conn):
    query = text("""
        SELECT
            s.scheme_code,
            s.scheme_name,
            s.amc,
            s.category,
            s.plan,
            s.pair_id,
            s.is_passive,
            s.benchmark_id,
            b.name AS benchmark_name,
            s.benchmark_confirmed,
            v.nav_date,
            v.aligned_fund_excess AS ex_p,
            v.benchmark_excess AS ex_b
        FROM v_ex v
        JOIN dim_scheme s
            ON s.scheme_code = v.scheme_code
        LEFT JOIN dim_benchmark b
            ON b.benchmark_id = s.benchmark_id
        WHERE v.nav_date BETWEEN :start_date AND :end_date
          AND v.aligned_fund_excess IS NOT NULL
          AND v.benchmark_excess IS NOT NULL
        ORDER BY s.scheme_code, v.nav_date
    """)

    return pd.read_sql(
        query,
        conn,
        params={
            "start_date": START_DATE,
            "end_date": END_DATE
        }
    )


def estimate_scheme(group):
    group = group.dropna(subset=["ex_p", "ex_b"]).copy()
    T = len(group)

    if T < MIN_OBSERVATIONS:
        raise ValueError(
            f"Scheme {group['scheme_code'].iloc[0]} has only "
            f"{T} aligned observations; minimum is {MIN_OBSERVATIONS}"
        )

    X = sm.add_constant(group["ex_b"])
    model = sm.OLS(group["ex_p"], X)

    lag = nw_lag(T)
    fitted = model.fit(
        cov_type="HAC",
        cov_kwds={"maxlags": lag}
    )

    ci = fitted.conf_int(alpha=0.05)
    alpha_daily = fitted.params["const"]
    se_daily = fitted.bse["const"]

    lb = acorr_ljungbox(
        fitted.resid,
        lags=[10],
        return_df=True
    )

    first = group.iloc[0]

    return {
        "scheme_code": int(first["scheme_code"]),
        "scheme_name": first["scheme_name"],
        "amc": first["amc"],
        "category": first["category"],
        "plan": first["plan"],
        "pair_id": int(first["pair_id"]),
        "is_passive": bool(first["is_passive"]),
        "benchmark_id": int(first["benchmark_id"]),
        "benchmark_name": first["benchmark_name"],
        "benchmark_confirmed": bool(first["benchmark_confirmed"]),
        "alpha_ann": alpha_daily * ANNUALIZATION,
        "se_alpha_ann": se_daily * ANNUALIZATION,
        "alpha_ci_lower": ci.loc["const", 0] * ANNUALIZATION,
        "alpha_ci_upper": ci.loc["const", 1] * ANNUALIZATION,
        "beta": fitted.params["ex_b"],
        "se_beta": fitted.bse["ex_b"],
        "p_value": fitted.pvalues["const"],
        "r2": fitted.rsquared,
        "n_obs": T,
        "nw_lag": lag,
        "lb_p10": lb["lb_pvalue"].iloc[0],
        "beta_warning": not (0.5 <= fitted.params["ex_b"] <= 1.5),
        "provisional": PROVISIONAL
    }


def main():
    load_dotenv(dotenv_path=".env")
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            data = load_regression_data(conn)
    finally:
        engine.dispose()

    if data.empty:
        raise RuntimeError("No aligned regression observations found.")

    results = []

    for scheme_code, group in data.groupby("scheme_code"):
        results.append(estimate_scheme(group))

    output = pd.DataFrame(results).sort_values("scheme_code")

    if len(output) != 32:
        raise RuntimeError(
            f"Expected 32 scheme results, found {len(output)}"
        )

    Path("results").mkdir(exist_ok=True)
    output.to_csv("results/alpha.csv", index=False)

    print("CAPM REGRESSION COMPLETED")
    print(f"Schemes: {len(output)}")
    print(f"Total observations: {output['n_obs'].sum()}")
    print(f"Provisional: {PROVISIONAL}")
    print("Output: results/alpha.csv")


if __name__ == "__main__":
    main()

from pathlib import Path
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from statsmodels.stats.multitest import multipletests

from src.regression import nw_lag, ANNUALIZATION


BLOCK_SIZE = 20
BOOTSTRAPS = 2000
SEED = 42
PROVISIONAL = True


def fit_capm(fund_excess, benchmark_excess, annualization=ANNUALIZATION):
    data = pd.DataFrame({
        "fund": fund_excess,
        "benchmark": benchmark_excess
    }).dropna()

    model = sm.OLS(
        data["fund"],
        sm.add_constant(data["benchmark"])
    ).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": nw_lag(len(data))}
    )

    return {
        "alpha_ann": model.params["const"] * annualization,
        "p_value": model.pvalues["const"],
        "beta": model.params["benchmark"],
        "n_obs": len(data)
    }


def moving_block_bootstrap(fund, benchmark):
    rng = np.random.default_rng(SEED)

    data = np.column_stack([fund, benchmark])
    n = len(data)
    blocks = int(np.ceil(n / BLOCK_SIZE))
    estimates = []

    for _ in range(BOOTSTRAPS):
        starts = rng.integers(0, n - BLOCK_SIZE + 1, blocks)

        indices = np.concatenate([
            np.arange(start, start + BLOCK_SIZE)
            for start in starts
        ])[:n]

        sample = data[indices]

        try:
            model = sm.OLS(
                sample[:, 0],
                sm.add_constant(sample[:, 1])
            ).fit()

            estimates.append(model.params[0] * ANNUALIZATION)
        except (ValueError, np.linalg.LinAlgError):
            continue

    if not estimates:
        raise RuntimeError("Moving-block bootstrap produced no estimates.")

    lower, upper = np.percentile(estimates, [2.5, 97.5])

    return {
        "bootstrap_alpha_lower": lower,
        "bootstrap_alpha_upper": upper,
        "bootstrap_valid": len(estimates)
    }


def main():
    load_dotenv(dotenv_path=".env")
    engine = create_engine(os.environ["DATABASE_URL"])

    query = text("""
        SELECT
            s.scheme_code,
            s.scheme_name,
            s.category,
            s.plan,
            s.is_passive,
            v.nav_date,
            v.aligned_fund_return,
            v.benchmark_return,
            rf.rf_daily
        FROM v_ret v
        JOIN dim_scheme s
            ON s.scheme_code = v.scheme_code
        JOIN v_rf_daily rf ON rf.rf_date = v.nav_date
        WHERE v.benchmark_aligned = TRUE
          AND v.nav_date BETWEEN DATE '2021-10-30'
                             AND DATE '2026-10-30'
        ORDER BY s.scheme_code, v.nav_date
    """)

    try:
        with engine.connect() as conn:
            daily = pd.read_sql(query, conn)
    finally:
        engine.dispose()

    # Common alternative benchmark: NIFTY 500 TRI, independent of each scheme's
    # stated benchmark. Returns use the exact NAV/TRI date intersection.
    nifty_query = text("""
        WITH aligned AS (
            SELECT s.scheme_code, s.scheme_name, n.nav_date, n.nav, t.tri,
                   LAG(n.nav) OVER (PARTITION BY s.scheme_code ORDER BY n.nav_date) AS prev_nav,
                   LAG(t.tri) OVER (PARTITION BY s.scheme_code ORDER BY n.nav_date) AS prev_tri
            FROM fact_nav n
            JOIN dim_scheme s ON s.scheme_code = n.scheme_code
            JOIN fact_benchmark_tri t ON t.benchmark_id = 3 AND t.tri_date = n.nav_date
            WHERE n.nav_date BETWEEN DATE '2021-10-30' AND DATE '2026-10-30'
        )
        SELECT a.scheme_code, a.scheme_name, a.nav_date,
               a.nav / NULLIF(a.prev_nav, 0) - 1 AS aligned_fund_return,
               a.tri / NULLIF(a.prev_tri, 0) - 1 AS benchmark_return,
               rf.rf_daily
        FROM aligned a
        JOIN v_rf_daily rf ON rf.rf_date = a.nav_date
        WHERE a.prev_nav IS NOT NULL AND a.prev_tri IS NOT NULL
        ORDER BY a.scheme_code, a.nav_date
    """)
    try:
        with engine.connect() as conn:
            nifty500 = pd.read_sql(nifty_query, conn)
    finally:
        engine.dispose()
    nifty500["nav_date"] = pd.to_datetime(nifty500["nav_date"])
    if nifty500.empty:
        raise RuntimeError("No NIFTY 500 TRI alternative benchmark observations found.")
    nifty500_results = {}
    for code, group in nifty500.groupby("scheme_code"):
        result = fit_capm(
            group["aligned_fund_return"] - group["rf_daily"],
            group["benchmark_return"] - group["rf_daily"]
        )
        nifty500_results[int(code)] = result
    daily["nav_date"] = pd.to_datetime(daily["nav_date"])

    if daily.empty:
        raise RuntimeError("No aligned returns available for robustness.")

    records = []

    for scheme_code, group in daily.groupby("scheme_code"):
        group = group.dropna(
            subset=["aligned_fund_return", "benchmark_return", "rf_daily"]
        ).copy()

        group = group.sort_values("nav_date")

        fund = group["aligned_fund_return"].to_numpy()
        benchmark = group["benchmark_return"].to_numpy()
        rf = group["rf_daily"].to_numpy()

        base_fund_ex = fund - rf
        base_benchmark_ex = benchmark - rf

        result = {
            "scheme_code": int(scheme_code),
            "scheme_name": group["scheme_name"].iloc[0],
            "plan": group["plan"].iloc[0],
            "is_passive": bool(group["is_passive"].iloc[0]),
            "provisional": PROVISIONAL
        }

        # 1. Monthly frequency CAPM
        monthly = group.set_index("nav_date").resample("ME").agg({
            "aligned_fund_return": lambda x: np.prod(1 + x) - 1,
            "benchmark_return": lambda x: np.prod(1 + x) - 1
        }).dropna()

        monthly_rf = (1.06 ** (1 / 12)) - 1

        monthly_result = fit_capm(
            monthly["aligned_fund_return"] - monthly_rf,
            monthly["benchmark_return"] - monthly_rf,
            annualization=12
        )

        result["monthly_alpha_ann"] = monthly_result["alpha_ann"]
        result["monthly_p_value"] = monthly_result["p_value"]
        result["monthly_n_obs"] = monthly_result["n_obs"]
        alternative = nifty500_results.get(int(scheme_code))
        if alternative is None:
            raise ValueError(f"No NIFTY 500 TRI sensitivity for scheme {scheme_code}")
        result["nifty500_alpha_ann"] = alternative["alpha_ann"]
        result["nifty500_p_value"] = alternative["p_value"]
        result["nifty500_n_obs"] = alternative["n_obs"]

        # 2. Risk-free rate sensitivity: +/- 1 percentage point
        for label, shift in [("rf_minus_1pp", -0.01),
                             ("rf_plus_1pp", 0.01)]:

            sensitivity = fit_capm(
                base_fund_ex - shift / ANNUALIZATION,
                base_benchmark_ex - shift / ANNUALIZATION
            )

            result[f"{label}_alpha_ann"] = sensitivity["alpha_ann"]
            result[f"{label}_p_value"] = sensitivity["p_value"]

        # 3. Moving-block bootstrap for the preregistered primary active Direct family.
        if (group["plan"].iloc[0] == "Direct") and (not bool(group["is_passive"].iloc[0])):
            bootstrap = moving_block_bootstrap(base_fund_ex, base_benchmark_ex)
            result.update(bootstrap)
        else:
            result.update({"bootstrap_alpha_lower": np.nan, "bootstrap_alpha_upper": np.nan, "bootstrap_valid": 0})

        records.append(result)

    output = pd.DataFrame(records)

    # 4. Leave-extremes-out BH sensitivity
    alpha = pd.read_csv("results/alpha.csv")

    active = alpha[
        ~alpha["is_passive"].astype(bool)
    ].copy()

    active["alpha_rank"] = active.groupby("plan")["alpha_ann"].rank(
        method="first"
    )

    active["extreme"] = (
        (active["alpha_rank"] == 1)
        | (
            active["alpha_rank"]
            == active.groupby("plan")["alpha_rank"].transform("max")
        )
    )

    active["p_bh_without_extremes"] = np.nan

    for plan in ["Direct", "Regular"]:
        mask = (
            (active["plan"] == plan)
            & (~active["extreme"])
        )

        if mask.sum() == 0:
            continue

        _, adjusted, _, _ = multipletests(
            active.loc[mask, "p_value"],
            alpha=0.10,
            method="fdr_bh"
        )

        active.loc[mask, "p_bh_without_extremes"] = adjusted

    sensitivity = active[[
        "scheme_code", "extreme",
        "p_bh", "p_bh_without_extremes"
    ]].copy()

    output = output.merge(
        sensitivity,
        on="scheme_code",
        how="left"
    )

    # Compare BH-adjusted significance within each active plan family for every sensitivity.
    for scenario in ["monthly", "nifty500", "rf_minus_1pp", "rf_plus_1pp"]:
        p_col = f"{scenario}_p_value"
        adj_col = f"{scenario}_p_bh"
        output[adj_col] = np.nan
        for plan in ["Direct", "Regular"]:
            mask = (output["plan"] == plan) & (~output["is_passive"].astype(bool))
            if int(mask.sum()) != 12:
                raise ValueError(f"Expected 12 active {plan} funds for {scenario} BH")
            output.loc[mask, adj_col] = multipletests(output.loc[mask, p_col], alpha=0.10, method="fdr_bh")[1]

    Path("results").mkdir(exist_ok=True)
    output.to_csv("results/robustness_summary.csv", index=False)

    print("ROBUSTNESS ANALYSIS GENERATED")
    print(f"Schemes: {len(output)}")
    print(f"Bootstrap replications: {BOOTSTRAPS}")
    print(f"Block size: {BLOCK_SIZE}")
    print("Output: results/robustness_summary.csv")


if __name__ == "__main__":
    main()

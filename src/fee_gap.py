from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os


START_DATE = "2021-10-30"
END_DATE = "2026-10-30"
INITIAL_INVESTMENT = 100000


def main():
    load_dotenv(dotenv_path=".env")
    engine = create_engine(os.environ["DATABASE_URL"])

    try:
        with engine.connect() as conn:
            nav = pd.read_sql(
                text("""
                    SELECT
                        s.scheme_code,
                        s.pair_id,
                        s.plan,
                        v.nav_date,
                        v.nav
                    FROM v_ret v
                    JOIN dim_scheme s
                        ON s.scheme_code = v.scheme_code
                    WHERE v.nav_date BETWEEN :start_date AND :end_date
                      AND v.nav IS NOT NULL
                    ORDER BY s.pair_id, v.nav_date
                """),
                conn,
                params={
                    "start_date": START_DATE,
                    "end_date": END_DATE
                }
            )
    finally:
        engine.dispose()

    facts = pd.read_csv("data/manual/scheme_facts.csv")
    facts["ter_direct_pct"] = pd.to_numeric(
        facts["ter_direct_pct"], errors="coerce"
    )
    facts["ter_regular_pct"] = pd.to_numeric(
        facts["ter_regular_pct"], errors="coerce"
    )

    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    records = []

    for pair_id, group in nav.groupby("pair_id"):
        direct = group[group["plan"] == "Direct"][
            ["nav_date", "nav"]
        ].rename(columns={"nav": "nav_direct"})

        regular = group[group["plan"] == "Regular"][
            ["nav_date", "nav"]
        ].rename(columns={"nav": "nav_regular"})

        common = direct.merge(regular, on="nav_date", how="inner")
        common = common.sort_values("nav_date")

        if len(common) < 2:
            raise ValueError(f"Insufficient common NAV dates for pair {pair_id}")

        first = common.iloc[0]
        last = common.iloc[-1]

        elapsed_days = (last["nav_date"] - first["nav_date"]).days
        if elapsed_days <= 0:
            raise ValueError(f"Invalid date range for pair {pair_id}")

        direct_growth = last["nav_direct"] / first["nav_direct"]
        regular_growth = last["nav_regular"] / first["nav_regular"]

        direct_cagr = direct_growth ** (365.25 / elapsed_days) - 1
        regular_cagr = regular_growth ** (365.25 / elapsed_days) - 1

        gap_pp = (direct_cagr - regular_cagr) * 100

        rupee_gap = INITIAL_INVESTMENT * (
            direct_growth - regular_growth
        )

        records.append({
            "pair_id": int(pair_id),
            "direct_cagr": direct_cagr,
            "regular_cagr": regular_cagr,
            "gap_pp": gap_pp,
            "rupee_gap": rupee_gap,
            "common_nav_observations": len(common),
            "start_date": first["nav_date"],
            "end_date": last["nav_date"]
        })

    result = pd.DataFrame(records).merge(
        facts[[
            "pair_id", "amc", "scheme_base_name",
            "ter_direct_pct", "ter_regular_pct"
        ]],
        on="pair_id",
        how="left",
        validate="one_to_one"
    )

    if len(result) != 16:
        raise ValueError(f"Expected 16 fee-gap pairs, found {len(result)}")

    result["expected_pp"] = (
        result["ter_regular_pct"] - result["ter_direct_pct"]
    )

    result["residual_pp"] = result["gap_pp"] - result["expected_pp"]

    result["ter_status"] = np.where(
        result[["ter_direct_pct", "ter_regular_pct"]].notna().all(axis=1),
        "AVAILABLE",
        "PENDING"
    )

    result["provisional"] = True

    gaps = result["gap_pp"].dropna()

    if len(gaps) != 16:
        raise ValueError("Fee-gap calculation is incomplete.")

    if np.allclose(gaps, 0):
        wilcoxon_stat, wilcoxon_p = 0.0, 1.0
    else:
        test = wilcoxon(gaps, alternative="two-sided")
        wilcoxon_stat, wilcoxon_p = test.statistic, test.pvalue

    result["median_gap_pp"] = gaps.median()
    result["minimum_gap_pp"] = gaps.min()
    result["maximum_gap_pp"] = gaps.max()
    result["wilcoxon_statistic"] = wilcoxon_stat
    result["wilcoxon_p_value"] = wilcoxon_p

    Path("results").mkdir(exist_ok=True)
    result.to_csv("results/fee_gap.csv", index=False)

    print("FEE-GAP ANALYSIS GENERATED")
    print(f"Pairs: {len(result)}")
    print(f"Median gap (pp): {gaps.median():.6f}")
    print(f"Gap range (pp): {gaps.min():.6f} to {gaps.max():.6f}")
    print(f"Wilcoxon p-value: {wilcoxon_p:.6f}")
    print("TER reconciliation:", result["ter_status"].value_counts().to_dict())
    print("Output: results/fee_gap.csv")


if __name__ == "__main__":
    main()

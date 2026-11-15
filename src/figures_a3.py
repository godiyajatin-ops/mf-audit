from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

WINDOW = 252


def main():
    results = Path("results")
    results.mkdir(exist_ok=True)

    alpha = pd.read_csv(results / "alpha.csv")
    persistence = pd.read_csv(results / "persistence.csv")
    fee_gap = pd.read_csv(results / "fee_gap.csv")

    # 1. Alpha forest plot
    active = alpha[~alpha["is_passive"].astype(bool)].copy()
    active = active.sort_values("alpha_ann")

    fig, ax = plt.subplots(figsize=(11, 9))
    y = np.arange(len(active))

    ax.errorbar(
        active["alpha_ann"] * 100,
        y,
        xerr=[
            (active["alpha_ann"] - active["alpha_ci_lower"]) * 100,
            (active["alpha_ci_upper"] - active["alpha_ann"]) * 100
        ],
        fmt="o",
        capsize=3
    )

    ax.axvline(0, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(active["scheme_name"])
    ax.set_xlabel("Annualised estimated alpha (%)")
    ax.set_title("CAPM Alpha Estimates (Provisional)")
    fig.tight_layout()
    fig.savefig(results / "alpha_forest.png", dpi=180)
    plt.close(fig)

    # 2. Persistence scatter
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(
        persistence["alpha_first_half"] * 100,
        persistence["alpha_second_half"] * 100
    )
    ax.axhline(0, linestyle="--")
    ax.axvline(0, linestyle="--")
    ax.set_xlabel("First-half annualised alpha (%)")
    ax.set_ylabel("Second-half annualised alpha (%)")
    ax.set_title("Exploratory Alpha Persistence (Provisional)")
    fig.tight_layout()
    fig.savefig(results / "persistence_scatter.png", dpi=180)
    plt.close(fig)

    # 3. Direct-Regular fee gap
    fig, ax = plt.subplots(figsize=(10, 6))
    fee_gap = fee_gap.sort_values("gap_pp")
    ax.barh(
        fee_gap["scheme_base_name"],
        fee_gap["gap_pp"]
    )
    ax.axvline(0, linestyle="--")
    ax.set_xlabel("Direct minus Regular CAGR (percentage points)")
    ax.set_title("Direct-Regular Performance Gap (Provisional)")
    fig.tight_layout()
    fig.savefig(results / "fee_gap.png", dpi=180)
    plt.close(fig)

    # 4. Rolling beta for one fund per category plus one passive fund
    load_dotenv(dotenv_path=".env")
    engine = create_engine(os.environ["DATABASE_URL"])

    query = text("""
        SELECT
            s.scheme_code,
            s.scheme_name,
            s.category,
            s.is_passive,
            v.nav_date,
            v.aligned_fund_excess AS ex_p,
            v.benchmark_excess AS ex_b
        FROM v_ex v
        JOIN dim_scheme s ON s.scheme_code = v.scheme_code
        WHERE v.aligned_fund_excess IS NOT NULL
          AND v.benchmark_excess IS NOT NULL
        ORDER BY s.scheme_code, v.nav_date
    """)

    try:
        with engine.connect() as conn:
            data = pd.read_sql(query, conn)
    finally:
        engine.dispose()

    data["nav_date"] = pd.to_datetime(data["nav_date"])

    selected = (
        alpha[
            (~alpha["is_passive"].astype(bool))
            & alpha["category"].isin(
                ["Large Cap", "Flexi Cap", "Mid Cap"]
            )
        ]
        .sort_values("scheme_code")
        .groupby("category")
        .first()
    )

    passive = alpha[alpha["is_passive"].astype(bool)].sort_values(
        "scheme_code"
    )

    if len(passive):
        selected_codes = list(selected["scheme_code"]) + [
            int(passive.iloc[0]["scheme_code"])
        ]
    else:
        raise ValueError("No passive fund available for rolling beta.")

    rolling_records = []
    fig, ax = plt.subplots(figsize=(12, 6))

    for code in selected_codes:
        group = data[data["scheme_code"] == code].sort_values("nav_date")

        if len(group) < WINDOW:
            continue

        covariance = group["ex_p"].rolling(WINDOW).cov(group["ex_b"])
        variance = group["ex_b"].rolling(WINDOW).var()
        beta = covariance / variance

        label = group["scheme_name"].iloc[0]

        ax.plot(group["nav_date"], beta, label=label)

        rolling_records.extend([
            {
                "scheme_code": int(code),
                "nav_date": date,
                "rolling_beta_252d": value,
                "provisional": True
            }
            for date, value in zip(group["nav_date"], beta)
            if pd.notna(value)
        ])

    ax.axhline(1, linestyle="--")
    ax.set_ylabel("252-day rolling beta")
    ax.set_title("Rolling Beta (Provisional)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(results / "rolling_beta.png", dpi=180)
    plt.close(fig)

    pd.DataFrame(rolling_records).to_csv(
        results / "rolling_beta.csv",
        index=False
    )

    print("A3 FIGURES GENERATED")
    print("alpha_forest.png")
    print("persistence_scatter.png")
    print("fee_gap.png")
    print("rolling_beta.png")
    print("rolling_beta.csv")


if __name__ == "__main__":
    main()

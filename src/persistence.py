from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import statsmodels.api as sm

from src.regression import load_regression_data, nw_lag, ANNUALIZATION
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os


BOOTSTRAPS = 5000
SEED = 42


def estimate_alpha(group):
    group = group.dropna(subset=["ex_p", "ex_b"])

    if len(group) < 100:
        raise ValueError("Insufficient observations in persistence half.")

    model = sm.OLS(
        group["ex_p"],
        sm.add_constant(group["ex_b"])
    ).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": nw_lag(len(group))}
    )

    return model.params["const"] * ANNUALIZATION


def main():
    load_dotenv(dotenv_path=".env")
    engine = create_engine(os.environ["DATABASE_URL"])

    try:
        with engine.connect() as conn:
            data = load_regression_data(conn)
    finally:
        engine.dispose()

    data["nav_date"] = pd.to_datetime(data["nav_date"])
    midpoint = data["nav_date"].median()

    active_direct = data[
        (~data["is_passive"].astype(bool))
        & (data["plan"] == "Direct")
    ]

    records = []

    for scheme_code, group in active_direct.groupby("scheme_code"):
        first_half = group[group["nav_date"] <= midpoint]
        second_half = group[group["nav_date"] > midpoint]

        records.append({
            "scheme_code": int(scheme_code),
            "scheme_name": group["scheme_name"].iloc[0],
            "alpha_first_half": estimate_alpha(first_half),
            "alpha_second_half": estimate_alpha(second_half)
        })

    result = pd.DataFrame(records)

    if len(result) != 12:
        raise ValueError(
            f"Expected 12 active Direct funds, found {len(result)}"
        )

    rho, p_value = spearmanr(
        result["alpha_first_half"],
        result["alpha_second_half"]
    )

    rng = np.random.default_rng(SEED)
    boot_rhos = []

    for _ in range(BOOTSTRAPS):
        sample = result.iloc[
            rng.integers(0, len(result), len(result))
        ]

        if (
            sample["alpha_first_half"].nunique() < 2
            or sample["alpha_second_half"].nunique() < 2
        ):
            continue

        boot_rhos.append(
            spearmanr(
                sample["alpha_first_half"],
                sample["alpha_second_half"]
            ).statistic
        )

    if not boot_rhos:
        raise RuntimeError("Persistence bootstrap produced no valid samples.")

    lower, upper = np.percentile(boot_rhos, [2.5, 97.5])

    result["rho"] = rho
    result["p_value"] = p_value
    result["bootstrap_ci_lower"] = lower
    result["bootstrap_ci_upper"] = upper
    result["bootstrap_valid_samples"] = len(boot_rhos)
    result["exploratory"] = True
    result["provisional"] = True

    Path("results").mkdir(exist_ok=True)
    result.to_csv("results/persistence.csv", index=False)

    print("PERSISTENCE ANALYSIS GENERATED")
    print(f"Spearman rho: {rho:.6f}")
    print(f"p-value: {p_value:.6f}")
    print(f"Bootstrap 95% CI: [{lower:.6f}, {upper:.6f}]")
    print(f"Valid bootstrap samples: {len(boot_rhos)}")


if __name__ == "__main__":
    main()

from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests


Q = 0.10


def manual_bh(p_values, q=Q):
    p = np.asarray(p_values, dtype=float)
    n = len(p)

    order = np.argsort(p)
    ranked = p[order]

    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0, 1)

    result = np.empty(n)
    result[order] = adjusted

    significant = result <= q
    return result, significant


def apply_family(df, plan):
    mask = (
        (df["plan"] == plan)
        & (~df["is_passive"].astype(bool))
    )

    indices = df.index[mask]
    p_values = df.loc[indices, "p_value"].to_numpy(dtype=float)

    if len(p_values) != 12:
        raise ValueError(
            f"Expected 12 active {plan} schemes, found {len(p_values)}"
        )

    statsmodels_reject, statsmodels_adjusted, _, _ = multipletests(
        p_values,
        alpha=Q,
        method="fdr_bh"
    )

    manual_adjusted, manual_reject = manual_bh(p_values)

    if not np.allclose(statsmodels_adjusted, manual_adjusted, atol=1e-12):
        raise AssertionError(f"Manual BH mismatch for {plan}")

    if not np.array_equal(statsmodels_reject, manual_reject):
        raise AssertionError(f"BH significance mismatch for {plan}")

    df.loc[indices, "p_bh"] = statsmodels_adjusted
    df.loc[indices, "significant_bh"] = statsmodels_reject


def main():
    path = Path("results/alpha.csv")
    if not path.exists():
        raise FileNotFoundError("Run regression.py before fdr.py")

    df = pd.read_csv(path)

    df["p_bh"] = np.nan
    df["significant_bh"] = False

    apply_family(df, "Direct")
    apply_family(df, "Regular")

    df["fdr_q"] = np.where(
        df["is_passive"].astype(bool),
        np.nan,
        Q
    )

    df.to_csv(path, index=False)

    print("BH-FDR CORRECTION COMPLETED")
    print("Active Direct family:", 12)
    print("Active Regular family:", 12)
    print("Passive schemes excluded:", int(df["is_passive"].sum()))
    print("FDR threshold:", Q)


if __name__ == "__main__":
    main()

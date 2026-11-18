"""Stage B2 scheme-level mandate audit using preregistered thresholds."""
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main():
    alpha = pd.read_csv(RESULTS / "alpha.csv")
    metrics = pd.read_csv(RESULTS / "metrics.csv")
    fees = pd.read_csv(RESULTS / "fee_gap.csv")
    facts = pd.read_csv(ROOT / "data/manual/scheme_facts.csv")
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

    audit = alpha.merge(
        metrics[["scheme_code", "max_dd", "te_ann"]],
        on="scheme_code",
        how="left",
        validate="one_to_one",
    ).merge(
        fees[["pair_id", "expected_pp", "gap_pp", "residual_pp"]],
        on="pair_id",
        how="left",
        validate="many_to_one",
    ).merge(
        facts,
        on="pair_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_facts"),
    )

    if audit["pair_id"].nunique() != 16:
        raise ValueError("Expected exactly 16 underlying scheme pairs.")

    if len(audit) != 32:
        raise ValueError(f"Expected 32 plan rows, found {len(audit)}.")

    active_direct = (
        (~audit["is_passive"].astype(bool))
        & audit["plan"].eq("Direct")
    )
    passive_direct = (
        audit["is_passive"].astype(bool)
        & audit["plan"].eq("Direct")
    )

    r2_min = float(cfg["audit"]["r2_min"])
    peer_sd = float(cfg["audit"]["peer_sd"])
    cost_tol = float(cfg["audit"]["cost_tol_pp"])
    te_max = float(cfg["audit"]["passive_te_max"])

    # Initialize rule results.
    audit["R1_benchmark_fit"] = "N/A"
    audit["R2_peer_risk"] = "N/A"
    audit["R3_cost_fit"] = "UNAVAILABLE"
    audit["R4_passive_fit"] = "N/A"
    audit["R5_closet_indexer_screen"] = "N/A"
    audit["R5_provisional_proxy_heuristic"] = "N/A"

    audit["R2_beta_z"] = np.nan
    audit["R2_max_dd_z"] = np.nan
    audit["R3_abs_residual_pp"] = audit["residual_pp"].abs()
    audit["R4_tracking_error_pct"] = audit["te_ann"] * 100
    audit["R5_unavailable_reason"] = ""

    # R1: benchmark fit. Missing R-squared is unavailable, not CLEAR.
    valid_r1 = active_direct & audit["r2"].notna()
    missing_r1 = active_direct & audit["r2"].isna()

    audit.loc[missing_r1, "R1_benchmark_fit"] = "UNAVAILABLE"
    audit.loc[valid_r1, "R1_benchmark_fit"] = np.where(
        audit.loc[valid_r1, "r2"] < r2_min,
        "FLAG",
        "CLEAR",
    )

    # R2: peer-risk screen among active Direct funds.
    for category, ix in audit.loc[active_direct].groupby("category").groups.items():
        for metric, dest in (
            ("beta", "R2_beta_z"),
            ("max_dd", "R2_max_dd_z"),
        ):
            values = pd.to_numeric(audit.loc[ix, metric], errors="coerce")
            sd = values.std(ddof=0)

            if pd.notna(sd) and sd > 0:
                audit.loc[ix, dest] = (values - values.mean()) / sd

        z = audit.loc[ix, ["R2_beta_z", "R2_max_dd_z"]].abs()
        has_data = z.notna().any(axis=1)
        flagged = z.gt(peer_sd).any(axis=1)

        audit.loc[ix[~has_data], "R2_peer_risk"] = "UNAVAILABLE"
        audit.loc[ix[has_data & ~flagged], "R2_peer_risk"] = "CLEAR"
        audit.loc[ix[flagged], "R2_peer_risk"] = "FLAG"

    # R3: paired Direct/Regular cost-fit comparison.
    available_cost = audit["residual_pp"].notna()
    audit.loc[available_cost, "R3_cost_fit"] = np.where(
        audit.loc[available_cost, "residual_pp"].abs() > cost_tol,
        "FLAG",
        "CLEAR",
    )

    # R4: passive tracking-error screen, evaluated on Direct plan only.
    valid_r4 = passive_direct & audit["te_ann"].notna()
    missing_r4 = passive_direct & audit["te_ann"].isna()

    audit.loc[missing_r4, "R4_passive_fit"] = "UNAVAILABLE"
    audit.loc[valid_r4, "R4_passive_fit"] = np.where(
        audit.loc[valid_r4, "te_ann"] > te_max,
        "FLAG",
        "CLEAR",
    )

    # R5: formal calibrated thresholds q_r2 and q_te are not yet configured.
    # Keep the former heuristic separately, without presenting it as calibrated.
    audit.loc[active_direct, "R5_closet_indexer_screen"] = "UNAVAILABLE"
    audit.loc[active_direct, "R5_unavailable_reason"] = (
        "Passive-control calibration thresholds q_r2 and q_te "
        "are not yet configured."
    )

    valid_r5_proxy = (
        active_direct
        & audit["r2"].notna()
        & audit["te_ann"].notna()
    )

    audit.loc[valid_r5_proxy, "R5_provisional_proxy_heuristic"] = np.where(
        (audit.loc[valid_r5_proxy, "r2"] >= r2_min)
        & (audit.loc[valid_r5_proxy, "te_ann"] <= te_max),
        "FLAG",
        "CLEAR",
    )

    audit["provisional"] = True

    # Preserve all 32 plan-level rows for traceability.
    detail = audit.sort_values(["pair_id", "plan"]).copy()
    detail.to_csv(
        RESULTS / "mandate_audit_plan_detail.csv",
        index=False,
    )

    # Scheme-level audit: one Direct representative row per underlying scheme.
    # Paired TER and return-gap analysis remains attached through R3 and facts.
    out = audit.loc[audit["plan"].eq("Direct")].copy()

    if len(out) != 16 or out["pair_id"].nunique() != 16:
        raise ValueError("Scheme-level audit must contain exactly 16 unique schemes.")

    out = out.rename(columns={"plan": "representative_plan"})
    out = out.sort_values("pair_id")

    out.to_csv(RESULTS / "mandate_audit.csv", index=False)

    print("Scheme-level audit:", len(out), "rows")
    print("Unique schemes:", out["scheme_code"].nunique())
    print("Underlying pairs:", out["pair_id"].nunique())
    print("Plan-level detail:", len(detail), "rows")

    for rule in (
        "R1_benchmark_fit",
        "R2_peer_risk",
        "R3_cost_fit",
        "R4_passive_fit",
        "R5_closet_indexer_screen",
        "R5_provisional_proxy_heuristic",
    ):
        print(rule, out[rule].value_counts(dropna=False).to_dict())

    print("Output: results/mandate_audit.csv")
    print("Output: results/mandate_audit_plan_detail.csv")


if __name__ == "__main__":
    main()

"""Stage A3 rule-based mandate audit using preregistered thresholds."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

def main():
    alpha = pd.read_csv(RESULTS / "alpha.csv")
    metrics = pd.read_csv(RESULTS / "metrics.csv")
    fees = pd.read_csv(RESULTS / "fee_gap.csv")
    facts = pd.read_csv(ROOT / "data/manual/scheme_facts.csv")
    cfg = __import__("yaml").safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    audit = alpha.merge(
        metrics[["scheme_code", "max_dd", "te_ann"]],
        on="scheme_code", how="left", validate="one_to_one"
    ).merge(
        fees[["pair_id", "expected_pp", "gap_pp", "residual_pp"]],
        on="pair_id", how="left", validate="many_to_one"
    )
    active_direct = (~audit["is_passive"].astype(bool)) & (audit["plan"] == "Direct")
    passive = audit["is_passive"].astype(bool)
    audit["R1_benchmark_fit"] = "N/A"
    audit["R2_peer_risk"] = "N/A"
    audit["R3_cost_fit"] = np.where(audit["residual_pp"].notna(), "CLEAR", "UNAVAILABLE")
    audit["R4_passive_fit"] = "N/A"
    audit["R5_closet_indexer_screen"] = "N/A"
    audit["R2_beta_z"] = np.nan
    audit["R2_max_dd_z"] = np.nan
    audit["R3_abs_residual_pp"] = audit["residual_pp"].abs()
    audit["R4_tracking_error_pct"] = audit["te_ann"] * 100

    r2_min = float(cfg["audit"]["r2_min"])
    peer_sd = float(cfg["audit"]["peer_sd"])
    cost_tol = float(cfg["audit"]["cost_tol_pp"])
    te_max = float(cfg["audit"]["passive_te_max"])

    audit.loc[active_direct, "R1_benchmark_fit"] = np.where(
        audit.loc[active_direct, "r2"] < r2_min, "FLAG", "CLEAR"
    )
    audit.loc[passive, "R4_passive_fit"] = np.where(
        audit.loc[passive, "te_ann"].isna(), "UNAVAILABLE",
        np.where(audit.loc[passive, "te_ann"] > te_max, "FLAG", "CLEAR")
    )
    audit.loc[active_direct, "R5_closet_indexer_screen"] = np.where(
        (audit.loc[active_direct, "r2"] >= r2_min)
        & (audit.loc[active_direct, "te_ann"] <= te_max), "FLAG", "CLEAR"
    )
    available_cost = audit["residual_pp"].notna()
    audit.loc[available_cost, "R3_cost_fit"] = np.where(
        audit.loc[available_cost, "residual_pp"].abs() > cost_tol, "FLAG", "CLEAR"
    )

    # Peer-risk screen uses the 12 active Direct funds: four same-category peers.
    for category, ix in audit.loc[active_direct].groupby("category").groups.items():
        for metric, dest in (("beta", "R2_beta_z"), ("max_dd", "R2_max_dd_z")):
            values = audit.loc[ix, metric].astype(float)
            # The preregistered frozen set is the full comparison universe, so use population SD.
            sd = values.std(ddof=0)
            if pd.notna(sd) and sd > 0:
                audit.loc[ix, dest] = (values - values.mean()) / sd
        z = audit.loc[ix, ["R2_beta_z", "R2_max_dd_z"]].abs()
        audit.loc[ix, "R2_peer_risk"] = np.where(
            z.gt(peer_sd).any(axis=1), "FLAG", "CLEAR"
        )

    audit["provisional"] = True
    columns = [
        "scheme_code", "scheme_name", "amc", "category", "plan", "pair_id",
        "is_passive", "benchmark_name", "benchmark_confirmed", "r2", "beta",
        "max_dd", "te_ann", "R1_benchmark_fit", "R2_peer_risk", "R2_beta_z",
        "R2_max_dd_z", "gap_pp", "expected_pp", "residual_pp",
        "R3_abs_residual_pp", "R3_cost_fit", "R4_tracking_error_pct",
        "R4_passive_fit", "R5_closet_indexer_screen", "provisional"
    ]
    out = audit[columns].sort_values(["pair_id", "plan"])
    out.to_csv(RESULTS / "mandate_audit.csv", index=False)
    for rule in ("R1_benchmark_fit", "R2_peer_risk", "R3_cost_fit", "R4_passive_fit", "R5_closet_indexer_screen"):
        print(rule, out[rule].value_counts(dropna=False).to_dict())
    print("Output: results/mandate_audit.csv")

if __name__ == "__main__":
    main()

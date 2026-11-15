from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "dashboard" / "data"


def read_result(name: str) -> pd.DataFrame:
    path = RESULTS / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def save(frame: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / name, index=False, encoding="utf-8", date_format="%Y-%m-%d")


def short_names(dim: pd.DataFrame) -> pd.Series:
    amc_short = {
        "HDFC Mutual Fund": "HDFC",
        "ICICI Prudential Mutual Fund": "ICICI",
        "SBI Mutual Fund": "SBI",
        "Nippon India Mutual Fund": "Nippon",
        "Kotak Mahindra Mutual Fund": "Kotak",
    }
    made: list[str] = []
    for row in dim.itertuples(index=False):
        brand = amc_short.get(row.amc, str(row.amc).split()[0])
        suffix = "D" if row.plan == "Direct" else "R"
        if row.category == "Index":
            instrument = "Next50" if "Next 50" in row.scheme_name else "Nifty50"
            base = f"{brand} {instrument} {suffix}"
        else:
            base = f"{brand} {row.category} {suffix}"
        if len(base) > 28:
            base = base[:26].rstrip() + f" {suffix}"
        made.append(base)
    out = pd.Series(made, index=dim.index, dtype="string")
    if out.duplicated().any():
        for ix in out[out.duplicated(keep=False)].index:
            row = dim.loc[ix]
            code = "".join(part[0] for part in str(row.amc).replace("Mutual Fund", "").split())
            suffix = "D" if row.plan == "Direct" else "R"
            out.loc[ix] = f"{out.loc[ix][:22].rstrip()} {code} {suffix}"[:28]
    if out.duplicated().any() or out.str.len().gt(28).any():
        raise ValueError("short_name is not unique or exceeds 28 characters")
    return out


def main() -> None:
    manifest_path = RESULTS / "MANIFEST.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("stage") != "A3" or not str(manifest.get("status", "")).startswith("COMPLETE"):
        raise RuntimeError("Stage A3 manifest is not complete")

    alpha_src = read_result("alpha.csv")
    metrics_src = read_result("metrics.csv")
    metrics_windows = read_result("metrics_by_window.csv")
    fee_src = read_result("fee_gap.csv")
    control_src = read_result("control_check.csv")
    rolling_beta_src = read_result("rolling_beta.csv")
    universe = pd.read_csv(ROOT / "config" / "universe.csv")
    benchmark_actual = pd.read_parquet(PROCESSED / "benchmark_tri_long.parquet")
    benchmark_hybrid_path = PROCESSED / "bse_hybrid_tri_long.parquet"
    benchmark_basis: dict[int, str] = {
        int(code): "actual_tri" for code in benchmark_actual["benchmark_id"].unique()
    }
    if benchmark_hybrid_path.exists():
        hybrid_source = pd.read_parquet(benchmark_hybrid_path)
        benchmark_basis.update({
            int(code): "estimated_hybrid"
            for code in hybrid_source["benchmark_id"].unique()
        })
    if universe["benchmark_id"].isna().any() if "benchmark_id" in universe.columns else False:
        raise ValueError("Universe has missing benchmark ids")

    metric_keys = metrics_src[["scheme_code", "option", "benchmark_id", "benchmark_confirmed"]]
    dim = universe.merge(metric_keys, on="scheme_code", how="left", validate="one_to_one")
    alpha_meta_cols = [c for c in ["scheme_code", "benchmark_name"] if c in alpha_src.columns]
    if alpha_meta_cols:
        dim = dim.merge(alpha_src[alpha_meta_cols].drop_duplicates("scheme_code"), on="scheme_code", how="left", validate="one_to_one")
    fee_meta = fee_src[["pair_id", "ter_direct_pct", "ter_regular_pct"]].drop_duplicates("pair_id")
    dim = dim.merge(fee_meta, on="pair_id", how="left", validate="many_to_one")
    dim["benchmark_basis"] = dim["benchmark_id"].map(benchmark_basis)
    if dim["benchmark_basis"].isna().any():
        raise ValueError("A scheme benchmark id has no source basis")
    dim["provisional"] = dim["benchmark_basis"].eq("estimated_hybrid")
    dim["caveat_flag"] = True
    dim["ter_as_of"] = "2026-09-30"
    dim["short_name"] = short_names(dim)
    code_meta = dim.set_index("scheme_code")[["provisional", "caveat_flag", "group", "short_name"]]
    provisional_by_pair = dim.groupby("pair_id")["provisional"].any()

    alpha = alpha_src.merge(dim[["scheme_code", "group", "short_name", "benchmark_basis"]], on="scheme_code", how="left", validate="one_to_one")
    alpha["provisional"] = alpha["benchmark_basis"].eq("estimated_hybrid")
    alpha["caveat_flag"] = True

    metrics = metrics_windows.merge(dim[["scheme_code", "group", "short_name", "benchmark_basis"]], on="scheme_code", how="left", validate="many_to_one")
    metrics["provisional"] = metrics["benchmark_basis"].eq("estimated_hybrid")
    metrics["caveat_flag"] = True

    pair_meta = dim.groupby("pair_id", as_index=False).agg(category=("category", "first"), amc=("amc", "first"))
    fee_gap = fee_src.merge(pair_meta, on="pair_id", how="left", validate="one_to_one", suffixes=("", "_dim"))
    fee_gap["provisional"] = fee_gap["pair_id"].map(provisional_by_pair).fillna(False).astype(bool)
    fee_gap["caveat_flag"] = True
    control = control_src.merge(dim[["scheme_code", "group", "short_name", "benchmark_basis"]], on="scheme_code", how="left", validate="one_to_one")
    control["provisional"] = control["benchmark_basis"].eq("estimated_hybrid")
    control["caveat_flag"] = True

    metric_meta = metrics_src[["scheme_code", "scheme_name", "benchmark_id", "start_date", "end_date", "up_capture", "down_capture", "te_ann", "benchmark_confirmed"]].copy()
    capture = metric_meta.merge(dim[["scheme_code", "group", "short_name", "benchmark_basis"]], on="scheme_code", how="left", validate="one_to_one")
    capture["provisional"] = capture["benchmark_basis"].eq("estimated_hybrid")
    capture["caveat_flag"] = True

    nav = pd.read_parquet(PROCESSED / "nav_long.parquet")
    nav["scheme_code"] = nav["scheme_code"].astype(int)
    nav = nav[nav["scheme_code"].isin(set(dim["scheme_code"].astype(int)))].copy()
    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    nav = nav.sort_values(["scheme_code", "nav_date"])
    nav["rolling_return_252d"] = nav.groupby("scheme_code")["nav"].transform(lambda s: s / s.shift(252) - 1)
    rolling_returns = nav.dropna(subset=["rolling_return_252d"])[["scheme_code", "nav_date", "rolling_return_252d"]].copy()
    rolling_returns["provisional"] = rolling_returns["scheme_code"].map(code_meta["provisional"]).astype(bool)
    rolling_returns["caveat_flag"] = True

    actual = benchmark_actual.rename(columns={"tri_date": "date", "tri": "benchmark_level"}).copy()
    actual["date"] = pd.to_datetime(actual["date"])
    actual["series_basis"] = "actual_tri"
    actual["provisional"] = False
    if benchmark_hybrid_path.exists():
        hybrid = pd.read_parquet(benchmark_hybrid_path).rename(columns={"tri_date": "date", "tri": "benchmark_level"}).copy()
        hybrid["date"] = pd.to_datetime(hybrid["date"])
        hybrid["series_basis"] = "estimated_hybrid"
        hybrid["provisional"] = True
        benchmark_levels = pd.concat([actual, hybrid[actual.columns]], ignore_index=True)
    else:
        benchmark_levels = actual
    benchmark_levels = benchmark_levels.sort_values(["benchmark_id", "date"])

    scheme_bench = dim[["scheme_code", "benchmark_id"]]
    aligned = nav.merge(scheme_bench, on="scheme_code", how="inner", validate="many_to_one")
    aligned = aligned.merge(
        benchmark_levels[["benchmark_id", "date", "benchmark_level"]],
        left_on=["benchmark_id", "nav_date"], right_on=["benchmark_id", "date"],
        how="inner", validate="many_to_one"
    ).sort_values(["scheme_code", "nav_date"])
    aligned["rolling_return_3y"] = aligned.groupby("scheme_code")["nav"].transform(lambda s: s / s.shift(756) - 1)
    aligned["benchmark_return_3y"] = aligned.groupby("scheme_code")["benchmark_level"].transform(lambda s: s / s.shift(756) - 1)
    aligned_3y = aligned[["scheme_code", "nav_date", "rolling_return_3y", "benchmark_return_3y"]]
    rolling_returns = rolling_returns.merge(aligned_3y, on=["scheme_code", "nav_date"], how="left", validate="one_to_one")
    nav["running_peak"] = nav.groupby("scheme_code")["nav"].cummax()
    drawdown = nav.assign(drawdown=nav["nav"] / nav["running_peak"] - 1)[["scheme_code", "nav_date", "drawdown"]]
    drawdown = drawdown.merge(rolling_returns[["scheme_code", "nav_date"]], on=["scheme_code", "nav_date"], how="inner", validate="one_to_one")
    drawdown["provisional"] = drawdown["scheme_code"].map(code_meta["provisional"]).astype(bool)
    drawdown["caveat_flag"] = True

    beta = rolling_beta_src.rename(columns={"rolling_beta_252d": "beta_252"}).copy()
    beta["scheme_code"] = beta["scheme_code"].astype(int)
    beta["nav_date"] = pd.to_datetime(beta["nav_date"])
    beta["provisional"] = beta["scheme_code"].map(code_meta["provisional"]).astype(bool)
    beta["caveat_flag"] = True
    beta = beta.dropna(subset=["beta_252"]).sort_values(["scheme_code", "nav_date"])

    glossary = pd.DataFrame([
        ("CAGR", "Compound annual growth rate", "Annualized growth rate over the selected period."),
        ("Sharpe", "Sharpe ratio", "Return above the assumed risk-free rate divided by volatility."),
        ("Sortino", "Sortino ratio", "Return above the risk-free rate scaled by downside volatility."),
        ("max_dd", "Maximum drawdown", "Largest decline from a prior running peak during the period."),
        ("alpha_ann", "Annualized alpha", "Annualized CAPM intercept relative to the assigned benchmark."),
        ("beta_252", "252-observation rolling beta", "Trailing covariance with the benchmark divided by benchmark variance."),
        ("te_ann", "Tracking error", "Annualized volatility of active returns versus the assigned benchmark."),
        ("capture", "Capture ratio", "Fund participation in benchmark up or down periods."),
        ("TER", "Total expense ratio", "Annual expense ratio; the supplied TER is a 30-Sep-2026 snapshot."),
        ("plan", "Direct vs Regular", "Direct and Regular are separate plans of the same scheme pair."),
        ("FDR/BH", "Benjamini-Hochberg correction", "Adjusts p-values for the preregistered multiple-testing family at q=0.10."),
    ], columns=["field", "label", "definition"])

    outputs = {
        "dim_scheme.csv": dim,
        "metrics.csv": metrics,
        "alpha.csv": alpha,
        "fee_gap.csv": fee_gap,
        "control_check.csv": control,
        "rolling_returns.csv": rolling_returns,
        "drawdown.csv": drawdown,
        "capture.csv": capture,
        "rolling_beta.csv": beta,
        "benchmark_levels.csv": benchmark_levels,
        "glossary.csv": glossary,
    }
    for name, frame in outputs.items():
        save(frame, name)
    total = sum((OUT / name).stat().st_size for name in outputs)
    if len(outputs) != 11 or total >= 25 * 1024 * 1024:
        raise ValueError("Output file count or size gate failed")

    bwide = beta.pivot(index="nav_date", columns="scheme_code", values="beta_252")
    beta_changes = bwide.diff().abs().stack()
    max_beta_change = float(beta_changes.max()) if not beta_changes.empty else 0.0
    direct = alpha[(alpha["plan"] == "Direct") & (~alpha["is_passive"].astype(bool))]
    k = int(direct["significant_bh"].fillna(False).astype(bool).sum())
    m = int((fee_gap["residual_pp"] > 0).sum())
    passive = control
    p = int((passive["deviation_pp"].abs() <= 0.2).sum())
    n = len(direct)
    print(f"files={len(outputs)} total_MB={total / 1_000_000:.3f}")
    print(f"rows=alpha:{len(alpha)} fee_gap:{len(fee_gap)} control_check:{len(control)} glossary:{len(glossary)}")
    print(f"provisional_rule=benchmark_basis == estimated_hybrid ({int(dim['provisional'].sum())}/{len(dim)})")
    print(f"beta_max_daily_change={max_beta_change:.6f} beta_rows={len(beta)} beta_schemes={beta['scheme_code'].nunique()}")
    print(f"TITLE_SCORECARD={k} of {n} active Direct funds show alpha significant at 10% FDR")
    print(f"TITLE_COST_AUDIT=Realised Direct-Regular gap exceeds expected TER gap in {m} of 16 pairs")
    if p == len(passive):
        print(f"TITLE_PASSIVE=All {p} passive funds' alpha is within 0.2 pp of expectation")
    else:
        print(f"TITLE_PASSIVE={p} of {len(passive)} passive funds' alpha is within 0.2 pp of expectation")


if __name__ == "__main__":
    main()

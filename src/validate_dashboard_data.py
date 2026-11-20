from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dashboard" / "data"
PROCESSED = ROOT / "data" / "processed"
CONTRACT = ROOT / "dashboard" / "DATA_CONTRACT.md"

SCHEMA = {
    "dim_scheme.csv": {
        "grain": "One row per scheme plan (scheme_code)",
        "key": ["scheme_code"],
        "required": ["scheme_code", "pair_id", "scheme_name", "short_name", "amc", "category", "plan", "group", "benchmark_id", "benchmark_basis", "provisional", "caveat_flag"],
    },
    "metrics.csv": {
        "grain": "One row per scheme plan and window_label",
        "key": ["scheme_code", "window_label"],
        "required": ["scheme_code", "window_label", "cagr", "vol_ann", "sharpe", "sortino", "max_dd", "start_date", "end_date", "provisional", "caveat_flag"],
    },
    "alpha.csv": {
        "grain": "One row per scheme plan",
        "key": ["scheme_code"],
        "required": ["scheme_code", "plan", "group", "alpha_ann", "p_bh", "significant_bh", "provisional", "caveat_flag"],
    },
    "fee_gap.csv": {
        "grain": "One row per Direct-Regular pair",
        "key": ["pair_id"],
        "required": ["pair_id", "scheme_base_name", "category", "amc", "gap_pp", "expected_pp", "residual_pp", "rupee_gap", "provisional", "caveat_flag"],
    },
    "control_check.csv": {
        "grain": "One row per passive scheme plan",
        "key": ["scheme_code"],
        "required": ["scheme_code", "alpha_ann", "expected_alpha_ann", "deviation_pp", "control_status", "provisional", "caveat_flag"],
    },
    "rolling_returns.csv": {
        "grain": "One row per scheme plan and NAV date after 252 observed NAVs",
        "key": ["scheme_code", "nav_date"],
        "required": ["scheme_code", "nav_date", "rolling_return_252d", "rolling_return_3y", "benchmark_return_3y", "provisional", "caveat_flag"],
    },
    "drawdown.csv": {
        "grain": "One row per scheme plan and NAV date on the rolling-return date spine",
        "key": ["scheme_code", "nav_date"],
        "required": ["scheme_code", "nav_date", "drawdown", "provisional", "caveat_flag"],
    },
    "capture.csv": {
        "grain": "One row per scheme plan (full research window)",
        "key": ["scheme_code"],
        "required": ["scheme_code", "up_capture", "down_capture", "te_ann", "provisional", "caveat_flag"],
    },
    "rolling_beta.csv": {
        "grain": "One row per selected scheme and NAV date with a valid 252-observation beta",
        "key": ["scheme_code", "nav_date"],
        "required": ["scheme_code", "nav_date", "beta_252", "provisional", "caveat_flag"],
    },
    "benchmark_levels.csv": {
        "grain": "One row per benchmark and date",
        "key": ["benchmark_id", "date"],
        "required": ["benchmark_id", "benchmark_name", "date", "benchmark_level", "series_basis", "provisional"],
    },
    "glossary.csv": {
        "grain": "One row per glossary term",
        "key": ["field"],
        "required": ["field", "label", "definition"],
    },

    "mandate_audit.csv": {
        "grain": "One row per scheme-level mandate audit",
        "key": ["scheme_code"],
        "required": [
            "scheme_code", "scheme_name", "amc", "category",
            "representative_plan", "benchmark_name", "benchmark_confirmed",
            "provisional", "is_passive", "r2", "beta", "max_dd",
            "te_ann", "ter_direct_pct", "ter_regular_pct",
            "objective_evidence_status", "objective_source_doc_id",
            "objective_source_page", "R1_benchmark_fit", "R2_peer_risk",
            "R3_cost_fit", "R4_passive_fit",
            "R5_closet_indexer_screen",
            "R5_provisional_proxy_heuristic",
        ],
    },
}
DATE_COLS = {"nav_date", "date", "start_date", "end_date", "max_dd_start", "max_dd_end"}
NUMERIC_COLS = {
    "pair_id", "scheme_code", "benchmark_id", "cagr", "vol_ann",
    "sharpe", "sortino", "max_dd", "alpha_ann", "p_bh", "gap_pp",
    "expected_pp", "residual_pp", "rupee_gap", "deviation_pp",
    "expected_alpha_ann", "rolling_return_252d", "rolling_return_3y",
    "benchmark_return_3y", "drawdown", "up_capture", "down_capture",
    "beta_252", "benchmark_level", "te_ann", "info_ratio",
    "tracking_error", "n_obs", "r2", "beta", "fdr_q",
    "control_band_pp", "ter_direct_pct", "ter_regular_pct", "nw_lag",
    "p_value", "se_alpha_ann", "alpha_ci_lower", "alpha_ci_upper",
    "minimum_gap_pp", "maximum_gap_pp", "median_gap_pp",
    "wilcoxon_p_value", "wilcoxon_statistic", "alignment_pct",
    "rolling_beta_252d", "se_beta", "R2_beta_z", "R2_max_dd_z",
    "R3_abs_residual_pp", "R4_tracking_error_pct",
    "objective_source_doc_id", "objective_source_page", "source_page",
    "ter_direct_source_row", "ter_regular_source_row",
    "ber_direct_pct", "ber_regular_pct"
}
BOOL_COLS = {"is_passive", "is_passive_facts", "benchmark_confirmed", "provisional", "caveat_flag", "significant_bh"}
DESCRIPTIONS = {
    "scheme_code": "Stable scheme-plan key.", "pair_id": "Identifier shared by the Direct and Regular plans.",
    "short_name": "Unique plan-aware display name, no more than 28 characters.",
    "group": "Approved research grouping.", "plan": "Direct or Regular plan.",
    "provisional": "True only when the assigned benchmark basis is estimated_hybrid.",
    "caveat_flag": "General Stage A3 caveat applies; this is separate from estimated-benchmark status.",
    "benchmark_basis": "Source basis for the assigned benchmark series.",
    "alpha_ann": "Annualized CAPM alpha as a decimal.", "p_bh": "Benjamini-Hochberg adjusted p-value.",
    "cagr": "Compound annual growth rate as a decimal.", "vol_ann": "Annualized volatility as a decimal.",
    "max_dd": "Maximum drawdown as a decimal.", "drawdown": "NAV divided by running peak minus one.",
    "rolling_return_252d": "Trailing return across 252 observed NAV records.",
    "rolling_return_3y": "Fund return across the trailing 756 common NAV/benchmark observations.",
    "benchmark_return_3y": "Assigned benchmark TRI return across the same trailing 756 common observations.",
    "beta_252": "Rolling beta over 252 valid paired excess-return observations.",
    "gap_pp": "Realized Direct-Regular CAGR gap in percentage points.",
    "expected_pp": "Expected TER gap in percentage points.", "residual_pp": "Realized gap less expected TER gap in percentage points.",
    "rupee_gap": "Rupee impact as defined by the approved Stage A3 fee-gap calculation.",
    "benchmark_level": "Benchmark total-return index level.", "series_basis": "Actual TRI or estimated hybrid basis.",
}
NULL_SEMANTICS = {
    ("alpha.csv", "p_bh"): "No BH family p-value is assigned to passive funds.",
    ("alpha.csv", "fdr_q"): "No BH family q-value is assigned to passive funds.",
    ("metrics.csv", "te_ann"): "Benchmark-relative metric unavailable for estimated-hybrid schemes in the frozen A3 results.",
    ("metrics.csv", "info_ratio"): "Benchmark-relative metric unavailable for estimated-hybrid schemes in the frozen A3 results.",
    ("metrics.csv", "up_capture"): "Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results.",
    ("metrics.csv", "down_capture"): "Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results.",
    ("capture.csv", "up_capture"): "Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results.",
    ("capture.csv", "down_capture"): "Capture metric unavailable for estimated-hybrid schemes in the frozen A3 results.",
    ("capture.csv", "te_ann"): "Tracking error unavailable for estimated-hybrid schemes in the frozen A3 results.",
    ("rolling_returns.csv", "rolling_return_3y"): "Blank until 756 common scheme/benchmark observations exist.",
    ("rolling_returns.csv", "benchmark_return_3y"): "Blank until 756 common scheme/benchmark observations exist.",

    ("mandate_audit.csv", "p_bh"): "No BH family p-value is assigned to passive schemes.",
    ("mandate_audit.csv", "fdr_q"): "No BH family q-value is assigned to passive schemes.",
    ("mandate_audit.csv", "R1_benchmark_fit"): "R1 is not applicable to passive schemes.",
    ("mandate_audit.csv", "R2_peer_risk"): "R2 is not applicable to passive schemes.",
    ("mandate_audit.csv", "R2_beta_z"): "R2 beta z-score is not calculated for passive schemes.",
    ("mandate_audit.csv", "R2_max_dd_z"): "R2 drawdown z-score is not calculated for passive schemes.",
    ("mandate_audit.csv", "R4_passive_fit"): "R4 is not applicable to active schemes.",
    ("mandate_audit.csv", "R4_tracking_error_pct"): "R4 tracking error is unavailable for BSE benchmark schemes.",
    ("mandate_audit.csv", "te_ann"): "Tracking error is unavailable for BSE benchmark schemes.",
    ("mandate_audit.csv", "R5_closet_indexer_screen"): "Formal R5 is not applicable to passive schemes; proxy heuristic is separate.",
    ("mandate_audit.csv", "R5_provisional_proxy_heuristic"): "Proxy heuristic is unavailable for passive or BSE benchmark schemes.",
    ("mandate_audit.csv", "R5_unavailable_reason"): "Formal R5 unavailability reason is not applicable to passive schemes.",
    ("mandate_audit.csv", "source_doc"): "Legacy source field; detailed provenance is held in dedicated objective and TER provenance columns.",
    ("mandate_audit.csv", "source_page"): "Legacy source field; detailed provenance is held in dedicated objective and TER provenance columns.",
}


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_pack(root: Path = ROOT) -> tuple[list[str], list[str]]:
    data = root / "dashboard" / "data"
    processed = root / "data" / "processed"
    errors: list[str] = []
    warnings: list[str] = []
    frames: dict[str, pd.DataFrame] = {}
    for filename, spec in SCHEMA.items():
        path = data / filename
        _assert(path.is_file(), f"missing {filename}", errors)
        if not path.is_file():
            continue
        frame = pd.read_csv(path)
        frames[filename] = frame
        missing = sorted(set(spec["required"]) - set(frame.columns))
        _assert(not missing, f"{filename} missing columns: {missing}", errors)
        if missing:
            continue
        _assert(not frame[spec["key"]].isna().any().any(), f"{filename} has null key", errors)
        _assert(not frame.duplicated(spec["key"]).any(), f"{filename} has duplicate key", errors)
        for col in frame.columns:
            missing = frame[col].isna()
            if missing.any():
                allowed = pd.Series(False, index=frame.index)
                if (filename, col) in NULL_SEMANTICS or filename == "mandate_audit.csv":
                    if filename == "alpha.csv":
                        allowed = frame["is_passive"].astype(str).str.lower().eq("true")
                    elif filename in {"metrics.csv", "capture.csv"}:
                        allowed = frame["benchmark_basis"].eq("estimated_hybrid")
                    elif filename == "rolling_returns.csv":
                        allowed = pd.Series(True, index=frame.index)
                    elif filename == "mandate_audit.csv":
                        passive = frame["is_passive"].astype(str).str.lower().eq("true")
                        bse = frame["benchmark_name"].astype(str).str.startswith("BSE ")
                        if col in {
                            "p_bh", "fdr_q", "R1_benchmark_fit",
                            "R2_peer_risk", "R2_beta_z", "R2_max_dd_z",
                            "R5_closet_indexer_screen", "R5_unavailable_reason"
                        }:
                            allowed = passive
                        elif col == "R4_passive_fit":
                            allowed = ~passive
                        elif col in {"te_ann", "R4_tracking_error_pct"}:
                            allowed = bse
                        elif col == "R5_provisional_proxy_heuristic":
                            allowed = passive | bse
                        elif col in {"source_doc", "source_page"}:
                            allowed = pd.Series(True, index=frame.index)
                _assert((~missing | allowed).all(), f"{filename}.{col} has unexpected missing value", errors)
            if col in DATE_COLS:
                _assert(pd.to_datetime(frame[col], errors="coerce").notna().all(), f"{filename}.{col} has invalid date", errors)
            elif col in NUMERIC_COLS:
                converted = pd.to_numeric(frame[col], errors="coerce")
                invalid = frame[col].notna() & converted.isna()
                _assert(not invalid.any(), f"{filename}.{col} has non-numeric value", errors)
            elif col in BOOL_COLS:
                vals = frame[col].astype(str).str.lower()
                _assert(vals.isin({"true", "false"}).all(), f"{filename}.{col} is not boolean", errors)

    if len(frames) == len(SCHEMA):
        dim = frames["dim_scheme.csv"]
        codes = set(pd.to_numeric(dim.scheme_code).astype(int))
        _assert(len(dim) == 32, f"dim_scheme rows={len(dim)}, expected 32", errors)
        _assert(dim.short_name.is_unique and dim.short_name.str.len().le(28).all(), "short_name uniqueness/length failed", errors)
        for name in ["alpha.csv", "metrics.csv", "control_check.csv", "rolling_returns.csv", "drawdown.csv", "capture.csv", "rolling_beta.csv"]:
            if name in frames:
                found = set(pd.to_numeric(frames[name].scheme_code).dropna().astype(int))
                _assert(found <= codes, f"{name} has scheme_code outside dim_scheme", errors)
        alpha = frames["alpha.csv"]
        fee = frames["fee_gap.csv"]
        control = frames["control_check.csv"]
        metrics = frames["metrics.csv"]
        _assert(len(alpha) == 32, f"alpha rows={len(alpha)}, expected 32", errors)
        _assert(len(fee) == 16, f"fee_gap rows={len(fee)}, expected 16", errors)
        _assert(len(control) == 4, f"control_check rows={len(control)}, expected 4", errors)
        _assert(len(frames["glossary.csv"]) == 11, "glossary term count is not 11", errors)
        _assert(
            len(frames["mandate_audit.csv"]) == 16,
            f"mandate_audit rows={len(frames['mandate_audit.csv'])}, expected 16",
            errors,
        )
        _assert(len(metrics) == 96, f"metrics rows={len(metrics)}, expected 96", errors)
        _assert(pd.to_numeric(alpha.alpha_ann).abs().lt(1).all(), "alpha_ann is not decimal-scale", errors)
        _assert(pd.to_numeric(metrics.cagr).abs().lt(1).all(), "cagr is not decimal-scale", errors)
        _assert(pd.to_numeric(metrics.vol_ann).abs().lt(1).all(), "vol_ann is not decimal-scale", errors)
        _assert(control.deviation_pp.sub((pd.to_numeric(control.alpha_ann) - pd.to_numeric(control.expected_alpha_ann)) * 100).abs().le(0.01).all(), "control deviation_pp does not match expected-alpha", errors)
        control_passive = control.scheme_code.astype(int).isin(dim.loc[dim.is_passive.astype(str).str.lower().eq("true"), "scheme_code"].astype(int))
        _assert(control_passive.all(), "control_check includes a non-passive scheme", errors)
        _assert(dim.provisional.astype(str).str.lower().eq(dim.benchmark_basis.eq("estimated_hybrid").astype(str).str.lower()).all(), "provisional rule mismatch", errors)
        for filename in ["rolling_returns.csv", "drawdown.csv"]:
            f = frames[filename]
            _assert(not f.duplicated(["scheme_code", "nav_date"]).any(), f"{filename} duplicate scheme/date", errors)
        rr_counts = frames["rolling_returns.csv"].groupby("scheme_code").size()
        dd_counts = frames["drawdown.csv"].groupby("scheme_code").size()
        common = rr_counts.index.intersection(dd_counts.index)
        ratio_error = ((rr_counts.loc[common] - dd_counts.loc[common]).abs() / rr_counts.loc[common]).max()
        _assert(pd.isna(ratio_error) or ratio_error <= 0.01, "rolling/drawdown rows differ by more than 1%", errors)
        rr = frames["rolling_returns.csv"]
        same_3y_nulls = rr.rolling_return_3y.isna().equals(rr.benchmark_return_3y.isna())
        _assert(same_3y_nulls, "rolling 3Y fund and benchmark values are not aligned", errors)
        for code, series in rr.groupby("scheme_code"):
            ordered = series.sort_values("nav_date")
            valid3 = ordered.rolling_return_3y.notna()
            _assert(valid3.any(), f"no rolling 3Y observations for scheme {code}", errors)
            if valid3.any():
                _assert(int(valid3.to_numpy().argmax()) >= 500, f"rolling 3Y appears too early for scheme {code}", errors)

        beta = frames["rolling_beta.csv"].copy()
        beta["nav_date"] = pd.to_datetime(beta.nav_date)
        beta["beta_252"] = pd.to_numeric(beta.beta_252)
        changes = beta.sort_values(["scheme_code", "nav_date"]).groupby("scheme_code").beta_252.diff().abs()
        max_change = float(changes.max()) if changes.notna().any() else 0.0
        if max_change > 0.25:
            warnings.append(f"beta_252 daily change exceeds 0.25 (max={max_change:.6f})")
        nav_path = processed / "nav_long.parquet"
        if nav_path.is_file():
            nav = pd.read_parquet(nav_path, columns=["scheme_code", "nav_date"])
            nav["nav_date"] = pd.to_datetime(nav.nav_date)
            for code, rows in beta.groupby("scheme_code"):
                first_beta = rows.nav_date.min()
                prior_navs = nav[(nav.scheme_code.astype(int) == int(code)) & (nav.nav_date <= first_beta)]
                _assert(len(prior_navs) >= 252, f"beta_252 begins before 252 NAV observations for {code}", errors)
        else:
            warnings.append("processed NAV not available; could not validate beta warm-up")

    total_bytes = sum(p.stat().st_size for p in (root / "dashboard" / "data").glob("*.csv"))
    _assert(total_bytes < 25 * 1024 * 1024, f"data pack size={total_bytes} bytes, expected <25 MB", errors)
    return errors, warnings


def write_contract(root: Path = ROOT) -> None:
    data = root / "dashboard" / "data"
    lines = ["# Dashboard Data Contract", "", "Generated from the same schema definitions used by `src/validate_dashboard_data.py`.", "", "| File | Grain / key | Column | CSV type | Meaning |", "|---|---|---|---|---|"]
    for filename, spec in SCHEMA.items():
        path = data / filename
        if not path.is_file():
            continue
        frame = pd.read_csv(path, nrows=3)
        for col in frame.columns:
            if col in DATE_COLS:
                kind = "ISO date"
            elif col in BOOL_COLS:
                kind = "boolean"
            elif col in NUMERIC_COLS:
                kind = "number"
            else:
                kind = "text"
            meaning = DESCRIPTIONS.get(col, "Source field preserved from the A3 result or approved data pack.")
            if (filename, col) in NULL_SEMANTICS:
                meaning += " Nullable: " + NULL_SEMANTICS[(filename, col)]
            lines.append(f"| `{filename}` | {spec['grain']} / `{', '.join(spec['key'])}` | `{col}` | {kind} | {meaning} |")
    (root / "dashboard" / "DATA_CONTRACT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    write_contract()
    errors, warnings = validate_pack()
    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"FAIL {error}")
    if errors:
        print(f"validator=FAIL errors={len(errors)} warnings={len(warnings)}")
        return 1
    print(f"validator=PASS files={len(SCHEMA)} warnings={len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

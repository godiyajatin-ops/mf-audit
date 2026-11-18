"""Allow-listed, parameterized read queries for Stage B2."""
from pathlib import Path

METRIC_COLUMNS = {
    "max_dd": "max_dd", "sharpe": "sharpe", "sortino": "sortino",
    "cagr": "cagr", "vol_ann": "vol_ann", "te_ann": "te_ann",
    "info_ratio": "info_ratio", "up_capture": "up_capture",
    "down_capture": "down_capture", "alpha_ann": "alpha_ann",
    "beta": "beta", "gap_pp": "gap_pp",
}
WINDOWS = {"full": "FULL", "1y": "1Y", "3y": "3Y"}
TABLES = {"metrics": "res_metrics", "alpha": "res_alpha", "fees": "res_fee_gap"}

def _metric(key):
    try:
        return METRIC_COLUMNS[key]
    except KeyError as exc:
        raise ValueError(f"Unsupported metric: {key}") from exc

def _window(value):
    try:
        return WINDOWS[value.lower()]
    except (KeyError, AttributeError) as exc:
        raise ValueError(f"Unsupported window: {value}") from exc

normalize_window = _window

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "sql" / "templates"

def _read_template(name, **replacements):
    sql = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        sql = sql.replace("{{" + key + "}}", value)
    if "{{" in sql or "}}" in sql:
        raise ValueError(f"Unresolved SQL template token in {name}")
    return sql

def metric_lookup_sql(metric_key):
    col = _metric(metric_key)
    if metric_key == "alpha_ann":
        return "SELECT scheme_code, window_label, alpha_ann AS value FROM public.res_alpha WHERE scheme_code = :scheme_code AND window_label = :window_label"
    if metric_key == "gap_pp":
        return "SELECT pair_id, gap_pp AS value FROM public.res_fee_gap WHERE pair_id = :pair_id"
    return _read_template("metric_lookup.sql", allowlisted_metric_column=col)

def top_n_sql(metric_key, direction="desc"):
    col = _metric(metric_key)
    if metric_key in {"alpha_ann", "gap_pp"}:
        raise ValueError("Metric is not available for category ranking")
    order = direction.lower()
    if order not in {"asc", "desc"}:
        raise ValueError("direction must be asc or desc")
    return _read_template("top_n.sql", allowlisted_metric_column=col, validated_order_direction=order.upper())

def compare_sql(metric_key):
    col = _metric(metric_key)
    if metric_key in {"gap_pp", "alpha_ann"}:
        raise ValueError("Use the dedicated fee or alpha lookup")
    return _read_template("compare.sql", allowlisted_metric_column=col)

def alpha_lookup_sql():
    return _read_template("alpha_lookup.sql")

def fee_gap_lookup_sql():
    return _read_template("fee_gap_lookup.sql")

def mandate_lookup_sql():
    return _read_template("mandate_lookup.sql")

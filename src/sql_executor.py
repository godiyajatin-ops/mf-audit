"""Execute only Stage B2 SQL builders through a read-only transaction."""
from sqlalchemy import text
from src import sql_templates as templates

BUILDERS = {
    "metric_lookup": templates.metric_lookup_sql,
    "top_n": templates.top_n_sql,
    "compare": templates.compare_sql,
    "alpha_lookup": lambda: templates.alpha_lookup_sql(),
    "fee_gap_lookup": lambda: templates.fee_gap_lookup_sql(),
    "mandate_lookup": lambda: templates.mandate_lookup_sql(),
}
BUILD_OPTIONS = {
    "metric_lookup": {"metric_key"},
    "top_n": {"metric_key", "direction"},
    "compare": {"metric_key"},
    "alpha_lookup": set(),
    "fee_gap_lookup": set(),
    "mandate_lookup": set(),
}
RUNTIME_PARAMS = {
    "metric_lookup": {"scheme_code", "window_label", "pair_id"},
    "top_n": {"category", "window_label", "n"},
    "compare": {"scheme_a", "scheme_b", "window_label"},
    "alpha_lookup": {"scheme_code", "window_label"},
    "fee_gap_lookup": {"pair_id"},
    "mandate_lookup": {"scheme_code"},
}
REQUIRED_PARAMS = {
    "metric_lookup": {"scheme_code", "window_label"},
    "top_n": {"category", "window_label", "n"},
    "compare": {"scheme_a", "scheme_b", "window_label"},
    "alpha_lookup": {"scheme_code", "window_label"},
    "fee_gap_lookup": {"pair_id"},
    "mandate_lookup": {"scheme_code"},
}

def execute_readonly(engine, template_name, params, *, timeout_ms=5000):
    if template_name not in BUILDERS:
        raise ValueError("Unsupported SQL template")
    if timeout_ms < 1 or timeout_ms > 60000:
        raise ValueError("timeout_ms must be between 1 and 60000")
    if not isinstance(params, dict):
        raise TypeError("params must be a mapping")
    options = BUILD_OPTIONS[template_name]
    if not options.issubset(params):
        raise ValueError(f"Missing template options: {sorted(options - set(params))}")
    required_runtime = set(REQUIRED_PARAMS[template_name])
    if template_name == "metric_lookup" and params.get("metric_key") == "gap_pp":
        required_runtime = {"pair_id"}
    if not required_runtime.issubset(params):
        raise ValueError(f"Missing query values: {sorted(required_runtime - set(params))}")
    allowed = options | required_runtime
    if set(params) != allowed:
        raise ValueError(f"Unsupported or missing parameters: {sorted(set(params) ^ allowed)}")
    bind_params = {key: value for key, value in params.items() if key in RUNTIME_PARAMS[template_name]}
    if "window_label" in bind_params:
        bind_params["window_label"] = templates.normalize_window(bind_params["window_label"])
    for key in ("scheme_code", "scheme_a", "scheme_b", "pair_id"):
        if key in bind_params:
            try:
                bind_params[key] = int(bind_params[key])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{key} must be an integer identifier") from exc
    if template_name == "top_n" and bind_params["category"] not in {"Large Cap", "Flexi Cap", "Mid Cap", "Index"}:
        raise ValueError("Unsupported category")
    if template_name == "top_n":
        try:
            bind_params["n"] = int(bind_params["n"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("n must be an integer from 1 to 32") from exc
        if not 1 <= bind_params["n"] <= 32:
            raise ValueError("n must be an integer from 1 to 32")
    sql = BUILDERS[template_name](**{key: params[key] for key in options})
    # SET TRANSACTION is the first statement in the transaction; statement_timeout
    # is transaction-local and cannot leak into the pooled connection.
    with engine.connect() as conn:
        with conn.begin():
            conn.exec_driver_sql("SET TRANSACTION READ ONLY")
            conn.execute(text("SELECT set_config('statement_timeout', :timeout, true)"), {"timeout": f"{timeout_ms}ms"})
            return conn.execute(text(sql), bind_params).mappings().all()

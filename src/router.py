"""Rule-first router for document, numeric, mixed, and out-of-scope questions."""
import re
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import yaml
from src.entities import detect_metric, detect_scheme, detect_scheme_codes, detect_window, DOCUMENT_TERMS

REFUSAL = "I can't give investment advice or predictions. I can share measured historical statistics and what the documents state."
ADVICE = re.compile(r"\b(should i|buy|sell|invest in|best fund|which fund is better|recommend|next year|predict|forecast)\b|\bwill\b.*\b(outperform|beat)\b", re.I)
MIX_HINTS = re.compile(r"\b(behave like|consistent with|mandate|matches? its|as stated)\b", re.I)


def load_rag_settings(config_path=None):
    """Load the frozen RAG configuration used by production DOC/MIX answers."""
    path = Path(config_path) if config_path else Path(__file__).resolve().parents[1] / "config.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rag = config.get("rag", {})

    strategy_map = {"fixed": "A", "section": "B"}
    chunking = rag.get("chunking")
    if chunking not in strategy_map:
        raise ValueError(f"Unsupported RAG chunking strategy: {chunking}")

    settings = {
        "strategy": strategy_map[chunking],
        "top_k": int(rag.get("top_k", 5)),
        "fusion_k": int(rag.get("fusion_k", 60)),
        "min_score": float(rag["min_score"]),
    }
    if settings["top_k"] < 1 or settings["fusion_k"] < 1:
        raise ValueError("RAG top_k and fusion_k must be positive")
    if not 0 <= settings["min_score"]:
        raise ValueError("RAG min_score must be non-negative")
    return settings

def route(question, *, universe_path=None):
    q = str(question).strip()
    metric = detect_metric(q)
    has_doc = any(term in q.lower() for term in DOCUMENT_TERMS)
    scheme = detect_scheme(q, universe_path=universe_path)
    if ADVICE.search(q): intent = "OOS"
    elif (metric and has_doc) or MIX_HINTS.search(q): intent = "MIX"
    elif metric: intent = "NUM"
    elif has_doc: intent = "DOC"
    else: intent = "DOC"
    return {"intent": intent, "scheme_code": scheme, "metric": metric,
            "window": detect_window(q),
            "rationale": "advice_or_prediction" if intent == "OOS" else "rule_match"}

def handle(question, *, universe_path=None):
    result = route(question, universe_path=universe_path)
    if result["intent"] == "OOS":
        result.update(answer=REFUSAL, refused=True)
    else:
        result.update(refused=False)
    return result

def numeric_query_plan(question, *, universe_path=None):
    """Map supported NUM wording to a fixed template and validated bind values."""
    parsed = route(question, universe_path=universe_path)
    if parsed["intent"] != "NUM" or not parsed["metric"]:
        raise ValueError("Question is not a supported numeric query")
    path = Path(universe_path) if universe_path else Path(__file__).resolve().parents[1] / "config" / "universe.csv"
    universe = pd.read_csv(path, dtype={"scheme_code": str})
    codes = detect_scheme_codes(question, universe_path=path)
    metric = parsed["metric"]
    if metric == "gap_pp":
        if not codes:
            raise ValueError("Name a scheme in the Direct-Regular pair")
        pair_rows = universe[universe["scheme_code"].eq(codes[0])]
        return "fee_gap_lookup", {"pair_id": int(pair_rows.iloc[0]["pair_id"])}, parsed
    comparison = re.search(r"\b(compare|versus|vs\.?|against)\b", question, re.I)
    if comparison and len(codes) >= 2:
        return "compare", {"metric_key": metric, "scheme_a": int(codes[0]), "scheme_b": int(codes[1]), "window_label": parsed["window"]}, parsed
    category = next((value for value in ("Large Cap", "Flexi Cap", "Mid Cap", "Index") if value.lower() in question.lower()), None)
    top_match = re.search(r"\b(top|highest|lowest|bottom)\s*(\d{1,2})?\b", question, re.I)
    if top_match:
        if category is None:
            raise ValueError("A category is required for a top-N request")
        direction = "asc" if top_match.group(1).lower() in {"lowest", "bottom"} else "desc"
        n = int(top_match.group(2) or 5)
        return "top_n", {"metric_key": metric, "direction": direction, "category": category, "window_label": parsed["window"], "n": n}, parsed
    if not codes:
        raise ValueError("Name a scheme for a numeric lookup")
    if metric == "alpha_ann":
        return "alpha_lookup", {"scheme_code": int(codes[0]), "window_label": "FULL"}, parsed
    return "metric_lookup", {"metric_key": metric, "scheme_code": int(codes[0]), "window_label": parsed["window"]}, parsed

def run_numeric_query(engine, question, *, universe_path=None, timeout_ms=5000, log_path=None):
    """Route and execute one safe numeric request; log only query metadata/results."""
    from src.sql_executor import execute_readonly
    started = time.perf_counter()
    template, params, parsed = numeric_query_plan(question, universe_path=universe_path)
    error = None
    try:
        rows = execute_readonly(engine, template, params, timeout_ms=timeout_ms)
        result = {"intent": "NUM", "scheme_code": parsed["scheme_code"], "metric": parsed["metric"], "window": parsed["window"], "sql_template": template, "rows": [dict(row) for row in rows], "refused": False}
        return result
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), "question": question, "intent_pred": "NUM", "metric": parsed["metric"], "scheme_code": parsed["scheme_code"], "sql_template": template, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error_type": error}
        _append_query_log(record, log_path)

def _append_query_log(record, log_path=None):
    target = Path(log_path) if log_path else Path(__file__).resolve().parents[1] / "logs" / "queries.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

def dispatch_question(engine, question, *, llm=None, min_score=None, strategy=None,
                      top_k=None, fusion_k=None, config_path=None,
                      universe_path=None, retriever=None, timeout_ms=5000, log_path=None):
    """Dispatch OOS/NUM/DOC/MIX; MIX combines fixed audit SQL with cited RAG."""
    started = time.perf_counter()
    parsed = route(question, universe_path=universe_path)
    if parsed["intent"] == "OOS":
        result = {**parsed, "answer": REFUSAL, "refused": True}
        _append_query_log({"timestamp": datetime.now(timezone.utc).isoformat(), "question": question, "intent_pred": "OOS", "refused": True, "latency_ms": round((time.perf_counter()-started)*1000, 2)}, log_path)
        return result
    if parsed["intent"] == "NUM":
        return run_numeric_query(engine, question, universe_path=universe_path, timeout_ms=timeout_ms, log_path=log_path)
    if llm is None:
        raise ValueError("An LLMClient is required for DOC and MIX answers")
    settings = load_rag_settings(config_path)
    strategy = settings["strategy"] if strategy is None else strategy
    min_score = settings["min_score"] if min_score is None else float(min_score)
    top_k = settings["top_k"] if top_k is None else int(top_k)
    fusion_k = settings["fusion_k"] if fusion_k is None else int(fusion_k)

    from src.rag.answer import answer_question
    if parsed["intent"] == "DOC":
        answer_result = answer_question(question, llm=llm, scheme_code=parsed["scheme_code"], strategy=strategy, min_score=min_score, retriever=retriever, top_k=top_k, fusion_k=fusion_k)
        result = {**parsed, **answer_result}
        log_record = {"timestamp": datetime.now(timezone.utc).isoformat(), "question": question, "intent_pred": "DOC", "retrieved_chunk_ids": result["retrieved_chunk_ids"], "citations": result["citations"], "refused": result["refused"], "latency_ms": round((time.perf_counter()-started)*1000, 2)}
        _append_query_log(log_record, log_path)
        return result
    audit_rows = []
    alpha_rows = []
    sql_templates = []
    if parsed["scheme_code"] is not None:
        from src.sql_executor import execute_readonly
        audit_rows = execute_readonly(engine, "mandate_lookup", {"scheme_code": int(parsed["scheme_code"])}, timeout_ms=timeout_ms)
        if audit_rows:
            sql_templates.append("mandate_lookup")
        # Mixed metric/document requests keep the numeric result deterministic.
        if parsed["metric"] == "alpha_ann":
            alpha_rows = execute_readonly(
                engine,
                "alpha_lookup",
                {"scheme_code": int(parsed["scheme_code"]), "window_label": "FULL"},
                timeout_ms=timeout_ms,
            )
            if alpha_rows:
                sql_templates.append("alpha_lookup")
    document_question = question
    if alpha_rows:
        document_question = re.sub(
            r"\s*,?\s*and\s+what\s+is\s+its\s+full-window\s+alpha\?\s*$",
            "?",
            question,
            flags=re.I,
        )
    answer_result = answer_question(document_question, llm=llm, scheme_code=parsed["scheme_code"], strategy=strategy, min_score=min_score, retriever=retriever, top_k=top_k, fusion_k=fusion_k)
    result = {
        **parsed,
        **answer_result,
        "mandate_audit": [dict(row) for row in audit_rows],
        "sql_templates": sql_templates,
    }
    numeric_value = None
    if alpha_rows:
        numeric_value = float(alpha_rows[0]["value"])
        result.update(
            sql_template="alpha_lookup",
            value=numeric_value,
            numeric_rows=[dict(row) for row in alpha_rows],
        )
        if not answer_result["refused"]:
            result["answer"] = (
                f"Alpha (FULL) = {numeric_value:.12g} [SQL: alpha_lookup]. "
                f"{answer_result['answer']}"
            )
    elif audit_rows:
        result["sql_template"] = "mandate_lookup"
    _append_query_log({"timestamp": datetime.now(timezone.utc).isoformat(), "question": question, "intent_pred": "MIX", "scheme_code": parsed["scheme_code"], "sql_template": result.get("sql_template"), "sql_templates": sql_templates, "value": numeric_value, "retrieved_chunk_ids": result["retrieved_chunk_ids"], "citations": result["citations"], "refused": result["refused"], "latency_ms": round((time.perf_counter()-started)*1000, 2)}, log_path)
    return result

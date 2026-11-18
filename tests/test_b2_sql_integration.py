"""Integration checks for the configured PostgreSQL read-only role."""
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from src.sql_executor import execute_readonly
from src.router import run_numeric_query, dispatch_question
from src.llm import MockLLM
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DATABASE_URL = os.getenv("READONLY_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="READONLY_DATABASE_URL is not configured")

@pytest.fixture(scope="module")
def engine():
    db = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    try:
        with db.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        db.dispose()
        pytest.fail(f"Configured PostgreSQL integration database is unreachable: {type(exc).__name__}")
    yield db
    db.dispose()

def test_metric_lookup_executes_with_read_only_executor(engine):
    rows = execute_readonly(engine, "metric_lookup", {
        "metric_key": "cagr", "scheme_code": 119018, "window_label": "full",
    })
    assert len(rows) == 1
    assert rows[0]["scheme_code"] == 119018
    assert rows[0]["window_label"] == "FULL"

def test_fee_gap_and_alpha_templates_execute(engine):
    fee_rows = execute_readonly(engine, "fee_gap_lookup", {"pair_id": 1})
    alpha_rows = execute_readonly(engine, "alpha_lookup", {"scheme_code": 119018, "window_label": "FULL"})
    assert len(fee_rows) == 1 and fee_rows[0]["pair_id"] == 1
    assert len(alpha_rows) == 1 and alpha_rows[0]["scheme_code"] == 119018

def test_top_n_and_compare_templates_execute(engine):
    top = execute_readonly(engine, "top_n", {
        "metric_key": "cagr", "direction": "desc", "category": "Large Cap",
        "window_label": "full", "n": 3,
    })
    comparison = execute_readonly(engine, "compare", {
        "metric_key": "sharpe", "scheme_a": 119018, "scheme_b": 119598,
        "window_label": "FULL",
    })
    assert len(top) == 3
    assert [row["value"] for row in top] == sorted([row["value"] for row in top], reverse=True)
    assert len(comparison) == 2

def test_router_to_sql_to_log(engine, tmp_path):
    log = tmp_path / "queries.jsonl"
    result = run_numeric_query(engine, "What is HDFC Large Cap Fund CAGR?", log_path=log)
    assert result["sql_template"] == "metric_lookup"
    assert len(result["rows"]) == 1 and result["rows"][0]["scheme_code"] == 119018
    event = log.read_text(encoding="utf-8")
    assert '"intent_pred": "NUM"' in event and '"sql_template": "metric_lookup"' in event

def test_mixed_router_combines_mandate_sql_and_cited_rag(engine, tmp_path):
    frame = pd.DataFrame([{
        "score": .9, "doc_id": 3, "page": 124, "chunk_id": "fixture-1",
        "section": "Benchmark", "text": "HDFC Large Cap Fund follows NIFTY 100 TRI as its stated benchmark.",
    }])
    log = tmp_path / "mix.jsonl"
    result = dispatch_question(
        engine, "What benchmark is stated for HDFC Large Cap Fund, and what is its full-window alpha?",
        llm=MockLLM(), min_score=.1,
        retriever=lambda **kwargs: frame, log_path=log,
    )
    alpha_rows = execute_readonly(engine, "alpha_lookup", {"scheme_code": 119018, "window_label": "FULL"})
    assert result["intent"] == "MIX"
    assert len(result["mandate_audit"]) == 1
    assert result["sql_template"] == "alpha_lookup"
    assert result["value"] == pytest.approx(float(alpha_rows[0]["value"]))
    assert result["citations"] == [(3, 124)]
    assert "[SQL: alpha_lookup]" in result["answer"]
    assert not result["refused"]

def test_readonly_role_and_transaction_reject_write(engine):
    with engine.connect() as conn:
        role = conn.execute(text("""
            SELECT current_user AS role,
                   has_table_privilege(current_user, 'public.res_metrics', 'INSERT') AS can_insert
        """)).mappings().one()
        assert role["role"] == "mf_readonly"
        assert not role["can_insert"]
        conn.rollback()
        with pytest.raises(DBAPIError):
            with conn.begin():
                conn.exec_driver_sql("SET TRANSACTION READ ONLY")
                conn.execute(text("""
                    INSERT INTO public.res_metrics
                      (scheme_code, window_label, cagr, vol_ann, sharpe, sortino,
                       max_dd, te_ann, info_ratio, up_capture, down_capture,
                       n_obs, start_date, end_date)
                    SELECT 119018, 'FULL', NULL, NULL, NULL, NULL, NULL, NULL,
                           NULL, NULL, NULL, 0, CURRENT_DATE, CURRENT_DATE
                    WHERE FALSE
                """))

import json
import pandas as pd
import pytest

from src import sql_templates
from src.router import route, handle, numeric_query_plan, dispatch_question, REFUSAL
from src.llm import MockLLM
from src.rag.answer import answer_question, REFUSAL as DOC_REFUSAL
from src.sql_executor import execute_readonly
from eval.run_eval import load_reviewed_set, assert_heldout_frozen

def test_router_refuses_advice():
    result = handle("Should I buy HDFC Large Cap Fund?")
    assert result["intent"] == "OOS"
    assert result["answer"] == REFUSAL

def test_sql_allowlist_and_binds():
    sql = sql_templates.metric_lookup_sql("cagr")
    assert ":scheme_code" in sql and ":window_label" in sql
    assert "DROP" not in sql
    with pytest.raises(ValueError):
        sql_templates.metric_lookup_sql("cagr; DROP TABLE x")
    assert "LIMIT :n" in sql_templates.top_n_sql("cagr", "desc")
    with pytest.raises(ValueError):
        sql_templates.top_n_sql("cagr", "desc; DROP TABLE x")

def test_executor_rejects_bad_params_before_connecting():
    class NeverConnect:
        def connect(self): raise AssertionError("must validate first")
    with pytest.raises(ValueError, match="Unsupported or missing"):
        execute_readonly(NeverConnect(), "metric_lookup", {"metric_key": "cagr", "scheme_code": 1, "window_label": "full", "sql": "DROP"})

def test_numeric_query_plans_bind_only_resolved_ids():
    template, params, _ = numeric_query_plan("What is HDFC Large Cap Fund CAGR?")
    assert template == "metric_lookup"
    assert params == {"metric_key": "cagr", "scheme_code": 119018, "window_label": "full"}
    template, params, _ = numeric_query_plan("What is the Direct vs Regular fee gap for HDFC Large Cap Fund?")
    assert template == "fee_gap_lookup" and params == {"pair_id": 1}

def test_numeric_compare_and_top_n_are_fixed_templates():
    template, params, _ = numeric_query_plan("Compare HDFC Large Cap Fund versus SBI Large Cap Fund sharpe")
    assert template == "compare" and params["scheme_a"] == 119018 and params["scheme_b"] == 119598
    template, params, _ = numeric_query_plan("Show top 3 Large Cap funds by CAGR")
    assert template == "top_n" and params["n"] == 3 and params["direction"] == "desc"

def test_eval_runner_blocks_unreviewed_gold(tmp_path, monkeypatch):
    from eval import run_eval

    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    held_types = ["doc", "doc", "doc", "num", "num", "num", "mix", "mix", "mix", "refusal"]
    rows = []
    dev_qids, heldout_qids = [], []
    for i in range(35):
        qid = f"Q{i:02d}"
        split = "dev" if i < 25 else "heldout"
        answer_type = "doc" if split == "dev" else held_types[i - 25]
        rows.append({"qid": qid, "question": f"Question {i}", "intent_expected": answer_type.upper(),
                     "scheme_code": "", "answer_type": answer_type, "gold_answer": "",
                     "gold_doc_id": "", "gold_page": "", "gold_sql_template": "", "gold_value": "",
                     "split": split, "notes": "DRAFT_PENDING_HUMAN_REVIEW: test fixture"})
        (dev_qids if split == "dev" else heldout_qids).append(qid)
    pd.DataFrame(rows).to_csv(eval_dir / "gold_questions.csv", index=False)
    (eval_dir / "split.json").write_text(json.dumps({
        "status": "draft_pending_human_review", "heldout_run_permitted": False,
        "dev_qids": dev_qids, "heldout_qids": heldout_qids,
    }), encoding="utf-8")
    monkeypatch.setattr(run_eval, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="human must review"):
        load_reviewed_set()

def test_heldout_runner_blocks_without_freeze():
    with pytest.raises(RuntimeError, match="Held-out run blocked"):
        assert_heldout_frozen({"rag": {"min_score": None, "frozen_at": None, "frozen_commit": None}}, {})

def test_mock_llm_cites_fixture_context():
    prompt = "CONTEXT:\n[7 p.4 | Fees] The expense ratio is 0.5 percent.\nQUESTION: expense ratio?\nANSWER:"
    assert "[7 p.4]" in MockLLM().generate(prompt)

def test_answer_refuses_without_context_and_does_not_call_llm():
    class Spy:
        called = False
        def generate(self, *args, **kwargs):
            self.called = True
            return ""
    spy = Spy()
    empty = pd.DataFrame()
    result = answer_question("TER?", llm=spy, min_score=0.1, retriever=lambda **kw: empty)
    assert result["answer"] == DOC_REFUSAL and result["refused"]
    assert not spy.called

def test_answer_rejects_unretrieved_citation():
    class LLM:
        def generate(self, *args, **kwargs): return "A claim [999 p.99]"
    frame = pd.DataFrame([{"score": .9, "doc_id": 1, "page": 2, "chunk_id": "x", "text": "Facts.", "section": "fees"}])
    result = answer_question("Fees?", llm=LLM(), min_score=.1, retriever=lambda **kw: frame)
    assert result["answer"] == DOC_REFUSAL and result["refused"]

def test_mixed_alpha_uses_sql_and_keeps_llm_on_document_claim(monkeypatch, tmp_path):
    import src.sql_executor as sql_executor

    calls = []
    def fake_execute(engine, template, params, *, timeout_ms=5000):
        calls.append((template, params))
        if template == "mandate_lookup":
            return [{"scheme_code": 119018, "benchmark_name": "NIFTY 100 TRI"}]
        if template == "alpha_lookup":
            return [{"scheme_code": 119018, "window_label": "FULL", "value": 0.02231491824738426,
                     "beta": 0.91, "p_bh": 0.42}]
        raise AssertionError(f"Unexpected SQL template: {template}")
    monkeypatch.setattr(sql_executor, "execute_readonly", fake_execute)

    chunks = pd.DataFrame([{
        "score": .9, "doc_id": 3, "page": 124, "chunk_id": "fixture-1",
        "section": "Benchmark", "text": "HDFC Large Cap Fund follows NIFTY 100 TRI as its stated benchmark.",
    }])
    class SpyLLM:
        prompt = None
        def generate(self, prompt, **kwargs):
            self.prompt = prompt
            return "The stated benchmark is NIFTY 100 TRI [3 p.124]."
    llm = SpyLLM()
    result = dispatch_question(
        object(),
        "What benchmark is stated for HDFC Large Cap Fund, and what is its full-window alpha?",
        llm=llm, min_score=.1, retriever=lambda **kwargs: chunks,
        log_path=tmp_path / "mix.jsonl",
    )

    assert result["intent"] == "MIX"
    assert result["sql_template"] == "alpha_lookup"
    assert result["value"] == pytest.approx(0.02231491824738426)
    assert result["answer"].startswith("Alpha (FULL) = ") and "[SQL: alpha_lookup]" in result["answer"]
    assert result["citations"] == [(3, 124)]
    assert "full-window alpha" not in llm.prompt.lower()
    assert "CITATION CONTRACT (mandatory)" in llm.prompt
    assert "exactly [<doc_id> p.<page>]" in llm.prompt
    assert [call[0] for call in calls] == ["mandate_lookup", "alpha_lookup"]


def test_router_classifies_metric():
    assert route("What is HDFC Large Cap Fund CAGR?")["intent"] == "NUM"

def test_production_doc_path_uses_configured_rag_settings(tmp_path):
    from src.router import load_rag_settings

    settings = load_rag_settings()
    assert settings == {
        "strategy": "A",
        "top_k": 5,
        "fusion_k": 60,
        "min_score": 0.028012,
    }

    captured = {}

    def fake_retriever(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame([{
            "score": 0.9,
            "doc_id": 1,
            "page": 2,
            "chunk_id": "test_chunk",
            "text": "The scheme seeks long-term capital appreciation.",
            "section": "Investment Objective",
        }])

    class FakeLLM:
        def generate(self, *args, **kwargs):
            return "The scheme seeks long-term capital appreciation [1 p.2]."

    result = dispatch_question(
        None,
        "What is the investment objective of HDFC Large Cap Fund?",
        llm=FakeLLM(),
        retriever=fake_retriever,
        log_path=tmp_path / "queries.jsonl",
    )

    assert captured["strategy"] == "A"
    assert captured["mode"] == "hybrid"
    assert captured["top_k"] == 5
    assert captured["fusion_k"] == 60
    assert result["refused"] is False
    assert result["citations"] == [(1, 2)]

def test_numeric_export_recovers_value_from_sql_rows():
    from eval.run_generation_eval import _numeric_export_fields

    result = {
        "value": "",
        "rows": [
            {
                "scheme_code": 119018,
                "window_label": "FULL",
                "value": "0.09285337333775094355",
            }
        ],
    }

    value, rows = _numeric_export_fields(result)

    assert value == "0.09285337333775094355"
    assert len(rows) == 1
    assert rows[0]["scheme_code"] == 119018


def test_numeric_export_preserves_existing_top_level_value():
    from eval.run_generation_eval import _numeric_export_fields

    result = {
        "value": "0.09285",
        "rows": [{"value": "0.09285337333775094355"}],
    }

    value, _ = _numeric_export_fields(result)

    assert value == "0.09285"

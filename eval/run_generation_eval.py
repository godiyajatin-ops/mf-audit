"""B2 generation evaluation with synthetic availability and heldout gates."""
import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import result

import pandas as pd
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_PATH = ROOT / "results" / "gemini_preflight.json"
LABEL_PATH = ROOT / "eval" / "faithfulness_to_label.csv"


def _numeric_export_fields(result):
    numeric_rows = result.get("rows", result.get("numeric_rows", []))
    actual_value = result.get("value", "")

    if actual_value in (None, "") and numeric_rows:
        actual_value = next(
            (
                item.get("value")
                for item in numeric_rows
                if isinstance(item, dict)
                and item.get("value") not in (None, "")
            ),
            "",
        )

    return actual_value, numeric_rows

def _now():
    return datetime.now(timezone.utc)


def _load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8")) or {}


def run_preflight():
    """Check the provider using a synthetic prompt only; never send project data."""
    from src.llm import configured_client

    client = configured_client(
        timeout_seconds_override=30,
        max_retries_override=0,
        cache_enabled_override=False,
    )
    record = {
        "checked_at": _now().isoformat(),
        "provider": "gemini",
        "model": client.model,
        "status": "failed",
        "prompt_kind": "synthetic_only",
    }
    try:
        response = client.generate(
            "Reply with exactly: GEMINI_CONNECTION_OK",
            temperature=0,
            max_tokens=64,
        )
        if response.strip() != "GEMINI_CONNECTION_OK":
            record["error_type"] = "UnexpectedSyntheticResponse"
            raise RuntimeError("Synthetic response did not match expected sentinel")
        record["status"] = "success"
        record["error_type"] = None
    except Exception as exc:
        record["error_type"] = record.get("error_type") or type(exc).__name__
        status = getattr(exc, "status_code", getattr(exc, "code", None))
        if status is not None:
            record["http_status"] = str(status)
        PREFLIGHT_PATH.parent.mkdir(parents=True, exist_ok=True)
        PREFLIGHT_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"Synthetic preflight: FAIL ({record['error_type']})")
        if status is not None:
            print(f"Provider status: {status}")
        return False
    PREFLIGHT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFLIGHT_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Synthetic preflight: PASS ({client.model})")
    print("No factsheet context was included.")
    return True


def _require_recent_preflight(model):
    if not PREFLIGHT_PATH.exists():
        raise RuntimeError("Generation blocked: run --preflight successfully first")
    record = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    if record.get("status") != "success" or record.get("model") != model:
        raise RuntimeError("Generation blocked: no successful preflight for the configured model")
    try:
        checked = datetime.fromisoformat(record["checked_at"].replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise RuntimeError("Generation blocked: preflight timestamp is invalid") from exc
    if checked.tzinfo is None or checked > _now() or _now() - checked > timedelta(hours=24):
        raise RuntimeError("Generation blocked: synthetic preflight must be successful and less than 24 hours old")


def _prepare_questions(split_name):
    from eval.run_eval import load_reviewed_set

    gold, split = load_reviewed_set()
    if split_name == "heldout":
        from eval.run_eval import assert_heldout_frozen

        assert_heldout_frozen(_load_config(), split)
        labels = pd.read_csv(LABEL_PATH, dtype=str).fillna("")
        if len(labels) < 20 or not labels.label.str.strip().isin(["0", "1"]).all() or labels.label.str.strip().eq("").any():
            raise RuntimeError("Held-out run blocked until 20 faithfulness labels are complete (0/1)")
        selected = gold[gold.split.eq("heldout")]
    else:
        selected = gold[gold.split.eq("dev")]
    if selected.empty:
        raise ValueError(f"No gold questions assigned to {split_name}")
    return gold, split, selected


def _faithfulness_rows(results, selected):
    """Build the 14+6 dev labeling sample without changing gold_questions.csv."""
    from src.rag.retrieve import load_chunks

    rows = []
    q_by_id = {str(row["qid"]): row for row in results}
    chunk_table = load_chunks("A").copy()
    chunk_table["chunk_id"] = chunk_table["chunk_id"].astype(str)
    chunk_lookup = chunk_table.set_index("chunk_id", drop=False)

    def context_blocks(result):
        cited_pages = {tuple(map(int, pair)) for pair in result.get("citations", [])}
        ids = result.get("retrieved_chunk_ids", [])
        retrieved, cited = [], []
        for chunk_id in ids:
            chunk_id = str(chunk_id)
            if chunk_id not in chunk_lookup.index:
                continue
            chunk = chunk_lookup.loc[chunk_id]
            page_key = (int(chunk.doc_id), int(chunk.page))
            block = f"[{page_key[0]} p.{page_key[1]}] {chunk.text}"
            retrieved.append(block)
            if page_key in cited_pages:
                cited.append(block)
        return "\n\n".join(cited), "\n\n".join(retrieved)
    for row in selected.itertuples(index=False):
        if row.answer_type not in {"doc", "mix"}:
            continue
        result = q_by_id.get(str(row.qid))
        if result is None or not result.get("answer"):
            continue
        cited_text, retrieved_text = context_blocks(result)
        review_note = "No validated citations; review retrieved context and abstention." if result.get("refused") else ""
        rows.append({"qid": str(row.qid), "question": row.question, "answer": result["answer"], "cited_chunks_text": cited_text, "retrieved_context_text": retrieved_text, "label": "", "note": review_note})

    smoke = pd.read_csv(ROOT / "eval" / "smoke_queries.csv", dtype={"scheme_code": str})
    supplements = smoke[smoke.query_id.isin([f"O{i:02d}" for i in range(1, 7)])]
    if len(supplements) != 6 or not supplements.verification_status.eq("excerpt_verified").all():
        raise RuntimeError("Approved O01-O06 smoke questions must remain excerpt_verified")
    for smoke_row in supplements.itertuples(index=False):
        qid = str(smoke_row.query_id)
        result = q_by_id.get(qid)
        if result is None or not result.get("answer"):
            continue
        cited_text, retrieved_text = context_blocks(result)
        review_note = "User-approved B1 smoke supplement; excerpt_verified; outside gold split."
        if result.get("refused"):
            review_note += " No validated citations; review retrieved context and abstention."
        rows.append({"qid": qid, "question": smoke_row.query, "answer": result["answer"], "cited_chunks_text": cited_text, "retrieved_context_text": retrieved_text, "label": "", "note": review_note})
    return rows


def _summarize_generation(rows, selected, strategy):
    """Score dev gold outputs without treating smoke supplements as gold rows."""
    from src.rag.retrieve import load_chunks

    by_qid = {str(row["qid"]): row for row in rows}
    chunks = load_chunks(strategy).copy()
    chunks["chunk_id"] = chunks["chunk_id"].astype(str)
    chunk_meta = chunks.set_index("chunk_id", drop=False)
    succeeded = [by_qid[str(row.qid)] for row in selected.itertuples(index=False)
                 if str(row.qid) in by_qid and not by_qid[str(row.qid)].get("error_type")]
    intent_hits = [r["intent_pred"] == r["intent_expected"] for r in succeeded]
    refusal_hits = []
    false_refusals = []
    retrieval_ranks = []
    citation_hits = []
    numeric_hits = []
    for gold in selected.itertuples(index=False):
        result = by_qid.get(str(gold.qid))
        if not result or result.get("error_type"):
            continue
        expect_refusal = gold.answer_type == "refusal"
        actual_refusal = str(result.get("refused", "")).strip().lower() in {"true", "1"}
        refusal_hits.append(actual_refusal == expect_refusal)
        if not expect_refusal:
            false_refusals.append(actual_refusal)
        if gold.answer_type in {"doc", "mix"} and pd.notna(gold.gold_doc_id) and pd.notna(gold.gold_page):
            target = (int(gold.gold_doc_id), int(gold.gold_page))
            ids = json.loads(result.get("retrieved_chunk_ids") or "[]")
            rank = next((i for i, chunk_id in enumerate(ids, start=1)
                         if chunk_id in chunk_meta.index
                         and (int(chunk_meta.loc[chunk_id, "doc_id"]), int(chunk_meta.loc[chunk_id, "page"])) == target), None)
            retrieval_ranks.append(rank)
            citations = json.loads(result.get("citations") or "[]")
            citation_hits.append(any(tuple(map(int, pair)) == target for pair in citations))
        expected_value = getattr(gold, "gold_value", None)
        if pd.notna(expected_value):
            actual_value = result.get("value")
            if actual_value in (None, ""):
                numeric_rows = json.loads(result.get("numeric_rows") or "[]")
                actual_value = next((item.get("value") for item in numeric_rows if "value" in item), None)
            try:
                numeric_hits.append(abs(float(actual_value) - float(expected_value)) <= 1e-6)
            except (TypeError, ValueError):
                numeric_hits.append(False)
    def mean(values):
        return sum(values) / len(values) if values else None
    summary = {
        "split": rows[0]["split"] if rows else "",
        "gold_questions": len(selected),
        "completed_questions": len(succeeded),
        "intent_accuracy": mean(intent_hits),
        "refusal_accuracy": mean(refusal_hits),
        "false_refusal_rate": mean(false_refusals),
        "doc_mix_retrieval_hit_at_3": mean([rank is not None and rank <= 3 for rank in retrieval_ranks]),
        "doc_mix_retrieval_hit_at_5": mean([rank is not None and rank <= 5 for rank in retrieval_ranks]),
        "doc_mix_retrieval_mrr": mean([1 / rank if rank else 0.0 for rank in retrieval_ranks]),
        "doc_mix_gold_page_citation_rate": mean(citation_hits),
        "numeric_exact_within_1e-6_rate": mean(numeric_hits),
        "mean_latency_ms": mean([float(r["latency_ms"]) for r in succeeded]),
    }
    return pd.DataFrame([summary])


def run_generation(split_name):
    from src.llm import configured_client
    from src.router import dispatch_question

    config = _load_config()
    model = str(config.get("llm", {}).get("model", ""))
    _require_recent_preflight(model)
    gold, split, selected = _prepare_questions(split_name)
    load_dotenv(ROOT / ".env")
    database_url = os.getenv("READONLY_DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("Generation needs READONLY_DATABASE_URL; no database credentials are printed or inferred")
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    llm = configured_client()
    strategy = "B" if config.get("rag", {}).get("chunking") == "section" else "A"
    min_score = float(config["rag"]["min_score"])
    rows = []
    to_run = list(selected.itertuples(index=False))
    if split_name == "dev":
        smoke = pd.read_csv(ROOT / "eval" / "smoke_queries.csv", dtype={"scheme_code": str})
        supplements = smoke[smoke.query_id.isin([f"O{i:02d}" for i in range(1, 7)])]
        if len(supplements) != 6 or not supplements.verification_status.eq("excerpt_verified").all():
            raise RuntimeError("Approved O01-O06 smoke questions must remain excerpt_verified")
        to_run += [type("SmokeQuestion", (), {"qid": str(r.query_id), "question": r.query, "scheme_code": str(r.scheme_code), "answer_type": "smoke", "intent_expected": "DOC", "gold_doc_id": r.expected_doc_id, "gold_page": r.expected_page, "gold_sql_template": "", "gold_value": None}) for r in supplements.itertuples(index=False)]
    try:
        for question in to_run:
            qid = str(question.qid)
            started = time.perf_counter()
            llm.last_usage = None
            try:
                result = dispatch_question(
                    engine,
                    question.question,
                    llm=llm,
                    min_score=min_score,
                    strategy=strategy,
                    top_k=int(config['rag']['top_k']),
                    fusion_k=int(config['rag']['fusion_k']),
                    timeout_ms=5000,
                )

                usage = llm.last_usage or {}
                actual_value, numeric_rows = _numeric_export_fields(result)

                if actual_value in (None, "") and numeric_rows:
                    actual_value = next(
                        (
                            item.get("value")
                            for item in numeric_rows
                            if isinstance(item, dict)
                            and item.get("value") not in (None, "")
                        ),
                        "",
                    )
                row = {
                    "split": split_name,
                    "qid": qid,
                    "answer_type": question.answer_type,
                    "intent_expected": question.intent_expected,
                    "intent_pred": result.get("intent"),
                    "answer": result.get("answer", ""),
                    "citations": json.dumps(result.get("citations", [])),
                    "retrieved_chunk_ids": json.dumps(result.get("retrieved_chunk_ids", [])),
                    "refused": bool(result.get("refused", False)),
                    "sql_template": result.get("sql_template", ""),
                    "value": actual_value,
                    "numeric_rows": json.dumps(numeric_rows, default=str),
                    "input_tokens": usage.get("input_tokens", ""),
                    "output_tokens": usage.get("output_tokens", ""),
                    "total_tokens": usage.get("total_tokens", ""),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    "error_type": "",
                }
            except Exception as exc:
                row = {"split": split_name, "qid": qid, "answer_type": question.answer_type, "intent_expected": question.intent_expected, "intent_pred": "", "answer": "", "citations": "[]", "retrieved_chunk_ids": "[]", "refused": "", "sql_template": "", "value": "", "numeric_rows": "[]", "input_tokens": "", "output_tokens": "", "total_tokens": "", "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error_type": type(exc).__name__}
            rows.append(row)
            print(f"{qid}: {'error=' + row['error_type'] if row['error_type'] else 'intent=' + str(row['intent_pred']) + ', refused=' + str(row['refused'])}", flush=True)
    finally:
        engine.dispose()
    frame = pd.DataFrame(rows)
    out = ROOT / "results" / f"generation_eval_{split_name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    summary = _summarize_generation(rows, selected, strategy)
    summary_path = ROOT / "results" / f"generation_summary_{split_name}.csv"
    summary.to_csv(summary_path, index=False)
    if split_name == "dev":
        generated = [
            {
                **row,
                "citations": json.loads(row.get("citations") or "[]"),
                "retrieved_chunk_ids": json.loads(row.get("retrieved_chunk_ids") or "[]"),
            }
            for row in rows
        ]
        faith_rows = _faithfulness_rows(generated, selected)
        if len(faith_rows) == 20:
            pd.DataFrame(faith_rows, columns=["qid", "question", "answer", "cited_chunks_text", "retrieved_context_text", "label", "note"]).to_csv(LABEL_PATH, index=False)
            print(f"Faithfulness sample prepared: {len(faith_rows)} rows, labels blank.")
        else:
            print(f"Faithfulness sample not written: expected 20 answers, got {len(faith_rows)}.")
    print(f"Wrote {len(frame)} generation rows to {out.relative_to(ROOT)}")
    print(f"Wrote generation metrics to {summary_path.relative_to(ROOT)}")
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true", help="Synthetic-only provider check; no project context")
    action.add_argument("--split", choices=("dev", "heldout"))
    args = parser.parse_args()
    if args.preflight:
        raise SystemExit(0 if run_preflight() else 1)
    run_generation(args.split)

def test_numeric_export_recovers_value_from_sql_rows():
    from eval.run_generation_eval import _numeric_export_fields

    result = {
        "value": "",
        "rows": [
            {"scheme_code": 119018, "window_label": "FULL",
             "value": "0.09285337333775094355"}
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

if __name__ == "__main__":
    main()

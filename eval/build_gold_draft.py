"""Create a deterministic B2 gold-set draft; every row requires human review."""
import json
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "eval" / "gold_questions.csv"
SPLIT = ROOT / "eval" / "split.json"
SEED = 42

def build():
    if GOLD.exists() or SPLIT.exists():
        raise FileExistsError("Gold draft or split already exists; preserve it and review manually")
    smoke = pd.read_csv(ROOT / "eval" / "smoke_queries.csv", dtype={"scheme_code": str})
    if not smoke["verification_status"].eq("excerpt_verified").all():
        raise ValueError("Only excerpt-verified smoke questions can seed DOC drafts")
    metrics = pd.read_csv(ROOT / "results" / "metrics_by_window.csv", dtype={"scheme_code": str})
    metrics = metrics[(metrics.window_label == "FULL") & (metrics.plan == "Direct")].sort_values("scheme_code")
    alpha = pd.read_csv(ROOT / "results" / "alpha.csv", dtype={"scheme_code": str})
    alpha = alpha[alpha.plan == "Direct"].set_index("scheme_code")
    rows = []
    note = "DRAFT_PENDING_HUMAN_REVIEW: generated deterministically from verified smoke queries and project result CSVs; not human-approved."
    for i, row in enumerate(smoke.iloc[:10].itertuples(index=False), 1):
        rows.append({"qid": f"D{i:02}", "question": row.query, "intent_expected": "DOC", "scheme_code": row.scheme_code, "answer_type": "doc", "gold_answer": row.expected_answer, "gold_doc_id": row.expected_doc_id, "gold_page": row.expected_page, "gold_sql_template": "", "gold_value": "", "split": "", "notes": note})
    for i, row in enumerate(metrics.iloc[:10].itertuples(index=False), 1):
        value = float(row.cagr)
        rows.append({"qid": f"N{i:02}", "question": f"What was the full-window CAGR for {row.scheme_name}?", "intent_expected": "NUM", "scheme_code": row.scheme_code, "answer_type": "num", "gold_answer": f"{value:.10g}", "gold_doc_id": "", "gold_page": "", "gold_sql_template": "metric_lookup", "gold_value": value, "split": "", "notes": note + " Gold value copied from results/metrics_by_window.csv (FULL, Direct)."})
    benchmark_docs = smoke[smoke.category.eq("benchmark")]
    if benchmark_docs.empty:
        raise ValueError("No verified benchmark smoke questions available for MIX drafts")
    for i in range(10):
        row = next(benchmark_docs.iloc[i % len(benchmark_docs):].itertuples(index=False), None)
        if row is None:
            row = next(benchmark_docs.itertuples(index=False))
        metric_row = alpha.loc[row.scheme_code]
        value = float(metric_row.alpha_ann)
        answer = f"Alpha (FULL) = {value:.10g}; stated benchmark = {row.expected_answer}"
        rows.append({"qid": f"M{i+1:02}", "question": f"What benchmark is stated for {row.scheme_name}, and what is its full-window alpha?", "intent_expected": "MIX", "scheme_code": row.scheme_code, "answer_type": "mix", "gold_answer": answer, "gold_doc_id": row.expected_doc_id, "gold_page": row.expected_page, "gold_sql_template": "alpha_lookup", "gold_value": value, "split": "", "notes": note + " Benchmark citation source comes from an excerpt-verified B1 smoke row; duplicate scheme/document cases need human review."})
    refusals = [
        ("Should I buy HDFC Large Cap Fund?", "OOS", "advice"),
        ("Which fund is the best investment for next year?", "OOS", "advice"),
        ("Will SBI Large Cap Fund outperform next year?", "OOS", "prediction"),
        ("What was HDFC Large Cap Fund's NAV on 2000-01-01 in its factsheet?", "DOC", "unanswerable"),
        ("How many investor complaints did SBI Large Cap Fund receive in 2000?", "DOC", "unanswerable"),
    ]
    for i, (question, intent, kind) in enumerate(refusals, 1):
        rows.append({"qid": f"R{i:02}", "question": question, "intent_expected": intent, "scheme_code": "", "answer_type": "refusal", "gold_answer": "I can't give investment advice or predictions. I can share measured historical statistics and what the documents state." if intent == "OOS" else "Not found in the provided documents.", "gold_doc_id": "", "gold_page": "", "gold_sql_template": "", "gold_value": "", "split": "", "notes": note + f" Refusal subtype: {kind}."})
    frame = pd.DataFrame(rows)
    if len(frame) != 35 or frame.answer_type.value_counts().to_dict() != {"doc": 10, "num": 10, "mix": 10, "refusal": 5}:
        raise ValueError("Draft gold-set counts do not match the Stage B2 specification")
    rng = random.Random(SEED)
    held = []
    for kind, count in (("doc", 3), ("num", 3), ("mix", 3), ("refusal", 1)):
        candidates = sorted(frame.loc[frame.answer_type.eq(kind), "qid"].tolist())
        held.extend(rng.sample(candidates, count))
    frame["split"] = frame.qid.map(lambda qid: "heldout" if qid in held else "dev")
    GOLD.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(GOLD, index=False)
    dev = frame.loc[frame.split.eq("dev"), "qid"].tolist()
    SPLIT.write_text(json.dumps({"seed": SEED, "status": "draft_pending_human_review", "heldout_run_permitted": False, "strata": {"doc": 3, "num": 3, "mix": 3, "refusal": 1}, "dev_qids": dev, "heldout_qids": held}, indent=2) + "\n", encoding="utf-8")
    print(f"Created {len(frame)} draft rows; 25 dev, 10 heldout; all require human review.")

if __name__ == "__main__":
    build()

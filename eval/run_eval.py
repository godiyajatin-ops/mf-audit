"""B2 retrieval ablation runner with human-review and held-out freeze gates."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from src.rag.retrieve import retrieve

ROOT = Path(__file__).resolve().parents[1]
MODES = ("bm25", "dense", "hybrid")
STRATEGIES = ("A", "B")

def load_reviewed_set():
    gold = pd.read_csv(ROOT / "eval" / "gold_questions.csv", dtype={"scheme_code": str})
    split = json.loads((ROOT / "eval" / "split.json").read_text(encoding="utf-8"))
    if len(gold) != 35 or gold.qid.nunique() != 35:
        raise ValueError("Expected 35 unique gold questions")
    if not gold.notes.fillna("").str.startswith("HUMAN_APPROVED:").all():
        raise RuntimeError("Gold set is a draft; a human must review every row and mark notes HUMAN_APPROVED:")
    if split.get("status") != "human_reviewed":
        raise RuntimeError("split.json must be marked human_reviewed after gold review")
    if len(split.get("dev_qids", [])) != 25 or len(split.get("heldout_qids", [])) != 10:
        raise ValueError("split.json must preserve the seeded 25/10 partition")
    if set(split["dev_qids"]) != set(gold.loc[gold.split.eq("dev"), "qid"]):
        raise ValueError("Gold CSV dev rows no longer match the frozen split")
    if set(split["heldout_qids"]) != set(gold.loc[gold.split.eq("heldout"), "qid"]):
        raise ValueError("Gold CSV heldout rows no longer match the frozen split")
    held = gold[gold.split.eq("heldout")].answer_type.value_counts().to_dict()
    if held != {"doc": 3, "num": 3, "mix": 3, "refusal": 1}:
        raise ValueError("Heldout must remain stratified 3 DOC / 3 NUM / 3 MIX / 1 refusal")
    return gold, split

def assert_heldout_frozen(config, split):
    rag = config.get("rag", {})
    if not rag.get("frozen_at") or not rag.get("frozen_commit") or rag.get("min_score") is None:
        raise RuntimeError("Held-out run blocked: freeze min_score/chunking in config.yaml and record its commit/time first")
    if not split.get("heldout_run_permitted", False):
        raise RuntimeError("Held-out run blocked until human review explicitly permits it in split.json")
    try:
        frozen_at = datetime.fromisoformat(str(rag["frozen_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("rag.frozen_at must be an ISO-8601 timestamp with timezone") from exc
    if frozen_at.tzinfo is None or frozen_at > datetime.now(timezone.utc):
        raise RuntimeError("rag.frozen_at must be a timezone-aware timestamp no later than the held-out run")
    commit = str(rag["frozen_commit"])
    if not all(ch in "0123456789abcdefABCDEF" for ch in commit) or not 7 <= len(commit) <= 40:
        raise RuntimeError("rag.frozen_commit must identify the committed config freeze")
    try:
        committed = subprocess.run(["git", "show", f"{commit}:config.yaml"], cwd=ROOT,
                                   check=True, capture_output=True, text=True).stdout
        committed_config = yaml.safe_load(committed)
    except (OSError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        raise RuntimeError("rag.frozen_commit must contain a readable config.yaml") from exc
    frozen_rag = committed_config.get("rag", {})
    for key in ("chunking", "top_k", "fusion_k", "min_score", "frozen_at"):
        if frozen_rag.get(key) != rag.get(key):
            raise RuntimeError(f"Current rag.{key} differs from the committed freeze")
    commit_time_text = subprocess.run(["git", "show", "-s", "--format=%cI", commit], cwd=ROOT,
                                     check=True, capture_output=True, text=True).stdout.strip()
    commit_time = datetime.fromisoformat(commit_time_text.replace("Z", "+00:00"))
    if commit_time > datetime.now(timezone.utc):
        raise RuntimeError("Freeze commit timestamp must precede held-out evaluation")

def score_query(row, strategy, mode):
    result = retrieve(query=row.question, strategy=strategy, mode=mode, top_k=5,
                      scheme_code=row.scheme_code if pd.notna(row.scheme_code) and str(row.scheme_code) else None)
    target = (int(row.gold_doc_id), int(row.gold_page)) if pd.notna(row.gold_doc_id) and pd.notna(row.gold_page) else None
    ranks = []
    if target:
        for rank, (_, chunk) in enumerate(result.iterrows(), start=1):
            if (int(chunk.doc_id), int(chunk.page)) == target:
                ranks.append(rank)
    rank = min(ranks) if ranks else None
    return {"qid": row.qid, "strategy": strategy, "mode": mode,
            "expected_rank": rank, "hit_at_1": bool(rank and rank <= 1),
            "hit_at_3": bool(rank and rank <= 3), "hit_at_5": bool(rank and rank <= 5),
            "reciprocal_rank": 1 / rank if rank else 0.0,
            "returned_chunks": len(result), "retrieval_status": "ok"}

def run(split_name, *, ablation=False):
    gold, split_data = load_reviewed_set()
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    if split_name == "heldout":
        assert_heldout_frozen(config, split_data)
    selected = gold[gold.split.eq(split_name)]
    if selected.empty:
        raise ValueError(f"No questions assigned to split {split_name}")
    configs = [(s, m) for s in STRATEGIES for m in MODES] if ablation else [(config.get("rag", {}).get("chunking", "section") == "section" and "B" or "A", "hybrid")]
    details = []
    for strategy, mode in configs:
        for row in selected.itertuples(index=False):
            if row.answer_type not in {"doc", "mix"}:
                continue
            try:
                details.append({"split": split_name, **score_query(row, strategy, mode)})
            except Exception as exc:
                details.append({"split": split_name, "qid": row.qid, "strategy": strategy,
                                "mode": mode, "retrieval_status": f"error:{type(exc).__name__}"})
    detail = pd.DataFrame(details)
    if ablation:
        summary = (detail[detail.retrieval_status.eq("ok")]
                   .groupby(["split", "strategy", "mode"], as_index=False)
                   .agg(queries=("qid", "count"), hit_at_1=("hit_at_1", "mean"),
                        hit_at_3=("hit_at_3", "mean"), hit_at_5=("hit_at_5", "mean"),
                        mrr=("reciprocal_rank", "mean")))
        path = ROOT / "results" / "ablation_retrieval.csv"
        if path.exists():
            old = pd.read_csv(path)
            old = old[old.split.ne(split_name)]
            summary = pd.concat([old, summary], ignore_index=True)
        summary.to_csv(path, index=False)
    else:
        path = ROOT / "results" / f"retrieval_{split_name}.csv"
        detail.to_csv(path, index=False)
    return detail

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "heldout"), required=True)
    parser.add_argument("--ablation", action="store_true")
    args = parser.parse_args()
    detail = run(args.split, ablation=args.ablation)
    print(detail.groupby(["strategy", "mode", "retrieval_status"]).size().to_string())

if __name__ == "__main__":
    main()

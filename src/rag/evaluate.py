
from pathlib import Path
import pandas as pd

from src.rag.retrieve import retrieve


ROOT = Path(__file__).resolve().parents[2]
QUERY_PATH = ROOT / "eval" / "smoke_queries.csv"
RESULTS_DIR = ROOT / "results"

CONFIGURATIONS = [
    (strategy, mode)
    for strategy in ["A", "B"]
    for mode in ["bm25", "dense", "hybrid"]
]


def evaluate_configuration(queries, strategy, mode):
    rows = []

    for _, query in queries.iterrows():
        results = retrieve(
            query=query["query"],
            strategy=strategy,
            mode=mode,
            top_k=20,
            scheme_code=str(query["scheme_code"]),
        )

        expected_doc = int(query["expected_doc_id"])
        expected_page = int(query["expected_page"])

        ranks = [
            rank
            for rank, (_, result) in enumerate(
                results.iterrows(), start=1
            )
            if int(result["doc_id"]) == expected_doc
            and int(result["page"]) == expected_page
        ]

        rank = min(ranks) if ranks else None

        rows.append({
            "query_id": query["query_id"],
            "category": query["category"],
            "scheme_code": query["scheme_code"],
            "strategy": strategy,
            "mode": mode,
            "expected_doc_id": expected_doc,
            "expected_page": expected_page,
            "expected_chunk_id": query["expected_chunk_id"],
            "expected_rank": rank,
            "hit_at_1": rank is not None and rank <= 1,
            "hit_at_3": rank is not None and rank <= 3,
            "hit_at_5": rank is not None and rank <= 5,
            "reciprocal_rank": 1 / rank if rank else 0.0,
            "returned_chunks": len(results),
        })

    return rows


def main():
    queries = pd.read_csv(
        QUERY_PATH,
        dtype={"scheme_code": str},
    )

    if len(queries) != 20:
        raise ValueError(
            f"Expected 20 smoke queries, found {len(queries)}"
        )

    if not queries["verification_status"].eq(
        "excerpt_verified"
    ).all():
        raise ValueError(
            "All smoke queries must have excerpt_verified status"
        )

    detail_rows = []

    for strategy, mode in CONFIGURATIONS:
        print(f"\nEvaluating Strategy {strategy} / {mode}")

        rows = evaluate_configuration(
            queries, strategy, mode
        )
        detail_rows.extend(rows)

        temp = pd.DataFrame(rows)
        print(
            f"Hit@1={temp['hit_at_1'].mean():.3f} | "
            f"Hit@3={temp['hit_at_3'].mean():.3f} | "
            f"Hit@5={temp['hit_at_5'].mean():.3f} | "
            f"MRR={temp['reciprocal_rank'].mean():.3f}"
        )

    details = pd.DataFrame(detail_rows)

    summary = (
        details.groupby(["strategy", "mode"])
        .agg(
            queries=("query_id", "count"),
            hit_at_1=("hit_at_1", "mean"),
            hit_at_3=("hit_at_3", "mean"),
            hit_at_5=("hit_at_5", "mean"),
            mrr=("reciprocal_rank", "mean"),
        )
        .reset_index()
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    details.to_csv(
        RESULTS_DIR / "b1_smoke_query_details.csv",
        index=False,
    )

    summary.to_csv(
        RESULTS_DIR / "b1_smoke_results.csv",
        index=False,
    )

    print("\n=== SUMMARY ===")
    print(summary.to_string(index=False))

    print("\nSaved:")
    print(RESULTS_DIR / "b1_smoke_results.csv")
    print(RESULTS_DIR / "b1_smoke_query_details.csv")


if __name__ == "__main__":
    main()

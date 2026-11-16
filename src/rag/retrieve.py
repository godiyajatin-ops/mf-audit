from pathlib import Path
import argparse
import pickle

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from src.rag.bm25 import tokenize
from src.rag.fuse import rrf


ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = ROOT / "data" / "index"
UNIVERSE_PATH = ROOT / "config" / "universe.csv"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RRF_K = 60

_EMBEDDING_MODEL = None


def get_embedding_model():
    global _EMBEDDING_MODEL

    if _EMBEDDING_MODEL is None:
        print(f"Loading embedding model: {MODEL_NAME}")
        _EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)

    return _EMBEDDING_MODEL

def load_chunks(strategy):
    path = INDEX_DIR / f"chunks{strategy}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)

    chunks = pd.read_parquet(path)

    if "chunk_id" not in chunks.columns or "text" not in chunks.columns:
        raise ValueError(f"Invalid chunk file: {path}")

    return chunks


def resolve_scheme(scheme_code):
    universe = pd.read_csv(UNIVERSE_PATH, dtype={"scheme_code": str})

    matches = universe[
        universe["scheme_code"].astype(str) == str(scheme_code)
    ]

    if matches.empty:
        raise ValueError(f"Unknown scheme_code: {scheme_code}")

    if len(matches) != 1:
        raise ValueError(f"Ambiguous scheme_code: {scheme_code}")

    row = matches.iloc[0]

    return int(row["pair_id"]), row["amc"]


def filter_chunks(chunks, scheme_code=None):
    if scheme_code is None:
        return chunks

    pair_id, amc = resolve_scheme(scheme_code)

    family_match = chunks["pair_id"].eq(pair_id).fillna(False)
    related_match = chunks["related_pair_id"].eq(pair_id).fillna(False)

    general_amc_match = (
        chunks["pair_id"].isna()
        & chunks["related_pair_id"].isna()
        & chunks["amc"].eq(amc)
    )

    filtered = chunks[
        family_match | related_match | general_amc_match
    ].copy()

    if filtered.empty:
        raise ValueError(
            f"No chunks found for scheme_code={scheme_code}, "
            f"pair_id={pair_id}, AMC={amc}"
        )

    return filtered


def load_bm25(strategy):
    model_path = INDEX_DIR / f"bm25{strategy}.pkl"
    mapping_path = INDEX_DIR / f"bm25{strategy}_ids.parquet"

    with model_path.open("rb") as file:
        payload = pickle.load(file)

    mapping = pd.read_parquet(mapping_path).sort_values("row_id")

    return payload["model"], mapping["chunk_id"].astype(str).tolist()


def load_dense(strategy):
    index_path = INDEX_DIR / f"faiss{strategy}.index"
    mapping_path = INDEX_DIR / f"dense{strategy}_ids.parquet"

    index = faiss.read_index(str(index_path))
    mapping = pd.read_parquet(mapping_path).sort_values("row_id")

    return index, mapping["chunk_id"].astype(str).tolist()


def bm25_rank(query, model, chunk_ids, allowed_ids):
    scores = np.asarray(model.get_scores(tokenize(query)))

    if len(scores) != len(chunk_ids):
        raise ValueError("BM25 score count does not match ID mapping")

    ranked = [
        (chunk_ids[i], float(scores[i]))
        for i in range(len(chunk_ids))
        if chunk_ids[i] in allowed_ids
    ]

    ranked.sort(key=lambda item: (-item[1], item[0]))

    return ranked


def dense_rank(query, index, chunk_ids, allowed_ids, model):
    if index.ntotal != len(chunk_ids):
        raise ValueError("FAISS index count does not match ID mapping")

    query_vector = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    distances, indices = index.search(query_vector, index.ntotal)

    ranked = []

    for score, row_id in zip(distances[0], indices[0]):
        if row_id < 0:
            continue

        chunk_id = chunk_ids[row_id]

        if chunk_id in allowed_ids:
            ranked.append((chunk_id, float(score)))

    return ranked


def retrieve(
    query,
    strategy="B",
    mode="hybrid",
    top_k=5,
    scheme_code=None,
):
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if strategy not in {"A", "B"}:
        raise ValueError("strategy must be A or B")

    if mode not in {"bm25", "dense", "hybrid"}:
        raise ValueError("mode must be bm25, dense or hybrid")

    if top_k < 1:
        raise ValueError("top_k must be positive")

    chunks = load_chunks(strategy)
    eligible = filter_chunks(chunks, scheme_code)

    allowed_ids = set(eligible["chunk_id"].astype(str))
    chunk_lookup = chunks.copy()
    chunk_lookup["chunk_id"] = chunk_lookup["chunk_id"].astype(str)
    chunk_lookup = chunk_lookup.set_index("chunk_id", drop=False)

    bm25_results = []
    dense_results = []

    if mode in {"bm25", "hybrid"}:
        bm25_model, bm25_ids = load_bm25(strategy)
        bm25_results = bm25_rank(
            query, bm25_model, bm25_ids, allowed_ids
        )

    if mode in {"dense", "hybrid"}:
        dense_index, dense_ids = load_dense(strategy)
        embedding_model = get_embedding_model()
        dense_results = dense_rank(
            query,
            dense_index,
            dense_ids,
            allowed_ids,
            embedding_model,
        )

    bm25_scores = dict(bm25_results)
    dense_scores = dict(dense_results)

    if mode == "bm25":
        final_results = [
            (chunk_id, score, "bm25")
            for chunk_id, score in bm25_results[:top_k]
        ]

    elif mode == "dense":
        final_results = [
            (chunk_id, score, "dense")
            for chunk_id, score in dense_results[:top_k]
        ]

    else:
        fused = rrf(
            [
                [chunk_id for chunk_id, _ in bm25_results],
                [chunk_id for chunk_id, _ in dense_results],
            ],
            k=RRF_K,
        )

        final_results = [
            (chunk_id, score, "hybrid")
            for chunk_id, score in fused[:top_k]
        ]

    output = []

    for chunk_id, score, source_mode in final_results:
        row = chunk_lookup.loc[chunk_id].to_dict()

        row["score"] = score
        row["source_mode"] = source_mode
        row["bm25_score"] = bm25_scores.get(chunk_id)
        row["dense_score"] = dense_scores.get(chunk_id)

        output.append(row)

    return pd.DataFrame(output)


def main():
    parser = argparse.ArgumentParser(
        description="Search the Mutual Fund Audit document corpus"
    )

    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--strategy", choices=["A", "B"], default="B"
    )
    parser.add_argument(
        "--mode",
        choices=["bm25", "dense", "hybrid"],
        default="hybrid",
    )
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--scheme-code", default=None)

    args = parser.parse_args()

    results = retrieve(
        query=args.query,
        strategy=args.strategy,
        mode=args.mode,
        top_k=args.k,
        scheme_code=args.scheme_code,
    )

    if results.empty:
        print("No matching results.")
        return

    for rank, (_, row) in enumerate(results.iterrows(), start=1):
        print(f"\n{'=' * 75}")
        print(
            f"Rank {rank} | Chunk: {row['chunk_id']} | "
            f"Score: {row['score']:.6f}"
        )
        print(
            f"AMC: {row['amc']} | Pair ID: {row['pair_id']} | "
            f"Doc ID: {row['doc_id']} | Page: {row['page']}"
        )
        print(
            f"Section: {row['section']} | "
            f"Strategy: {row['strategy']} | "
            f"Source: {row['source_mode']}"
        )
        print("-" * 75)
        print(str(row["text"])[:2500])


if __name__ == "__main__":
    main()

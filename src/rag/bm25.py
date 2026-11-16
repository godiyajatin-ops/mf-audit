from pathlib import Path
import pickle
import re

import pandas as pd
from rank_bm25 import BM25Okapi


ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = ROOT / "data" / "index"

TOKEN_PATTERN = re.compile(r"[a-zA-Z]+|\d+(?:\.\d+)?%?")

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by",
    "for", "from", "in", "is", "it", "of", "on", "or",
    "that", "the", "this", "to", "was", "were", "with",
}


def tokenize(text):
    text = str(text).lower()
    tokens = TOKEN_PATTERN.findall(text)
    return [token for token in tokens if token not in STOP_WORDS]


def build_index(strategy):
    chunks_path = INDEX_DIR / f"chunks{strategy}.parquet"
    index_path = INDEX_DIR / f"bm25{strategy}.pkl"
    mapping_path = INDEX_DIR / f"bm25{strategy}_ids.parquet"

    if not chunks_path.exists():
        raise FileNotFoundError(f"Missing chunk file: {chunks_path}")

    chunks = pd.read_parquet(chunks_path)

    required = {"chunk_id", "text"}
    missing = required - set(chunks.columns)
    if missing:
        raise ValueError(
            f"Strategy {strategy} missing columns: {sorted(missing)}"
        )

    if chunks.empty:
        raise ValueError(f"Strategy {strategy} contains no chunks")

    if chunks["chunk_id"].duplicated().any():
        raise ValueError(f"Duplicate chunk IDs in strategy {strategy}")

    corpus = [tokenize(text) for text in chunks["text"]]

    if any(not tokens for tokens in corpus):
        raise ValueError(
            f"Strategy {strategy} contains chunks with no searchable tokens"
        )

    model = BM25Okapi(corpus)

    with index_path.open("wb") as file:
        pickle.dump(
            {
                "model": model,
                "tokenizer": "TOKEN_PATTERN",
                "stop_words": sorted(STOP_WORDS),
                "strategy": strategy,
            },
            file,
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    mapping = pd.DataFrame({
        "row_id": range(len(chunks)),
        "chunk_id": chunks["chunk_id"].astype(str).values,
    })
    mapping.to_parquet(mapping_path, index=False)

    token_lengths = pd.Series([len(tokens) for tokens in corpus])

    print(f"\n=== BM25 STRATEGY {strategy} ===")
    print(f"Chunks indexed: {len(corpus)}")
    print(f"Vocabulary size: {len(model.idf)}")
    print(f"Mean tokens per chunk: {token_lengths.mean():.1f}")
    print(f"Median tokens per chunk: {token_lengths.median():.1f}")
    print(f"BM25 index: {index_path}")
    print(f"Chunk mapping: {mapping_path}")

    return {
        "strategy": strategy,
        "chunks": len(corpus),
        "vocabulary": len(model.idf),
    }


def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for strategy in ["A", "B"]:
        results.append(build_index(strategy))

    print("\n=== BM25 INDEX SUMMARY ===")
    print(pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()

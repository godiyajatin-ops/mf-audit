from pathlib import Path
import random

import faiss
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = ROOT / "data" / "index"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64
SEED = 42
DEVICE = "cpu"


def set_seeds():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.set_num_threads(4)


def build_index(strategy, model):
    chunks_path = INDEX_DIR / f"chunks{strategy}.parquet"
    index_path = INDEX_DIR / f"faiss{strategy}.index"
    mapping_path = INDEX_DIR / f"dense{strategy}_ids.parquet"

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

    if chunks["text"].isna().any():
        raise ValueError(f"Null chunk text in strategy {strategy}")

    texts = chunks["text"].astype(str).tolist()

    print(f"\n=== EMBEDDING STRATEGY {strategy} ===")
    print(f"Chunks: {len(chunks)}")
    print(f"Model: {MODEL_NAME}")
    print(f"Device: {DEVICE}")
    print(f"Batch size: {BATCH_SIZE}")

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
        device=DEVICE,
    )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    if embeddings.ndim != 2:
        raise ValueError("Embedding output must be a 2D matrix")

    if embeddings.shape[0] != len(chunks):
        raise ValueError("Embedding count does not match chunk count")

    if not np.isfinite(embeddings).all():
        raise ValueError("Embeddings contain NaN or infinite values")

    norms = np.linalg.norm(embeddings, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-4):
        raise ValueError("Embeddings are not L2-normalized")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, str(index_path))

    mapping = pd.DataFrame({
        "row_id": np.arange(len(chunks), dtype=np.int64),
        "chunk_id": chunks["chunk_id"].astype(str).values,
    })
    mapping.to_parquet(mapping_path, index=False)

    print(f"Embedding dimensions: {dimension}")
    print(f"Index vectors: {index.ntotal}")
    print(f"Vector norm mean: {norms.mean():.6f}")
    print(f"Vector norm min: {norms.min():.6f}")
    print(f"Vector norm max: {norms.max():.6f}")
    print(f"FAISS index: {index_path}")
    print(f"Chunk mapping: {mapping_path}")

    return {
        "strategy": strategy,
        "chunks": len(chunks),
        "dimension": dimension,
        "index_vectors": index.ntotal,
    }


def main():
    set_seeds()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading embedding model...")
    print(f"Model: {MODEL_NAME}")
    print(f"Device: {DEVICE}")

    model = SentenceTransformer(
        MODEL_NAME,
        device=DEVICE,
    )
    model.eval()

    results = []

    for strategy in ["A", "B"]:
        results.append(build_index(strategy, model))

    print("\n=== DENSE INDEX SUMMARY ===")
    print(pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()

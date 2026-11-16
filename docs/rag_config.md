# RAG Configuration

## 1. Corpus

- Source documents: 17 PDFs
- Extracted pages: 1,742
- Pages below 200 extracted characters: 82
- Extraction method: PyMuPDF
- Scheme universe: 16 scheme pairs
- Strategy A chunks: 5,682
- Strategy B chunks: 4,697

The page-level dataset is stored at `data/processed/pages_assigned.parquet`.
Chunk datasets and index artifacts are stored under `data/index/`.

## 2. Chunking

Character counts use an approximate conversion of four characters per token.

| Parameter | Strategy A | Strategy B |
|---|---:|---:|
| Target / maximum size | 1,600 chars | 2,400 chars |
| Overlap | 200 chars | 200 chars |
| Minimum section size | N/A | 160 chars |
| Mean actual chunk size | 1,380.7 chars | 1,565.4 chars |
| Median actual chunk size | 1,594 chars | 1,627 chars |

### Strategy A
Fixed-size chunking, preferring word boundaries. Chunks do not cross source-page boundaries.

### Strategy B
Section-aware chunking. Short sections are merged, and oversized sections are split using the fixed-size splitter. Chunks retain source-page metadata.

## 3. Dense retrieval

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Embedding dimensions: 384
- Batch size: 64
- Device used during index build: CPU
- Seed configured: 42
- Embeddings normalized before indexing
- Vector index: FAISS

## 4. BM25 retrieval

Implementation: `rank_bm25.BM25Okapi`

Default scoring parameters:
- k1: 1.5
- b: 0.75
- epsilon: 0.25

Tokenizer:
- Lowercase text
- Regex: `[a-zA-Z]+|\d+(?:\.\d+)?%?`
- Custom stop-word list defined in `src/rag/bm25.py`

Vocabulary size reported during index build: 29,004.

## 5. Hybrid retrieval

Hybrid retrieval combines BM25 and dense rankings using Reciprocal Rank Fusion.

- RRF smoothing constant: 60
- Fusion implementation: `src/rag/fuse.py`
- Retrieval implementation and CLI: `src/rag/retrieve.py`

The retrieval function supports:
- Strategy A or B
- BM25, dense, or hybrid mode
- Configurable top-k
- Optional scheme-code filtering

Example:

```powershell
.\.venv\Scripts\python.exe -m src.rag.retrieve "HDFC Large Cap exit load" --strategy B --mode hybrid --k 5 --scheme-code YOUR_SCHEME_CODE
```

Replace `YOUR_SCHEME_CODE` with a valid code from `config/universe.csv`.

## 6. Build commands

Run from the project root, in this order:

```powershell
.\.venv\Scripts\python.exe -m src.rag.ingest
.\.venv\Scripts\python.exe -m src.rag.assign_schemes
.\.venv\Scripts\python.exe -m src.rag.chunking
.\.venv\Scripts\python.exe -m src.rag.embed
.\.venv\Scripts\python.exe -m src.rag.bm25
```

The current project does not provide a single `make index` or equivalent orchestrator. Run these steps in sequence.

## 7. Evaluation

Evaluation entry point:

```powershell
.\.venv\Scripts\python.exe -m src.rag.evaluate
```

Smoke evaluation uses 20 queries. Results are saved to:
- `results/b1_smoke_results.csv`
- `results/b1_smoke_query_details.csv`

The indexes are generated artifacts and should not be committed unless the project repository explicitly requires them.

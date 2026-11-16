# Stage B1 Report: Document Retrieval System

## 1. Status

**COMPLETE_WITH_LIMITATIONS**

The document ingestion, scheme assignment, chunking, indexing, retrieval, smoke evaluation, and focused automated tests have been implemented and executed.

The retrieval Hit@3 acceptance target was not achieved. This limitation is retained explicitly rather than tuning against the same smoke queries.

## 2. Scope delivered

- Ingested 17 PDF documents.
- Extracted 1,742 pages using PyMuPDF.
- Produced page-level text and metadata.
- Assigned scheme-family metadata across the 16 configured scheme pairs.
- Generated two chunking strategies.
- Built dense FAISS indexes for both strategies.
- Built BM25 indexes for both strategies.
- Implemented BM25, dense, and hybrid retrieval.
- Implemented scheme-code filtering.
- Implemented Reciprocal Rank Fusion.
- Added a command-line retrieval interface in `src/rag/retrieve.py`.
- Added smoke evaluation outputs and focused tests.

## 3. Corpus and chunking results

| Measure | Result |
|---|---:|
| Source PDFs | 17 |
| Extracted pages | 1,742 |
| Pages below 200 characters | 82 |
| Strategy A chunks | 5,682 |
| Strategy B chunks | 4,697 |
| Unique source pages represented in chunks | 1,736 |

Scheme assignment produced coverage across all 16 configured scheme pairs. Some factsheet content remains AMC-level or unclassified because not every page identifies an individual scheme.

## 4. Retrieval evaluation

The smoke evaluation contains 20 queries. Results:

| Strategy | Mode | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---:|---:|---:|---:|
| A | BM25 | 0.20 | 0.40 | 0.45 | 0.332070 |
| A | Dense | 0.25 | 0.35 | 0.50 | 0.348422 |
| A | Hybrid | 0.20 | 0.40 | 0.50 | 0.348808 |
| B | BM25 | 0.25 | 0.45 | 0.55 | 0.407495 |
| B | Dense | 0.20 | 0.40 | 0.45 | 0.344147 |
| B | Hybrid | 0.25 | 0.50 | 0.65 | 0.393333 |

### Interpretation

- Strategy B Hybrid achieved the highest Hit@5: 0.65.
- Strategy B BM25 achieved the highest MRR: 0.407495.
- Strategy B Hybrid Hit@3 was 0.50, below the target of 0.60.
- Dense-only retrieval did not outperform BM25 consistently.
- Exact scheme names, financial terminology, percentages, and tabular content appear to benefit from lexical retrieval.

Strategy B Hybrid is retained as the default general-purpose retrieval configuration because it provides the strongest top-five coverage. Strategy B BM25 remains a useful alternative where early ranking quality is prioritized.

The smoke evaluation is a diagnostic set, not an independent final benchmark. Its results should not be interpreted as production accuracy.

## 5. Automated tests

Focused test command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chunking.py tests/test_fuse_rrf.py tests/test_retrieve_smoke.py -q
```

Latest result:

**10 passed in 7.93 seconds.**

Coverage includes chunk size and source-page boundaries, section handling, RRF behavior, and retrieval smoke checks.

## 6. Known limitations and risks

1. **Hit@3 shortfall:** Strategy B Hybrid achieved 0.50 against the 0.60 target.
2. **Extraction quality:** 82 pages contain fewer than 200 extracted characters. These require manual review where relevant.
3. **OCR:** The current ingestion process uses PyMuPDF. OCR coverage for image-only or poorly extracted pages has not been established.
4. **Scheme attribution:** Some factsheet pages remain AMC-level or unclassified rather than being assigned to a single scheme.
5. **Metadata completeness:** Source URLs and document dates are not populated for every source document.
6. **Build orchestration:** The pipeline currently requires sequential module execution. There is no single `make index` target or equivalent build orchestrator.
7. **Evaluation size:** The smoke evaluation contains only 20 queries and should not be treated as a statistically comprehensive benchmark.
8. **Dense retrieval:** Dense-only performance is weaker than lexical retrieval on this corpus. Financial numeric and exact-term queries remain challenging.

## 7. Reproduction

Run these commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.rag.ingest
.\.venv\Scripts\python.exe -m src.rag.assign_schemes
.\.venv\Scripts\python.exe -m src.rag.chunking
.\.venv\Scripts\python.exe -m src.rag.embed
.\.venv\Scripts\python.exe -m src.rag.bm25
.\.venv\Scripts\python.exe -m src.rag.evaluate
```

Run focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chunking.py tests/test_fuse_rrf.py tests/test_retrieve_smoke.py -q
```

Configuration details are documented in `docs/rag_config.md`.

## 8. Acceptance assessment

| Requirement | Assessment |
|---|---|
| Document ingestion | Completed |
| Page-level extraction | Completed, with low-text exceptions |
| Scheme assignment | Completed across configured scheme pairs, with AMC-level exceptions |
| Two chunking strategies | Completed |
| Dense indexes | Built for A and B |
| BM25 indexes | Built for A and B |
| Hybrid RRF retrieval | Implemented |
| Scheme filtering | Implemented |
| Retrieval CLI | Implemented in `retrieve.py` |
| Six retrieval evaluation configurations | Completed |
| Hit@3 target >= 0.60 | Not met |
| Focused automated tests | 10 passed |
| Configuration documentation | Completed |
| Stage report | Completed |
| Single-command index orchestration | Not implemented |

## 9. Closure decision

B1 is closed as **COMPLETE_WITH_LIMITATIONS**.

The retrieval pipeline is implemented, indexes have been rebuilt, evaluation outputs are available, and focused tests pass. The Hit@3 shortfall, extraction exceptions, incomplete metadata, and missing build orchestrator remain documented limitations.

Further retrieval tuning is deferred. The existing smoke evaluation should not be repeatedly used as a tuning target.

**Recommended downstream use:** Strategy B Hybrid as the default retrieval mode, with source citations and human verification required for factual answers.

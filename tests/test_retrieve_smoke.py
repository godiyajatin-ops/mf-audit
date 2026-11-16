import pandas as pd
from rank_bm25 import BM25Okapi

from src.rag.retrieve import filter_chunks, bm25_rank
from src.rag.bm25 import tokenize


def test_scheme_filter_keeps_family_and_same_amc_general_chunks():
    chunks = pd.DataFrame([
        {
            "chunk_id": "family",
            "pair_id": 1,
            "related_pair_id": pd.NA,
            "amc": "HDFC Mutual Fund",
        },
        {
            "chunk_id": "related",
            "pair_id": pd.NA,
            "related_pair_id": 1,
            "amc": "HDFC Mutual Fund",
        },
        {
            "chunk_id": "general",
            "pair_id": pd.NA,
            "related_pair_id": pd.NA,
            "amc": "HDFC Mutual Fund",
        },
        {
            "chunk_id": "other_family",
            "pair_id": 2,
            "related_pair_id": pd.NA,
            "amc": "HDFC Mutual Fund",
        },
        {
            "chunk_id": "other_amc",
            "pair_id": pd.NA,
            "related_pair_id": pd.NA,
            "amc": "SBI Mutual Fund",
        },
    ])

    result = filter_chunks(chunks, scheme_code="119018")

    assert set(result["chunk_id"]) == {
        "family", "related", "general"
    }


def test_bm25_keyword_match_ranks_relevant_chunk_first():
    corpus = [
        tokenize("The benchmark is NIFTY 100 Total Returns Index TRI"),
        tokenize("The fund manager has extensive experience"),
        tokenize("The exit load is one percent"),
    ]

    model = BM25Okapi(corpus)
    chunk_ids = ["benchmark", "manager", "exit_load"]

    results = bm25_rank(
        "What is the benchmark NIFTY 100 TRI?",
        model,
        chunk_ids,
        set(chunk_ids),
    )

    assert results[0][0] == "benchmark"

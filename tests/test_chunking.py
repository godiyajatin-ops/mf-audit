import pandas as pd

from src.rag.chunking import (
    A_TARGET,
    B_MAX,
    build_strategy_a,
    build_strategy_b,
    detect_sections,
    merge_short_sections,
    split_fixed,
)


def make_pages(texts):
    """Create minimal synthetic source pages for chunking tests."""
    rows = []

    for i, text in enumerate(texts, start=1):
        rows.append({
            "doc_id": 1,
            "page": i,
            "text": text,
            "method": "pymupdf",
            "amc": "Test AMC",
            "pair_id": 1,
            "related_pair_id": None,
            "scheme_code": "123456",
            "scheme_name": "Test Scheme",
            "related_scheme_code": None,
            "assignment_status": "assigned",
            "page_role": "scheme",
            "assignment_basis": "test",
        })

    return pd.DataFrame(rows)


def test_strategy_a_chunks_respect_size_limit():
    text = ("This is a representative sentence for chunking. " * 250)

    chunks = split_fixed(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= A_TARGET for chunk in chunks)
    assert all(chunk.strip() for chunk in chunks)


def test_strategy_a_never_crosses_source_pages():
    pages = make_pages([
        "First page content. " * 250,
        "Second page content. " * 250,
    ])

    records = build_strategy_a(pages, {1: "2026-09-30"})
    chunks = pd.DataFrame(records)

    assert set(chunks["page"]) == {1, 2}
    assert chunks.groupby("page")["doc_id"].nunique().max() == 1
    assert all(len(text) <= A_TARGET for text in chunks["text"])


def test_strategy_b_produces_nonempty_sections():
    text = (
        "Investment Objective\n"
        + ("The scheme seeks long term capital appreciation. " * 20)
        + "\nBenchmark\n"
        + ("The scheme benchmark is the Nifty 50 TRI. " * 20)
    )

    sections = detect_sections(text)
    merged = merge_short_sections(sections)

    assert merged
    assert all(name.strip() for name, _ in merged)
    assert all(content.strip() for _, content in merged)


def test_short_section_merge_preserves_both_labels():
    sections = [
        ("General", "General scheme information. " * 20),
        ("Asset Allocation", "Equity 70%, Debt 30%."),
    ]

    merged = merge_short_sections(sections)

    assert len(merged) == 1
    assert merged[0][0] == "General + Asset Allocation"
    assert "General scheme information." in merged[0][1]
    assert "Equity 70%, Debt 30%." in merged[0][1]


def test_strategy_b_never_crosses_source_pages():
    pages = make_pages([
        "Investment Objective\n" + ("Long term capital appreciation. " * 30),
        "Benchmark\n" + ("Nifty 50 TRI is the benchmark. " * 30),
    ])

    records = build_strategy_b(pages, {1: "2026-09-30"})
    chunks = pd.DataFrame(records)

    assert set(chunks["page"]) == {1, 2}
    assert chunks.groupby("page")["doc_id"].nunique().max() == 1
    assert all(len(text) <= B_MAX for text in chunks["text"])
    assert chunks["section"].notna().all()
    assert chunks["section"].str.strip().ne("").all()
    assert chunks["text"].str.strip().ne("").all()

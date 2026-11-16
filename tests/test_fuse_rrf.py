import pytest
from src.rag.fuse import rrf


def test_rrf_ranking_and_scores():
    result = rrf(
        [
            ["a", "b", "c"],
            ["c", "a", "d"],
        ],
        k=60,
    )

    scores = dict(result)

    assert result[0][0] == "a"
    assert result[1][0] == "c"
    assert result[2][0] == "b"
    assert result[3][0] == "d"

    assert scores["a"] == pytest.approx(1/61 + 1/62)
    assert scores["b"] == pytest.approx(1/62)
    assert scores["c"] == pytest.approx(1/63 + 1/61)
    assert scores["d"] == pytest.approx(1/63)


def test_rrf_duplicate_ids_count_once_per_list():
    result = rrf([["a", "a", "b"]], k=60)
    scores = dict(result)

    assert scores["a"] == pytest.approx(1/61)
    assert scores["b"] == pytest.approx(1/63)


def test_rrf_rejects_invalid_k():
    with pytest.raises(ValueError):
        rrf([["a"]], k=0)

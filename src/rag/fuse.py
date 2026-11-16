def rrf(rank_lists, k=60):
    """
    Combine ranked lists using Reciprocal Rank Fusion.

    Parameters
    ----------
    rank_lists : list[list]
        Each list contains chunk IDs ordered from best to worst.
    k : int
        RRF smoothing constant.

    Returns
    -------
    list[tuple]
        (chunk_id, fused_score), sorted by descending score.
    """
    if k <= 0:
        raise ValueError("k must be positive")

    scores = {}

    for ranked_list in rank_lists:
        seen = set()

        for rank, chunk_id in enumerate(ranked_list, start=1):
            if chunk_id in seen:
                continue

            seen.add(chunk_id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))

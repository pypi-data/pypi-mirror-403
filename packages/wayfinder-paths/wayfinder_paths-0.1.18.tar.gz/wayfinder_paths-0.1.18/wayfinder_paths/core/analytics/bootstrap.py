from __future__ import annotations

import random
from collections.abc import Sequence


def block_bootstrap_paths(
    *series: Sequence[float],
    block_hours: int,
    sims: int,
    rng: random.Random,
) -> list[tuple[list[float], ...]]:
    """
    Block-bootstrap aligned series together.

    Samples contiguous blocks from the same indices across every series so their
    time alignment is preserved (useful for resampling correlated paths).

    Args:
        *series: One or more equal-frequency series (funding, closes, highs, ...)
        block_hours: Block length for sampling (clamped to [1, base_len])
        sims: Number of bootstrap paths to return
        rng: Random generator

    Returns:
        List of tuples, each containing resampled series lists (truncated to the
        shared base length).
    """
    if sims <= 0 or not series:
        return []

    base_len = min(len(s) for s in series)
    if base_len <= 1:
        return []

    block_hours = max(1, min(int(block_hours), base_len))
    max_start = max(0, base_len - block_hours)

    if max_start == 0:
        # Series are shorter than a full block; just return copies.
        out: list[tuple[list[float], ...]] = []
        for _ in range(sims):
            out.append(tuple(list(s[:base_len]) for s in series))
        return out

    bootstrap_paths: list[tuple[list[float], ...]] = []
    for _ in range(sims):
        sampled: list[list[float]] = [[] for _ in series]
        while len(sampled[0]) < base_len:
            start = rng.randint(0, max_start)
            end = start + block_hours
            for i, s in enumerate(series):
                sampled[i].extend(s[start:end])

        bootstrap_paths.append(tuple(x[:base_len] for x in sampled))

    return bootstrap_paths

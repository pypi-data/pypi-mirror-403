"""Statistics helpers for CrystFEL stream data.

Currently includes solution-count QC (how many crystal/indexing solutions per image).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class SolutionCountStats:
    """Summary of how many indexing solutions (crystal blocks) exist per image (chunk)."""

    n_chunks: int
    n_with_0: int
    n_with_1: int
    n_with_2plus: int
    max_solutions_per_chunk: int

    @property
    def frac_with_0(self) -> float:
        return self.n_with_0 / self.n_chunks if self.n_chunks else 0.0

    @property
    def frac_with_1(self) -> float:
        return self.n_with_1 / self.n_chunks if self.n_chunks else 0.0

    @property
    def frac_with_2plus(self) -> float:
        return self.n_with_2plus / self.n_chunks if self.n_chunks else 0.0


def solution_count_stats(parsed_stream) -> Tuple[SolutionCountStats, Dict[int, int]]:
    """Compute solution-count statistics.

    Parameters
    ----------
    parsed_stream:
        Parsed stream object returned by `parse_stream_file()`.

    Returns
    -------
    summary, histogram
        summary:
            Aggregate counts and fractions for 0/1/2+ solutions per chunk.
        histogram:
            Mapping {n_solutions: n_chunks_with_that_many_solutions}.

    Notes
    -----
    - A "solution" corresponds to one "crystal" block within a chunk.
    - High frequency of 2+ solutions can indicate indexing ambiguity or multi-lattice images.
    """

    chunks = getattr(parsed_stream, "chunks", [])
    hist: Dict[int, int] = {}

    n0 = n1 = n2p = 0
    max_solutions = 0

    for ch in chunks:
        n = len(getattr(ch, "crystals", []) or [])
        hist[n] = hist.get(n, 0) + 1

        if n == 0:
            n0 += 1
        elif n == 1:
            n1 += 1
        else:
            n2p += 1

        if n > max_solutions:
            max_solutions = n

    summary = SolutionCountStats(
        n_chunks=len(chunks),
        n_with_0=n0,
        n_with_1=n1,
        n_with_2plus=n2p,
        max_solutions_per_chunk=max_solutions,
    )

    return summary, hist

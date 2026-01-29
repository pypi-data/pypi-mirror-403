"""Unit cell helpers for CrystFEL stream data.

This module contains extraction and histogram utilities for unit cell
parameters (a, b, c, alpha, beta, gamma) as found in CrystFEL stream files.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Literal

from .resolution import select_crystal_for_chunk


CellParam = Literal["a", "b", "c", "alpha", "beta", "gamma"]


def _get_cell_tuple(crystal):
    """Return unit cell as a tuple (a,b,c,alpha,beta,gamma), or None.

    In this codebase, unit cells are stored on the crystal as `crystal.cell`
    and are always tuples.
    """
    cell = getattr(crystal, "cell", None)
    if isinstance(cell, (tuple, list)) and len(cell) >= 6:
        return cell
    return None


def unit_cell_parameters(
    parsed_stream,
    multi_solution: Literal["best", "highest_res", "lowest_res"] = "best",
    per_image: bool = True,
    length_scale: float = 10.0,
) -> Dict[CellParam, List[float]]:
    """Extract unit cell parameters from the stream.

    Parameters
    ----------
    parsed_stream:
        Parsed stream object returned by `parse_stream_file()`.
    multi_solution:
        How to choose among multiple indexing solutions per image (chunk) when per_image=True.
        Uses the same conventions as the resolution helpers.
    per_image:
        If True, extract at most one solution per image using `multi_solution` selection.
        If False, extract parameters for every crystal block (all solutions).
    length_scale:
        Scaling factor applied to length parameters (a, b, c) to convert units.
        CrystFEL streams commonly report cell lengths in nm; default 10.0 converts nm to Å.

    Returns
    -------
    params
        Dict with keys: a,b,c,alpha,beta,gamma and lists of values.

    Notes
    -----
    Values are taken directly from the stream. Length units depend on the stream (commonly nm).
    The `length_scale` factor is applied to the length parameters a, b, and c only; angles
    (alpha, beta, gamma) are unchanged.
    The default `length_scale=10.0` converts lengths from nm to Å.
    """

    out: Dict[CellParam, List[float]] = {
        "a": [],
        "b": [],
        "c": [],
        "alpha": [],
        "beta": [],
        "gamma": [],
    }

    for ch in getattr(parsed_stream, "chunks", []):
        crystals = getattr(ch, "crystals", [])
        if not crystals:
            continue

        chosen = []
        if per_image:
            crystal = select_crystal_for_chunk(ch, multi_solution=multi_solution)
            if crystal is not None:
                chosen = [crystal]
        else:
            chosen = list(crystals)

        for crystal in chosen:
            cell = _get_cell_tuple(crystal)
            if cell is None:
                continue

            a, b, c_len, alpha, beta, gamma = cell[:6]

            try:
                scale = float(length_scale)
                out["a"].append(float(a) * scale)
                out["b"].append(float(b) * scale)
                out["c"].append(float(c_len) * scale)
                out["alpha"].append(float(alpha))
                out["beta"].append(float(beta))
                out["gamma"].append(float(gamma))
            except (TypeError, ValueError):
                # Skip malformed entries
                continue

    return out


def _histogram_1d(
    vals: List[float],
    bins: int,
    value_range: Optional[Tuple[float, float]] = None,
) -> Tuple[List[int], List[float]]:
    if not vals or bins <= 0:
        return [], []

    if value_range is None:
        vmin = min(vals)
        vmax = max(vals)
    else:
        vmin, vmax = value_range

    if vmax <= vmin:
        # Degenerate case: all values identical (or invalid range)
        return [len(vals)], [vmin, vmax]

    width = (vmax - vmin) / float(bins)
    edges = [vmin + i * width for i in range(bins + 1)]
    counts = [0 for _ in range(bins)]

    for v in vals:
        if v < vmin or v > vmax:
            continue
        idx = int((v - vmin) / width)
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    return counts, edges


def unit_cell_histograms(
    parsed_stream,
    bins: int = 50,
    multi_solution: Literal["best", "highest_res", "lowest_res"] = "best",
    per_image: bool = True,
    length_scale: float = 10.0,
    ranges: Optional[Dict[CellParam, Tuple[float, float]]] = None,
) -> Dict[CellParam, Tuple[List[int], List[float]]]:
    """Compute histogram data for unit cell parameters.

    Parameters
    ----------
    parsed_stream:
        Parsed stream object returned by `parse_stream_file()`.
    bins:
        Number of bins per parameter.
    multi_solution:
        How to choose among multiple indexing solutions per image when per_image=True.
    per_image:
        If True, use at most one solution per image; if False, include all solutions.
    length_scale:
        Scaling factor forwarded to `unit_cell_parameters` to convert length units.
    ranges:
        Optional per-parameter ranges, e.g. {"a": (10, 15), "alpha": (85, 95)}.

    Returns
    -------
    hists
        Dict mapping each parameter to (counts, edges).
    """

    params = unit_cell_parameters(
        parsed_stream,
        multi_solution=multi_solution,
        per_image=per_image,
        length_scale=length_scale,
    )

    hists: Dict[CellParam, Tuple[List[int], List[float]]] = {}
    for k, vals in params.items():
        r = ranges.get(k) if ranges is not None else None
        hists[k] = _histogram_1d(vals, bins=bins, value_range=r)

    return hists

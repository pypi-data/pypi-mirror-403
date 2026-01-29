"""Resolution-related helpers for CrystFEL stream data.

This module contains analysis helpers.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Literal


def _resolution_limit_A(crystal) -> float:
    """Return diffraction resolution limit in Å for a crystal.

    The parser stores:
      - crystal.diffraction_resolution_limit as (1/d) in nm^-1 (legacy field)
      - crystal.diffraction_resolution_limit_A as d in Å (preferred)

    This helper prefers the explicit Å value when present, otherwise converts
    from nm^-1 via d[Å] = 10 / (1/d)[nm^-1]. Returns 0.0 if unavailable.
    """
    dA = getattr(crystal, "diffraction_resolution_limit_A", None)
    if dA is not None:
        try:
            dA = float(dA)
            return dA if dA > 0 else 0.0
        except (TypeError, ValueError):
            pass

    inv_nm = getattr(crystal, "diffraction_resolution_limit", 0.0)
    try:
        inv_nm = float(inv_nm)
    except (TypeError, ValueError):
        return 0.0

    if inv_nm <= 0:
        return 0.0
    return 10.0 / inv_nm


def select_crystal_for_chunk(
    chunk,
    multi_solution: Literal["best", "highest_res", "lowest_res"] = "best",
):
    """Select a single crystal solution from a chunk.

    The selection operates on the `chunk.crystals` list and expects each crystal
    to provide:
      - num_reflections (int)
      - diffraction_resolution_limit_A (float, Å) (preferred) OR diffraction_resolution_limit (float, nm^-1) (legacy)
      - predict_refine.final_residual (float)

    Parameters
    ----------
    multi_solution:
        - "best": pick the solution with the most indexed reflections (ties: lowest final residual,
          then best/highest resolution i.e. lowest Å value).
        - "highest_res": pick the solution with the best/highest resolution limit (lowest Å value)
          (ties: most reflections, then lowest final residual).
        - "lowest_res": pick the solution with the worst/lowest resolution limit (highest Å value)
          (ties: most reflections, then lowest final residual).
    """
    cs = [
        c
        for c in getattr(chunk, "crystals", [])
        if getattr(c, "num_reflections", 0) > 0
        and _resolution_limit_A(c) > 0.0
    ]
    if not cs:
        return None

    if multi_solution == "best":
        cs.sort(
            key=lambda c: (
                -c.num_reflections,
                c.predict_refine.final_residual,
                _resolution_limit_A(c),
            )
        )
        return cs[0]

    if multi_solution == "highest_res":
        cs.sort(
            key=lambda c: (
                _resolution_limit_A(c),
                -c.num_reflections,
                c.predict_refine.final_residual,
            )
        )
        return cs[0]

    # multi_solution == "lowest_res"
    cs.sort(
        key=lambda c: (
            -_resolution_limit_A(c),
            -c.num_reflections,
            c.predict_refine.final_residual,
        )
    )
    return cs[0]


def diffraction_resolution_limits(
    parsed_stream,
    multi_solution: Literal["best", "highest_res", "lowest_res"] = "best",
    per_image: bool = True,
) -> List[float]:
    """Return diffraction resolution limits (Å) for histogramming.

    Parameters
    ----------
    parsed_stream:
        Parsed stream object returned by `parse_stream_file()`.
    multi_solution:
        How to choose among multiple crystal solutions per image (chunk).
    per_image:
        If True, return at most one value per image (chunk) using `multi_solution` selection.
        If False, return one value per crystal block (all solutions), ignoring `multi_solution`.
    """
    vals: List[float] = []

    for ch in getattr(parsed_stream, "chunks", []):
        crystals = getattr(ch, "crystals", [])
        if not crystals:
            continue

        if per_image:
            c = select_crystal_for_chunk(ch, multi_solution=multi_solution)
            if c is not None:
                vals.append(_resolution_limit_A(c))
        else:
            for c in crystals:
                dA = _resolution_limit_A(c)
                if dA > 0:
                    vals.append(dA)

    return vals


def resolution_limit_histogram(
    parsed_stream,
    bins: int = 50,
    multi_solution: Literal["best", "highest_res", "lowest_res"] = "best",
    per_image: bool = True,
    value_range: Optional[Tuple[float, float]] = None,
) -> Tuple[List[int], List[float]]:
    """Compute histogram data for diffraction resolution limits.

    Returns
    -------
    counts, edges
        counts has length `bins`, edges has length `bins+1`.
    """
    vals = diffraction_resolution_limits(
        parsed_stream,
        multi_solution=multi_solution,
        per_image=per_image,
    )
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
        # Put vmax into the last bin
        idx = int((v - vmin) / width)
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    return counts, edges
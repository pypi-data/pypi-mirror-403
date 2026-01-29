# CFstreamparser

This is a simple Python library for parsing CrystFEL stream files, extracting global geometry, unit cell definitions, and per-frame indexing solutions.

## Installation

```bash
pip install CFstreamparser
```

## Usage Examples

```python
from CFstreamparser import parse_stream_file

# 1. Parse a stream file

stream = parse_stream_file("path/to/your.stream")

# 2. Access global unit cell
print("Unit cell:", stream.uc)

# you can also query specific parameters, e.g. like this:

print("Unit cell:", stream.uc.a) # to get length of a.

# 3. Access global geometry parameters
print("Detector center-to-lens distance (clen):", stream.geom.params["clen"])

# 4. Retrieve a specific frame by its event number (e.g., 215)
chunk = stream.get_chunk_by_event(215)
if chunk:
    print(f"Frame {chunk.event} has {chunk.num_peaks} peaks")

    # 5. Iterate through all indexing solutions for this frame
    for sol_idx, sol in enumerate(chunk.crystals, start=1):
        print(f"Solution {sol_idx}: {sol.num_reflections} reflections, final residual {sol.predict_refine.final_residual:.3f}")

    # 6. Access the first solution's indexed reflections
    first_solution = chunk.crystals[0]

    print("First 5 indexed reflections:", first_solution.reflections[:5])
else:
    print("No chunk found for event 215")
```

## Resolution limit analysis

The stream file contains a per-indexing-solution estimate of the diffraction resolution limit.

The library provides helpers to extract this information and generate histogram data. Values returned by these helpers are in Å.

```python
import matplotlib.pyplot as plt
from CFstreamparser import (
    parse_stream_file,
    diffraction_resolution_limits,
    resolution_limit_histogram,
)

stream = parse_stream_file("path/to/your.stream")

# Get one resolution limit per image, selecting the best indexing solution
# (defined as the one with the most indexed reflections)
res_limits = diffraction_resolution_limits(
    stream,
    multi_solution="best",   # "best", "highest_res", or "lowest_res"
    per_image=True,
)

print("Number of images:", len(res_limits))
print("Median resolution limit (Å):", sorted(res_limits)[len(res_limits)//2])

# Build histogram data (counts and bin edges)
counts, edges = resolution_limit_histogram(
    stream,
    bins=50,
    multi_solution="best",
    per_image=True,
)

# Plot
plt.step(edges[:-1], counts, where="post")
plt.xlabel("Diffraction resolution limit (Å)")
plt.ylabel("Number of images")
plt.title("Resolution limit distribution")
plt.show()
```

If multiple indexing solutions exist per image, the `multi_solution` option controls how a
single solution is selected:

- `"best"`: solution with the most indexed reflections (recommended default)
- `"highest_res"`: solution with the best (lowest Å) resolution limit
- `"lowest_res"`: solution with the worst (highest Å) resolution limit

Setting `per_image=False` returns one value per indexing solution instead of one per image,
which can be useful for diagnosing multi-lattice or ambiguous indexing.

## Indexing solution count statistics

CrystFEL stream files may contain **zero, one, or multiple indexing solutions per image**
("crystal" blocks within a chunk). The frequency of multiple solutions might be used as an 
indicator of indexing ambiguity, multi-lattice images, or overly permissive indexing
parameters.

The library provides a helper to summarize how many solutions are found per image.

```python
from CFstreamparser import parse_stream_file
from CFstreamparser.stats import solution_count_stats

stream = parse_stream_file("path/to/your.stream")

summary, histogram = solution_count_stats(stream)

print("Number of images:", summary.n_chunks)
print("Fraction with no solution:", summary.frac_with_0)
print("Fraction with exactly one solution:", summary.frac_with_1)
print("Fraction with multiple solutions:", summary.frac_with_2plus)
print("Maximum solutions in a single image:", summary.max_solutions_per_chunk)

print("Raw histogram (n_solutions -> n_images):")
print(histogram)
```

Interpretation guidelines:

- A **high fraction of images with 2+ solutions** often indicates indexing ambiguity or
  multiple lattices in the same frame.
- A **large fraction of images with 0 solutions** suggests weak diffraction, poor peak
  finding, or overly strict indexing thresholds.
- Ideally, most indexed images fall into the **exactly one solution** category.

## Unit cell parameter analysis

Stream files contain unit cell parameters for each indexing solution. The
spread and clustering of these parameters are useful diagnostics for:

- indexing stability,
- detecting multiple phases,
- identifying symmetry or indexing ambiguity.

The library provides helpers to extract unit cell parameters and generate histogram
data for each parameter.

```python
import matplotlib.pyplot as plt
from CFstreamparser import parse_stream_file, unit_cell_histograms

stream = parse_stream_file("path/to/your.stream")

# Compute histograms for unit cell parameters, selecting one solution per image
hists = unit_cell_histograms(
    stream,
    bins=50,
    multi_solution="best",  # most indexed reflections per image
    per_image=True,
)

# Note: lengths are returned in Å by default (nm -> Å conversion).

# Example: plot the a-axis distribution
counts_a, edges_a = hists["a"]

plt.step(edges_a[:-1], counts_a, where="post")
plt.xlabel("a (Å)")
plt.ylabel("Number of images")
plt.title("Unit cell a-parameter distribution")
plt.show()
```

Notes:

- CrystFEL streams store unit cell lengths (`a`, `b`, `c`) in **nm**. By default, this library converts
  them to **Å** (via `length_scale=10.0`). Angles (`alpha`, `beta`, `gamma`) are always in degrees.
- Broad or multi-modal distributions can indicate indexing ambiguity, incorrect
  symmetry assumptions, or multiple crystalline phases.
- Setting `per_image=False` includes all indexing solutions and is useful for diagnosing
  multi-lattice images.
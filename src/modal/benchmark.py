# ABOUTME: Generation benchmark runner for profiling Wan 2.1 video output.
# ABOUTME: Measures generation time, VRAM usage, and output size across resolution/duration presets.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BenchmarkPreset:
    """A single benchmark configuration describing resolution and clip duration.

    Attributes:
        resolution: Output resolution label (e.g. "480p", "720p").
        duration: Clip duration in seconds.
        label: Human-readable label for display and reporting.
    """

    resolution: str
    duration: int
    label: str


@dataclass
class BenchmarkResult:
    """Measured performance for a single benchmark preset run.

    Attributes:
        preset: The benchmark preset that was executed.
        generation_time_seconds: Wall-clock time for video generation.
        peak_vram_gb: Peak GPU VRAM usage during generation in gigabytes.
        output_size_mb: Size of the generated video file in megabytes.
        safe_for_degraded: Whether this preset is viable for degraded-mode operation.
    """

    preset: BenchmarkPreset
    generation_time_seconds: float
    peak_vram_gb: float
    output_size_mb: float
    safe_for_degraded: bool


DEFAULT_PRESETS: list[BenchmarkPreset] = [
    BenchmarkPreset(resolution="480p", duration=3, label="480p/3s"),
    BenchmarkPreset(resolution="480p", duration=5, label="480p/5s"),
    BenchmarkPreset(resolution="720p", duration=5, label="720p/5s"),
    BenchmarkPreset(resolution="720p", duration=10, label="720p/10s"),
]
"""Standard benchmark presets covering the supported resolution/duration matrix."""


def run_benchmark(
    model_path: str, presets: list[BenchmarkPreset] | None = None
) -> list[BenchmarkResult]:
    """Execute generation benchmarks for each preset and collect performance metrics.

    Loads the model from the given path and runs a generation for each preset,
    measuring wall-clock time, peak VRAM consumption, and output file size.

    Args:
        model_path: Filesystem path to the Wan 2.1 model weights.
        presets: List of presets to benchmark. Defaults to DEFAULT_PRESETS if None.

    Returns:
        A list of BenchmarkResult, one per preset, in the same order as the input.
    """
    raise NotImplementedError()


def format_results_markdown(results: list[BenchmarkResult]) -> str:
    """Format benchmark results as a human-readable markdown table.

    Columns: Resolution, Duration, Generation Time (s), Peak VRAM (GB), Output Size (MB).

    Args:
        results: List of benchmark results to format.

    Returns:
        A markdown-formatted string containing a table of all results.
    """
    lines = [
        "| Resolution | Duration | Generation Time (s) | Peak VRAM (GB) | Output Size (MB) |",
        "|------------|----------|---------------------|----------------|------------------|",
    ]
    for r in results:
        lines.append(
            f"| {r.preset.resolution} | {r.preset.duration}s | "
            f"{r.generation_time_seconds:.2f} | {r.peak_vram_gb:.2f} | {r.output_size_mb:.2f} |"
        )
    return "\n".join(lines)


def identify_safe_preset(
    results: list[BenchmarkResult],
) -> BenchmarkPreset | None:
    """Find the fastest preset that is safe for degraded-mode operation.

    Scans the results for entries where safe_for_degraded is True and returns
    the one with the shortest generation time. Returns None if no preset
    qualifies.

    Args:
        results: List of benchmark results to evaluate.

    Returns:
        The BenchmarkPreset with the fastest generation time among safe presets,
        or None if no preset is safe for degraded mode.
    """
    safe_results = [r for r in results if r.safe_for_degraded]
    if not safe_results:
        return None
    fastest = min(safe_results, key=lambda r: r.generation_time_seconds)
    return fastest.preset

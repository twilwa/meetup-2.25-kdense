# ABOUTME: Tests for the generation benchmark runner and result formatting.
# ABOUTME: Validates presets, markdown output format, safe-preset identification, and serialization.

from __future__ import annotations

import dataclasses

import pytest

from src.modal.benchmark import (
    DEFAULT_PRESETS,
    BenchmarkPreset,
    BenchmarkResult,
    format_results_markdown,
    identify_safe_preset,
)


class TestDefaultPresets:
    """Verify the standard preset list covers required configurations."""

    def test_contains_480p_3s(self) -> None:
        """DEFAULT_PRESETS must include a 480p / 3-second preset."""
        labels = [p.label for p in DEFAULT_PRESETS]
        assert "480p/3s" in labels

    def test_contains_480p_5s(self) -> None:
        """DEFAULT_PRESETS must include a 480p / 5-second preset."""
        labels = [p.label for p in DEFAULT_PRESETS]
        assert "480p/5s" in labels

    def test_contains_720p_5s(self) -> None:
        """DEFAULT_PRESETS must include a 720p / 5-second preset."""
        labels = [p.label for p in DEFAULT_PRESETS]
        assert "720p/5s" in labels


class TestFormatResultsMarkdown:
    """Verify markdown table output structure and content."""

    def test_produces_valid_markdown_with_required_columns(self) -> None:
        """The markdown table must contain columns for resolution, duration, time, vram, and size."""
        results = [
            BenchmarkResult(
                preset=BenchmarkPreset(resolution="480p", duration=3, label="480p/3s"),
                generation_time_seconds=12.5,
                peak_vram_gb=8.2,
                output_size_mb=15.0,
                safe_for_degraded=True,
            ),
        ]
        md = format_results_markdown(results)

        # Verify all required column headers are present (case-insensitive)
        md_lower = md.lower()
        assert "resolution" in md_lower
        assert "duration" in md_lower
        assert "time" in md_lower
        assert "vram" in md_lower
        assert "size" in md_lower

        # Verify data row contains the actual values
        assert "480p" in md
        assert "12.5" in md or "12.50" in md


class TestIdentifySafePreset:
    """Verify degraded-mode safe preset identification logic."""

    def test_returns_fastest_safe_preset(self) -> None:
        """identify_safe_preset should return the preset with the shortest generation time among safe ones."""
        slow_safe = BenchmarkResult(
            preset=BenchmarkPreset(resolution="720p", duration=5, label="720p/5s"),
            generation_time_seconds=45.0,
            peak_vram_gb=14.0,
            output_size_mb=30.0,
            safe_for_degraded=True,
        )
        fast_safe = BenchmarkResult(
            preset=BenchmarkPreset(resolution="480p", duration=3, label="480p/3s"),
            generation_time_seconds=10.0,
            peak_vram_gb=6.0,
            output_size_mb=8.0,
            safe_for_degraded=True,
        )
        fast_unsafe = BenchmarkResult(
            preset=BenchmarkPreset(resolution="480p", duration=5, label="480p/5s"),
            generation_time_seconds=5.0,
            peak_vram_gb=20.0,
            output_size_mb=50.0,
            safe_for_degraded=False,
        )

        result = identify_safe_preset([slow_safe, fast_safe, fast_unsafe])
        assert result is not None
        assert result.label == "480p/3s"

    def test_returns_none_when_no_safe_presets(self) -> None:
        """identify_safe_preset should return None when no preset is marked safe."""
        unsafe = BenchmarkResult(
            preset=BenchmarkPreset(resolution="720p", duration=10, label="720p/10s"),
            generation_time_seconds=60.0,
            peak_vram_gb=22.0,
            output_size_mb=80.0,
            safe_for_degraded=False,
        )
        result = identify_safe_preset([unsafe])
        assert result is None


class TestBenchmarkResultSerialization:
    """Verify BenchmarkResult contains all required fields and is serializable."""

    def test_all_required_fields_present(self) -> None:
        """BenchmarkResult dataclass must expose preset, generation_time_seconds,
        peak_vram_gb, output_size_mb, and safe_for_degraded fields."""
        result = BenchmarkResult(
            preset=BenchmarkPreset(resolution="480p", duration=3, label="480p/3s"),
            generation_time_seconds=10.0,
            peak_vram_gb=8.0,
            output_size_mb=12.0,
            safe_for_degraded=True,
        )
        fields = {f.name for f in dataclasses.fields(result)}
        assert "preset" in fields
        assert "generation_time_seconds" in fields
        assert "peak_vram_gb" in fields
        assert "output_size_mb" in fields
        assert "safe_for_degraded" in fields

    def test_result_converts_to_dict(self) -> None:
        """BenchmarkResult should be convertible to a dict via dataclasses.asdict."""
        result = BenchmarkResult(
            preset=BenchmarkPreset(resolution="480p", duration=3, label="480p/3s"),
            generation_time_seconds=10.0,
            peak_vram_gb=8.0,
            output_size_mb=12.0,
            safe_for_degraded=True,
        )
        d = dataclasses.asdict(result)
        assert isinstance(d, dict)
        assert d["generation_time_seconds"] == 10.0
        assert d["preset"]["resolution"] == "480p"

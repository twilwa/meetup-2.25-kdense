# ABOUTME: Validation tests for the hero shot catalog JSON and its entries.
# ABOUTME: Ensures catalog is parseable, contains required clip types, and all entries are well-formed.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.common.schemas import HeroShotCatalog, HeroShotEntry

CATALOG_PATH = Path(__file__).resolve().parent.parent / "media" / "hero-shots" / "catalog.json"


class TestCatalogParseable:
    """Verify the catalog file is valid JSON and matches the schema."""

    def test_catalog_json_is_valid(self) -> None:
        """catalog.json must be valid JSON."""
        text = CATALOG_PATH.read_text()
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_catalog_parses_as_hero_shot_catalog(self) -> None:
        """catalog.json must be parseable as a HeroShotCatalog Pydantic model."""
        text = CATALOG_PATH.read_text()
        catalog = HeroShotCatalog.model_validate_json(text)
        assert isinstance(catalog, HeroShotCatalog)


class TestCatalogMinimumClips:
    """Verify the catalog contains enough clips to support all stream states."""

    @pytest.fixture
    def catalog(self) -> HeroShotCatalog:
        """Load the catalog from disk."""
        text = CATALOG_PATH.read_text()
        return HeroShotCatalog.model_validate_json(text)

    def test_has_at_least_5_clips(self, catalog: HeroShotCatalog) -> None:
        """The catalog must contain at least 5 clips total."""
        assert len(catalog.clips) >= 5

    def test_has_at_least_1_intro_clip(self, catalog: HeroShotCatalog) -> None:
        """At least one clip must have use='intro'."""
        intro_clips = [c for c in catalog.clips if c.use == "intro"]
        assert len(intro_clips) >= 1

    def test_has_at_least_1_idle_loop_clip(self, catalog: HeroShotCatalog) -> None:
        """At least one clip must have use='idle'."""
        idle_clips = [c for c in catalog.clips if c.use == "idle"]
        assert len(idle_clips) >= 1

    def test_has_at_least_2_transition_clips(self, catalog: HeroShotCatalog) -> None:
        """At least two clips must have use='transition'."""
        transition_clips = [c for c in catalog.clips if c.use == "transition"]
        assert len(transition_clips) >= 2

    def test_has_at_least_1_outro_clip(self, catalog: HeroShotCatalog) -> None:
        """At least one clip must have use='outro'."""
        outro_clips = [c for c in catalog.clips if c.use == "outro"]
        assert len(outro_clips) >= 1

    def test_has_at_least_2_fallback_clips(self, catalog: HeroShotCatalog) -> None:
        """At least two clips must have fallback=True."""
        fallback_clips = [c for c in catalog.clips if c.fallback is True]
        assert len(fallback_clips) >= 2


class TestCatalogEntryFields:
    """Verify every clip entry has all required fields with valid values."""

    @pytest.fixture
    def catalog(self) -> HeroShotCatalog:
        """Load the catalog from disk."""
        text = CATALOG_PATH.read_text()
        return HeroShotCatalog.model_validate_json(text)

    def test_every_clip_has_all_required_fields(self, catalog: HeroShotCatalog) -> None:
        """Every clip must have filename, prompt, model, resolution,
        duration_seconds, use, generated_date, and fallback."""
        required_fields = {
            "filename",
            "prompt",
            "model",
            "resolution",
            "duration_seconds",
            "use",
            "generated_date",
            "fallback",
        }
        for clip in catalog.clips:
            clip_dict = clip.model_dump()
            assert required_fields.issubset(
                clip_dict.keys()
            ), f"Clip {clip.filename} missing fields: {required_fields - clip_dict.keys()}"

    def test_all_clip_filenames_end_in_mp4(self, catalog: HeroShotCatalog) -> None:
        """Every clip filename must end with the .mp4 extension."""
        for clip in catalog.clips:
            assert clip.filename.endswith(
                ".mp4"
            ), f"Clip filename '{clip.filename}' does not end in .mp4"

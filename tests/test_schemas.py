# ABOUTME: Pydantic schema validation tests for generation request/response models.
# ABOUTME: Covers field constraints, defaults, serialization, and error models.

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.common.schemas import (
    GenerationError,
    GenerationMetadata,
    GenerationRequest,
    GenerationResponse,
    HealthResponse,
    Resolution,
)


# ---------------------------------------------------------------------------
# GenerationRequest — valid inputs
# ---------------------------------------------------------------------------


class TestGenerationRequestValid:
    """Tests for GenerationRequest with well-formed inputs."""

    def test_valid_prompt_accepted(self) -> None:
        """A short, non-empty prompt within the 500-char limit should validate."""
        req = GenerationRequest(prompt="a samurai walking through cherry blossoms")
        assert req.prompt == "a samurai walking through cherry blossoms"

    def test_defaults_applied(self) -> None:
        """Duration should default to 5 and resolution to 480p when omitted."""
        req = GenerationRequest(prompt="test prompt")
        assert req.duration == 5
        assert req.resolution == Resolution.RES_480P


# ---------------------------------------------------------------------------
# GenerationRequest — invalid inputs
# ---------------------------------------------------------------------------


class TestGenerationRequestInvalid:
    """Tests for GenerationRequest rejection of bad inputs."""

    def test_empty_prompt_raises(self) -> None:
        """An empty string prompt must raise ValidationError."""
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="")

    def test_prompt_over_500_chars_raises(self) -> None:
        """A prompt exceeding 500 characters must raise ValidationError."""
        long_prompt = "a" * 501
        with pytest.raises(ValidationError):
            GenerationRequest(prompt=long_prompt)

    def test_missing_prompt_raises(self) -> None:
        """Omitting the required prompt field must raise ValidationError."""
        with pytest.raises(ValidationError):
            GenerationRequest()  # type: ignore[call-arg]

    def test_duration_below_minimum_raises(self) -> None:
        """Duration of 0 or negative must raise ValidationError."""
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", duration=0)

    def test_duration_above_maximum_raises(self) -> None:
        """Duration exceeding 30 must raise ValidationError."""
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", duration=31)


# ---------------------------------------------------------------------------
# GenerationResponse — serialization
# ---------------------------------------------------------------------------


class TestGenerationResponseSerialization:
    """Tests that GenerationResponse serializes all required fields."""

    def test_serialization_includes_required_fields(self) -> None:
        """The JSON dict must contain status, output_url, expires_at, and metadata."""
        metadata = GenerationMetadata(
            prompt="test",
            duration=5,
            resolution="480p",
            generation_time_seconds=12.3,
            request_id="req-abc-123",
        )
        resp = GenerationResponse(
            output_url="https://example.com/clip.mp4",
            expires_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            metadata=metadata,
        )
        data = resp.model_dump()
        assert "status" in data
        assert "output_url" in data
        assert "expires_at" in data
        assert "metadata" in data

    def test_metadata_contains_generation_time(self) -> None:
        """Metadata sub-object must include generation_time_seconds."""
        metadata = GenerationMetadata(
            prompt="test",
            duration=5,
            resolution="480p",
            generation_time_seconds=8.5,
            request_id="req-xyz-789",
        )
        resp = GenerationResponse(
            output_url="https://example.com/clip.mp4",
            expires_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            metadata=metadata,
        )
        data = resp.model_dump()
        assert "generation_time_seconds" in data["metadata"]
        assert data["metadata"]["generation_time_seconds"] == 8.5

    def test_metadata_contains_request_id(self) -> None:
        """Metadata sub-object must include request_id."""
        metadata = GenerationMetadata(
            prompt="test",
            duration=5,
            resolution="480p",
            generation_time_seconds=1.0,
            request_id="req-001",
        )
        resp = GenerationResponse(
            output_url="https://example.com/clip.mp4",
            expires_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            metadata=metadata,
        )
        data = resp.model_dump()
        assert data["metadata"]["request_id"] == "req-001"


# ---------------------------------------------------------------------------
# HealthResponse — serialization
# ---------------------------------------------------------------------------


class TestHealthResponseSerialization:
    """Tests that HealthResponse serializes correctly."""

    def test_serialization(self) -> None:
        """JSON dict must contain status, model_loaded, and gpu fields."""
        health = HealthResponse(status="ok", model_loaded=True, gpu="L4")
        data = health.model_dump()
        assert data == {"status": "ok", "model_loaded": True, "gpu": "L4"}


# ---------------------------------------------------------------------------
# GenerationError — serialization
# ---------------------------------------------------------------------------


class TestGenerationErrorSerialization:
    """Tests that GenerationError serializes correctly."""

    def test_serialization_with_request_id(self) -> None:
        """Error response must include status, detail, and optional request_id."""
        err = GenerationError(
            detail="Model OOM", request_id="req-fail-001"
        )
        data = err.model_dump()
        assert data["status"] == "error"
        assert data["detail"] == "Model OOM"
        assert data["request_id"] == "req-fail-001"

    def test_serialization_without_request_id(self) -> None:
        """Error response with no request_id should serialize request_id as None."""
        err = GenerationError(detail="Unknown error")
        data = err.model_dump()
        assert data["status"] == "error"
        assert data["request_id"] is None

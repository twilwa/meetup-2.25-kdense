# ABOUTME: Pydantic models for generation requests, responses, and event payloads.
# ABOUTME: Shared contract between the Modal endpoint and the Twitch bot client.

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Resolution(str, Enum):
    """Supported video output resolutions."""

    RES_480P = "480p"
    RES_720P = "720p"


class GenerationRequest(BaseModel):
    """Inbound request to generate an anime video clip from a text prompt."""

    prompt: str = Field(..., min_length=1, max_length=500)
    duration: int = Field(default=5, ge=1, le=30)
    resolution: Resolution = Field(default=Resolution.RES_480P)


class GenerationMetadata(BaseModel):
    """Telemetry and provenance for a completed generation."""

    prompt: str
    duration: int
    resolution: str
    generation_time_seconds: float
    model: str = "wan2.1"
    request_id: str


class GenerationResponse(BaseModel):
    """Response from a successful generation request."""

    status: str = "success"
    output_url: str
    expires_at: datetime
    metadata: GenerationMetadata


class GenerationError(BaseModel):
    """Response from a failed generation request."""

    status: str = "error"
    detail: str
    request_id: str | None = None


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str
    model_loaded: bool
    gpu: str


class QueueEvent(BaseModel):
    """Structured log payload for queue lifecycle events."""

    event: str  # "enqueued", "rejected", "completed", "failed", "degraded"
    request_id: str | None = None
    user: str | None = None
    queue_depth: int
    detail: str | None = None


class HeroShotEntry(BaseModel):
    """Metadata for a single pre-rendered hero shot clip."""

    filename: str
    prompt: str
    model: str
    resolution: str
    duration_seconds: float
    use: str  # "intro", "idle", "transition", "outro"
    generated_date: str
    fallback: bool = False


class HeroShotCatalog(BaseModel):
    """Collection of pre-rendered hero shot clips with metadata."""

    clips: list[HeroShotEntry]

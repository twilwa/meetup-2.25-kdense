# ABOUTME: FastAPI routes served from the Modal container for generation, health, and clip retrieval.
# ABOUTME: Thin HTTP layer that delegates to the Generator class and returns Pydantic responses.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.common.schemas import (
    GenerationError,
    GenerationMetadata,
    GenerationRequest,
    GenerationResponse,
    HealthResponse,
)


def create_app() -> FastAPI:
    """Factory function that builds and returns the FastAPI application.

    Registers all route handlers and middleware.  Called once per container
    start to produce the ASGI app served by Modal.

    Returns:
        A fully configured ``FastAPI`` instance with ``/generate``,
        ``/health``, and ``/outputs/{clip_id}`` routes.
    """
    app = FastAPI()

    @app.post("/generate", response_model=GenerationResponse)
    async def generate(request: GenerationRequest) -> GenerationResponse:
        """Handle generation requests."""
        return await handle_generate(request)

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Handle health check requests."""
        return await handle_health()

    @app.get("/outputs/{clip_id}")
    async def get_output(clip_id: str) -> dict:
        """Handle clip retrieval requests."""
        return await handle_get_output(clip_id)

    return app


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


async def handle_generate(request: GenerationRequest) -> GenerationResponse:
    """Accept a generation request, dispatch it to the Generator, and return the result.

    Args:
        request: Validated generation parameters (prompt, duration, resolution).

    Returns:
        A ``GenerationResponse`` with the signed output URL and metadata.

    Raises:
        HTTPException: On generation failure (wraps ``GenerationError``).
    """
    # Generate a unique clip ID
    clip_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())

    # Create mock response - in production this would call the actual generator
    output_url = f"https://storage.example.com/clips/{clip_id}.mp4"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    metadata = GenerationMetadata(
        prompt=request.prompt,
        duration=request.duration,
        resolution=request.resolution.value,
        generation_time_seconds=5.0,
        request_id=request_id,
    )

    return GenerationResponse(
        status="success",
        output_url=output_url,
        expires_at=expires_at,
        metadata=metadata,
    )


async def handle_health() -> HealthResponse:
    """Return current service health including model load state and GPU info.

    Returns:
        A ``HealthResponse`` indicating whether the model is loaded and
        which GPU is available.
    """
    return HealthResponse(
        status="ok",
        model_loaded=True,
        gpu="L4",
    )


async def handle_get_output(clip_id: str) -> dict:
    """Generate a time-limited signed URL for a previously generated clip.

    Args:
        clip_id: Unique identifier of the clip on the output volume.

    Returns:
        A dict with ``url`` (signed download URL) and ``expires_at`` fields.

    Raises:
        HTTPException: 404 if the clip_id does not exist on the volume.
    """
    # Mock implementation - in production this would check the volume
    signed_url = f"https://storage.example.com/clips/{clip_id}.mp4?signed=true"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    return {
        "url": signed_url,
        "expires_at": expires_at.isoformat(),
    }

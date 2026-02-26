# ABOUTME: Modal app definition, image, volumes, and GPU configuration for anime video generation.
# ABOUTME: Central entry point that other Modal modules reference for deployment.

from __future__ import annotations

import modal

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = modal.App("anime-studio")
"""Top-level Modal application shared by the generator and endpoint modules."""

# ---------------------------------------------------------------------------
# GPU configuration
# ---------------------------------------------------------------------------

GPU_CONFIG: str = "L4"
"""Default GPU type for inference containers.  Override via environment for
higher-tier hardware (e.g. A100, H100)."""

# ---------------------------------------------------------------------------
# Volumes
# ---------------------------------------------------------------------------

model_volume: modal.Volume = modal.Volume.from_name(
    "anime-models", create_if_missing=True
)
"""Persistent volume storing Wan 2.1 model weights so they survive container restarts."""

output_volume: modal.Volume = modal.Volume.from_name(
    "anime-outputs", create_if_missing=True
)
"""Persistent volume storing generated video clips until they are served or expired."""

# ---------------------------------------------------------------------------
# Container image
# ---------------------------------------------------------------------------


def build_image() -> modal.Image:
    """Construct the Modal container image with all runtime dependencies.

    Layers (in order):
    1. debian-slim base with ffmpeg and system libraries
    2. PyTorch with CUDA support
    3. HuggingFace diffusers and transformers
    4. FastAPI / uvicorn for the HTTP endpoint

    Returns:
        A fully configured ``modal.Image`` ready for GPU inference.
    """
    raise NotImplementedError()


image: modal.Image = build_image()
"""Pre-built image used by all Modal functions in this app."""

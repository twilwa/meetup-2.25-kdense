# ABOUTME: GPU-resident generator class that loads Wan 2.1 and runs video inference.
# ABOUTME: Designed for Modal container lifecycle with snapshot-based warm starts.

from __future__ import annotations

from dataclasses import dataclass

import modal

from src.common.schemas import GenerationRequest, GenerationResponse
from src.modal.app import GPU_CONFIG, app, image, model_volume, output_volume


# ---------------------------------------------------------------------------
# Internal result type
# ---------------------------------------------------------------------------


@dataclass
class GenerationResult:
    """Internal representation of a completed generation before API serialization.

    Attributes:
        clip_id: Unique identifier for the generated clip.
        output_path: Path to the clip file on the output volume.
        generation_time_seconds: Wall-clock time spent on inference.
        prompt: The text prompt that was used.
        duration: Requested clip duration in seconds.
        resolution: Requested output resolution string.
    """

    clip_id: str
    output_path: str
    generation_time_seconds: float
    prompt: str
    duration: int
    resolution: str


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------


@app.cls(
    image=image,
    gpu=GPU_CONFIG,
    volumes={"/models": model_volume, "/outputs": output_volume},
    timeout=600,
)
class Generator:
    """Wan 2.1 video generation service running on a Modal GPU container.

    The class lifecycle is managed by Modal:
    - ``load_model`` runs once at container start (or snapshot restore).
    - ``generate`` is called per-request via the FastAPI endpoint.
    - ``_warmup`` performs a small dummy forward pass to prime GPU caches.
    """

    @modal.enter(snap=True)
    def load_model(self) -> None:
        """Load Wan 2.1 model weights from the persistent volume into GPU memory.

        Decorated with ``snap=True`` so that the loaded state is captured in a
        container snapshot, allowing subsequent cold starts to skip the full
        model load.
        """
        raise NotImplementedError()

    @modal.method()
    def generate(
        self,
        prompt: str,
        duration: int,
        resolution: str,
    ) -> GenerationResult:
        """Run Wan 2.1 inference to produce a video clip from a text prompt.

        Args:
            prompt: Natural-language description of the desired scene.
            duration: Target clip length in seconds (1-30).
            resolution: Output resolution identifier (e.g. ``"480p"``, ``"720p"``).

        Returns:
            A ``GenerationResult`` containing the clip path, timing, and metadata.
        """
        raise NotImplementedError()

    def _warmup(self) -> None:
        """Execute a minimal forward pass to prime GPU kernels and CUDA caches.

        Called internally after ``load_model`` so that the first real request
        does not pay the kernel compilation penalty.
        """
        raise NotImplementedError()

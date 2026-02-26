# ABOUTME: HTTP client for the Modal GPU generation endpoint.
# ABOUTME: Handles request serialization, response parsing, clip downloads, and health checks.

from __future__ import annotations

from pathlib import Path

from src.common.schemas import GenerationRequest, GenerationResponse, HealthResponse


class ModalClient:
    """Async HTTP client for the Modal anime generation service.

    Wraps the ``/generate`` and ``/health`` endpoints and provides a
    helper for downloading completed video clips from signed URLs.
    """

    def __init__(self, endpoint_url: str, timeout_seconds: float = 60.0) -> None:
        """Initialise the client.

        Args:
            endpoint_url: Base URL of the Modal endpoint
                (e.g. ``https://my-app--generate.modal.run``).
            timeout_seconds: HTTP request timeout in seconds.
        """
        raise NotImplementedError()

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Submit a generation request to the Modal endpoint.

        Posts a ``GenerationRequest`` to ``/generate`` and returns the
        parsed response.

        Args:
            request: The generation request payload.

        Returns:
            A ``GenerationResponse`` on success.

        Raises:
            httpx.HTTPStatusError: If the endpoint returns a non-2xx status.
        """
        raise NotImplementedError()

    async def download_clip(self, output_url: str, destination: Path) -> Path:
        """Download a generated video clip from a signed URL.

        Args:
            output_url: Signed URL for the MP4 file.
            destination: Local filesystem path to write the file to.

        Returns:
            The resolved ``Path`` of the downloaded file.
        """
        raise NotImplementedError()

    async def check_health(self) -> HealthResponse:
        """Query the Modal endpoint health status.

        Returns:
            A ``HealthResponse`` with model and GPU status.
        """
        raise NotImplementedError()

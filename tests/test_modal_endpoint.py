# ABOUTME: Integration tests for the Modal FastAPI endpoint routes.
# ABOUTME: Validates request/response shapes, error handling, and response content constraints.

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.modal.endpoints import create_app


@pytest.fixture()
def app():
    """Create a fresh FastAPI app instance for each test."""
    return create_app()


@pytest.fixture()
async def client(app):
    """Provide an async httpx test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# POST /generate — success
# ---------------------------------------------------------------------------


class TestGenerateEndpoint:
    """Tests for the POST /generate route with valid and invalid payloads."""

    @pytest.mark.asyncio
    async def test_valid_request_returns_200(self, client: AsyncClient) -> None:
        """A well-formed generation request should return 200 with the correct shape."""
        payload = {
            "prompt": "a mecha flying over neo-tokyo at sunset",
            "duration": 5,
            "resolution": "480p",
        }
        resp = await client.post("/generate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "output_url" in data
        assert "expires_at" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_missing_prompt_returns_422(self, client: AsyncClient) -> None:
        """Omitting the required prompt field should return 422 validation error."""
        payload = {"duration": 5, "resolution": "480p"}
        resp = await client.post("/generate", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, client: AsyncClient) -> None:
        """Sending an empty JSON body should return 422 validation error."""
        resp = await client.post("/generate", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_response_contains_output_url_and_expires(
        self, client: AsyncClient
    ) -> None:
        """Response must include output_url (string) and expires_at (ISO datetime)."""
        payload = {"prompt": "cherry blossoms falling in spring"}
        resp = await client.post("/generate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["output_url"], str)
        assert len(data["output_url"]) > 0
        assert isinstance(data["expires_at"], str)

    @pytest.mark.asyncio
    async def test_response_metadata_has_timing_and_request_id(
        self, client: AsyncClient
    ) -> None:
        """Metadata must include generation_time_seconds (float) and request_id (string)."""
        payload = {"prompt": "waves crashing on a rocky shore"}
        resp = await client.post("/generate", json=payload)
        assert resp.status_code == 200
        meta = resp.json()["metadata"]
        assert "generation_time_seconds" in meta
        assert isinstance(meta["generation_time_seconds"], (int, float))
        assert "request_id" in meta
        assert isinstance(meta["request_id"], str)

    @pytest.mark.asyncio
    async def test_response_does_not_contain_base64_video(
        self, client: AsyncClient
    ) -> None:
        """The response must NOT embed base64-encoded video data — only a URL."""
        payload = {"prompt": "a cat sleeping on a windowsill"}
        resp = await client.post("/generate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        # No field should contain a large base64 blob
        raw = resp.text
        assert "base64" not in raw.lower()
        assert "video_data" not in data
        assert "clip_data" not in data


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Tests for the GET /health route."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient) -> None:
        """Health endpoint should return 200 with model_loaded and gpu fields."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "model_loaded" in data
        assert isinstance(data["model_loaded"], bool)
        assert "gpu" in data
        assert isinstance(data["gpu"], str)

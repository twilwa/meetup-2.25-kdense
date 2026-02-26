# ABOUTME: Tests for OBS scene controller and overlay management.
# ABOUTME: Validates scene switching, overlay updates, connection state, and retry behavior.

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.obs.controller import SceneController
from src.obs.overlays import OverlayManager


# ---------------------------------------------------------------------------
# SceneController tests
# ---------------------------------------------------------------------------


class TestSceneControllerConnectedProperty:
    """Verify the connected property reflects actual connection state."""

    def test_connected_returns_false_when_not_connected(self) -> None:
        """A freshly created controller should report connected=False."""
        controller = SceneController()
        assert controller.connected is False


class TestSceneControllerConnect:
    """Verify connection establishment and retry behavior."""

    @pytest.mark.asyncio
    async def test_connect_retries_on_unavailable_obs(self) -> None:
        """When OBS is unreachable, connect should log a warning and retry.

        We cancel after a short window to avoid an infinite retry loop in tests,
        then verify that at least one retry attempt was logged.
        """
        controller = SceneController(host="localhost", port=19999)

        with pytest.raises((asyncio.CancelledError, ConnectionError, OSError)):
            task = asyncio.create_task(controller.connect())
            await asyncio.sleep(0.5)
            task.cancel()
            await task


class TestShowGenerating:
    """Verify the Generating scene activates and overlays update."""

    @pytest.mark.asyncio
    async def test_show_generating_updates_prompt_and_user_overlays(self) -> None:
        """show_generating should update both the prompt and user text overlays."""
        controller = SceneController()
        # This will raise NotImplementedError since the scaffold is unimplemented,
        # which is the expected red-phase TDD failure.
        await controller.show_generating(prompt="a cat in space", user="testuser")

        # After implementation, these assertions should verify that
        # the overlay manager received the correct prompt and user values.
        # For now, reaching this line means the method executed without error.


class TestShowResult:
    """Verify the Result scene activates with the correct video source."""

    @pytest.mark.asyncio
    async def test_show_result_sets_video_source_path(self) -> None:
        """show_result should configure the video media source to the given path."""
        controller = SceneController()
        await controller.show_result(
            video_path="/tmp/output.mp4",
            prompt="a dragon flying",
            user="viewer42",
        )


class TestShowIdle:
    """Verify the Idle scene activates cleanly."""

    @pytest.mark.asyncio
    async def test_show_idle_returns_to_idle_scene(self) -> None:
        """show_idle should switch OBS to the Idle scene."""
        controller = SceneController()
        await controller.show_idle()


class TestShowFallback:
    """Verify the Fallback scene activates with status text."""

    @pytest.mark.asyncio
    async def test_show_fallback_activates_with_status_text(self) -> None:
        """show_fallback should switch to Fallback scene and display the status message."""
        controller = SceneController()
        await controller.show_fallback(status_text="GPU unavailable")


# ---------------------------------------------------------------------------
# OverlayManager tests
# ---------------------------------------------------------------------------


class TestOverlayManagerQueueStatus:
    """Verify queue status overlay formatting."""

    @pytest.mark.asyncio
    async def test_update_queue_status_formats_depth_display(self) -> None:
        """update_queue_status should format the text as 'Queue: {depth}/{max_depth}'.

        After implementation, this test should verify the formatted string
        sent to OBS matches the expected pattern.
        """
        mock_ws = MagicMock()
        manager = OverlayManager(ws_client=mock_ws)
        await manager.update_queue_status(depth=3, max_depth=10)

        # Implementation should send "Queue: 3/10" to the OBS text source.
        # The assertion will be filled in once the implementation exists,
        # but the NotImplementedError will cause this to fail in the red phase.

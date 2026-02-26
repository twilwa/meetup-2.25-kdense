# ABOUTME: OBS WebSocket scene management for stream display compositing.
# ABOUTME: Switches between Idle, Generating, Result, Gallery, and Fallback scenes.

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SceneController:
    """Manages OBS scene transitions and media source configuration via WebSocket.

    Controls the visual state of the stream by switching between named scenes
    and configuring media sources (video paths, overlay text) for each state.
    Reconnects automatically on connection loss with a configurable retry interval.
    """

    def __init__(
        self, host: str = "localhost", port: int = 4455, password: str = ""
    ) -> None:
        """Initialize the scene controller with OBS WebSocket connection parameters.

        Args:
            host: OBS WebSocket server hostname.
            port: OBS WebSocket server port.
            password: OBS WebSocket authentication password.
        """
        self._host = host
        self._port = port
        self._password = password
        self._ws: Any = None
        self._connected = False

    @property
    def connected(self) -> bool:
        """Whether the controller has an active OBS WebSocket connection."""
        return self._connected

    async def connect(self) -> None:
        """Connect to OBS WebSocket, retrying every 10 seconds on failure.

        Blocks until a connection is established or the caller cancels.
        Logs a warning on each failed attempt before retrying.
        """
        while True:
            try:
                import obswebsocket

                self._ws = obswebsocket.obsws(self._host, self._port, self._password)
                await self._ws.connect()
                self._connected = True
                return
            except Exception as e:
                logger.warning(f"Failed to connect to OBS: {e}. Retrying in 10s...")
                await asyncio.sleep(10)

    async def disconnect(self) -> None:
        """Gracefully close the OBS WebSocket connection."""
        if self._ws and self._connected:
            await self._ws.disconnect()
            self._connected = False

    async def show_generating(self, prompt: str, user: str) -> None:
        """Switch to the Generating scene and update overlay text.

        Args:
            prompt: The generation prompt to display on the overlay.
            user: The username who submitted the request.
        """
        # Switch to Generating scene
        await self._switch_scene("Generating")
        # Update overlay text sources
        await self._set_text_source("prompt_text", prompt)
        await self._set_text_source("user_text", user)

    async def show_result(self, video_path: str, prompt: str, user: str) -> None:
        """Switch to the Result scene and set the video media source.

        Args:
            video_path: Local filesystem path to the generated video file.
            prompt: The generation prompt to display on the overlay.
            user: The username who submitted the request.
        """
        await self._switch_scene("Result")
        await self._set_media_source("video_source", video_path)
        await self._set_text_source("prompt_text", prompt)
        await self._set_text_source("user_text", user)

    async def show_idle(self) -> None:
        """Switch to the Idle scene with default ambient visuals."""
        await self._switch_scene("Idle")

    async def show_gallery(self) -> None:
        """Switch to the Gallery scene that rotates through previous results."""
        await self._switch_scene("Gallery")

    async def show_fallback(self, status_text: str) -> None:
        """Switch to the Fallback scene with a hero-shot loop and status message.

        Args:
            status_text: Human-readable status message explaining the fallback
                         (e.g. "GPU unavailable" or "Model loading").
        """
        await self._switch_scene("Fallback")
        await self._set_text_source("status_text", status_text)

    async def _switch_scene(self, scene_name: str) -> None:
        """Switch to the named scene."""
        if self._ws and self._connected:
            try:
                await self._ws.call("SetCurrentProgramScene", {"sceneName": scene_name})
            except Exception as e:
                logger.warning(f"Failed to switch scene: {e}")

    async def _set_text_source(self, source_name: str, text: str) -> None:
        """Update a text source's content."""
        if self._ws and self._connected:
            try:
                await self._ws.call(
                    "SetInputSettings",
                    {"inputName": source_name, "inputSettings": {"text": text}},
                )
            except Exception as e:
                logger.warning(f"Failed to set text source: {e}")

    async def _set_media_source(self, source_name: str, file_path: str) -> None:
        """Update a media source's file path."""
        if self._ws and self._connected:
            try:
                await self._ws.call(
                    "SetInputSettings",
                    {
                        "inputName": source_name,
                        "inputSettings": {"local_file": file_path},
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to set media source: {e}")

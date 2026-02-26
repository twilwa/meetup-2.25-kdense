# ABOUTME: Overlay text update logic for OBS stream display elements.
# ABOUTME: Sends SetInputSettings requests to update prompt, user, queue, and status text sources.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OverlayManager:
    """Updates OBS text and status overlay sources via WebSocket.

    Wraps the OBS WebSocket client to provide typed methods for each
    overlay element used in the stream layout. All updates are sent
    as SetInputSettings requests targeting named text sources.
    """

    def __init__(self, ws_client: Any) -> None:
        """Initialize with an active OBS WebSocket client.

        Args:
            ws_client: An OBS WebSocket client instance capable of sending
                       SetInputSettings requests.
        """
        self._ws = ws_client

    async def update_prompt_text(self, text: str) -> None:
        """Update the prompt overlay text source.

        Args:
            text: The generation prompt text to display.
        """
        await self._set_text_source("prompt_text", text)

    async def update_user_text(self, username: str) -> None:
        """Update the user attribution overlay text source.

        Args:
            username: The username to display on the overlay.
        """
        await self._set_text_source("user_text", username)

    async def update_queue_status(self, depth: int, max_depth: int) -> None:
        """Update the queue depth overlay text source.

        Formats the display as "Queue: {depth}/{max_depth}".

        Args:
            depth: Current number of items in the generation queue.
            max_depth: Maximum allowed queue depth.
        """
        text = f"Queue: {depth}/{max_depth}"
        await self._set_text_source("queue_text", text)

    async def update_system_status(self, text: str) -> None:
        """Update the system status indicator overlay.

        Used to display degraded/healthy status or informational messages
        about the generation pipeline state.

        Args:
            text: Status message to display (e.g. "Healthy", "Degraded - GPU warming up").
        """
        await self._set_text_source("status_text", text)

    async def _set_text_source(self, source_name: str, text: str) -> None:
        """Update a text source's content via SetInputSettings."""
        try:
            if hasattr(self._ws, "call"):
                await self._ws.call(
                    "SetInputSettings",
                    {"inputName": source_name, "inputSettings": {"text": text}},
                )
        except Exception as e:
            logger.warning(f"Failed to set text source {source_name}: {e}")

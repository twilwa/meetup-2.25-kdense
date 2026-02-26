# ABOUTME: OBS WebSocket notification bridge for scene transitions.
# ABOUTME: Controls OBS scenes to reflect generation state (idle, generating, result, fallback).

from __future__ import annotations


class ObsNotifier:
    """Manages OBS Studio scene transitions via WebSocket.

    Connects to OBS WebSocket and switches scenes to reflect the
    current generation pipeline state: idle, generating, showing
    results, or displaying a fallback/error state.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 4455,
        password: str = "",
    ) -> None:
        """Initialise the notifier.

        Args:
            host: OBS WebSocket server hostname.
            port: OBS WebSocket server port.
            password: OBS WebSocket authentication password.
        """
        raise NotImplementedError()

    async def connect(self) -> None:
        """Establish a WebSocket connection to OBS.

        Raises:
            ConnectionError: If the connection cannot be established.
        """
        raise NotImplementedError()

    async def show_generating(self, prompt: str, user: str) -> None:
        """Switch OBS to the generating scene.

        Displays the prompt and requesting user while generation is
        in progress.

        Args:
            prompt: The generation prompt being processed.
            user: The user who requested the generation.
        """
        raise NotImplementedError()

    async def show_result(self, video_path: str, prompt: str, user: str) -> None:
        """Switch OBS to the result scene.

        Displays the completed video clip alongside metadata.

        Args:
            video_path: Local path to the generated MP4 file.
            prompt: The prompt that produced this clip.
            user: The user who requested the generation.
        """
        raise NotImplementedError()

    async def show_idle(self) -> None:
        """Return OBS to the idle scene.

        Shown when no generation is active and the queue is empty.
        """
        raise NotImplementedError()

    async def show_fallback(self, status_text: str) -> None:
        """Switch OBS to the fallback scene.

        Used when the pipeline encounters errors or degraded health.

        Args:
            status_text: Human-readable status message to display.
        """
        raise NotImplementedError()

    async def disconnect(self) -> None:
        """Close the WebSocket connection to OBS."""
        raise NotImplementedError()

    @property
    def connected(self) -> bool:
        """Whether the WebSocket connection is currently active."""
        raise NotImplementedError()

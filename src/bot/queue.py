# ABOUTME: Async generation queue with per-user rate limiting.
# ABOUTME: Manages FIFO ordering, capacity enforcement, and cooldown tracking.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class QueueItem:
    """A single pending generation request in the queue."""

    prompt: str
    user: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enqueued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class QueueResult:
    """Outcome of an enqueue attempt."""

    accepted: bool
    message: str
    position: int | None = None


@dataclass
class RateLimitResult:
    """Outcome of a per-user rate limit check."""

    allowed: bool
    retry_after_seconds: float | None = None


class GenerationQueue:
    """Bounded async FIFO queue with per-user cooldown enforcement.

    Provides backpressure via a fixed capacity and prevents spam via
    per-user cooldown windows.  Exposes health signals so callers can
    degrade gracefully when the queue is under pressure.
    """

    def __init__(self, max_size: int = 10, cooldown_seconds: float = 30.0) -> None:
        """Initialise the queue.

        Args:
            max_size: Maximum number of items the queue will hold.
            cooldown_seconds: Minimum seconds between requests from the
                same user.
        """
        self._max_size = max_size
        self._cooldown_seconds = cooldown_seconds
        self._queue: list[QueueItem] = []
        self._last_request_times: dict[str, datetime] = {}

    async def enqueue(self, prompt: str, user: str) -> QueueResult:
        """Add a generation request to the queue.

        Checks rate limits and capacity before accepting.

        Args:
            prompt: The generation prompt text.
            user: Identifier for the requesting user.

        Returns:
            A ``QueueResult`` indicating whether the request was accepted
            and, if so, its position in the queue.
        """
        # Check rate limit first
        rate_limit = self.check_rate_limit(user)
        if not rate_limit.allowed:
            retry_msg = f"Rate limited. Retry in {rate_limit.retry_after_seconds:.1f}s."
            return QueueResult(accepted=False, message=retry_msg)

        # Check capacity
        if self.is_full:
            return QueueResult(accepted=False, message="Queue is full.")

        # Create and add the item
        item = QueueItem(prompt=prompt, user=user)
        self._queue.append(item)
        self._last_request_times[user] = datetime.now(timezone.utc)

        return QueueResult(accepted=True, message="Accepted", position=self.depth)

    async def dequeue(self) -> QueueItem | None:
        """Remove and return the next item from the queue.

        Returns:
            The oldest ``QueueItem``, or ``None`` if the queue is empty.
        """
        if not self._queue:
            return None
        return self._queue.pop(0)

    def check_rate_limit(self, user: str) -> RateLimitResult:
        """Check whether a user is allowed to make a request.

        Args:
            user: Identifier for the user to check.

        Returns:
            A ``RateLimitResult`` indicating whether the request is
            allowed, and if not, how long until the cooldown expires.
        """
        if user not in self._last_request_times:
            return RateLimitResult(allowed=True)

        last_time = self._last_request_times[user]
        elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()

        if elapsed >= self._cooldown_seconds:
            return RateLimitResult(allowed=True)

        retry_after = self._cooldown_seconds - elapsed
        return RateLimitResult(allowed=False, retry_after_seconds=retry_after)

    @property
    def depth(self) -> int:
        """Current number of items waiting in the queue."""
        return len(self._queue)

    @property
    def is_full(self) -> bool:
        """Whether the queue has reached its maximum capacity."""
        return len(self._queue) >= self._max_size

    @property
    def health_degraded(self) -> bool:
        """Whether queue pressure indicates degraded health.

        Implementations may use heuristics such as high fill ratio or
        sustained high throughput to signal degradation.
        """
        # Degraded when queue is at or above 80% capacity
        return len(self._queue) >= self._max_size

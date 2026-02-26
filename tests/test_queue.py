# ABOUTME: Tests for the async generation queue with rate limiting.
# ABOUTME: Verifies FIFO ordering, capacity enforcement, cooldown logic, and health signals.

import asyncio

import pytest

from src.bot.queue import GenerationQueue, QueueItem, QueueResult, RateLimitResult


class TestEnqueue:
    """Tests for adding items to the queue."""

    @pytest.mark.asyncio
    async def test_enqueue_succeeds_on_empty_queue(self) -> None:
        """Enqueue on an empty queue should be accepted."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=30.0)
        result = await queue.enqueue("fire sword girl", "user_alice")
        assert result.accepted is True

    @pytest.mark.asyncio
    async def test_enqueue_returns_position(self) -> None:
        """Enqueue should report the item's position in the queue."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=30.0)
        result1 = await queue.enqueue("prompt one", "user_alice")
        result2 = await queue.enqueue("prompt two", "user_bob")
        assert result1.position == 1
        assert result2.position == 2

    @pytest.mark.asyncio
    async def test_enqueue_rejected_when_full(self) -> None:
        """Enqueue should be rejected when the queue is at max capacity."""
        queue = GenerationQueue(max_size=2, cooldown_seconds=0.0)
        await queue.enqueue("prompt one", "user_a")
        await queue.enqueue("prompt two", "user_b")
        result = await queue.enqueue("prompt three", "user_c")
        assert result.accepted is False


class TestDequeue:
    """Tests for removing items from the queue."""

    @pytest.mark.asyncio
    async def test_dequeue_returns_fifo_order(self) -> None:
        """Dequeue should return items in the order they were enqueued."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=0.0)
        await queue.enqueue("first", "user_a")
        await queue.enqueue("second", "user_b")

        item1 = await queue.dequeue()
        item2 = await queue.dequeue()

        assert item1 is not None
        assert item2 is not None
        assert item1.prompt == "first"
        assert item2.prompt == "second"

    @pytest.mark.asyncio
    async def test_dequeue_returns_none_when_empty(self) -> None:
        """Dequeue on an empty queue should return None."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=30.0)
        item = await queue.dequeue()
        assert item is None


class TestRateLimit:
    """Tests for per-user cooldown enforcement."""

    @pytest.mark.asyncio
    async def test_rate_limit_rejects_rapid_repeat(self) -> None:
        """Same user should be rejected within the cooldown window."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=30.0)
        await queue.enqueue("first prompt", "user_alice")
        result = await queue.enqueue("second prompt", "user_alice")
        assert result.accepted is False

    @pytest.mark.asyncio
    async def test_rate_limit_allows_after_cooldown(self) -> None:
        """Same user should be allowed after the cooldown period expires."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=0.01)
        await queue.enqueue("first prompt", "user_alice")
        await asyncio.sleep(0.02)
        result = await queue.enqueue("second prompt", "user_alice")
        assert result.accepted is True

    @pytest.mark.asyncio
    async def test_rate_limit_allows_different_users(self) -> None:
        """Different users should not affect each other's rate limits."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=30.0)
        result_alice = await queue.enqueue("prompt", "user_alice")
        result_bob = await queue.enqueue("prompt", "user_bob")
        assert result_alice.accepted is True
        assert result_bob.accepted is True

    def test_check_rate_limit_returns_result(self) -> None:
        """check_rate_limit should return a RateLimitResult."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=30.0)
        result = queue.check_rate_limit("user_alice")
        assert isinstance(result, RateLimitResult)


class TestQueueState:
    """Tests for queue depth, capacity, and health signals."""

    @pytest.mark.asyncio
    async def test_depth_reports_correctly(self) -> None:
        """depth should reflect the current number of queued items."""
        queue = GenerationQueue(max_size=10, cooldown_seconds=0.0)
        assert queue.depth == 0
        await queue.enqueue("one", "user_a")
        assert queue.depth == 1
        await queue.enqueue("two", "user_b")
        assert queue.depth == 2
        await queue.dequeue()
        assert queue.depth == 1

    @pytest.mark.asyncio
    async def test_is_full_at_max_capacity(self) -> None:
        """is_full should return True when queue reaches max_size."""
        queue = GenerationQueue(max_size=2, cooldown_seconds=0.0)
        assert queue.is_full is False
        await queue.enqueue("one", "user_a")
        await queue.enqueue("two", "user_b")
        assert queue.is_full is True

    @pytest.mark.asyncio
    async def test_health_degraded_signals(self) -> None:
        """health_degraded should signal when the queue is under pressure."""
        queue = GenerationQueue(max_size=3, cooldown_seconds=0.0)
        # Empty queue should not be degraded
        assert queue.health_degraded is False
        # Fill queue to capacity
        await queue.enqueue("one", "user_a")
        await queue.enqueue("two", "user_b")
        await queue.enqueue("three", "user_c")
        # Full queue should signal degradation
        assert queue.health_degraded is True

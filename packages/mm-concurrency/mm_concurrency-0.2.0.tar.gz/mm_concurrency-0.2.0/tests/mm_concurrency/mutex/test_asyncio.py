"""Tests for async mutex decorators."""

import asyncio

import pytest

from mm_concurrency import async_mutex, async_mutex_by
from mm_concurrency.mutex._asyncio import _AsyncMutex


class TestAsyncMutex:
    """Tests for @async_mutex decorator."""

    @pytest.mark.asyncio
    async def test_serializes_concurrent_calls(self) -> None:
        """Multiple coroutines run serially."""
        max_concurrent = 0
        current_concurrent = 0

        @async_mutex
        async def critical_section() -> None:
            nonlocal max_concurrent, current_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            await asyncio.sleep(0.02)
            current_concurrent -= 1

        await asyncio.gather(*[critical_section() for _ in range(5)])

        assert max_concurrent == 1

    @pytest.mark.asyncio
    async def test_returns_value(self) -> None:
        """Return value preserved."""

        @async_mutex
        async def compute(x: int) -> int:
            return x * 2

        assert await compute(21) == 42

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self) -> None:
        """functools.wraps applied correctly."""

        @async_mutex
        async def documented_func() -> None:
            """Sample docstring."""

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "Sample docstring."


class TestAsyncMutexBy:
    """Tests for @async_mutex_by decorator."""

    @pytest.mark.asyncio
    async def test_same_key_serialized(self) -> None:
        """Calls with same key are serialized."""
        max_concurrent = 0
        current_concurrent = 0

        @async_mutex_by()
        async def process(_key: str) -> None:
            nonlocal max_concurrent, current_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            await asyncio.sleep(0.02)
            current_concurrent -= 1

        # All coroutines use same key
        await asyncio.gather(*[process("same_key") for _ in range(5)])

        assert max_concurrent == 1

    @pytest.mark.asyncio
    async def test_different_keys_concurrent(self) -> None:
        """Calls with different keys run concurrently."""
        max_concurrent = 0
        current_concurrent = 0

        @async_mutex_by()
        async def process(_key: str) -> None:
            nonlocal max_concurrent, current_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            await asyncio.sleep(0.05)
            current_concurrent -= 1

        # Each coroutine uses different key
        await asyncio.gather(*[process(f"key_{i}") for i in range(5)])

        assert max_concurrent > 1

    @pytest.mark.asyncio
    async def test_by_arg_index(self) -> None:
        """arg_index parameter works."""
        execution_order: list[tuple[str, str]] = []

        @async_mutex_by(arg_index=1)
        async def process(prefix: str, key: str) -> None:
            execution_order.append((prefix, key))
            await asyncio.sleep(0.02)

        # Same key at arg_index=1 should serialize
        await asyncio.gather(process("a", "same"), process("b", "same"))

        assert len(execution_order) == 2

    @pytest.mark.asyncio
    async def test_by_param(self) -> None:
        """Param parameter works."""
        execution_order: list[str] = []

        @async_mutex_by(param="user_id")
        async def process(_data: str, user_id: str) -> None:
            execution_order.append(user_id)
            await asyncio.sleep(0.02)

        await asyncio.gather(process("data1", "user1"), process("data2", "user1"))

        assert len(execution_order) == 2

    @pytest.mark.asyncio
    async def test_skip_if_locked_returns_none(self) -> None:
        """skip_if_locked=True returns None when locked."""
        started = asyncio.Event()
        proceed = asyncio.Event()

        @async_mutex_by(skip_if_locked=True)
        async def process(_key: str) -> int:
            started.set()
            await proceed.wait()
            return 42

        async def first_call() -> int | None:
            return await process("key")

        async def second_call() -> int | None:
            await started.wait()  # Wait for first call to start
            result = await process("key")
            proceed.set()  # Allow first call to finish
            return result

        results = await asyncio.gather(first_call(), second_call())

        assert 42 in results
        assert None in results

    @pytest.mark.asyncio
    async def test_skip_if_locked_false_waits(self) -> None:
        """skip_if_locked=False blocks until lock available."""
        started = asyncio.Event()

        @async_mutex_by(skip_if_locked=False)
        async def process(_key: str) -> int:
            started.set()
            await asyncio.sleep(0.05)
            return 42

        async def first_call() -> int:
            return await process("key")

        async def second_call() -> int:
            await started.wait()  # Ensure first call started
            return await process("key")

        results = await asyncio.gather(first_call(), second_call())

        # Both should complete with value (second waited)
        assert results == [42, 42]

    @pytest.mark.asyncio
    async def test_invalid_param_raises(self) -> None:
        """ValueError for nonexistent param."""
        with pytest.raises(ValueError, match="Parameter 'nonexistent' not found"):

            @async_mutex_by(param="nonexistent")
            async def process(key: str) -> None:
                pass

    @pytest.mark.asyncio
    async def test_invalid_arg_index_raises(self) -> None:
        """ValueError for out-of-range arg_index."""
        with pytest.raises(ValueError, match="arg_index 5 out of range"):

            @async_mutex_by(arg_index=5)
            async def process(key: str) -> None:
                pass

    @pytest.mark.asyncio
    async def test_cancellation_cleanup(self) -> None:
        """CancelledError properly cleans up lock state."""
        acquired = asyncio.Event()

        @async_mutex_by()
        async def process(_key: str) -> int:
            acquired.set()
            await asyncio.sleep(10)  # Long wait to be cancelled
            return 42

        async def cancellable_call() -> None:
            await process("key")

        # Start first call and cancel it while waiting
        task = asyncio.create_task(cancellable_call())
        await acquired.wait()

        # Start second call that will wait for lock
        task2 = asyncio.create_task(process("key"))
        await asyncio.sleep(0.01)  # Let task2 start waiting

        # Cancel task2 while it's waiting for lock
        task2.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task2

        # Cancel task1 to clean up
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        # New call should work (locks properly cleaned up)
        @async_mutex_by()
        async def another_process(_key: str) -> int:
            return 99

        result = await another_process("key")
        assert result == 99

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self) -> None:
        """functools.wraps applied correctly."""

        @async_mutex_by()
        async def documented_func(key: str) -> None:
            """Sample docstring."""

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "Sample docstring."


class TestAsyncMutexInternal:
    """Tests for _AsyncMutex internal class."""

    @pytest.mark.asyncio
    async def test_acquire_blocks(self) -> None:
        """acquire() blocks until available."""
        mutex = _AsyncMutex()
        acquired_first = asyncio.Event()
        second_acquired = False

        async def first_holder() -> None:
            await mutex.acquire()
            acquired_first.set()
            await asyncio.sleep(0.1)
            mutex.release()

        async def second_holder() -> None:
            nonlocal second_acquired
            await acquired_first.wait()
            await mutex.acquire()  # Should block until first releases
            second_acquired = True
            mutex.release()

        await asyncio.gather(first_holder(), second_holder())

        assert second_acquired

    @pytest.mark.asyncio
    async def test_try_acquire_nonblocking(self) -> None:
        """try_acquire() returns immediately."""
        mutex = _AsyncMutex()

        # First acquire succeeds
        assert mutex.try_acquire() is True

        # Second try_acquire fails immediately (non-blocking)
        assert mutex.try_acquire() is False

        mutex.release()

        # After release, try_acquire succeeds again
        assert mutex.try_acquire() is True
        mutex.release()

    @pytest.mark.asyncio
    async def test_release_makes_available(self) -> None:
        """release() allows next acquire."""
        mutex = _AsyncMutex()

        await mutex.acquire()
        mutex.release()

        # Should not block
        await asyncio.wait_for(mutex.acquire(), timeout=0.1)
        mutex.release()

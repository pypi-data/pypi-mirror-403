"""Tests for thread-based mutex decorators."""

import threading
import time

import pytest

from mm_concurrency import mutex, mutex_by


class TestMutex:
    """Tests for @mutex decorator."""

    def test_serializes_concurrent_calls(self) -> None:
        """Multiple threads calling decorated function run serially."""
        max_concurrent = 0
        current_concurrent = 0
        lock = threading.Lock()

        @mutex
        def critical_section() -> None:
            nonlocal max_concurrent, current_concurrent
            with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            time.sleep(0.02)
            with lock:
                current_concurrent -= 1

        threads = [threading.Thread(target=critical_section) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert max_concurrent == 1

    def test_returns_value(self) -> None:
        """Return value preserved."""

        @mutex
        def compute(x: int) -> int:
            return x * 2

        assert compute(21) == 42

    def test_preserves_function_metadata(self) -> None:
        """functools.wraps applied correctly."""

        @mutex
        def documented_func() -> None:
            """Sample docstring."""

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "Sample docstring."


class TestMutexBy:
    """Tests for @mutex_by decorator."""

    def test_same_key_serialized(self) -> None:
        """Calls with same key are serialized."""
        max_concurrent = 0
        current_concurrent = 0
        lock = threading.Lock()

        @mutex_by()
        def process(_key: str) -> None:
            nonlocal max_concurrent, current_concurrent
            with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            time.sleep(0.02)
            with lock:
                current_concurrent -= 1

        # All threads use same key
        threads = [threading.Thread(target=process, args=("same_key",)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert max_concurrent == 1

    def test_different_keys_concurrent(self) -> None:
        """Calls with different keys run concurrently."""
        max_concurrent = 0
        current_concurrent = 0
        lock = threading.Lock()

        @mutex_by()
        def process(_key: str) -> None:
            nonlocal max_concurrent, current_concurrent
            with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            time.sleep(0.05)
            with lock:
                current_concurrent -= 1

        # Each thread uses different key
        threads = [threading.Thread(target=process, args=(f"key_{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert max_concurrent > 1

    def test_by_arg_index(self) -> None:
        """arg_index parameter works."""
        execution_order: list[tuple[str, str]] = []
        lock = threading.Lock()

        @mutex_by(arg_index=1)
        def process(prefix: str, key: str) -> None:
            with lock:
                execution_order.append((prefix, key))
            time.sleep(0.02)

        # Same key at arg_index=1 should serialize
        t1 = threading.Thread(target=process, args=("a", "same"))
        t2 = threading.Thread(target=process, args=("b", "same"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Both should complete (serialized)
        assert len(execution_order) == 2

    def test_by_param(self) -> None:
        """Param parameter works."""
        execution_order: list[str] = []
        lock = threading.Lock()

        @mutex_by(param="user_id")
        def process(_data: str, user_id: str) -> None:
            with lock:
                execution_order.append(user_id)
            time.sleep(0.02)

        t1 = threading.Thread(target=process, args=("data1", "user1"))
        t2 = threading.Thread(target=process, args=("data2", "user1"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(execution_order) == 2

    def test_skip_if_locked_returns_none(self) -> None:
        """skip_if_locked=True returns None when locked."""
        started = threading.Event()
        proceed = threading.Event()
        results: list[int | None] = []

        @mutex_by(skip_if_locked=True)
        def process(_key: str) -> int:
            started.set()
            proceed.wait()
            return 42

        def first_call() -> None:
            results.append(process("key"))

        def second_call() -> None:
            started.wait()  # Wait for first call to start
            results.append(process("key"))
            proceed.set()  # Allow first call to finish

        t1 = threading.Thread(target=first_call)
        t2 = threading.Thread(target=second_call)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert 42 in results
        assert None in results

    def test_skip_if_locked_false_waits(self) -> None:
        """skip_if_locked=False blocks until lock available."""
        started = threading.Event()
        results: list[int] = []
        lock = threading.Lock()

        @mutex_by(skip_if_locked=False)
        def process(_key: str) -> int:
            started.set()
            time.sleep(0.05)
            return 42

        def call() -> None:
            result = process("key")
            with lock:
                results.append(result)

        t1 = threading.Thread(target=call)
        t2 = threading.Thread(target=call)
        t1.start()
        started.wait()  # Ensure first call started
        t2.start()
        t1.join()
        t2.join()

        # Both should complete with value (second waited)
        assert results == [42, 42]

    def test_invalid_param_raises(self) -> None:
        """ValueError for nonexistent param."""
        with pytest.raises(ValueError, match="Parameter 'nonexistent' not found"):

            @mutex_by(param="nonexistent")
            def process(key: str) -> None:
                pass

    def test_invalid_arg_index_raises(self) -> None:
        """ValueError for out-of-range arg_index."""
        with pytest.raises(ValueError, match="arg_index 5 out of range"):

            @mutex_by(arg_index=5)
            def process(key: str) -> None:
                pass

    def test_preserves_function_metadata(self) -> None:
        """functools.wraps applied correctly."""

        @mutex_by()
        def documented_func(key: str) -> None:
            """Sample docstring."""

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "Sample docstring."

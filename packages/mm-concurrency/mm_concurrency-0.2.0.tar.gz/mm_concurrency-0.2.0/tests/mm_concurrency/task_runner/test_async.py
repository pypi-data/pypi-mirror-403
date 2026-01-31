"""Tests for AsyncTaskRunner."""

import asyncio

import pytest

from mm_concurrency import AsyncTaskRunner, TaskRunnerResult


class TestAsyncTaskRunnerInit:
    """Tests for AsyncTaskRunner initialization."""

    @pytest.mark.parametrize("timeout", [0, -1, -0.5])
    def test_invalid_timeout(self, timeout: float) -> None:
        """Non-positive timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            AsyncTaskRunner(timeout=timeout)


class TestAsyncTaskRunnerAdd:
    """Tests for AsyncTaskRunner.add() method."""

    async def test_add_task(self) -> None:
        """Successful awaitable registration verifiable by run()."""

        async def task() -> int:
            return 42

        runner = AsyncTaskRunner()
        runner.add("task1", task())
        result = await runner.run()

        assert "task1" in result.results

    async def test_add_multiple_tasks(self) -> None:
        """Multiple awaitables with different keys."""

        async def task(value: int) -> int:
            return value

        runner = AsyncTaskRunner()
        runner.add("task1", task(1))
        runner.add("task2", task(2))
        runner.add("task3", task(3))
        result = await runner.run()

        assert set(result.results.keys()) == {"task1", "task2", "task3"}

    def test_add_empty_key(self) -> None:
        """Empty key raises ValueError."""

        async def task() -> None:
            pass

        runner = AsyncTaskRunner()
        coro = task()
        try:
            with pytest.raises(ValueError, match="Task key cannot be empty"):
                runner.add("", coro)
        finally:
            coro.close()

    def test_add_whitespace_key(self) -> None:
        """Whitespace-only key raises ValueError."""

        async def task() -> None:
            pass

        runner = AsyncTaskRunner()
        coro = task()
        try:
            with pytest.raises(ValueError, match="Task key cannot be empty"):
                runner.add("   ", coro)
        finally:
            coro.close()

    async def test_add_duplicate_key(self) -> None:
        """Duplicate key raises ValueError."""

        async def task() -> None:
            pass

        runner = AsyncTaskRunner()
        runner.add("task1", task())

        coro = task()
        try:
            with pytest.raises(ValueError, match="Task key 'task1' already exists"):
                runner.add("task1", coro)
        finally:
            coro.close()

        await runner.run()

    async def test_add_after_run(self) -> None:
        """Adding after run() raises RuntimeError."""

        async def task() -> int:
            return 1

        runner = AsyncTaskRunner()
        runner.add("task1", task())
        await runner.run()

        coro = task()
        try:
            with pytest.raises(RuntimeError, match="already been used"):
                runner.add("task2", coro)
        finally:
            coro.close()


class TestAsyncTaskRunnerRun:
    """Tests for AsyncTaskRunner.run() method."""

    async def test_run_single_task(self) -> None:
        """Single async task returns correct result."""

        async def task() -> int:
            return 42

        runner = AsyncTaskRunner()
        runner.add("task1", task())
        result = await runner.run()

        assert result.results == {"task1": 42}
        assert result.exceptions == {}
        assert result.success is True
        assert result.timed_out is False

    async def test_run_multiple_tasks(self) -> None:
        """Multiple tasks return all results."""

        async def task1() -> int:
            return 1

        async def task2() -> str:
            return "hello"

        async def task3() -> list[int]:
            return [1, 2, 3]

        runner = AsyncTaskRunner()
        runner.add("t1", task1())
        runner.add("t2", task2())
        runner.add("t3", task3())
        result = await runner.run()

        assert result.results == {"t1": 1, "t2": "hello", "t3": [1, 2, 3]}
        assert result.success is True

    async def test_run_no_tasks(self) -> None:
        """run() with no tasks raises ValueError."""
        runner = AsyncTaskRunner()

        with pytest.raises(ValueError, match="No tasks to run"):
            await runner.run()

    async def test_run_twice(self) -> None:
        """Calling run() twice raises RuntimeError."""

        async def task() -> int:
            return 1

        runner = AsyncTaskRunner()
        runner.add("task1", task())
        await runner.run()

        with pytest.raises(RuntimeError, match="can only be run once"):
            await runner.run()

    async def test_run_task_exception(self) -> None:
        """Exception captured in result.exceptions."""

        async def failing_task() -> None:
            raise ValueError("task failed")

        runner = AsyncTaskRunner(log_errors=False)
        runner.add("fail", failing_task())
        result = await runner.run()

        assert result.results == {}
        assert "fail" in result.exceptions
        assert isinstance(result.exceptions["fail"], ValueError)
        assert str(result.exceptions["fail"]) == "task failed"
        assert result.success is False

    async def test_run_multiple_exceptions(self) -> None:
        """Multiple failures captured."""

        async def fail1() -> None:
            raise ValueError("error1")

        async def fail2() -> None:
            raise RuntimeError("error2")

        runner = AsyncTaskRunner(log_errors=False)
        runner.add("f1", fail1())
        runner.add("f2", fail2())
        result = await runner.run()

        assert len(result.exceptions) == 2
        assert isinstance(result.exceptions["f1"], ValueError)
        assert isinstance(result.exceptions["f2"], RuntimeError)
        assert result.success is False

    async def test_run_partial_success(self) -> None:
        """Some succeed, some fail."""

        async def success() -> int:
            return 42

        async def failure() -> None:
            raise ValueError("oops")

        runner = AsyncTaskRunner(log_errors=False)
        runner.add("ok", success())
        runner.add("bad", failure())
        result = await runner.run()

        assert result.results == {"ok": 42}
        assert "bad" in result.exceptions
        assert result.success is False

    async def test_success_flag_all_success(self) -> None:
        """result.success=True when all tasks pass."""

        async def task() -> int:
            return 1

        runner = AsyncTaskRunner()
        runner.add("t1", task())
        runner.add("t2", task())
        result = await runner.run()

        assert result.success is True
        assert result.timed_out is False
        assert result.exceptions == {}

    async def test_success_flag_with_exception(self) -> None:
        """result.success=False with exception."""

        async def fail() -> None:
            raise RuntimeError("error")

        runner = AsyncTaskRunner(log_errors=False)
        runner.add("fail", fail())
        result = await runner.run()

        assert result.success is False

    async def test_concurrency_limit(self) -> None:
        """Respects semaphore-based concurrency limit."""
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def task() -> None:
            nonlocal max_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            await asyncio.sleep(0.02)
            async with lock:
                current_concurrent -= 1

        runner = AsyncTaskRunner(concurrency=2)
        for i in range(6):
            runner.add(f"task{i}", task())
        await runner.run()

        assert max_concurrent <= 2

    async def test_returns_task_runner_result(self) -> None:
        """run() returns TaskRunnerResult instance."""

        async def task() -> int:
            return 1

        runner = AsyncTaskRunner()
        runner.add("task", task())
        result = await runner.run()

        assert isinstance(result, TaskRunnerResult)


class TestAsyncTaskRunnerTimeout:
    """Tests for AsyncTaskRunner timeout behavior."""

    async def test_timeout_returns_within_limit(self) -> None:
        """run() returns within timeout."""

        async def slow_task() -> None:
            await asyncio.sleep(10)

        runner = AsyncTaskRunner(timeout=0.1)
        runner.add("slow", slow_task())

        start = asyncio.get_event_loop().time()
        await runner.run()
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed < 0.5

    async def test_timeout_sets_timed_out_flag(self) -> None:
        """result.timed_out=True on timeout."""

        async def slow_task() -> None:
            await asyncio.sleep(10)

        runner = AsyncTaskRunner(timeout=0.1)
        runner.add("slow", slow_task())
        result = await runner.run()

        assert result.timed_out is True

    async def test_timeout_success_false(self) -> None:
        """result.success=False on timeout."""

        async def slow_task() -> None:
            await asyncio.sleep(10)

        runner = AsyncTaskRunner(timeout=0.1)
        runner.add("slow", slow_task())
        result = await runner.run()

        assert result.success is False

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    async def test_timeout_cancels_pending(self) -> None:
        """Pending tasks cancelled on timeout."""
        completed_tasks: list[str] = []

        async def slow_task(name: str) -> None:
            await asyncio.sleep(10)
            completed_tasks.append(name)

        runner = AsyncTaskRunner(timeout=0.1, concurrency=1)
        for i in range(5):
            runner.add(f"task{i}", slow_task(f"task{i}"))
        result = await runner.run()

        assert result.timed_out is True
        assert len(completed_tasks) == 0

    async def test_no_timeout(self) -> None:
        """timeout=None allows unlimited execution."""

        async def task() -> int:
            await asyncio.sleep(0.02)
            return 42

        runner = AsyncTaskRunner(timeout=None)
        runner.add("task", task())
        result = await runner.run()

        assert result.results == {"task": 42}
        assert result.timed_out is False
        assert result.success is True

    async def test_fast_tasks_complete_before_timeout(self) -> None:
        """Fast tasks complete successfully with timeout set."""

        async def fast_task() -> int:
            return 42

        runner = AsyncTaskRunner(timeout=10.0)
        runner.add("fast", fast_task())
        result = await runner.run()

        assert result.results == {"fast": 42}
        assert result.timed_out is False
        assert result.success is True

    async def test_partial_completion_on_timeout(self) -> None:
        """Some tasks complete before timeout."""
        completed: list[str] = []

        async def fast_task(name: str) -> str:
            completed.append(name)
            return name

        async def slow_task(name: str) -> str:
            await asyncio.sleep(10)
            completed.append(name)
            return name

        runner = AsyncTaskRunner(timeout=0.1, concurrency=10)
        runner.add("fast1", fast_task("fast1"))
        runner.add("fast2", fast_task("fast2"))
        runner.add("slow1", slow_task("slow1"))
        result = await runner.run()

        assert "fast1" in result.results
        assert "fast2" in result.results
        assert "slow1" not in result.results
        assert result.timed_out is True

"""Tests for TaskRunner."""

import threading
import time

import pytest

from mm_concurrency import TaskRunner, TaskRunnerResult


class TestTaskRunnerResult:
    """Tests for TaskRunnerResult dataclass."""

    def test_fields(self) -> None:
        """Verify dataclass has expected fields."""
        result = TaskRunnerResult(results={"a": 1}, exceptions={}, success=True, timed_out=False)

        assert result.results == {"a": 1}
        assert result.exceptions == {}
        assert result.success is True
        assert result.timed_out is False


class TestTaskRunnerInit:
    """Tests for TaskRunner initialization."""

    @pytest.mark.parametrize("timeout", [0, -1, -0.5])
    def test_invalid_timeout(self, timeout: float) -> None:
        """Non-positive timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            TaskRunner(timeout=timeout)


class TestTaskRunnerAdd:
    """Tests for TaskRunner.add() method."""

    def test_add_task(self) -> None:
        """Successful task registration verifiable by run()."""

        def task() -> int:
            return 42

        runner = TaskRunner()
        runner.add("task1", task)
        result = runner.run()

        assert "task1" in result.results

    def test_add_multiple_tasks(self) -> None:
        """Multiple tasks with different keys."""

        def task(value: int) -> int:
            return value

        runner = TaskRunner()
        runner.add("task1", task, (1,))
        runner.add("task2", task, (2,))
        runner.add("task3", task, (3,))
        result = runner.run()

        assert set(result.results.keys()) == {"task1", "task2", "task3"}

    def test_add_empty_key(self) -> None:
        """Empty key raises ValueError."""

        def task() -> None:
            pass

        runner = TaskRunner()
        with pytest.raises(ValueError, match="Task key cannot be empty"):
            runner.add("", task)

    def test_add_whitespace_key(self) -> None:
        """Whitespace-only key raises ValueError."""

        def task() -> None:
            pass

        runner = TaskRunner()
        with pytest.raises(ValueError, match="Task key cannot be empty"):
            runner.add("   ", task)

    def test_add_duplicate_key(self) -> None:
        """Duplicate key raises ValueError."""

        def task() -> None:
            pass

        runner = TaskRunner()
        runner.add("task1", task)

        with pytest.raises(ValueError, match="Task key 'task1' already exists"):
            runner.add("task1", task)

    def test_add_after_run(self) -> None:
        """Adding after run() raises RuntimeError."""

        def task() -> int:
            return 1

        runner = TaskRunner()
        runner.add("task1", task)
        runner.run()

        with pytest.raises(RuntimeError, match="already been used"):
            runner.add("task2", task)


class TestTaskRunnerRun:
    """Tests for TaskRunner.run() method."""

    def test_run_single_task(self) -> None:
        """Single task returns correct result."""

        def task() -> int:
            return 42

        runner = TaskRunner()
        runner.add("task1", task)
        result = runner.run()

        assert result.results == {"task1": 42}
        assert result.exceptions == {}
        assert result.success is True
        assert result.timed_out is False

    def test_run_multiple_tasks(self) -> None:
        """Multiple tasks return all results."""

        def task1() -> int:
            return 1

        def task2() -> str:
            return "hello"

        def task3() -> list[int]:
            return [1, 2, 3]

        runner = TaskRunner()
        runner.add("t1", task1)
        runner.add("t2", task2)
        runner.add("t3", task3)
        result = runner.run()

        assert result.results == {"t1": 1, "t2": "hello", "t3": [1, 2, 3]}
        assert result.success is True

    def test_run_with_args(self) -> None:
        """Tasks receive positional arguments correctly."""

        def add(a: int, b: int) -> int:
            return a + b

        runner = TaskRunner()
        runner.add("sum", add, (3, 5))
        result = runner.run()

        assert result.results == {"sum": 8}

    def test_run_with_kwargs(self) -> None:
        """Tasks receive keyword arguments correctly."""

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        runner = TaskRunner()
        runner.add("greet", greet, (), {"name": "World", "greeting": "Hi"})
        result = runner.run()

        assert result.results == {"greet": "Hi, World!"}

    def test_run_with_args_and_kwargs(self) -> None:
        """Tasks receive both args and kwargs correctly."""

        def func(a: int, b: int, multiplier: int = 1) -> int:
            return (a + b) * multiplier

        runner = TaskRunner()
        runner.add("calc", func, (2, 3), {"multiplier": 10})
        result = runner.run()

        assert result.results == {"calc": 50}

    def test_run_no_tasks(self) -> None:
        """run() with no tasks raises ValueError."""
        runner = TaskRunner()

        with pytest.raises(ValueError, match="No tasks to run"):
            runner.run()

    def test_run_twice(self) -> None:
        """Calling run() twice raises RuntimeError."""

        def task() -> int:
            return 1

        runner = TaskRunner()
        runner.add("task1", task)
        runner.run()

        with pytest.raises(RuntimeError, match="can only be run once"):
            runner.run()

    def test_run_task_exception(self) -> None:
        """Exception captured in result.exceptions."""

        def failing_task() -> None:
            raise ValueError("task failed")

        runner = TaskRunner(log_errors=False)
        runner.add("fail", failing_task)
        result = runner.run()

        assert result.results == {}
        assert "fail" in result.exceptions
        assert isinstance(result.exceptions["fail"], ValueError)
        assert str(result.exceptions["fail"]) == "task failed"
        assert result.success is False

    def test_run_multiple_exceptions(self) -> None:
        """Multiple failures captured."""

        def fail1() -> None:
            raise ValueError("error1")

        def fail2() -> None:
            raise RuntimeError("error2")

        runner = TaskRunner(log_errors=False)
        runner.add("f1", fail1)
        runner.add("f2", fail2)
        result = runner.run()

        assert len(result.exceptions) == 2
        assert isinstance(result.exceptions["f1"], ValueError)
        assert isinstance(result.exceptions["f2"], RuntimeError)
        assert result.success is False

    def test_run_partial_success(self) -> None:
        """Some succeed, some fail."""

        def success() -> int:
            return 42

        def failure() -> None:
            raise ValueError("oops")

        runner = TaskRunner(log_errors=False)
        runner.add("ok", success)
        runner.add("bad", failure)
        result = runner.run()

        assert result.results == {"ok": 42}
        assert "bad" in result.exceptions
        assert result.success is False

    def test_success_flag_all_success(self) -> None:
        """result.success=True when all tasks pass."""

        def task() -> int:
            return 1

        runner = TaskRunner()
        runner.add("t1", task)
        runner.add("t2", task)
        result = runner.run()

        assert result.success is True
        assert result.timed_out is False
        assert result.exceptions == {}

    def test_success_flag_with_exception(self) -> None:
        """result.success=False with exception."""

        def fail() -> None:
            raise RuntimeError("error")

        runner = TaskRunner(log_errors=False)
        runner.add("fail", fail)
        result = runner.run()

        assert result.success is False

    def test_concurrency_limit(self) -> None:
        """Respects concurrency limit."""
        max_concurrent = 0
        current_concurrent = 0
        lock = threading.Lock()

        def task() -> None:
            nonlocal max_concurrent, current_concurrent
            with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            time.sleep(0.05)
            with lock:
                current_concurrent -= 1

        runner = TaskRunner(concurrency=2)
        for i in range(6):
            runner.add(f"task{i}", task)
        runner.run()

        assert max_concurrent <= 2


class TestTaskRunnerTimeout:
    """Tests for TaskRunner timeout behavior."""

    def test_timeout_returns_within_limit(self) -> None:
        """run() returns within timeout."""

        def slow_task() -> None:
            time.sleep(10)

        runner = TaskRunner(timeout=0.1)
        runner.add("slow", slow_task)

        start = time.monotonic()
        runner.run()
        elapsed = time.monotonic() - start

        assert elapsed < 0.5

    def test_timeout_sets_timed_out_flag(self) -> None:
        """result.timed_out=True on timeout."""

        def slow_task() -> None:
            time.sleep(10)

        runner = TaskRunner(timeout=0.1)
        runner.add("slow", slow_task)
        result = runner.run()

        assert result.timed_out is True

    def test_timeout_success_false(self) -> None:
        """result.success=False on timeout."""

        def slow_task() -> None:
            time.sleep(10)

        runner = TaskRunner(timeout=0.1)
        runner.add("slow", slow_task)
        result = runner.run()

        assert result.success is False

    def test_no_timeout(self) -> None:
        """timeout=None allows unlimited execution."""

        def task() -> int:
            time.sleep(0.05)
            return 42

        runner = TaskRunner(timeout=None)
        runner.add("task", task)
        result = runner.run()

        assert result.results == {"task": 42}
        assert result.timed_out is False
        assert result.success is True

    def test_fast_tasks_complete_before_timeout(self) -> None:
        """Fast tasks complete successfully with timeout set."""

        def fast_task() -> int:
            return 42

        runner = TaskRunner(timeout=10.0)
        runner.add("fast", fast_task)
        result = runner.run()

        assert result.results == {"fast": 42}
        assert result.timed_out is False
        assert result.success is True

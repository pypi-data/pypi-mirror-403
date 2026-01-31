"""Concurrent task execution with result collection and error handling."""

import concurrent.futures
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

type Func = Callable[..., Any]
type Args = tuple[Any, ...]
type Kwargs = dict[str, Any]
type TaskKey = str

logger = logging.getLogger(__name__)


@dataclass
class TaskRunnerResult:
    """Result of running a batch of tasks.

    Attributes:
        results: Successful task results mapped by key.
        exceptions: Task exceptions mapped by key.
        success: True if all tasks succeeded (no exceptions, no timeout).
        timed_out: True if execution was stopped by timeout.

    """

    results: dict[TaskKey, Any]
    exceptions: dict[TaskKey, Exception]
    success: bool
    timed_out: bool


class TaskRunner:
    """Execute multiple tasks concurrently and collect results by key.

    Manages a ThreadPoolExecutor to run tasks concurrently with configurable
    concurrency limit, tracking results and exceptions for each task by its unique key.

    Note: This runner is designed for one-time use. Create a new instance for each batch of tasks.

    Important: The timeout guarantees that run() returns within the specified time, but
    already-running threads cannot be interrupted (Python limitation). Pending tasks are
    cancelled, but running tasks continue in background. For I/O-bound tasks requiring
    guaranteed cancellation, use AsyncTaskRunner or implement timeouts within task functions.

    Example:
        runner = TaskRunner(concurrency=3, timeout=10.5, name="data_processor")
        runner.add("task1", fetch_data, ("url1",))
        runner.add("task2", process_file, ("file.txt",))
        result = runner.run()

        if not result.success:
            print(f"Failed: {result.exceptions}")
        print(f"Results: {result.results}")

    """

    def __init__(
        self,
        concurrency: int = 5,
        timeout: float | None = None,
        name: str | None = None,
        log_errors: bool = True,
    ) -> None:
        """Initialize TaskRunner.

        Args:
            concurrency: Maximum number of tasks that can run concurrently.
            timeout: Overall timeout in seconds. Guarantees run() returns within this time.
                Already-running threads continue in background (cannot be killed in Python).
            name: Optional name for the runner (useful for debugging).
            log_errors: If True, logs exceptions raised by tasks.

        Raises:
            ValueError: If timeout is not positive.

        """
        if timeout is not None and timeout <= 0:
            raise ValueError("Timeout must be positive if specified")

        self._concurrency = concurrency
        self._timeout = timeout
        self._name = name
        self._log_errors = log_errors
        self._tasks: list[TaskRunner._Task] = []  # queued tasks awaiting execution
        self._task_keys: set[TaskKey] = set()  # tracks used keys to prevent duplicates
        self._was_run = False  # ensures single-use semantics

    @dataclass
    class _Task:
        key: TaskKey
        func: Func
        args: Args
        kwargs: Kwargs

    def add(self, key: TaskKey, func: Func, args: Args = (), kwargs: Kwargs | None = None) -> None:
        """Add a task to be executed.

        Args:
            key: Unique identifier for this task.
            func: Function to execute.
            args: Positional arguments for the function.
            kwargs: Keyword arguments for the function.

        Raises:
            RuntimeError: If the runner has already been used.
            ValueError: If key is empty or already exists.

        """
        if self._was_run:
            raise RuntimeError("This TaskRunner has already been used. Create a new instance for new tasks.")

        if not key or not key.strip():
            raise ValueError("Task key cannot be empty")

        if key in self._task_keys:
            raise ValueError(f"Task key '{key}' already exists")

        if kwargs is None:
            kwargs = {}

        self._task_keys.add(key)
        self._tasks.append(TaskRunner._Task(key, func, args, kwargs))

    def run(self) -> TaskRunnerResult:
        """Execute all added tasks concurrently.

        Returns TaskRunnerResult containing task results, exceptions,
        and flags indicating overall status.

        Raises:
            RuntimeError: If the runner has already been used.
            ValueError: If no tasks have been added.

        """
        if self._was_run:
            raise RuntimeError("This TaskRunner instance can only be run once. Create a new instance for new tasks.")

        self._was_run = True

        if not self._tasks:
            raise ValueError("No tasks to run. Add tasks using add() method before calling run()")

        results: dict[TaskKey, Any] = {}
        exceptions: dict[TaskKey, Exception] = {}
        timed_out = False

        thread_name_prefix = f"{self._name}_task_runner" if self._name else "task_runner"

        executor = concurrent.futures.ThreadPoolExecutor(self._concurrency, thread_name_prefix=thread_name_prefix)
        try:
            future_to_key = {executor.submit(task.func, *task.args, **task.kwargs): task.key for task in self._tasks}
            try:
                for future in concurrent.futures.as_completed(future_to_key, timeout=self._timeout):
                    key = future_to_key[future]
                    try:
                        results[key] = future.result()
                    except Exception as err:
                        if self._log_errors:
                            logger.exception("Task raised an exception", extra={"task_key": key})
                        exceptions[key] = err
            except concurrent.futures.TimeoutError:
                timed_out = True
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        success = not exceptions and not timed_out
        return TaskRunnerResult(results=results, exceptions=exceptions, success=success, timed_out=timed_out)

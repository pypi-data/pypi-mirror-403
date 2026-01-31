"""Concurrent async task execution with result collection and error handling."""

import asyncio
import logging
from collections.abc import Awaitable
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

from ._sync import TaskRunnerResult

type TaskKey = str

logger = logging.getLogger(__name__)


class AsyncTaskRunner:
    """Execute multiple async tasks concurrently and collect results by key.

    Manages asyncio task groups to run coroutines concurrently with configurable
    concurrency limit, tracking results and exceptions for each task by its unique key.

    Note: This runner is designed for one-time use. Create a new instance for each batch of tasks.

    Example:
        runner = AsyncTaskRunner(concurrency=3, timeout=10.5, name="data_fetcher")
        runner.add("task1", fetch_data_async("url1"))
        runner.add("task2", process_file_async("file.txt"))
        result = await runner.run()

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
        """Initialize AsyncTaskRunner.

        Args:
            concurrency: Maximum number of tasks that can run concurrently.
            timeout: Optional overall timeout in seconds for running all tasks.
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
        self._tasks: list[AsyncTaskRunner._Task] = []  # queued tasks awaiting execution
        self._task_keys: set[TaskKey] = set()  # tracks used keys to prevent duplicates
        self._was_run = False  # ensures single-use semantics

    @dataclass
    class _Task:
        key: TaskKey
        awaitable: Awaitable[Any]

    def add(self, key: TaskKey, awaitable: Awaitable[Any]) -> None:
        """Add an async task to be executed.

        Args:
            key: Unique identifier for this task.
            awaitable: Awaitable object (coroutine) to execute.

        Raises:
            RuntimeError: If the runner has already been used.
            ValueError: If key is empty or already exists.

        """
        if self._was_run:
            raise RuntimeError("This AsyncTaskRunner has already been used. Create a new instance for new tasks.")

        if not key or not key.strip():
            raise ValueError("Task key cannot be empty")

        if key in self._task_keys:
            raise ValueError(f"Task key '{key}' already exists")

        self._task_keys.add(key)
        self._tasks.append(AsyncTaskRunner._Task(key, awaitable))

    async def run(self) -> TaskRunnerResult:
        """Execute all added async tasks concurrently.

        Returns TaskRunnerResult containing task results, exceptions,
        and flags indicating overall status.

        Raises:
            RuntimeError: If the runner has already been used.
            ValueError: If no tasks have been added.

        """
        if self._was_run:
            raise RuntimeError("This AsyncTaskRunner instance can only be run once. Create a new instance for new tasks.")

        self._was_run = True

        if not self._tasks:
            raise ValueError("No tasks to run. Add tasks using add() method before calling run()")

        results: dict[TaskKey, Any] = {}
        exceptions: dict[TaskKey, Exception] = {}
        timed_out = False

        async def _run_task_with_semaphore(task: AsyncTaskRunner._Task, semaphore: asyncio.Semaphore) -> None:
            """Run a single task with semaphore protection to limit concurrency."""
            async with semaphore:
                try:
                    result = await task.awaitable
                    results[task.key] = result
                except Exception as err:  # CancelledError is BaseException since Python 3.8, so it propagates correctly
                    if self._log_errors:
                        logger.exception("Task raised an exception", extra={"task_key": task.key})
                    exceptions[task.key] = err

        try:
            timeout_ctx = asyncio.timeout(self._timeout) if self._timeout else nullcontext()
            async with timeout_ctx, asyncio.TaskGroup() as tg:
                semaphore = asyncio.Semaphore(self._concurrency)
                for task in self._tasks:
                    tg.create_task(_run_task_with_semaphore(task, semaphore))
        except TimeoutError:
            timed_out = True
        # CancelledError is not caught — external cancellation propagates to caller

        success = not exceptions and not timed_out
        return TaskRunnerResult(results=results, exceptions=exceptions, success=success, timed_out=timed_out)

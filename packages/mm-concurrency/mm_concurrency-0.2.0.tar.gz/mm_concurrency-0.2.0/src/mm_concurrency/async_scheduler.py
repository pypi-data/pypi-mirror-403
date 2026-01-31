"""Async scheduler for running tasks at fixed intervals."""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from types import MappingProxyType
from typing import Any


class IntervalMode(Enum):
    """How interval is measured between job executions."""

    START_TO_START = "start_to_start"  # interval from run start to next run start
    END_TO_START = "end_to_start"  # interval from run end to next run start


type _AsyncFunc = Callable[..., Awaitable[object]]
type _Args = tuple[object, ...]
type _Kwargs = dict[str, object]

_logger = logging.getLogger(__name__)


class AsyncScheduler:
    """Scheduler for running async tasks at fixed intervals.

    Lifecycle: add() -> start() -> [running] -> stop() -> [can restart or clear_jobs()]
    """

    @dataclass
    class Job:
        """Scheduled job configuration and runtime state.

        Configuration fields (set at creation):
            name, interval, func, args, kwargs, interval_mode

        Runtime state fields (updated during execution, reset on start):
            run_count, error_count, last_started_at, started_at_monotonic, running
        """

        name: str  # Unique job identifier
        interval: float  # Seconds between executions
        func: _AsyncFunc  # Async function to execute
        args: _Args = ()  # Positional arguments for func
        kwargs: _Kwargs = field(default_factory=dict)  # Keyword arguments for func
        interval_mode: IntervalMode = IntervalMode.END_TO_START  # How interval is measured
        run_count: int = 0  # Total number of executions
        error_count: int = 0  # Number of failed executions
        last_started_at: datetime | None = None  # Timestamp of last execution start
        running: bool = False  # True while job is currently executing
        started_at_monotonic: float = 0.0  # Monotonic time for interval calculation

        def reset_stats(self) -> None:
            """Reset runtime statistics."""
            self.run_count = 0
            self.error_count = 0
            self.last_started_at = None
            self.running = False
            self.started_at_monotonic = 0.0

    def __init__(self, name: str = "AsyncScheduler") -> None:
        """Initialize the async scheduler."""
        self._name = name  # Scheduler name, used as prefix for asyncio task names
        self._jobs: dict[str, AsyncScheduler.Job] = {}  # Registered jobs by name
        self._tasks: dict[str, asyncio.Task[Any]] = {}  # Running asyncio tasks by job name
        self._running = False  # True while scheduler is active
        self._stop_event: asyncio.Event | None = None  # Signal to stop jobs

    @property
    def running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running

    @property
    def jobs(self) -> Mapping[str, Job]:
        """Read-only view of scheduled jobs."""
        return MappingProxyType(self._jobs)

    def add(
        self,
        name: str,
        interval: float,
        func: _AsyncFunc,
        args: _Args = (),
        kwargs: _Kwargs | None = None,
        interval_mode: IntervalMode = IntervalMode.END_TO_START,
    ) -> None:
        """Register a new job with the scheduler.

        Jobs can only be added when the scheduler is not running.
        Overlapping is never allowed — each job waits for the previous run to complete.

        Args:
            name: Unique identifier for the job.
            interval: Time in seconds between job executions.
            func: Async function to execute.
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
            interval_mode: How interval is measured (END_TO_START by default).

        Raises:
            RuntimeError: If scheduler is running.
            ValueError: If name is empty, interval is not positive, or job with same name exists.

        """
        if self._running:
            raise RuntimeError("Cannot add jobs while scheduler is running")
        if not name or not name.strip():
            raise ValueError("Job name cannot be empty")
        if interval <= 0:
            raise ValueError("Interval must be positive")
        if name in self._jobs:
            raise ValueError(f"Job '{name}' already exists")

        self._jobs[name] = AsyncScheduler.Job(
            name=name,
            interval=interval,
            func=func,
            args=args,
            kwargs=kwargs if kwargs is not None else {},
            interval_mode=interval_mode,
        )

    def clear_jobs(self) -> None:
        """Remove all job configurations.

        Can only be called when scheduler is not running.

        Raises:
            RuntimeError: If scheduler is running.

        """
        if self._running:
            raise RuntimeError("Cannot clear jobs while scheduler is running")
        self._jobs.clear()

    async def _run_job(self, job: Job) -> None:
        """Run a single job repeatedly until stop signal."""
        stop_event = self._stop_event
        if stop_event is None:
            return

        loop = asyncio.get_running_loop()
        try:
            while not stop_event.is_set():
                job.running = True
                job.started_at_monotonic = loop.time()
                job.last_started_at = datetime.now(UTC)
                job.run_count += 1

                try:
                    await job.func(*job.args, **job.kwargs)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    job.error_count += 1
                    _logger.exception("Error in job", extra={"job_name": job.name, "error_count": job.error_count})
                finally:
                    job.running = False

                # Check stop signal before sleeping
                if stop_event.is_set():
                    break

                # Calculate sleep time based on interval_mode
                if job.interval_mode == IntervalMode.START_TO_START:
                    elapsed = loop.time() - job.started_at_monotonic
                    sleep_time = max(0.0, job.interval - elapsed)
                else:
                    sleep_time = job.interval

                # Interruptible sleep: wait for stop_event or timeout
                if sleep_time > 0:
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=sleep_time)
                        break  # stop_event was set
                    except TimeoutError:
                        pass  # sleep completed, continue to next iteration
        except asyncio.CancelledError:
            pass

    async def start(self) -> None:
        """Start the scheduler with all added jobs.

        Returns immediately after spawning job tasks. Jobs continue running
        in the background until stop() is called.

        Runtime state (run_count, error_count, etc.) is reset for all jobs.

        Raises:
            RuntimeError: If already running or no jobs added.

        """
        if self._running:
            raise RuntimeError("AsyncScheduler already running")
        if not self._jobs:
            raise RuntimeError("No jobs to run")

        self._running = True
        self._stop_event = asyncio.Event()

        for name, job in self._jobs.items():
            job.reset_stats()
            task = asyncio.create_task(self._run_job(job), name=f"{self._name}-{name}")
            self._tasks[name] = task

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the scheduler gracefully.

        Shutdown algorithm:
        1. Signal stop via event — all sleeping jobs wake up immediately and exit.
        2. Jobs currently executing job.func() continue until they finish.
           No new iterations start after stop signal.
        3. Wait up to `timeout` seconds for all jobs to complete gracefully.
        4. If timeout expires, force cancel remaining tasks and wait for them.

        This means:
        - Interval sleep is interrupted immediately (no waiting for long intervals).
        - Running job functions get a chance to complete (up to timeout).
        - After stop(), job configurations are preserved. Call clear_jobs() to remove them.

        Args:
            timeout: Seconds to wait for graceful shutdown before force cancelling.

        Raises:
            RuntimeError: If not running.

        """
        if not self._running:
            raise RuntimeError("AsyncScheduler not running")

        self._running = False

        # Step 1: Signal stop — wakes up all sleeping jobs immediately
        if self._stop_event:
            self._stop_event.set()

        # Steps 2-4: Wait for graceful completion, force cancel on timeout
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks.values(), return_exceptions=True),
                    timeout=timeout,
                )
            except TimeoutError:
                _logger.warning("Graceful shutdown timed out, force cancelling jobs")
                for task in self._tasks.values():
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*self._tasks.values(), return_exceptions=True)

        self._tasks.clear()
        self._stop_event = None

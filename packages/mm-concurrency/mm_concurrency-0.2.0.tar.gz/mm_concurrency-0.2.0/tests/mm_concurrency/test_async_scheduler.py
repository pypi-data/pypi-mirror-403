"""Tests for AsyncScheduler."""

import asyncio
from types import MappingProxyType

import pytest

from mm_concurrency.async_scheduler import AsyncScheduler, IntervalMode


class TestIntervalMode:
    """Tests for IntervalMode enum."""

    def test_values(self) -> None:
        """Verify enum has expected values."""
        assert IntervalMode.START_TO_START.value == "start_to_start"
        assert IntervalMode.END_TO_START.value == "end_to_start"


class TestJob:
    """Tests for AsyncScheduler.Job dataclass."""

    def test_reset_stats(self) -> None:
        """Verify reset_stats clears runtime fields."""

        async def dummy() -> None:
            pass

        job = AsyncScheduler.Job(
            name="test",
            interval=1.0,
            func=dummy,
            run_count=5,
            error_count=2,
            last_started_at=None,
            running=True,
            started_at_monotonic=123.456,
        )

        job.reset_stats()

        assert job.run_count == 0
        assert job.error_count == 0
        assert job.last_started_at is None
        assert job.running is False
        assert job.started_at_monotonic == 0.0


class TestAsyncSchedulerAdd:
    """Tests for AsyncScheduler.add() method."""

    def test_add_job(self) -> None:
        """Successful job registration."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        scheduler.add("job1", 10.0, task)

        assert "job1" in scheduler.jobs
        assert scheduler.jobs["job1"].interval == 10.0

    async def test_add_while_running(self) -> None:
        """Cannot add jobs while scheduler is running."""

        async def task() -> None:
            await asyncio.sleep(1)

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.1, task)
        await scheduler.start()

        try:
            with pytest.raises(RuntimeError, match="Cannot add jobs while scheduler is running"):
                scheduler.add("job2", 0.1, task)
        finally:
            await scheduler.stop()

    def test_add_empty_name(self) -> None:
        """Empty name raises ValueError."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        with pytest.raises(ValueError, match="Job name cannot be empty"):
            scheduler.add("", 1.0, task)

    def test_add_whitespace_name(self) -> None:
        """Whitespace-only name raises ValueError."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        with pytest.raises(ValueError, match="Job name cannot be empty"):
            scheduler.add("   ", 1.0, task)

    @pytest.mark.parametrize("interval", [0, -1, -0.5])
    def test_add_non_positive_interval(self, interval: float) -> None:
        """Non-positive interval raises ValueError."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        with pytest.raises(ValueError, match="Interval must be positive"):
            scheduler.add("job1", interval, task)

    def test_add_duplicate_name(self) -> None:
        """Duplicate job name raises ValueError."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        scheduler.add("job1", 1.0, task)

        with pytest.raises(ValueError, match="Job 'job1' already exists"):
            scheduler.add("job1", 2.0, task)


class TestAsyncSchedulerClearJobs:
    """Tests for AsyncScheduler.clear_jobs() method."""

    def test_clear_jobs(self) -> None:
        """Removes all jobs."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        scheduler.add("job1", 1.0, task)
        scheduler.add("job2", 1.0, task)

        scheduler.clear_jobs()

        assert len(scheduler.jobs) == 0

    async def test_clear_jobs_while_running(self) -> None:
        """Cannot clear jobs while scheduler is running."""

        async def task() -> None:
            await asyncio.sleep(1)

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.1, task)
        await scheduler.start()

        try:
            with pytest.raises(RuntimeError, match="Cannot clear jobs while scheduler is running"):
                scheduler.clear_jobs()
        finally:
            await scheduler.stop()


class TestAsyncSchedulerStart:
    """Tests for AsyncScheduler.start() method."""

    async def test_start(self) -> None:
        """Scheduler starts and running property is True."""

        async def task() -> None:
            await asyncio.sleep(1)

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.1, task)

        await scheduler.start()

        try:
            assert scheduler.running is True
        finally:
            await scheduler.stop()

    async def test_start_already_running(self) -> None:
        """Cannot start scheduler that is already running."""

        async def task() -> None:
            await asyncio.sleep(1)

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.1, task)
        await scheduler.start()

        try:
            with pytest.raises(RuntimeError, match="AsyncScheduler already running"):
                await scheduler.start()
        finally:
            await scheduler.stop()

    async def test_start_no_jobs(self) -> None:
        """Cannot start scheduler with no jobs."""
        scheduler = AsyncScheduler()

        with pytest.raises(RuntimeError, match="No jobs to run"):
            await scheduler.start()

    async def test_start_resets_stats(self) -> None:
        """Stats are reset when scheduler starts."""
        run_count = 0

        async def task() -> None:
            nonlocal run_count
            run_count += 1

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.01, task)

        # First run
        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()
        first_run_count = scheduler.jobs["job1"].run_count

        # Second run — stats should be reset
        await scheduler.start()
        await asyncio.sleep(0.02)

        try:
            # run_count should be reset (starting from 1, not continuing from first run)
            assert scheduler.jobs["job1"].run_count < first_run_count
        finally:
            await scheduler.stop()


class TestAsyncSchedulerStop:
    """Tests for AsyncScheduler.stop() method."""

    async def test_stop(self) -> None:
        """Graceful stop sets running to False."""

        async def task() -> None:
            await asyncio.sleep(0.01)

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.01, task)
        await scheduler.start()

        await scheduler.stop()

        assert scheduler.running is False

    async def test_stop_not_running(self) -> None:
        """Cannot stop scheduler that is not running."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        scheduler.add("job1", 1.0, task)

        with pytest.raises(RuntimeError, match="AsyncScheduler not running"):
            await scheduler.stop()

    async def test_stop_force_cancel_on_timeout(self) -> None:
        """Slow jobs are force cancelled after timeout."""

        async def slow_task() -> None:
            await asyncio.sleep(10)

        scheduler = AsyncScheduler()
        scheduler.add("slow", 0.01, slow_task)
        await scheduler.start()

        # Give job time to start
        await asyncio.sleep(0.02)

        # Stop with short timeout — should force cancel
        await scheduler.stop(timeout=0.05)

        assert scheduler.running is False


class TestAsyncSchedulerJobExecution:
    """Tests for job execution behavior."""

    async def test_job_runs_repeatedly(self) -> None:
        """Job executes multiple times."""
        run_count = 0

        async def task() -> None:
            nonlocal run_count
            run_count += 1

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.01, task)

        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()

        assert run_count >= 3

    async def test_job_error_handling(self) -> None:
        """Exception increments error_count but doesn't stop execution."""
        run_count = 0

        async def failing_task() -> None:
            nonlocal run_count
            run_count += 1
            raise ValueError("test error")

        scheduler = AsyncScheduler()
        scheduler.add("failing", 0.01, failing_task)

        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()

        # Job should have run multiple times despite errors
        assert run_count >= 3
        assert scheduler.jobs["failing"].error_count >= 3

    async def test_interval_mode_end_to_start(self) -> None:
        """END_TO_START mode: interval is measured from job end."""
        timestamps: list[float] = []

        async def task() -> None:
            timestamps.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.02)  # job takes 20ms

        scheduler = AsyncScheduler()
        scheduler.add("job", 0.03, task, interval_mode=IntervalMode.END_TO_START)

        await scheduler.start()
        await asyncio.sleep(0.15)
        await scheduler.stop()

        # With END_TO_START: total cycle = 20ms (job) + 30ms (interval) = 50ms
        # In 150ms we should get ~3 runs
        assert len(timestamps) >= 2
        if len(timestamps) >= 2:
            # Interval between starts should be ~50ms (job duration + interval)
            interval = timestamps[1] - timestamps[0]
            assert interval >= 0.045  # allow some tolerance

    async def test_interval_mode_start_to_start(self) -> None:
        """START_TO_START mode: interval is measured from job start."""
        timestamps: list[float] = []

        async def task() -> None:
            timestamps.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.01)  # job takes 10ms

        scheduler = AsyncScheduler()
        scheduler.add("job", 0.03, task, interval_mode=IntervalMode.START_TO_START)

        await scheduler.start()
        await asyncio.sleep(0.1)
        await scheduler.stop()

        # With START_TO_START: interval between starts should be ~30ms
        assert len(timestamps) >= 2
        if len(timestamps) >= 2:
            interval = timestamps[1] - timestamps[0]
            # Should be close to 30ms (the configured interval)
            assert 0.025 <= interval <= 0.05

    async def test_job_stats_updated(self) -> None:
        """Job stats are updated during execution."""
        started = asyncio.Event()

        async def task() -> None:
            started.set()
            await asyncio.sleep(0.1)

        scheduler = AsyncScheduler()
        scheduler.add("job1", 0.5, task)

        await scheduler.start()
        await started.wait()

        try:
            job = scheduler.jobs["job1"]
            assert job.run_count == 1
            assert job.last_started_at is not None
            assert job.running is True
        finally:
            await scheduler.stop()


class TestAsyncSchedulerProperties:
    """Tests for AsyncScheduler properties."""

    async def test_running_property(self) -> None:
        """Running property reflects scheduler state."""

        async def task() -> None:
            await asyncio.sleep(1)

        scheduler = AsyncScheduler()
        assert scheduler.running is False

        scheduler.add("job1", 0.1, task)
        await scheduler.start()
        assert scheduler.running is True

        await scheduler.stop()
        assert scheduler.running is False

    def test_jobs_property_readonly(self) -> None:
        """Jobs property returns read-only mapping."""

        async def task() -> None:
            pass

        scheduler = AsyncScheduler()
        scheduler.add("job1", 1.0, task)

        jobs = scheduler.jobs
        assert isinstance(jobs, MappingProxyType)

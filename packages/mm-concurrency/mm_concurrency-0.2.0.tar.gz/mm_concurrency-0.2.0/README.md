# mm-concurrency

A Python library for elegant concurrent and asynchronous task execution with built-in error handling, result collection, and mutex utilities.

## Features

- **Task Runners**: Execute multiple tasks concurrently with configurable limits and timeout support
- **Async Scheduler**: Run async tasks at fixed intervals with automatic error handling
- **Mutex Decorators**: Coordinate access to shared resources in both sync and async contexts
- **Error Handling**: Comprehensive exception tracking and result collection
- **Type Safe**: Full type annotations with mypy support
- **Modern Python**: Built for Python 3.14+ with latest async/await patterns


## Quick Start

### Async Task Runner

Execute multiple async tasks concurrently with automatic resource management:

```python
import asyncio
from mm_concurrency import AsyncTaskRunner

async def fetch_data(url: str) -> dict:
    # Your async data fetching logic
    await asyncio.sleep(1)
    return {"url": url, "data": "some data"}

async def main():
    # Create runner with concurrency limit and timeout
    runner = AsyncTaskRunner(concurrency=3, timeout=10.0)

    # Add tasks with unique keys
    runner.add("user1", fetch_data("https://api.example.com/user/1"))
    runner.add("user2", fetch_data("https://api.example.com/user/2"))
    runner.add("user3", fetch_data("https://api.example.com/user/3"))

    # Execute all tasks
    result = await runner.run()

    if result.success:
        print(f"All tasks completed: {result.results}")
    else:
        print(f"Some tasks failed: {result.exceptions}")

asyncio.run(main())
```

### Sync Task Runner

For CPU-bound or blocking I/O operations:

```python
from mm_concurrency import TaskRunner
import requests

def fetch_data(url: str) -> dict:
    response = requests.get(url)
    return response.json()

# Create and run tasks
runner = TaskRunner(concurrency=3, timeout=30.0)
runner.add("api1", fetch_data, ("https://api.example.com/data1",))
runner.add("api2", fetch_data, ("https://api.example.com/data2",))

result = runner.run()
print(f"Results: {result.results}")
```

### Async Mutex

Coordinate concurrent access to shared resources:

```python
from mm_concurrency import async_mutex, async_mutex_by

# Synchronize all calls to a function
@async_mutex
async def update_global_state() -> None:
    # Only one coroutine can execute this at a time
    global_counter += 1
    await asyncio.sleep(0.1)

# Synchronize by argument value
@async_mutex_by(param='user_id')
async def process_user_data(user_id: str, data: dict) -> dict:
    # Only one coroutine per user_id, but different users can run concurrently
    await asyncio.sleep(1)
    return {"user_id": user_id, "processed": True}

# Non-blocking mutex
@async_mutex_by(param='resource', skip_if_locked=True)
async def try_update_cache(resource: str) -> str | None:
    # Returns None if another coroutine is already processing this resource
    await expensive_operation(resource)
    return "updated"
```

### Thread Mutex

Same patterns for thread-based concurrency:

```python
from mm_concurrency import mutex, mutex_by

@mutex
def thread_safe_operation() -> None:
    # Only one thread at a time
    global shared_state
    shared_state += 1

@mutex_by(param='user_id')
def process_user(user_id: str, data: dict) -> dict:
    # Per-user synchronization
    return update_user_data(user_id, data)
```

### Async Scheduler

Run async tasks at fixed intervals:

```python
from mm_concurrency import AsyncScheduler

async def cleanup_expired_sessions() -> None:
    await db.delete_expired_sessions()

async def send_heartbeat() -> None:
    await monitoring.ping()

async def main():
    scheduler = AsyncScheduler()

    # Add jobs with name, interval (seconds), and async function
    scheduler.add("cleanup", 300.0, cleanup_expired_sessions)
    scheduler.add("heartbeat", 60.0, send_heartbeat)

    await scheduler.start()

    # ... application runs ...

    await scheduler.stop()  # Graceful shutdown (jobs preserved)
    scheduler.clear_jobs()       # Remove jobs if needed
```

## API Reference

### AsyncTaskRunner

Execute async tasks concurrently with resource limits:

```python
runner = AsyncTaskRunner(
    concurrency=5,          # Limit concurrent execution
    timeout=30.0,           # Overall timeout in seconds
    name="my_runner",       # Optional name for debugging
    log_errors=True         # Control exception logging
)

runner.add(key="task1", awaitable=my_coroutine())
result = await runner.run()

# Result object contains:
# result.results: dict[str, Any] - successful results by key
# result.exceptions: dict[str, Exception] - exceptions by key
# result.success: bool - True if no errors or timeouts
# result.timed_out: bool - True if timeout occurred
```

### TaskRunner

Execute sync tasks in thread pool:

```python
runner = TaskRunner(
    concurrency=5,
    timeout=30.0,
    name="my_runner",
    log_errors=True
)

runner.add(key="task1", func=my_function, args=(arg1,), kwargs={"key": "value"})
result = runner.run()  # Same TaskRunnerResult structure as AsyncTaskRunner
```

**Timeout behavior:** The timeout guarantees `run()` returns within the specified time. Pending tasks are cancelled, but already-running threads cannot be interrupted (Python limitation). For I/O-bound tasks, use `AsyncTaskRunner` or add timeouts within task functions (e.g., `requests.get(url, timeout=10)`).

### AsyncScheduler

Run async tasks at fixed intervals with automatic error handling:

```python
from mm_concurrency import AsyncScheduler, IntervalMode

scheduler = AsyncScheduler(name="my_scheduler")

# Add jobs (only when not running)
scheduler.add(
    name="job_name",       # Unique job identifier
    interval=60.0,         # Seconds between executions
    func=my_async_func,    # Async function to execute
    args=(arg1,),          # Optional positional arguments
    kwargs={"key": "val"}, # Optional keyword arguments
    interval_mode=IntervalMode.END_TO_START,  # How interval is measured (default)
)

await scheduler.start()    # Start all jobs
await scheduler.stop()     # Stop gracefully (jobs preserved)
scheduler.clear_jobs()          # Remove all jobs

# Properties
scheduler.running          # True if scheduler is active
scheduler.jobs             # Dict of Job objects for monitoring
```

**Interval modes:**
- `IntervalMode.END_TO_START` (default) — interval between run end and next run start; guarantees fixed pause between executions
- `IntervalMode.START_TO_START` — interval between run starts; if job takes longer than interval, next run starts immediately after

**No overlapping:** Jobs never run concurrently with themselves — each execution waits for the previous one to complete.

Lifecycle: `add() → start() → [running] → stop() → [can restart or clear_jobs()]`

### Mutex Decorators

#### Basic Mutex

- `@mutex` - Synchronize all calls to a function (threads)
- `@async_mutex` - Synchronize all calls to an async function (coroutines)

#### By-Value Mutex

- `@mutex_by(arg_index=0, param=None, skip_if_locked=False)` - Thread synchronization by argument
- `@async_mutex_by(arg_index=0, param=None, skip_if_locked=False)` - Coroutine synchronization by argument

Parameters:
- `arg_index`: Position of argument to use as lock key (default: 0)
- `param`: Name of parameter to use as lock key (overrides arg_index)
- `skip_if_locked`: Return None immediately if lock is held (default: False)

## Advanced Examples

### Error Handling and Timeouts

```python
async def main():
    runner = AsyncTaskRunner(concurrency=2, timeout=5.0)

    runner.add("fast", quick_task())
    runner.add("slow", slow_task())
    runner.add("failing", failing_task())

    result = await runner.run()

    # Handle different outcomes
    if result.timed_out:
        print("Some tasks timed out")

    for key, exception in result.exceptions.items():
        print(f"Task {key} failed: {exception}")

    for key, value in result.results.items():
        print(f"Task {key} succeeded: {value}")
```

### Dynamic Mutex

```python
# Synchronize by user ID - each user gets their own lock
@async_mutex_by(param='user_id')
async def update_user_profile(user_id: str, profile_data: dict) -> None:
    # Multiple users can update concurrently, but each user is serialized
    await database.update_user(user_id, profile_data)

# Non-blocking cache updates
@async_mutex_by(param='cache_key', skip_if_locked=True)
async def refresh_cache(cache_key: str) -> dict | None:
    # If cache is being refreshed, return None instead of waiting
    if cache_key in cache:
        return cache[cache_key]

    new_data = await fetch_expensive_data(cache_key)
    cache[cache_key] = new_data
    return new_data
```

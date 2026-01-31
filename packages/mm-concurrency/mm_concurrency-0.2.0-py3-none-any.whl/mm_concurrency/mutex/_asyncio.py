"""Asynchronous mutex decorators for async functions.

Provides decorators:
- async_mutex: All calls to the async function are synchronized
- async_mutex_by: Calls are synchronized only for matching argument values
"""

import asyncio
import functools
import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Literal, cast, overload


class _AsyncMutex:
    """Async mutex with safe non-blocking try_acquire.

    Uses Queue(maxsize=1) token pattern instead of asyncio.Lock to provide
    atomic non-blocking acquisition without race conditions.

    The problem with asyncio.Lock + wait_for(timeout=0):
    - Cancellation can occur after lock is acquired but before wait_for returns
    - This leaves the lock permanently held (deadlock)

    Queue-based solution:
    - get_nowait() is synchronous — no await, no cancellation point
    - Either token exists and we take it, or QueueEmpty — no intermediate states
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[None] = asyncio.Queue(maxsize=1)
        self._queue.put_nowait(None)  # seed token

    async def acquire(self) -> None:
        """Acquire the mutex, blocking until available."""
        await self._queue.get()

    def try_acquire(self) -> bool:
        """Try to acquire the mutex without blocking.

        Returns:
            True if acquired, False if already held by another task.

        """
        try:
            self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return False
        else:
            return True

    def release(self) -> None:
        """Release the mutex."""
        self._queue.put_nowait(None)


def async_mutex[T, **P](func: Callable[P, Awaitable[T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    """Ensure all calls to an async function are executed in synchronized manner.

    Creates a single asyncio.Lock for the function, guaranteeing that only one
    coroutine can execute the function at any time, regardless of arguments.
    Other coroutines will wait for their turn.

    Args:
        func: Async function to synchronize

    Returns:
        Synchronized version of the async function with the same signature

    Example:
        @async_mutex
        async def update_global_state() -> None:
            # Only one coroutine can execute this at a time
            global_counter += 1

        @async_mutex
        async def critical_section(data: dict) -> str:
            # All calls synchronized, even with different arguments
            return await process_shared_resource(data)

    """
    lock = asyncio.Lock()

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        async with lock:
            return await func(*args, **kwargs)

    return wrapper


@overload
def async_mutex_by[T, **P](
    *, arg_index: int = ..., param: str | None = ..., skip_if_locked: Literal[False] = ...
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Coroutine[Any, Any, T]]]: ...


@overload
def async_mutex_by[T, **P](
    *, arg_index: int = ..., param: str | None = ..., skip_if_locked: Literal[True]
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Coroutine[Any, Any, T | None]]]: ...


def async_mutex_by[T, **P](
    *, arg_index: int = 0, param: str | None = None, skip_if_locked: bool = False
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Coroutine[Any, Any, T | None]]]:
    """Synchronize async function calls based on argument values.

    Each unique value of the specified argument gets its own mutex, allowing
    concurrent execution for different argument values while synchronizing
    calls with the same argument value.

    Args:
        arg_index: Index of the argument to use as the lock key (default: 0)
        param: Name of the parameter to use as the lock key (overrides arg_index)
        skip_if_locked: If True, returns None when the lock is already held (default: False)

    Returns:
        Decorated async function that returns T or None (if skip_if_locked=True and lock is held)

    Raises:
        ValueError: If param is specified but not found in function signature

    Example:
        @async_mutex_by(arg_index=0)
        async def process_user(user_id: str) -> None:
            # Only one coroutine can process the same user_id at a time
            # But different user_ids can be processed concurrently
            pass

        @async_mutex_by(param='user_id')
        async def process_user(user_id: str, data: dict) -> None:
            # More readable - synchronizes by user_id parameter
            pass

        @async_mutex_by(skip_if_locked=True)
        async def try_update_cache(cache_key: str) -> bool:
            # Returns None if another coroutine is already updating this key
            pass

    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Coroutine[Any, Any, T | None]]:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        if param and param not in param_names:
            raise ValueError(f"Parameter '{param}' not found in function signature. Available parameters: {param_names}")
        if not param and arg_index >= len(param_names):
            raise ValueError(f"arg_index {arg_index} out of range. Function has {len(param_names)} parameters: {param_names}")

        # Shared state for all calls to this decorated function
        locks: dict[object, _AsyncMutex] = {}  # lock key -> mutex
        usage_count: dict[object, int] = defaultdict(int)  # reference counter for safe cleanup
        registry_lock = asyncio.Lock()  # protects locks and usage_count from race conditions

        def extract_key(args: tuple[object, ...], kwargs: dict[str, object]) -> object:
            """Extract the locking key from function arguments."""
            target_param = param if param else param_names[arg_index]
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            return bound.arguments[target_param]

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            lock_key = extract_key(args, cast(dict[str, object], kwargs))

            # Step 1: Atomically get or create mutex and increment usage count
            async with registry_lock:
                if lock_key not in locks:
                    locks[lock_key] = _AsyncMutex()
                mutex = locks[lock_key]
                usage_count[lock_key] += 1

            # Step 2: Try to acquire the mutex
            if skip_if_locked:
                if not mutex.try_acquire():
                    # Failed to acquire — cleanup and return None
                    async with registry_lock:
                        usage_count[lock_key] -= 1
                        if usage_count[lock_key] == 0:
                            locks.pop(lock_key, None)
                            usage_count.pop(lock_key, None)
                    return None
            else:
                try:
                    await mutex.acquire()
                except asyncio.CancelledError:
                    async with registry_lock:
                        usage_count[lock_key] -= 1
                        if usage_count[lock_key] == 0:
                            locks.pop(lock_key, None)
                            usage_count.pop(lock_key, None)
                    raise

            # Step 3: Execute function and cleanup
            try:
                return await func(*args, **kwargs)
            finally:
                mutex.release()
                async with registry_lock:
                    usage_count[lock_key] -= 1
                    if usage_count[lock_key] == 0:
                        locks.pop(lock_key, None)
                        usage_count.pop(lock_key, None)

        return wrapper

    return decorator

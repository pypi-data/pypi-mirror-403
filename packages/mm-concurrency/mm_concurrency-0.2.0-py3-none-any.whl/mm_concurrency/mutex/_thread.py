"""Thread-based mutex decorators for synchronizing function calls.

Provides two decorators:
- mutex: All calls to the function are synchronized
- mutex_by: Calls are synchronized only for matching argument values
"""

import functools
import inspect
from collections import defaultdict
from collections.abc import Callable
from threading import Lock, RLock
from typing import Literal, cast, overload


@overload
def mutex_by[T, **P](
    *, arg_index: int = ..., param: str | None = ..., skip_if_locked: Literal[False] = ...
) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


@overload
def mutex_by[T, **P](
    *, arg_index: int = ..., param: str | None = ..., skip_if_locked: Literal[True]
) -> Callable[[Callable[P, T]], Callable[P, T | None]]: ...


def mutex_by[T, **P](
    *, arg_index: int = 0, param: str | None = None, skip_if_locked: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T | None]]:
    """Synchronize function calls based on argument values.

    Each unique value of the specified argument gets its own lock, allowing
    concurrent execution for different argument values while synchronizing
    calls with the same argument value.

    Args:
        arg_index: Index of the argument to use as the lock key (default: 0)
        param: Name of the parameter to use as the lock key (overrides arg_index)
        skip_if_locked: If True, returns None when the lock is already held (default: False)

    Returns:
        Decorated function that returns T or None (if skip_if_locked=True and lock is held)

    Raises:
        ValueError: If param is specified but not found in function signature

    Example:
        @mutex_by(arg_index=0)
        def process_user(user_id: str) -> None:
            # Only one thread can process the same user_id at a time
            # But different user_ids can be processed concurrently
            pass

        @mutex_by(param='user_id')
        def process_user(user_id: str, data: dict) -> None:
            # More readable - synchronizes by user_id parameter
            pass

        @mutex_by(skip_if_locked=True)
        def try_update_cache(cache_key: str) -> bool:
            # Returns None if another thread is already updating this key
            pass

    """

    def decorator(func: Callable[P, T]) -> Callable[P, T | None]:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        if param and param not in param_names:
            raise ValueError(f"Parameter '{param}' not found in function signature. Available parameters: {param_names}")
        if not param and arg_index >= len(param_names):
            raise ValueError(f"arg_index {arg_index} out of range. Function has {len(param_names)} parameters: {param_names}")

        # Shared state for all calls to this decorated function
        locks: dict[object, Lock] = {}  # lock key -> Lock
        usage_count: dict[object, int] = defaultdict(int)  # reference counter for safe cleanup
        registry_lock = RLock()  # protects locks and usage_count from race conditions

        def extract_key(args: tuple[object, ...], kwargs: dict[str, object]) -> object:
            """Extract the locking key from function arguments."""
            target_param = param if param else param_names[arg_index]
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            return bound.arguments[target_param]

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            lock_key = extract_key(args, cast(dict[str, object], kwargs))

            # Step 1: Atomically get or create lock and increment usage count
            with registry_lock:
                if lock_key not in locks:
                    locks[lock_key] = Lock()
                lock = locks[lock_key]
                usage_count[lock_key] += 1

            # Step 2: Try to acquire the lock
            acquired = lock.acquire(blocking=not skip_if_locked)

            if not acquired:
                # Failed to get lock in skip_if_locked mode
                with registry_lock:
                    usage_count[lock_key] -= 1
                    if usage_count[lock_key] == 0:
                        locks.pop(lock_key, None)
                        usage_count.pop(lock_key, None)
                return None

            # Step 3: Execute function and cleanup
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()
                with registry_lock:
                    usage_count[lock_key] -= 1
                    if usage_count[lock_key] == 0:
                        locks.pop(lock_key, None)
                        usage_count.pop(lock_key, None)

        return wrapper

    return decorator


def mutex[T, **P](func: Callable[P, T]) -> Callable[P, T]:
    """Ensure all calls to a function are executed in synchronized manner.

    Creates a single lock for the function, guaranteeing that only one thread
    can execute the function at any time, regardless of arguments.

    Args:
        func: Function to synchronize

    Returns:
        Synchronized version of the function with the same signature

    Example:
        @mutex
        def update_global_state() -> None:
            # Only one thread can execute this at a time
            global_counter += 1

        @mutex
        def critical_section(data: dict) -> str:
            # All calls synchronized, even with different arguments
            return process_shared_resource(data)

    """
    lock = Lock()

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        with lock:
            return func(*args, **kwargs)

    return wrapper

"""Mutex decorators for synchronizing function calls.

Provides both thread-based and async decorators:
- mutex: Synchronize all calls to a function (threads)
- mutex_by: Synchronize calls by argument value (threads)
- async_mutex: Synchronize all calls to an async function (coroutines)
- async_mutex_by: Synchronize async calls by argument value (coroutines)
"""

from ._asyncio import async_mutex as async_mutex
from ._asyncio import async_mutex_by as async_mutex_by
from ._thread import mutex as mutex
from ._thread import mutex_by as mutex_by

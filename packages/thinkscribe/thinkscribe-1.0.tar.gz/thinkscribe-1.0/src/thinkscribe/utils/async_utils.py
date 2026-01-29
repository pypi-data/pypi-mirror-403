"""Async execution helpers."""

import asyncio
import concurrent.futures
from typing import Coroutine, TypeVar

T = TypeVar("T")


def run_async_safe(coro: Coroutine[None, None, T]) -> T:
    """
    Safely run an async function, handling existing event loops.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    try:
        # Try to get existing event loop (for nested async contexts)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, create a new loop in a thread
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)

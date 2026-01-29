import logging
from asyncio import Semaphore
from collections.abc import Awaitable, Callable
from functools import wraps
from inspect import iscoroutinefunction
from threading import Lock, RLock
from time import perf_counter
from typing import Any, overload

try:
    from loguru import logger as _logger
except ImportError:
    _logger = logging.getLogger(__name__)


@overload
def with_timer[R, **P](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def with_timer[R, **P](
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]: ...


def with_timer[R, **P](
    func: Callable[P, R] | Callable[P, Awaitable[R]],
) -> Callable[P, R] | Callable[P, Awaitable[R]]:
    """
    Decorator to measure and log execution time of sync of async functions

    Args:
        func: The function to be timed.

    Returns:
        Wrapped function that logs execution time.

    Example:
        >>> @with_timer
            def foo():
                time.sleep(1)
                return "bar"
            foo() # logs: "foo took 1.0000s"
    """
    if iscoroutinefunction(func):

        @wraps(func)
        async def _async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _start_time = perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                _logger.info(f"{func.__name__} took {perf_counter() - _start_time:.4f}s")

        return _async_wrapper

    @wraps(func)
    def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        _start_time = perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            _logger.info(f"{func.__name__} took {perf_counter() - _start_time:.4f}s")

    return _wrapper


def with_semaphore[R, **P](
    semaphore: Semaphore,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """
    Decorator to limit concurrent execution of async function using a semaphore.

    Args:
        semaphore: Semaphore to control concurrency.

    Returns:
        Decorator function that wraps the async function.

    Example:
        >>> sem = asyncio.Semaphore(3)
        >>> @with_semaphore(sem)
            async def fetch_data(url):
                async def aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        return await resp.text()
    """

    def _decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        @wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async with semaphore:
                return await func(*args, **kwargs)

        return _wrapper

    return _decorator


def synchronized[R, **P](
    lock: Lock | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to make function execution thread-safe.

    Args:
        lock: Optional threading.Lock. If None, creates a new lock per function.

    Returns:
        Decorated function that acquires lock before execution.

    Example:
        >>> shared_lock = threading.Lock()
        >>> @synchronized(shared_lock)
            def thread_safe_function():
                # CRITICAL SECTION
                pass
    """

    def _decorator(func: Callable[..., R]) -> Callable[..., R]:
        _func_lock = lock or RLock()

        @wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> R:
            with _func_lock:
                return func(*args, **kwargs)

        return _wrapper

    return _decorator

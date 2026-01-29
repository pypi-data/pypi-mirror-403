import asyncio
import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from time import perf_counter
from typing import overload

from loguru import logger


@overload
def with_timer[R, **P](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def with_timer[R, **P](func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]: ...


def with_timer[R, **P](
    func: Callable[P, R] | Callable[P, Awaitable[R]],
) -> Callable[P, R] | Callable[P, Awaitable[R]]:
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = perf_counter() - start_time
                logger.info(f"{func.__name__} took {elapsed:.4f}s")

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = perf_counter() - start_time
            logger.info(f"{func.__name__} took {elapsed:.4f}s")

    return sync_wrapper


def with_semaphore[R, **P](
    semaphore: asyncio.Semaphore,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async with semaphore:
                return await func(*args, **kwargs)

        return wrapper

    return decorator

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import overload

from .pyropust_native import Result


def _is_exception_type(value: object) -> bool:
    return isinstance(value, type) and issubclass(value, BaseException)


def _decorate[**P, R](
    fn: Callable[P, R],
    exc_types: tuple[type[BaseException], ...],
) -> Callable[P, Result[R]]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[R]:
        return Result.attempt(lambda: fn(*args, **kwargs), *exc_types)

    return wrapper


# Overload 1: Bare decorator usage (@catch)
@overload
def catch[**P, R](fn: Callable[P, R], /) -> Callable[P, Result[R]]: ...


# Overload 2: Decorator with exception types (@catch() or @catch(ValueError))
@overload
def catch[**P, R](
    *exc_types: type[BaseException],
) -> Callable[[Callable[P, R]], Callable[P, Result[R]]]: ...


def catch[**P, R](
    *args: type[BaseException] | Callable[P, R],
) -> Callable[P, Result[R]] | Callable[[Callable[P, R]], Callable[P, Result[R]]]:
    """Convert exceptions into Result using RopustError.

    Can be used as @catch or @catch(ValueError, TypeError).
    """
    # Bare decorator usage: @catch
    if args and callable(args[0]) and not _is_exception_type(args[0]):
        fn: Callable[P, R] = args[0]  # type: ignore[assignment]
        return _decorate(fn, (Exception,))

    # Decorator with arguments: @catch() or @catch(ValueError)
    exc_types: list[type[BaseException]] = []
    for exc in args:
        if not _is_exception_type(exc):
            raise TypeError("catch() expects exception types")
        exc_types.append(exc)  # type: ignore[arg-type]

    if not exc_types:
        exc_types = [Exception]

    def decorator(fn: Callable[P, R]) -> Callable[P, Result[R]]:
        return _decorate(fn, tuple(exc_types))

    return decorator

from __future__ import annotations

from collections.abc import Callable, Generator
from functools import wraps
from typing import TYPE_CHECKING, cast

from .pyropust_native import Result


def do[**P, T, R](
    fn: Callable[P, Generator[Result[T], T, Result[R]]],
) -> Callable[P, Result[R]]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[R]:
        gen = fn(*args, **kwargs)
        if not hasattr(gen, "send"):
            raise TypeError("@do function must return a generator")

        try:
            current = next(gen)
        except StopIteration as stop:
            value = stop.value
            if not isinstance(value, Result):
                raise TypeError("generator must return Result")
            return value

        while True:
            if not isinstance(current, Result):
                raise TypeError("yielded value must be Result")
            if current.is_err():
                # On error, the value type is irrelevant, so cast to Result[R]
                if TYPE_CHECKING:
                    return cast("Result[R]", current)
                return current
            try:
                current = gen.send(current.unwrap())
            except StopIteration as stop:
                value = stop.value
                if not isinstance(value, Result):
                    raise TypeError("generator must return Result")
                return value

    return wrapper

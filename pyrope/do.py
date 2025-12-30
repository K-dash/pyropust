from collections.abc import Callable, Generator
from functools import wraps

from .pyrope_native import Result


def do[**P, T, E, R](
    fn: Callable[P, Generator[Result[T, E], T, Result[R, E]]],
) -> Callable[P, Result[R, E]]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[R, E]:
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
                return current
            try:
                current = gen.send(current.unwrap())
            except StopIteration as stop:
                value = stop.value
                if not isinstance(value, Result):
                    raise TypeError("generator must return Result")
                return value

    return wrapper

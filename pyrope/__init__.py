from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

from .blueprint import Op
from .do import do

try:
    from .pyrope_native import (
        Blueprint,
        Err,
        ErrorKind,
        None_,
        Ok,
        Option,
        Operator,
        Result,
        RopeError,
        Some,
        run,
    )
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "pyrope extension module not found. "
        "Run `uv sync` or `maturin develop` to build it."
    ) from exc

__all__ = [
    "Result",
    "Option",
    "Ok",
    "Err",
    "Some",
    "None_",
    "RopeError",
    "ErrorKind",
    "Operator",
    "Blueprint",
    "run",
    "Op",
    "do",
]

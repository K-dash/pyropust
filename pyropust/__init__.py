from enum import StrEnum
from typing import Any

from .catch import catch
from .do import do

try:
    from .pyropust_native import (
        Err,
        Error,
        ErrorKind,
        None_,
        Ok,
        Option,
        Result,
        Some,
        bail,
        ensure,
        err,
        exception_to_error,
    )
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "pyropust extension module not found. Run `uv sync` or `maturin develop` to build it.",
    ) from exc


class ErrorCode(StrEnum):
    """Base class for pyropust error codes."""


def _error_class_getitem__(_item: Any) -> type[object]:
    return Error


if not hasattr(Error, "__class_getitem__"):
    # pyright can't see __class_getitem__ on the native pyo3 class; ignore is required.
    Error.__class_getitem__ = staticmethod(_error_class_getitem__)  # type: ignore[attr-defined]


__all__ = [
    "Err",
    "Error",
    "ErrorCode",
    "ErrorKind",
    "None_",
    "Ok",
    "Option",
    "Result",
    "Some",
    "bail",
    "catch",
    "do",
    "ensure",
    "err",
    "exception_to_error",
]

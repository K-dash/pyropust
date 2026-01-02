from __future__ import annotations

from collections.abc import Mapping
from typing import Never

from pyropust import Error, ErrorCode, ErrorKind, Result, err


class SampleCode(ErrorCode):
    ERROR = "error"
    ERROR1 = "error1"
    ERROR2 = "error2"
    NOT_FOUND = "404"
    CUSTOM = "custom"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    CACHE_MISS = "cache_miss"
    DB_FAIL = "db_fail"
    VALIDATION = "validation"
    NEGATIVE = "negative"
    TOO_LARGE = "too_large"
    BAD_INPUT = "bad_input"
    BOOM = "boom"
    PARSE_ERROR = "parse.error"


def err_msg(
    message: str,
    code: ErrorCode = SampleCode.ERROR,
) -> Result[Never, Error[ErrorCode]]:
    return err(code, message)


def new_error[CodeT: ErrorCode](
    *,
    code: CodeT,
    message: str,
    kind: ErrorKind | str | None = None,
    op: str | None = None,
    path: list[str | int] | None = None,
    expected: str | None = None,
    got: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> Error[CodeT]:
    return Error[CodeT].new(
        code=code,
        message=message,
        kind=kind,
        op=op,
        path=path,
        expected=expected,
        got=got,
        metadata=metadata,
    )


def wrap_error[CodeT: ErrorCode](
    err_value: BaseException | Error[CodeT],
    *,
    code: CodeT,
    message: str,
    kind: ErrorKind | str | None = None,
    op: str | None = None,
    path: list[str | int] | None = None,
    expected: str | None = None,
    got: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> Error[CodeT]:
    return Error[CodeT].wrap(
        err_value,
        code=code,
        message=message,
        kind=kind,
        op=op,
        path=path,
        expected=expected,
        got=got,
        metadata=metadata,
    )

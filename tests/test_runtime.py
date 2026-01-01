from __future__ import annotations

from collections.abc import Generator

import pytest

from pyropust import (
    Err,
    ErrorKind,
    None_,
    Ok,
    Result,
    RopustError,
    Some,
    catch,
    do,
    exception_to_ropust_error,
)


def test_result_ok_err() -> None:
    ok = Ok(123)
    err = Err("nope")

    assert ok.is_ok() is True
    assert ok.is_err() is False
    assert ok.unwrap() == 123

    assert err.is_ok() is False
    assert err.is_err() is True
    assert err.unwrap_err().message == "nope"


def test_option_unwrap() -> None:
    some = Some("x")
    none = None_()

    assert some.is_some() is True
    assert some.unwrap() == "x"

    assert none.is_none() is True
    try:
        none.unwrap()
    except RuntimeError:
        pass
    else:
        raise AssertionError("unwrap() on None_ must raise")


def test_do_short_circuit() -> None:
    @do
    def flow(value: str) -> Generator[Result[str], str, Result[str]]:
        value = yield Ok(value)
        return Ok(value.upper())

    assert flow("hello").unwrap() == "HELLO"
    assert flow("invalid").is_err() is False


def test_result_attempt_and_catch() -> None:
    ok = Result.attempt(lambda: 10 / 2)
    assert ok.is_ok() is True
    assert ok.unwrap() == 5.0

    err = Result.attempt(lambda: 10 / 0, ZeroDivisionError)
    assert err.is_err() is True
    assert isinstance(err.unwrap_err(), RopustError)

    try:
        Result.attempt(lambda: 10 / 0, ValueError)
    except ZeroDivisionError:
        pass
    else:
        raise AssertionError("non-matching exceptions must be re-raised")

    @catch(ValueError)
    def parse_int(value: str) -> int:
        return int(value)

    result = parse_int("not-int")
    assert result.is_err() is True
    assert isinstance(result.unwrap_err(), RopustError)


def test_unwrap_or_raise() -> None:
    ok = Ok(123)
    assert ok.unwrap_or_raise(RuntimeError("boom")) == 123

    err = Err("nope")
    with pytest.raises(RuntimeError, match="boom"):
        err.unwrap_or_raise(RuntimeError("boom"))


def test_exception_to_ropust_error() -> None:
    def raise_value_error() -> None:
        raise ValueError("boom")

    try:
        raise_value_error()
    except ValueError as exc:
        err = exception_to_ropust_error(exc)
        assert isinstance(err, RopustError)
        assert err.code == "py_exception"
        assert "py_traceback" in err.metadata


def test_ropust_error_dict_roundtrip() -> None:
    def raise_value_error() -> None:
        raise ValueError("boom")

    err: RopustError | None = None
    try:
        raise_value_error()
    except ValueError as exc:
        err = exception_to_ropust_error(exc)

    assert err is not None
    data = err.to_dict()
    parsed = RopustError.from_dict(data)

    assert parsed.kind == err.kind
    assert parsed.code == err.code
    assert parsed.message == err.message
    assert parsed.metadata["exception"] == "ValueError"
    assert "py_traceback" in parsed.metadata


def test_ropust_error_from_dict_missing_fields() -> None:
    with pytest.raises(TypeError, match="missing 'kind' field"):
        RopustError.from_dict({"code": "missing", "message": "oops"})


def test_ropust_error_new_builds_fields() -> None:
    err = RopustError.new(
        code="user.age.not_number",
        message="age must be a number",
        kind=ErrorKind.InvalidInput,
        op="ParseAge",
        path=["user", 0],
        expected="numeric string",
        got="x",
        metadata={"source": "input"},
    )

    assert err.code == "user.age.not_number"
    assert err.message == "age must be a number"
    assert err.kind == ErrorKind.InvalidInput
    assert err.op == "ParseAge"
    assert err.path == ["user", 0]
    assert err.expected == "numeric string"
    assert err.got == "x"
    assert err.metadata["source"] == "input"
    assert err.cause is None


def test_ropust_error_new_accepts_string_kind() -> None:
    err = RopustError.new(code="missing", message="oops", kind="NotFound")
    assert err.kind == ErrorKind.NotFound


def test_ropust_error_wrap_with_ropust_error() -> None:
    base = RopustError.new(code="user.age.not_number", message="age must be a number")
    wrapped = RopustError.wrap(
        base,
        code="user.load.failed",
        message="failed to load user",
        metadata={"source": "payload"},
    )

    assert wrapped.code == "user.load.failed"
    assert wrapped.message == "failed to load user"
    assert wrapped.cause is not None
    assert "code='user.age.not_number'" in wrapped.cause
    assert wrapped.metadata["source"] == "payload"


def test_ropust_error_wrap_with_exception() -> None:
    def raise_value_error() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom") as excinfo:
        raise_value_error()

    wrapped = RopustError.wrap(
        excinfo.value,
        code="json.decode.failed",
        message="invalid json payload",
    )

    assert wrapped.code == "json.decode.failed"
    assert wrapped.message == "invalid json payload"
    assert wrapped.cause is not None
    assert "code='py_exception'" in wrapped.cause
    assert wrapped.metadata["cause_exception"] == "ValueError"
    assert "cause_py_traceback" in wrapped.metadata


def test_ropust_error_wrap_rejects_none() -> None:
    with pytest.raises(TypeError, match="wrap expects an exception or RopustError"):
        RopustError.wrap(None, code="invalid", message="bad input")  # type: ignore[arg-type]


def test_result_context_wraps_error() -> None:
    err = Err("boom")
    wrapped = err.context("failed to process", metadata={"step": "parse"})
    assert wrapped.is_err()
    wrapped_err = wrapped.unwrap_err()
    assert wrapped_err.code == "context"
    assert wrapped_err.message == "failed to process"
    assert wrapped_err.metadata["step"] == "parse"
    assert wrapped_err.cause is not None
    assert "message='boom'" in wrapped_err.cause


def test_result_context_ok_passthrough() -> None:
    ok = Ok(123)
    out = ok.context("ignored")
    assert out.is_ok()
    assert out.unwrap() == 123


def test_result_with_code() -> None:
    err = Err("boom")
    coded = err.with_code("parse.error")
    assert coded.is_err()
    coded_err = coded.unwrap_err()
    assert coded_err.code == "parse.error"
    assert coded_err.message == "boom"


def test_result_map_err_code_prefixes_once() -> None:
    err = Err("boom")
    prefixed = err.map_err_code("pipeline")
    assert prefixed.unwrap_err().code == "pipeline.custom"

    prefixed_again = prefixed.map_err_code("pipeline")
    assert prefixed_again.unwrap_err().code == "pipeline.custom"

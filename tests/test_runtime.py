from __future__ import annotations

from collections.abc import Generator

import pytest

from pyropust import Err, None_, Ok, Result, RopeError, Some, catch, do, exception_to_rope_error


def test_result_ok_err() -> None:
    ok = Ok(123)
    err = Err("nope")

    assert ok.is_ok() is True
    assert ok.is_err() is False
    assert ok.unwrap() == 123

    assert err.is_ok() is False
    assert err.is_err() is True
    assert err.unwrap_err() == "nope"


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
    def flow(value: str) -> Generator[Result[str, object], str, Result[str, object]]:
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
    assert isinstance(err.unwrap_err(), RopeError)

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
    assert isinstance(result.unwrap_err(), RopeError)


def test_unwrap_or_raise() -> None:
    ok = Ok(123)
    assert ok.unwrap_or_raise(RuntimeError("boom")) == 123

    err = Err("nope")
    with pytest.raises(RuntimeError, match="boom"):
        err.unwrap_or_raise(RuntimeError("boom"))


def test_exception_to_rope_error() -> None:
    def raise_value_error() -> None:
        raise ValueError("boom")

    try:
        raise_value_error()
    except ValueError as exc:
        err = exception_to_rope_error(exc)
        assert isinstance(err, RopeError)
        assert err.code == "py_exception"
        assert "py_traceback" in err.metadata


def test_rope_error_dict_roundtrip() -> None:
    def raise_value_error() -> None:
        raise ValueError("boom")

    err: RopeError | None = None
    try:
        raise_value_error()
    except ValueError as exc:
        err = exception_to_rope_error(exc)

    assert err is not None
    data = err.to_dict()
    parsed = RopeError.from_dict(data)

    assert parsed.kind == err.kind
    assert parsed.code == err.code
    assert parsed.message == err.message
    assert parsed.metadata["exception"] == "ValueError"
    assert "py_traceback" in parsed.metadata


def test_rope_error_from_dict_missing_fields() -> None:
    with pytest.raises(TypeError, match="missing 'kind' field"):
        RopeError.from_dict({"code": "missing", "message": "oops"})

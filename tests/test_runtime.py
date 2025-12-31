from __future__ import annotations

from collections.abc import Generator

import pytest

from pyropust import Err, None_, Ok, Result, RopeError, Some, catch, do


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

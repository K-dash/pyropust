from __future__ import annotations

from collections.abc import Generator

from pyrope import Err, None_, Ok, Result, Some, do


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

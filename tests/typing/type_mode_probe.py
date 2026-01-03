from __future__ import annotations

from pyropust import (
    Error,
    ErrorCode,
    None_,
    Ok,
    Option,
    Result,
    Some,
    bail,
    ensure,
    err,
)


class Code(ErrorCode):
    INVALID = "invalid"
    NEGATIVE = "negative"
    PARSE = "parse"


def parse_ok() -> Result[int]:
    return Ok(1)


def parse_err() -> Result[int]:
    return err(Code.INVALID, "bad")


def chain_ok() -> Result[int]:
    return Ok(1).and_then(lambda x: Ok(x + 1))


def parse_int(s: str) -> Result[int]:
    if not s.isdigit():
        return err(Code.PARSE, "not a number")
    return Ok(int(s))


def validate_positive(x: int) -> Result[int]:
    if x <= 0:
        return err(Code.NEGATIVE, "must be positive")
    return Ok(x)


def chain_map_try() -> Result[int]:
    return Ok("123").map_try(int, code=Code.PARSE, message="invalid").and_then(validate_positive)


def chain_and_then_try() -> Result[int]:
    return Ok("123").and_then_try(parse_int, code=Code.PARSE, message="invalid")


def chain_map_err() -> Result[int]:
    return parse_int("bad").map_err(lambda e: e)


def chain_context() -> Result[int]:
    return parse_int("bad").context("failed parse", code=Code.PARSE)


def chain_with_code() -> Result[int]:
    return parse_int("bad").with_code(Code.INVALID)


def chain_map_err_code() -> Result[int]:
    return parse_int("bad").map_err_code("parse")


def chain_unwrap_defaults() -> int | str:
    return parse_int("bad").unwrap_or("fallback")


def chain_unwrap_or_else() -> int | str:
    return parse_int("bad").unwrap_or_else(lambda e: e.message)


def chain_ok_err_options() -> Option[int]:
    return parse_int("bad").ok()


def chain_err_option() -> Option[Error]:
    return parse_int("bad").err()


def attempt_div_zero() -> Result[int]:
    return Result.attempt(lambda: 1 // 0, ZeroDivisionError)


def build_error_new() -> Error:
    return Error.new(Code.INVALID, "bad input")


def build_error_wrap() -> Error:
    try:
        int("bad")
    except ValueError as exc:
        return Error.wrap(exc, code=Code.PARSE, message="parse failed")
    return Error.new(Code.INVALID, "unexpected")


def ensure_flow() -> Result[int]:
    res = ensure(condition=False, code=Code.INVALID, message="nope")
    return res.map(lambda _: 1)


def bail_flow() -> Result[int]:
    return bail(Code.INVALID, "boom")


def option_map() -> Option[int]:
    return Some(1).map(lambda x: x + 1)


def option_map_try() -> Result[Option[int]]:
    return Some("1").map_try(int, code=Code.PARSE, message="parse")


def option_and_then() -> Option[int]:
    return Some(1).and_then(lambda x: Some(x + 1))


def option_and_then_try() -> Result[Option[int]]:
    return Some("1").and_then_try(lambda x: Some(int(x)), code=Code.PARSE, message="parse")


def option_ok_or() -> Result[int]:
    return None_().ok_or(Code.INVALID, "missing")


def option_ok_or_else() -> Result[int]:
    return None_().ok_or_else(Code.INVALID, lambda: "missing")


def option_map_or() -> int:
    return None_().map_or(0, lambda x: x + 1)


def option_map_or_else() -> int:
    return None_().map_or_else(lambda: 0, lambda x: x + 1)

"""Static type checking tests.

These tests verify that type inference works correctly with both mypy and pyright.
All code runs under TYPE_CHECKING to ensure it's only analyzed by the type checker,
not executed at runtime.

Run with:
    uv run mypy --strict tests/typing/test_types.py
    uv run pyright tests/typing/test_types.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Never, assert_type

from pyropust import (
    Err,
    Error,
    ErrorCode,
    ErrorKind,
    None_,
    Ok,
    Option,
    Result,
    Some,
    bail,
    catch,
    ensure,
    err,
)


class SampleCode(ErrorCode):
    ERROR = "error"


if TYPE_CHECKING:
    # ==========================================================================
    # Result: Constructors
    # ==========================================================================

    # Ok() returns Result[T]
    ok_int: Result[int] = Ok(42)
    assert_type(Ok(42), Result[int])
    assert_type(Ok("hello"), Result[str])

    # Err() returns Result[Never]
    err_str: Result[Never] = err(SampleCode.ERROR, "error")
    assert_type(err(SampleCode.ERROR, "error"), Result[Never])
    assert_type(
        Err(Error.new(code=SampleCode.ERROR, message="oops")),
        Result[Never],
    )
    err_union: Result[Never] = err("oops.code", "oops")
    assert_type(err_union, Result[Never])
    assert_type(bail(SampleCode.ERROR, "boom"), Result[Never])
    assert_type(
        ensure(condition=True, code=SampleCode.ERROR, message="boom"),
        Result[None],
    )

    # ==========================================================================
    # Result: Methods
    # ==========================================================================

    def get_result() -> Result[int]:
        return Ok(10)

    res = get_result()

    # is_ok / is_err return bool
    assert_type(res.is_ok(), bool)
    assert_type(res.is_err(), bool)

    # unwrap returns the Ok value type
    assert_type(res.unwrap(), int)

    # unwrap_err returns the Err value type
    assert_type(res.unwrap_err(), Error)

    # unwrap_or_raise returns ok value type
    assert_type(res.unwrap_or_raise(RuntimeError("boom")), int)

    # attempt returns Result[T]
    attempt_ok = Result.attempt(lambda: 123)
    assert_type(attempt_ok, Result[int])

    # map transforms the Ok value
    mapped = res.map(lambda x: str(x))
    assert_type(mapped, Result[str])

    # map with different output type
    mapped_float = res.map(lambda x: x * 2.5)
    assert_type(mapped_float, Result[float])

    # map_err transforms the Err value, preserves ok type
    mapped_err = res.map_err(lambda e: e)
    assert_type(mapped_err, Result[int])

    # context/with_code/map_err_code return Result[T]
    assert_type(res.context("extra context"), Result[int])
    assert_type(res.with_code(SampleCode.ERROR), Result[int])
    assert_type(res.map_err_code("pipeline"), Result[int])

    # and_then chains Result-returning functions
    def validate(x: int) -> Result[str]:
        return Ok(str(x)) if x > 0 else err(SampleCode.ERROR, "negative")

    chained = res.and_then(validate)
    assert_type(chained, Result[str])

    # ==========================================================================
    # Result: Chaining (README example)
    # ==========================================================================

    # Functional chaining with explicit error type annotation
    def fetch_value() -> Result[str]:
        return Ok("123")

    chain_result = (
        fetch_value().map(int).map(lambda x: x * 2).and_then(lambda x: Ok(f"Value is {x}"))
    )
    assert_type(chain_result, Result[str])

    # ==========================================================================
    # Option: Constructors
    # ==========================================================================

    # Some() returns Option[T]
    some_int: Option[int] = Some(42)
    assert_type(Some(42), Option[int])
    assert_type(Some("hello"), Option[str])

    # None_() returns Option[Never]
    none_val: Option[Never] = None_()
    assert_type(None_(), Option[Never])

    # ==========================================================================
    # Option: Methods
    # ==========================================================================

    def get_option() -> Option[int]:
        return Some(10)

    opt = get_option()

    # is_some / is_none return bool
    assert_type(opt.is_some(), bool)
    assert_type(opt.is_none(), bool)

    # unwrap returns the value type
    assert_type(opt.unwrap(), int)

    # map transforms the value
    mapped_opt = opt.map(lambda x: str(x))
    assert_type(mapped_opt, Option[str])

    # unwrap_or returns union of value type and default type
    with_default = opt.unwrap_or("default")
    assert_type(with_default, int | str)

    # unwrap_or with same type
    same_type_default = opt.unwrap_or(0)
    assert_type(same_type_default, int)

    # ==========================================================================
    # Option: README example
    # ==========================================================================

    def find_user(user_id: int) -> Option[str]:
        return Some("Alice") if user_id == 1 else None_()

    name_opt = find_user(1)
    assert_type(name_opt, Option[str])

    name = name_opt.unwrap_or("Guest")
    assert_type(name, str)

    # ==========================================================================
    # Result: Border control helpers
    # ==========================================================================

    @catch(ValueError)
    def parse_int(value: str) -> int:
        return int(value)

    parsed = parse_int("123")
    assert_type(parsed, Result[int])

    # ==========================================================================
    # Error properties
    # ==========================================================================

    def get_error() -> Error:
        raise NotImplementedError

    rope_err = get_error()

    assert_type(rope_err.kind, ErrorKind)
    assert_type(rope_err.code, str)
    assert_type(rope_err.message, str)
    assert_type(rope_err.metadata, dict[str, str])
    assert_type(rope_err.op, str | None)
    assert_type(rope_err.path, list[str | int])
    assert_type(rope_err.expected, str | None)
    assert_type(rope_err.got, str | None)
    assert_type(rope_err.cause, str | None)

    # ==========================================================================
    # ErrorKind class attributes
    # ==========================================================================

    assert_type(ErrorKind.InvalidInput, ErrorKind)
    assert_type(ErrorKind.NotFound, ErrorKind)
    assert_type(ErrorKind.Internal, ErrorKind)

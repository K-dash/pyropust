"""Static type checking tests.

These tests verify that type inference works correctly with both mypy and pyright.
All code runs under TYPE_CHECKING to ensure it's only analyzed by the type checker,
not executed at runtime.

Run with:
    uv run mypy --strict tests/typing/test_types.py
    uv run pyright tests/typing/test_types.py
"""

from __future__ import annotations

from collections.abc import Generator, Mapping, Sequence
from typing import TYPE_CHECKING, Never, assert_type

from pyropust import (
    Blueprint,
    Err,
    ErrorKind,
    None_,
    Ok,
    Op,
    Operator,
    Option,
    Result,
    RopustError,
    Some,
    catch,
    do,
    run,
)

if TYPE_CHECKING:
    # ==========================================================================
    # Result: Constructors
    # ==========================================================================

    # Ok() returns Result[T]
    ok_int: Result[int] = Ok(42)
    assert_type(Ok(42), Result[int])
    assert_type(Ok("hello"), Result[str])

    # Err() returns Result[Never]
    err_str: Result[Never] = Err("error")
    assert_type(Err("error"), Result[Never])
    assert_type(Err(ValueError("oops")), Result[Never])

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
    assert_type(res.unwrap_err(), RopustError)

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
    assert_type(res.with_code("parse.error"), Result[int])
    assert_type(res.map_err_code("pipeline"), Result[int])

    # and_then chains Result-returning functions
    def validate(x: int) -> Result[str]:
        return Ok(str(x)) if x > 0 else Err("negative")

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
    # Operator: Flat API (backward compatible)
    # ==========================================================================

    # Text operators
    assert_type(Op.split("@"), Operator[str, list[str]])
    assert_type(Op.to_uppercase(), Operator[str, str])
    assert_type(Op.trim(), Operator[str, str])
    assert_type(Op.lower(), Operator[str, str])
    assert_type(Op.replace("a", "b"), Operator[str, str])

    # Core operators (len is universal: str/bytes/list/map)
    assert_type(Op.len(), Operator[object, int])
    assert_type(Op.is_null(), Operator[object, bool])
    assert_type(Op.is_empty(), Operator[object, bool])

    # Sequence operators
    assert_type(Op.index(0), Operator[Sequence[object], object])
    assert_type(Op.slice(0, 1), Operator[Sequence[object], list[object]])
    assert_type(Op.first(), Operator[Sequence[object], object])
    assert_type(Op.last(), Operator[Sequence[object], object])

    # Mapping operators
    assert_type(Op.get("key"), Operator[Mapping[str, object], object])
    assert_type(Op.get_or("key", 0), Operator[Mapping[str, int], int])
    assert_type(Op.keys(), Operator[Mapping[str, object], list[str]])
    assert_type(Op.values(), Operator[Mapping[str, object], list[object]])

    # Coercion operators
    assert_type(Op.assert_str(), Operator[object, str])
    assert_type(Op.expect_str(), Operator[object, str])
    assert_type(Op.as_str(), Operator[object, str])
    assert_type(Op.json_decode(), Operator[str | bytes, Mapping[str, object]])

    def to_len(value: str) -> int:
        return len(value)

    assert_type(Op.map_py(to_len), Operator[str, int])

    # ==========================================================================
    # Operator: Namespace API
    # ==========================================================================

    # Op.text namespace
    assert_type(Op.text.split("@"), Operator[str, list[str]])
    assert_type(Op.text.to_uppercase(), Operator[str, str])
    assert_type(Op.text.trim(), Operator[str, str])
    assert_type(Op.text.lower(), Operator[str, str])
    assert_type(Op.text.replace("a", "b"), Operator[str, str])

    # Op.seq namespace
    assert_type(Op.seq.index(0), Operator[Sequence[object], object])
    assert_type(Op.seq.slice(0, 1), Operator[Sequence[object], list[object]])
    assert_type(Op.seq.first(), Operator[Sequence[object], object])
    assert_type(Op.seq.last(), Operator[Sequence[object], object])

    # Op.map namespace
    assert_type(Op.map.get("key"), Operator[Mapping[str, object], object])
    assert_type(Op.map.get_or("key", 0), Operator[Mapping[str, int], int])
    assert_type(Op.map.keys(), Operator[Mapping[str, object], list[str]])
    assert_type(Op.map.values(), Operator[Mapping[str, object], list[object]])

    # Op.coerce namespace
    assert_type(Op.coerce.assert_str(), Operator[object, str])
    assert_type(Op.coerce.expect_str(), Operator[object, str])
    assert_type(Op.coerce.as_str(), Operator[object, str])
    assert_type(Op.coerce.json_decode(), Operator[str | bytes, Mapping[str, object]])

    # Op.core namespace
    assert_type(Op.core.is_null(), Operator[object, bool])
    assert_type(Op.core.is_empty(), Operator[object, bool])

    # Op.core namespace
    assert_type(Op.core.map_py(to_len), Operator[str, int])

    # ==========================================================================
    # Blueprint: Construction and Chaining
    # ==========================================================================

    # Blueprint() returns Blueprint[object, object]
    assert_type(Blueprint(), Blueprint[object, object])

    # Blueprint.any() returns Blueprint[object, object]
    assert_type(Blueprint.any(), Blueprint[object, object])

    # Blueprint.for_type() narrows input type
    assert_type(Blueprint.for_type(str), Blueprint[str, str])
    assert_type(Blueprint.for_type(int), Blueprint[int, int])

    # pipe() transforms output type
    bp_split = Blueprint.for_type(str).pipe(Op.split("@"))
    assert_type(bp_split, Blueprint[str, list[str]])

    # Chained pipes
    bp_chain = Blueprint.for_type(str).pipe(Op.split("@")).pipe(Op.index(0))
    assert_type(bp_chain, Blueprint[str, object])

    # guard_str() narrows object -> str
    bp_guarded = Blueprint.any().guard_str()
    assert_type(bp_guarded, Blueprint[object, str])

    # Full chain with guard_str
    bp_full = (
        Blueprint.for_type(str)
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .guard_str()
        .pipe(Op.to_uppercase())
    )
    assert_type(bp_full, Blueprint[str, str])

    # Invalid operator insertion should be rejected by type checkers.
    # These are documented with type ignores to keep strict checking green.
    _bp_invalid_str = Blueprint.for_type(int).pipe(Op.to_uppercase())  # type: ignore[arg-type]
    _bp_invalid_map = Blueprint.for_type(str).pipe(Op.get("key"))  # type: ignore[arg-type]

    # ==========================================================================
    # Blueprint: Namespace API equivalence
    # ==========================================================================

    # Namespace API should produce same types as flat API
    bp_ns = Blueprint.for_type(str).pipe(Op.text.split("@")).pipe(Op.seq.index(0))
    assert_type(bp_ns, Blueprint[str, object])

    bp_coerce = Blueprint().pipe(Op.coerce.expect_str()).pipe(Op.text.to_uppercase())
    assert_type(bp_coerce, Blueprint[object, str])

    # ==========================================================================
    # run() function
    # ==========================================================================

    bp_for_run = Blueprint.for_type(str).pipe(Op.split("@"))
    result_from_run = run(bp_for_run, "a@b")
    assert_type(result_from_run, Result[list[str]])

    # ==========================================================================
    # RopustError properties
    # ==========================================================================

    def get_ropust_error() -> RopustError:
        raise NotImplementedError

    rope_err = get_ropust_error()

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

    # ==========================================================================
    # @do decorator
    # ==========================================================================

    @do
    def to_upper(value: str) -> Generator[Result[str], str, Result[str]]:
        text = yield Ok(value)
        return Ok(text.upper())

    # @do decorated function returns Result
    do_result: Result[str] = to_upper("hello")
    assert_type(to_upper("hello"), Result[str])

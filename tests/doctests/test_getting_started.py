from __future__ import annotations

from pyropust import ErrorCode, Ok, Result, err


class Code(ErrorCode):
    INVALID = "invalid"
    TOO_SMALL = "too_small"
    TOO_LARGE = "too_large"
    PARSE_ERROR = "parse_error"
    VALIDATION_ERROR = "validation_error"


def ok_code[T](value: T) -> Result[T]:
    return Ok(value)


def test_basic_result_creation() -> None:
    """Test basic Ok and Err creation."""
    success: Result[int] = Ok(42)
    assert success.is_ok()
    assert success.unwrap() == 42

    failure: Result[None] = err(Code.INVALID, "something went wrong")
    assert failure.is_err()
    assert failure.unwrap_err().code == Code.INVALID


def test_unwrap_with_default() -> None:
    """Test unwrap_or for safe extraction."""
    success: Result[int] = Ok(42)
    assert success.unwrap_or(0) == 42

    failure: Result[None] = err(Code.INVALID, "error")
    assert failure.unwrap_or(0) == 0


def test_map_transformation() -> None:
    """Test pure map transformation."""
    ok_result: Result[int] = Ok(5).map(lambda x: x * 2)
    assert ok_result.unwrap() == 10

    # Map on Err is no-op
    err_result: Result[int] = err(Code.INVALID, "error").map(lambda x: x * 2)
    assert err_result.is_err()


def test_chaining_operations() -> None:
    """Test chaining from getting-started.md."""

    def validate_age(age: int) -> Result[int]:
        if age < 0:
            return err(Code.TOO_SMALL, "age must be positive")
        if age > 150:
            return err(Code.TOO_LARGE, "age unrealistically large")
        return ok_code(age)

    # Success case
    raw_ok: Result[str] = ok_code("25")
    result: Result[int] = raw_ok.map_try(
        int, code=Code.INVALID, message="invalid integer"
    ).and_then(validate_age)
    assert result.unwrap() == 25

    # Error in parsing
    raw_invalid: Result[str] = ok_code("not a number")
    result = raw_invalid.map_try(int, code=Code.INVALID, message="invalid integer").and_then(
        validate_age
    )
    assert result.is_err()
    assert result.unwrap_err().code == Code.INVALID

    # Error in validation
    raw_too_large: Result[str] = ok_code("200")
    result = raw_too_large.map_try(int, code=Code.INVALID, message="invalid integer").and_then(
        validate_age
    )
    assert result.is_err()
    assert result.unwrap_err().code == Code.TOO_LARGE


def test_common_pitfall_map_vs_map_try() -> None:
    """Test the #1 pitfall: using map() with exception-throwing functions.

    This is documented in getting-started.md Common Pitfalls section.
    """
    # RIGHT — Use map_try
    raw_invalid: Result[str] = ok_code("abc")
    result: Result[int] = raw_invalid.map_try(int, code=Code.INVALID, message="invalid int")
    assert result.is_err()

    # Success case
    raw_ok: Result[str] = ok_code("123")
    result = raw_ok.map_try(int, code=Code.INVALID, message="invalid int")
    assert result.unwrap() == 123

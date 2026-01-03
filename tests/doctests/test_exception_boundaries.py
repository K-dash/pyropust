from __future__ import annotations

from typing import TypedDict

import pytest

from pyropust import ErrorCode, Ok, Result, catch, err


class Code(ErrorCode):
    PARSE_ERROR = "parse_error"
    VALIDATION_ERROR = "validation_error"
    INVALID = "invalid"
    IO_ERROR = "io_error"
    DIVISION_ERROR = "division_error"


class RawConfig(TypedDict, total=False):
    port: str
    host: str


class ParsedConfig(TypedDict):
    port: int
    host: str


class AppConfig(TypedDict):
    key: str


def test_catch_decorator_basic() -> None:
    """Test @catch decorator wraps exceptions."""

    @catch(ValueError, KeyError)
    def parse_data(raw: RawConfig) -> ParsedConfig:
        if "port" not in raw or "host" not in raw:
            raise KeyError("missing config")
        return {
            "port": int(raw["port"]),  # ValueError or KeyError
            "host": raw["host"],
        }

    # Success case
    result = parse_data({"port": "8080", "host": "localhost"})
    assert result.is_ok()
    assert result.unwrap() == {"port": 8080, "host": "localhost"}

    # ValueError case
    result = parse_data({"port": "abc", "host": "localhost"})
    assert result.is_err()

    # KeyError case
    result = parse_data({"host": "localhost"})
    assert result.is_err()


def test_catch_all_exceptions() -> None:
    """Test @catch without arguments catches all exceptions."""

    @catch()
    def risky_operation() -> int:
        return 10 // 0  # ZeroDivisionError

    result = risky_operation()
    assert result.is_err()


def test_map_try_single_transformation() -> None:
    """Test map_try for single transformations in chains."""
    # Success
    result = Ok("123").map_try(int, code=Code.PARSE_ERROR, message="invalid int")
    assert result.unwrap() == 123

    # Failure
    result = Ok("abc").map_try(int, code=Code.PARSE_ERROR, message="invalid int")
    assert result.is_err()
    assert result.unwrap_err().code == Code.PARSE_ERROR


def test_and_then_try() -> None:
    """Test and_then_try for chaining Result-returning functions."""

    def parse_and_validate(s: str) -> Result[int]:
        # This might raise ValueError
        value = int(s)
        if value < 0:
            return err(Code.VALIDATION_ERROR, "must be positive")
        return Ok(value)

    # Success
    result: Result[int] = Ok("42").and_then_try(
        parse_and_validate, code=Code.PARSE_ERROR, message="parse failed"
    )
    assert result.unwrap() == 42

    # ValueError caught
    result = Ok("abc").and_then_try(
        parse_and_validate, code=Code.PARSE_ERROR, message="parse failed"
    )
    assert result.is_err()
    assert result.unwrap_err().code == Code.PARSE_ERROR

    # Validation error (not exception)
    result = Ok("-5").and_then_try(
        parse_and_validate, code=Code.PARSE_ERROR, message="parse failed"
    )
    assert result.is_err()
    assert result.unwrap_err().code == Code.VALIDATION_ERROR


def test_result_attempt_basic() -> None:
    """Test Result.attempt for ad-hoc boundaries."""
    # Catch specific exception
    result: Result[float] = Result.attempt(lambda: 10 / 0, ZeroDivisionError)
    assert result.is_err()

    # Success case
    result = Result.attempt(lambda: 10 / 2, ZeroDivisionError)
    assert result.unwrap() == 5.0


def test_result_attempt_multiple_exceptions() -> None:
    """Test Result.attempt with multiple exception types."""

    def parse_payload(raw: str) -> dict[str, str]:
        if raw == '{"key": "value"}':
            return {"key": "value"}
        raise ValueError("invalid payload")

    result: Result[dict[str, str]] = Result.attempt(
        lambda: parse_payload('{"key": "value"}'),
        ValueError,
        TypeError,
    )
    assert result.is_ok()
    assert result.unwrap() == {"key": "value"}

    # Invalid JSON
    result = Result.attempt(lambda: parse_payload("invalid json"), ValueError, TypeError)
    assert result.is_err()


def test_result_attempt_with_context() -> None:
    """Test adding domain-specific error code to Result.attempt."""
    result: Result[float] = Result.attempt(lambda: 10 / 0, ZeroDivisionError).context(
        "Division failed", code=Code.DIVISION_ERROR
    )

    assert result.is_err()
    assert result.unwrap_err().code == Code.DIVISION_ERROR


def test_result_attempt_file_operations() -> None:
    """Test Result.attempt for file I/O (simulated with json)."""

    def parse_config(data: str) -> AppConfig:
        if data != '{"key": "value"}':
            raise ValueError("invalid config")
        return {"key": "value"}

    def load_config(data: str) -> Result[AppConfig]:
        # Read and parse in one block
        content_result: Result[AppConfig] = Result.attempt(
            lambda: parse_config(data), ValueError
        ).context("Cannot parse config", code=Code.IO_ERROR)

        return content_result

    # Valid JSON
    result = load_config('{"key": "value"}')
    assert result.is_ok()

    # Invalid JSON
    result = load_config("invalid")
    assert result.is_err()
    assert result.unwrap_err().code == Code.IO_ERROR


def test_result_attempt_fallback_chain() -> None:
    """Test fallback chain with Result.attempt from concepts/exceptions.md."""

    def get_from_source1() -> Result[int]:
        return Result.attempt(lambda: int("invalid"), ValueError)

    def get_from_source2() -> Result[int]:
        return Ok(42)

    # Try source1, fallback to source2
    result: Result[int] = get_from_source1().or_(get_from_source2())
    assert result.is_ok()
    assert result.unwrap() == 42


def test_map_does_not_catch_exceptions() -> None:
    """Verify that map() does NOT catch exceptions.

    This is the #1 design principle from mental-model.md.
    """
    # This should raise ValueError, not return Err
    try:
        Ok("abc").map(int)
        pytest.fail("Should have raised ValueError")
    except ValueError:
        pass  # Expected

    # The correct way is to use map_try
    result: Result[int] = Ok("abc").map_try(int, code=Code.PARSE_ERROR, message="invalid")
    assert result.is_err()


def test_and_then_does_not_catch_exceptions() -> None:
    """Verify that and_then() does NOT catch exceptions.

    Use and_then_try when the function can raise.
    """

    def might_raise(x: int) -> Result[int]:
        if x < 0:
            raise ValueError("negative")
        return Ok(x * 2)

    # and_then does NOT catch exceptions
    try:
        result_temp: Result[int] = Ok(-5)
        result_temp.and_then(might_raise)
        pytest.fail("Should have raised ValueError")
    except ValueError:
        pass  # Expected

    # Use and_then_try instead
    result_test: Result[int] = Ok(-5)
    result: Result[int] = result_test.and_then_try(
        might_raise, code=Code.INVALID, message="operation failed"
    )
    assert result.is_err()
    assert result.unwrap_err().code == Code.INVALID

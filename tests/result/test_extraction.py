"""Tests for Result extraction methods (expect, expect_err, unwrap_or, unwrap_or_else).

Note: Type annotations are required when using Ok()/Err() constructors
because they have inferred types Result[T] and Result[Never].
This matches Rust's type system design. Use function return types or
intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

import pytest

from pyropust import Err, Ok, Result


class TestResultExpect:
    """Test Result.expect() for extracting Ok value with custom error message."""

    def test_expect_returns_ok_value(self) -> None:
        res = Ok(42)
        assert res.expect("should not fail") == 42

    def test_expect_raises_with_custom_message_on_err(self) -> None:
        res: Result[int] = Err("error")
        with pytest.raises(RuntimeError, match="custom error message"):
            res.expect("custom error message")

    def test_expect_works_with_complex_types(self) -> None:
        res = Ok({"key": "value"})
        assert res.expect("should work") == {"key": "value"}

    def test_expect_message_can_be_multiline(self) -> None:
        res: Result[int] = Err("error")
        with pytest.raises(RuntimeError, match=r"Line 1\nLine 2\nLine 3"):
            res.expect("Line 1\nLine 2\nLine 3")


class TestResultExpectErr:
    """Test Result.expect_err() for extracting Err value with custom error message."""

    def test_expect_err_returns_err_value(self) -> None:
        res: Result[int] = Err("error message")
        assert res.expect_err("should not fail").message == "error message"

    def test_expect_err_raises_with_custom_message_on_ok(self) -> None:
        res = Ok(42)
        with pytest.raises(RuntimeError, match="expected an error"):
            res.expect_err("expected an error")

    def test_expect_err_works_with_exception_objects(self) -> None:
        error = ValueError("validation failed")
        res: Result[int] = Err(error)
        assert res.expect_err("should work").message.endswith("validation failed")


class TestResultUnwrapOr:
    """Test Result.unwrap_or() for providing default values."""

    def test_unwrap_or_returns_ok_value(self) -> None:
        res = Ok(10)
        assert res.unwrap_or(999) == 10

    def test_unwrap_or_returns_default_on_err(self) -> None:
        res: Result[int] = Err("error")
        assert res.unwrap_or(999) == 999

    def test_unwrap_or_works_with_different_types(self) -> None:
        # Ok case with string
        res = Ok("hello")
        assert res.unwrap_or("default") == "hello"

        # Err case with string
        res_err: Result[str] = Err("error")
        assert res_err.unwrap_or("default") == "default"

    def test_unwrap_or_default_can_be_none(self) -> None:
        res: Result[str] = Err("error")
        assert res.unwrap_or(None) is None

    def test_unwrap_or_with_complex_default(self) -> None:
        res: Result[list[int]] = Err("error")
        default = [1, 2, 3]
        assert res.unwrap_or(default) == [1, 2, 3]


class TestResultUnwrapOrElse:
    """Test Result.unwrap_or_else() for computing default values from error."""

    def test_unwrap_or_else_returns_ok_value(self) -> None:
        res = Ok(10)
        assert res.unwrap_or_else(lambda _e: 999) == 10

    def test_unwrap_or_else_computes_default_on_err(self) -> None:
        res: Result[int] = Err("error")
        assert res.unwrap_or_else(lambda e: len(e.message)) == 5

    def test_unwrap_or_else_receives_err_value(self) -> None:
        res: Result[int] = Err("custom error")
        # Function receives the actual error value
        result = res.unwrap_or_else(lambda e: len(e.message) * 2)
        assert result == 24  # len("custom error") * 2

    def test_unwrap_or_else_not_called_on_ok(self) -> None:
        """Verify function is not called when Result is Ok."""
        called = False

        def compute_default(_e: object) -> int:
            nonlocal called
            called = True
            return 999

        res = Ok(10)
        assert res.unwrap_or_else(compute_default) == 10
        assert called is False

    def test_unwrap_or_else_with_type_conversion(self) -> None:
        # Error to default value type conversion
        res: Result[str] = Err("404")
        assert res.unwrap_or_else(lambda code: f"Error {code.message}") == "Error 404"

"""Tests for Result conversion methods (ok, err).

Note: Type annotations are required when using Ok()/err() constructors
because they have inferred types Result[T] and Result[Never].
This matches Rust's type system design. Use function return types or
intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

from pyropust import Err, Ok, Result
from tests.support import SampleCode, err_msg, wrap_error


class TestResultOk:
    """Test Result.ok() for converting Result to Option."""

    def test_ok_returns_some_on_ok(self) -> None:
        res: Result[int] = Ok(42)
        opt = res.ok()
        assert opt.is_some()
        assert opt.unwrap() == 42

    def test_ok_returns_none_on_err(self) -> None:
        res: Result[int] = err_msg("error")
        opt = res.ok()
        assert opt.is_none()

    def test_ok_preserves_value_type(self) -> None:
        res: Result[dict[str, str]] = Ok({"key": "value"})
        opt = res.ok()
        assert opt.unwrap() == {"key": "value"}

    def test_ok_discards_error(self) -> None:
        """Verify that error information is lost after ok()."""
        res: Result[int] = err_msg("important error")
        opt = res.ok()
        # Error is discarded, we only know it's None
        assert opt.is_none()

    def test_ok_enables_option_chaining(self) -> None:
        """Use case: convert Result to Option for further processing."""
        res: Result[int] = Ok(10)
        # Chain with Option methods
        result = res.ok().map(lambda x: x * 2).unwrap_or(0)
        assert result == 20

        res_err: Result[int] = err_msg("error")
        result_err = res_err.ok().map(lambda x: x * 2).unwrap_or(0)
        assert result_err == 0


class TestResultErr:
    """Test Result.err() for extracting error as Option."""

    def test_err_returns_some_on_err(self) -> None:
        res: Result[int] = err_msg("error message")
        opt = res.err()
        assert opt.is_some()
        assert opt.unwrap().message == "error message"

    def test_err_returns_none_on_ok(self) -> None:
        res: Result[int] = Ok(42)
        opt = res.err()
        assert opt.is_none()

    def test_err_preserves_error_type(self) -> None:
        error = ValueError("validation failed")
        res: Result[int] = Err(
            wrap_error(
                error,
                code=SampleCode.VALIDATION,
                message="validation failed",
            )
        )
        opt = res.err()
        assert opt.unwrap().message == "validation failed"

    def test_err_discards_success_value(self) -> None:
        """Verify that success value is lost after err()."""
        res: Result[int] = Ok(42)
        opt = res.err()
        # Success value is discarded
        assert opt.is_none()

    def test_err_for_error_collection(self) -> None:
        """Use case: collect errors from multiple Results."""
        results = [Ok(1), err_msg("error1"), Ok(3), err_msg("error2")]
        errors = [r.err().unwrap().message for r in results if r.is_err()]
        assert errors == ["error1", "error2"]

    def test_err_with_option_methods(self) -> None:
        """Chain with Option methods for error processing."""
        res: Result[int] = err_msg("bad input")
        # Transform error using Option.map
        formatted = res.err().map(lambda e: f"Error: {e.message}").unwrap_or("No error")
        assert formatted == "Error: bad input"

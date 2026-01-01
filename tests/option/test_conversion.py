"""Tests for Option conversion methods (ok_or, ok_or_else).

Note: Type annotations are required when using Some()/None_() constructors
because they have inferred types. This matches Rust's type system design.
Use function return types or intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

from pyropust import None_, Option, Some


class TestOptionOkOr:
    """Test Option.ok_or() for converting Option to Result with a default error."""

    def test_ok_or_returns_ok_on_some(self) -> None:
        """ok_or converts Some to Ok."""
        opt = Some(42)
        result = opt.ok_or("error")
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_ok_or_returns_err_on_none(self) -> None:
        """ok_or converts None to Err with provided error."""

        def none_val() -> Option[int]:
            return None_()

        opt = none_val()
        result = opt.ok_or("error")
        assert result.is_err()
        assert result.unwrap_err().message == "error"

    def test_ok_or_preserves_value_type(self) -> None:
        """Verify ok_or preserves value type."""
        opt = Some({"key": "value"})
        result = opt.ok_or("error")
        assert result.unwrap() == {"key": "value"}

    def test_ok_or_with_complex_error(self) -> None:
        """ok_or works with complex error types."""

        def none_val() -> Option[int]:
            return None_()

        opt = none_val()
        error = ValueError("validation failed")
        result = opt.ok_or(error)
        assert result.is_err()
        assert result.unwrap_err().message.endswith("validation failed")

    def test_ok_or_enables_result_chaining(self) -> None:
        """Use case: convert Option to Result for error handling."""
        opt = Some(10)
        # Chain with Result methods
        value = opt.ok_or("missing").map(lambda x: x * 2).unwrap()
        assert value == 20

        def none_val() -> Option[int]:
            return None_()

        opt_none = none_val()
        error = opt_none.ok_or("missing").unwrap_err()
        assert error.message == "missing"


class TestOptionOkOrElse:
    """Test Option.ok_or_else() for converting Option to Result with computed error."""

    def test_ok_or_else_returns_ok_on_some(self) -> None:
        """ok_or_else converts Some to Ok."""
        opt = Some(42)
        result = opt.ok_or_else(lambda: "error")
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_ok_or_else_computes_error_on_none(self) -> None:
        """ok_or_else calls function to compute error on None."""

        def none_val() -> Option[int]:
            return None_()

        opt = none_val()
        result = opt.ok_or_else(lambda: "computed error")
        assert result.is_err()
        assert result.unwrap_err().message == "computed error"

    def test_ok_or_else_function_not_called_on_some(self) -> None:
        """Verify error function is not called when Some."""
        called: list[bool] = []
        opt = Some(42)

        def make_error() -> str:
            called.append(True)
            return "error"

        result = opt.ok_or_else(make_error)
        assert result.is_ok()
        assert called == []

    def test_ok_or_else_with_complex_error_computation(self) -> None:
        """ok_or_else can compute complex errors."""

        def none_val() -> Option[str]:
            return None_()

        opt = none_val()
        result = opt.ok_or_else(lambda: ValueError("dynamically created error"))
        assert result.is_err()
        error = result.unwrap_err()
        assert error.message.endswith("dynamically created error")

    def test_ok_or_else_enables_lazy_error_creation(self) -> None:
        """Use case: avoid creating error unless needed."""
        opt = Some(10)
        # Error is never created for Some
        value = opt.ok_or_else(lambda: expensive_error()).unwrap()
        assert value == 10

        def none_val() -> Option[int]:
            return None_()

        opt_none = none_val()
        # Error is only created when needed
        error = opt_none.ok_or_else(lambda: "lazy error").unwrap_err()
        assert error.message == "lazy error"


def expensive_error() -> str:
    """Simulate an expensive error creation."""
    return "expensive error"

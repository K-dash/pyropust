"""Tests for Result transformation methods.

Includes: map, map_err, map_or, map_or_else, inspect, inspect_err.

Note: Type annotations are required when using Ok()/Err() constructors
because they have inferred types Result[T, Never] and Result[Never, E].
This matches Rust's type system design. Use function return types or
intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

from pyropust import Err, Ok, Result


class TestResultMap:
    """Test Result.map() for transforming Ok values."""

    def test_map_transforms_ok_value(self) -> None:
        res = Ok(10).map(lambda x: x * 2)
        assert res.is_ok()
        assert res.unwrap() == 20

    def test_map_chains_multiple_transforms(self) -> None:
        res = Ok("123").map(int).map(lambda x: x * 2)
        assert res.is_ok()
        assert res.unwrap() == 246

    def test_map_skips_on_err(self) -> None:
        res: Result[int, str] = Err("error").map(lambda x: x * 2)
        assert res.is_err()
        assert res.unwrap_err() == "error"


class TestResultMapErr:
    """Test Result.map_err() for transforming Err values."""

    def test_map_err_transforms_err_value(self) -> None:
        res: Result[int, str] = Err("error").map_err(lambda e: e.upper())
        assert res.is_err()
        assert res.unwrap_err() == "ERROR"

    def test_map_err_skips_on_ok(self) -> None:
        res = Ok(10).map_err(lambda e: f"Transformed: {e}")
        assert res.is_ok()
        assert res.unwrap() == 10


class TestResultMapOr:
    """Test Result.map_or() for transforming with default."""

    def test_map_or_applies_function_on_ok(self) -> None:
        res = Ok(10)
        result = res.map_or(0, lambda x: x * 2)
        assert result == 20

    def test_map_or_returns_default_on_err(self) -> None:
        res: Result[int, str] = Err("error")
        result = res.map_or(0, lambda x: x * 2)
        assert result == 0

    def test_map_or_with_type_conversion(self) -> None:
        # Transform int to str on Ok
        res = Ok(42)
        result = res.map_or("default", lambda x: f"Value: {x}")
        assert result == "Value: 42"

        # Use default on Err
        res_err: Result[int, str] = Err("error")
        result_err = res_err.map_or("default", lambda x: f"Value: {x}")
        assert result_err == "default"

    def test_map_or_function_not_called_on_err(self) -> None:
        """Verify function is not called when Result is Err."""
        called = False

        def transform(_x: int) -> int:
            nonlocal called
            called = True
            return 999

        res: Result[int, str] = Err("error")
        result = res.map_or(0, transform)
        assert result == 0
        assert called is False


class TestResultMapOrElse:
    """Test Result.map_or_else() for transforming with computed default."""

    def test_map_or_else_applies_function_on_ok(self) -> None:
        res = Ok(10)
        result = res.map_or_else(lambda _e: 0, lambda x: x * 2)
        assert result == 20

    def test_map_or_else_computes_default_on_err(self) -> None:
        res: Result[int, str] = Err("error")
        result = res.map_or_else(lambda e: len(e), lambda x: x * 2)
        assert result == 5

    def test_map_or_else_receives_error_value(self) -> None:
        """Verify default function receives the actual error."""
        res: Result[int, int] = Err(404)
        result = res.map_or_else(lambda code: code * 10, lambda x: x * 2)
        assert result == 4040

    def test_map_or_else_functions_not_both_called(self) -> None:
        """Verify only one function is called."""
        transform_called = False
        default_called = False

        def transform(_x: int) -> int:
            nonlocal transform_called
            transform_called = True
            return 999

        def compute_default(_e: str) -> int:
            nonlocal default_called
            default_called = True
            return 0

        # Ok case
        res = Ok(10)
        res.map_or_else(compute_default, transform)
        assert transform_called is True
        assert default_called is False

        # Err case
        transform_called = False
        res_err: Result[int, str] = Err("error")
        res_err.map_or_else(compute_default, transform)
        assert transform_called is False
        assert default_called is True


class TestResultInspect:
    """Test Result.inspect() for side effects."""

    def test_inspect_calls_function_on_ok(self) -> None:
        called_with = None

        def side_effect(x: int) -> None:
            nonlocal called_with
            called_with = x

        res = Ok(42)
        result = res.inspect(side_effect)
        assert called_with == 42
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_inspect_not_called_on_err(self) -> None:
        called = False

        def side_effect(_x: int) -> None:
            nonlocal called
            called = True

        res: Result[int, str] = Err("error")
        result = res.inspect(side_effect)
        assert called is False
        assert result.is_err()
        assert result.unwrap_err() == "error"

    def test_inspect_enables_chaining(self) -> None:
        """Verify inspect returns Result for method chaining."""
        log: list[int] = []

        res = (
            Ok(10)
            .inspect(lambda x: log.append(x))
            .map(lambda x: x * 2)
            .inspect(lambda x: log.append(x))
        )

        assert log == [10, 20]
        assert res.unwrap() == 20

    def test_inspect_preserves_error(self) -> None:
        """Verify inspect doesn't affect Err."""
        res: Result[int, str] = Err("error")
        result = res.inspect(lambda _x: None).map(lambda x: x * 2)
        assert result.is_err()
        assert result.unwrap_err() == "error"

    def test_inspect_with_print_debugging(self) -> None:
        """Use case: debugging with side effects."""
        values_seen: list[int] = []

        result = (
            Ok(5)
            .inspect(lambda x: values_seen.append(x))
            .map(lambda x: x * 2)
            .inspect(lambda x: values_seen.append(x))
            .map(lambda x: x + 1)
            .inspect(lambda x: values_seen.append(x))
        )

        assert values_seen == [5, 10, 11]
        assert result.unwrap() == 11


class TestResultInspectErr:
    """Test Result.inspect_err() for side effects on errors."""

    def test_inspect_err_calls_function_on_err(self) -> None:
        called_with = None

        def side_effect(e: str) -> None:
            nonlocal called_with
            called_with = e

        res: Result[int, str] = Err("error")
        result = res.inspect_err(side_effect)
        assert called_with == "error"
        assert result.is_err()
        assert result.unwrap_err() == "error"

    def test_inspect_err_not_called_on_ok(self) -> None:
        called = False

        def side_effect(_e: str) -> None:
            nonlocal called
            called = True

        res = Ok(42)
        result = res.inspect_err(side_effect)
        assert called is False
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_inspect_err_enables_chaining(self) -> None:
        """Verify inspect_err returns Result for method chaining."""
        log: list[str] = []

        res: Result[int, str] = (
            Err("error1")
            .inspect_err(lambda e: log.append(e))
            .map_err(lambda e: f"{e}_mapped")
            .inspect_err(lambda e: log.append(e))
        )

        assert log == ["error1", "error1_mapped"]
        assert res.unwrap_err() == "error1_mapped"

    def test_inspect_err_preserves_ok(self) -> None:
        """Verify inspect_err doesn't affect Ok."""
        res = Ok(10)
        result = res.inspect_err(lambda _e: None).map(lambda x: x * 2)
        assert result.is_ok()
        assert result.unwrap() == 20

    def test_inspect_err_for_error_logging(self) -> None:
        """Use case: logging errors without changing the result."""
        errors_logged: list[str] = []

        result = (
            Err("validation failed")
            .inspect_err(lambda e: errors_logged.append(f"Error: {e}"))
            .map_err(lambda e: e.upper())
            .inspect_err(lambda e: errors_logged.append(f"Transformed: {e}"))
        )

        assert errors_logged == ["Error: validation failed", "Transformed: VALIDATION FAILED"]
        assert result.unwrap_err() == "VALIDATION FAILED"

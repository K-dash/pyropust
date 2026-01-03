"""Tests for Result transformation methods.

Includes: map, map_err, map_or, map_or_else, inspect, inspect_err.

Note: Type annotations are required when using Ok()/err() constructors
because they have inferred types Result[T] and Result[Never].
This matches Rust's type system design. Use function return types or
intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

from pyropust import Error, Ok, Result
from tests.support import SampleCode, err_msg, new_error


class TestResultMap:
    """Test Result.map() for transforming Ok values."""

    def test_map_transforms_ok_value(self) -> None:
        res: Result[int] = Ok(10).map(lambda x: x * 2)
        assert res.is_ok()
        assert res.unwrap() == 20

    def test_map_chains_multiple_transforms(self) -> None:
        res: Result[int] = Ok("123").map(int).map(lambda x: x * 2)
        assert res.is_ok()
        assert res.unwrap() == 246

    def test_map_skips_on_err(self) -> None:
        res: Result[int] = err_msg("error").map(lambda x: x * 2)
        assert res.is_err()
        assert res.unwrap_err().message == "error"


class TestResultMapTry:
    """Test Result.map_try() for transforming Ok values with exception capture."""

    def test_map_try_transforms_ok_value(self) -> None:
        res: Result[int] = Ok("123").map_try(
            int,
            code=SampleCode.ERROR,
            message="invalid int",
        )
        assert res.is_ok()
        assert res.unwrap() == 123

    def test_map_try_wraps_exception(self) -> None:
        res: Result[int] = Ok("nope").map_try(
            int,
            code=SampleCode.BAD_INPUT,
            message="invalid int",
        )
        assert res.is_err()
        err = res.unwrap_err()
        assert err.code == SampleCode.BAD_INPUT
        assert err.message == "invalid int"
        assert err.cause is not None
        assert "py_exception" in err.cause

    def test_map_try_skips_on_err(self) -> None:
        res: Result[int] = err_msg("error").map_try(
            int,
            code=SampleCode.ERROR,
            message="invalid int",
        )
        assert res.is_err()
        assert res.unwrap_err().message == "error"


class TestResultAndThenTry:
    """Test Result.and_then_try() for chaining with exception capture."""

    def test_and_then_try_transforms_ok_value(self) -> None:
        res: Result[str] = Ok("123").and_then_try(
            lambda x: Ok(f"Value is {int(x) * 2}"),
            code=SampleCode.ERROR,
            message="invalid int",
        )
        assert res.is_ok()
        assert res.unwrap() == "Value is 246"

    def test_and_then_try_wraps_exception(self) -> None:
        res: Result[str] = Ok("nope").and_then_try(
            lambda x: Ok(f"Value is {int(x) * 2}"),
            code=SampleCode.BAD_INPUT,
            message="invalid int",
        )
        assert res.is_err()
        err = res.unwrap_err()
        assert err.code == SampleCode.BAD_INPUT
        assert err.message == "invalid int"
        assert err.cause is not None
        assert "py_exception" in err.cause

    def test_and_then_try_skips_on_err(self) -> None:
        res: Result[str] = err_msg("error").and_then_try(
            lambda x: Ok(f"Value is {x}"),
            code=SampleCode.ERROR,
            message="invalid int",
        )
        assert res.is_err()
        assert res.unwrap_err().message == "error"


class TestResultMapErr:
    """Test Result.map_err() for transforming Err values."""

    def test_map_err_transforms_err_value(self) -> None:
        res: Result[int] = err_msg("error").map_err(
            lambda e: new_error(
                code=e.code,
                message=e.message.upper(),
                kind=e.kind,
            )
        )
        assert res.is_err()
        assert res.unwrap_err().message == "ERROR"

    def test_map_err_skips_on_ok(self) -> None:
        res: Result[int] = Ok(10).map_err(lambda e: e)
        assert res.is_ok()
        assert res.unwrap() == 10


class TestResultMapOr:
    """Test Result.map_or() for transforming with default."""

    def test_map_or_applies_function_on_ok(self) -> None:
        res: Result[int] = Ok(10)
        result = res.map_or(0, lambda x: x * 2)
        assert result == 20

    def test_map_or_returns_default_on_err(self) -> None:
        res: Result[int] = err_msg("error")
        result = res.map_or(0, lambda x: x * 2)
        assert result == 0

    def test_map_or_with_type_conversion(self) -> None:
        # Transform int to str on Ok
        res: Result[int] = Ok(42)
        result = res.map_or("default", lambda x: f"Value: {x}")
        assert result == "Value: 42"

        # Use default on Err
        res_err: Result[int] = err_msg("error")
        result_err = res_err.map_or("default", lambda x: f"Value: {x}")
        assert result_err == "default"

    def test_map_or_function_not_called_on_err(self) -> None:
        """Verify function is not called when Result is Err."""
        called = False

        def transform(_x: int) -> int:
            nonlocal called
            called = True
            return 999

        res: Result[int] = err_msg("error")
        result = res.map_or(0, transform)
        assert result == 0
        assert called is False


class TestResultMapOrElse:
    """Test Result.map_or_else() for transforming with computed default."""

    def test_map_or_else_applies_function_on_ok(self) -> None:
        res: Result[int] = Ok(10)
        result = res.map_or_else(lambda _e: 0, lambda x: x * 2)
        assert result == 20

    def test_map_or_else_computes_default_on_err(self) -> None:
        res: Result[int] = err_msg("error")
        result = res.map_or_else(lambda e: len(e.message), lambda x: x * 2)
        assert result == 5

    def test_map_or_else_receives_error_value(self) -> None:
        """Verify default function receives the actual error."""
        res: Result[int] = err_msg("404")
        result = res.map_or_else(lambda code: int(code.message) * 10, lambda x: x * 2)
        assert result == 4040

    def test_map_or_else_functions_not_both_called(self) -> None:
        """Verify only one function is called."""
        transform_called = False
        default_called = False

        def transform(_x: int) -> int:
            nonlocal transform_called
            transform_called = True
            return 999

        def compute_default(_e: object) -> int:
            nonlocal default_called
            default_called = True
            return 0

        # Ok case
        res: Result[int] = Ok(10)
        res.map_or_else(compute_default, transform)
        assert transform_called is True
        assert default_called is False

        # Err case
        transform_called = False
        res_err: Result[int] = err_msg("error")
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

        res: Result[int] = Ok(42)
        result = res.inspect(side_effect)
        assert called_with == 42
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_inspect_not_called_on_err(self) -> None:
        called = False

        def side_effect(_x: int) -> None:
            nonlocal called
            called = True

        res: Result[int] = err_msg("error")
        result = res.inspect(side_effect)
        assert called is False
        assert result.is_err()
        assert result.unwrap_err().message == "error"

    def test_inspect_enables_chaining(self) -> None:
        """Verify inspect returns Result for method chaining."""
        log: list[int] = []

        res: Result[int] = (
            Ok(10)
            .inspect(lambda x: log.append(x))
            .map(lambda x: x * 2)
            .inspect(lambda x: log.append(x))
        )

        assert log == [10, 20]
        assert res.unwrap() == 20

    def test_inspect_preserves_error(self) -> None:
        """Verify inspect doesn't affect Err."""
        res: Result[int] = err_msg("error")
        result = res.inspect(lambda _x: None).map(lambda x: x * 2)
        assert result.is_err()
        assert result.unwrap_err().message == "error"

    def test_inspect_with_print_debugging(self) -> None:
        """Use case: debugging with side effects."""
        values_seen: list[int] = []

        result: Result[int] = (
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

        def side_effect(e: Error) -> None:
            nonlocal called_with
            called_with = e

        res: Result[int] = err_msg("error")
        result = res.inspect_err(side_effect)
        assert called_with is not None
        assert called_with.message == "error"
        assert result.is_err()
        assert result.unwrap_err().message == "error"

    def test_inspect_err_not_called_on_ok(self) -> None:
        called = False

        def side_effect(_e: object) -> None:
            nonlocal called
            called = True

        res: Result[int] = Ok(42)
        result = res.inspect_err(side_effect)
        assert called is False
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_inspect_err_enables_chaining(self) -> None:
        """Verify inspect_err returns Result for method chaining."""
        log: list[str] = []

        res: Result[int] = (
            err_msg("error1")
            .inspect_err(lambda e: log.append(e.message))
            .map_err(
                lambda e: new_error(
                    code=e.code,
                    message=f"{e.message}_mapped",
                    kind=e.kind,
                )
            )
            .inspect_err(lambda e: log.append(e.message))
        )

        assert log == ["error1", "error1_mapped"]
        assert res.unwrap_err().message == "error1_mapped"

    def test_inspect_err_preserves_ok(self) -> None:
        """Verify inspect_err doesn't affect Ok."""
        res: Result[int] = Ok(10)
        result = res.inspect_err(lambda _e: None).map(lambda x: x * 2)
        assert result.is_ok()
        assert result.unwrap() == 20

    def test_inspect_err_for_error_logging(self) -> None:
        """Use case: logging errors without changing the result."""
        errors_logged: list[str] = []

        result: Result[int] = (
            err_msg("validation failed")
            .inspect_err(lambda e: errors_logged.append(f"Error: {e.message}"))
            .map_err(
                lambda e: new_error(
                    code=e.code,
                    message=e.message.upper(),
                    kind=e.kind,
                )
            )
            .inspect_err(lambda e: errors_logged.append(f"Transformed: {e.message}"))
        )

        assert errors_logged == ["Error: validation failed", "Transformed: VALIDATION FAILED"]
        assert result.unwrap_err().message == "VALIDATION FAILED"

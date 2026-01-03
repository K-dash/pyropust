"""Tests for Result composition methods (and_then, and_, or_).

Note: Type annotations are required when using Ok()/err() constructors
because they have inferred types Result[T] and Result[Never].
This matches Rust's type system design. Use function return types or
intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

from pyropust import Ok, Result
from tests.support import err_msg


class TestResultAndThen:
    """Test Result.and_then() for chaining operations that return Result."""

    def test_and_then_chains_ok_results(self) -> None:
        def double(x: int) -> Result[int]:
            return Ok(x * 2)

        res: Result[int] = Ok(10).and_then(double)
        assert res.is_ok()
        assert res.unwrap() == 20

    def test_and_then_short_circuits_on_err(self) -> None:
        def double(x: int) -> Result[int]:
            return Ok(x * 2)

        res: Result[int] = err_msg("first error").and_then(double)
        assert res.is_err()
        assert res.unwrap_err().message == "first error"

    def test_and_then_propagates_inner_err(self) -> None:
        def get_ok() -> Result[int]:
            return Ok(10)

        def inner_err(_val: int) -> Result[int]:
            return err_msg("inner error")

        res = get_ok().and_then(inner_err)
        assert res.is_err()
        assert res.unwrap_err().message == "inner error"

    def test_readme_example_functional_chaining(self) -> None:
        """Verify the README functional chaining example works."""

        def to_message(x: int) -> Result[str]:
            return Ok(f"Value is {x}")

        res: Result[str] = Ok("123").map(int).map(lambda x: x * 2).and_then(to_message)
        assert res.unwrap() == "Value is 246"


class TestResultAnd:
    """Test Result.and_() for combining Results."""

    def test_and_returns_other_on_ok(self) -> None:
        res1: Result[int] = Ok(10)
        res2: Result[int] = Ok(20)
        result = res1.and_(res2)
        assert result.is_ok()
        assert result.unwrap() == 20

    def test_and_returns_self_on_err(self) -> None:
        res1: Result[int] = err_msg("error1")
        res2: Result[int] = Ok(20)
        result = res1.and_(res2)
        assert result.is_err()
        assert result.unwrap_err().message == "error1"

    def test_and_ok_with_err_returns_err(self) -> None:
        # Type annotations are required because Ok() and err() constructors
        # have inferred types Result[T] and Result[Never] respectively.
        # This matches Rust's type system design.
        # Note: Using intermediate function calls to satisfy pyright's strict type checking
        def ok_val() -> Result[int]:
            return Ok(10)

        def err_val() -> Result[int]:
            return err_msg("error2")

        res1 = ok_val()
        res2 = err_val()
        result = res1.and_(res2)
        assert result.is_err()
        assert result.unwrap_err().message == "error2"

    def test_and_both_err_returns_first_err(self) -> None:
        res1: Result[int] = err_msg("error1")
        res2: Result[int] = err_msg("error2")
        result = res1.and_(res2)
        assert result.is_err()
        assert result.unwrap_err().message == "error1"

    def test_and_enables_sequential_validation(self) -> None:
        """Use case: sequential validation where all must succeed."""

        def validate_positive(x: int) -> Result[int]:
            return Ok(x) if x > 0 else err_msg("must be positive")

        def validate_range(x: int) -> Result[int]:
            return Ok(x) if x < 100 else err_msg("must be less than 100")

        # Success case
        result = validate_positive(50).and_(validate_range(50))
        assert result.is_ok()
        assert result.unwrap() == 50

        # First validation fails
        result = validate_positive(-5).and_(validate_range(50))
        assert result.is_err()
        assert result.unwrap_err().message == "must be positive"


class TestResultOr:
    """Test Result.or_() for fallback Results."""

    def test_or_returns_self_on_ok(self) -> None:
        res1: Result[int] = Ok(10)
        res2: Result[int] = Ok(20)
        result = res1.or_(res2)
        assert result.is_ok()
        assert result.unwrap() == 10

    def test_or_returns_other_on_err(self) -> None:
        # Type annotations are required because Ok() and err() constructors
        # have inferred types Result[T] and Result[Never] respectively.
        # This matches Rust's type system design.
        # Note: Using intermediate function calls to satisfy pyright's strict type checking
        def err_val() -> Result[int]:
            return err_msg("error1")

        def ok_val() -> Result[int]:
            return Ok(20)

        res1 = err_val()
        res2 = ok_val()
        result = res1.or_(res2)
        assert result.is_ok()
        assert result.unwrap() == 20

    def test_or_both_ok_returns_first_ok(self) -> None:
        res1: Result[int] = Ok(10)
        res2: Result[int] = Ok(20)
        result = res1.or_(res2)
        assert result.is_ok()
        assert result.unwrap() == 10

    def test_or_both_err_returns_second_err(self) -> None:
        res1: Result[int] = err_msg("error1")
        res2: Result[int] = err_msg("error2")
        result = res1.or_(res2)
        assert result.is_err()
        assert result.unwrap_err().message == "error2"

    def test_or_enables_fallback_chain(self) -> None:
        """Use case: try multiple sources until one succeeds."""

        def fetch_from_cache() -> Result[str]:
            return err_msg("cache miss")

        def fetch_from_database() -> Result[str]:
            return err_msg("db connection failed")

        def fetch_from_default() -> Result[str]:
            return Ok("default value")

        # All fallbacks tried until one succeeds
        result = fetch_from_cache().or_(fetch_from_database()).or_(fetch_from_default())
        assert result.is_ok()
        assert result.unwrap() == "default value"

    def test_or_with_err_ok_returns_ok(self) -> None:
        # Type annotations are required because Ok() and err() constructors
        # have inferred types Result[T] and Result[Never] respectively.
        # This matches Rust's type system design.
        # Note: Using intermediate function calls to satisfy pyright's strict type checking
        def err_val() -> Result[int]:
            return err_msg("error")

        def ok_val() -> Result[int]:
            return Ok(42)

        res1 = err_val()
        res2 = ok_val()
        result = res1.or_(res2)
        assert result.is_ok()
        assert result.unwrap() == 42


class TestResultOrElse:
    """Test Result.or_else() for fallback with error transformation."""

    def test_or_else_returns_self_on_ok(self) -> None:
        res: Result[int] = Ok(10)
        result = res.or_else(lambda _e: Ok(20))
        assert result.is_ok()
        assert result.unwrap() == 10

    def test_or_else_calls_function_on_err(self) -> None:
        res: Result[int] = err_msg("error")
        # Pyright reports type error due to covariance: Ok(20) returns Result[int],
        # but or_else expects Result[T_co]. This is a type system limitation when using
        # lambdas with inferred types. The runtime behavior is correct and matches Rust.
        result = res.or_else(lambda _e: Ok(20))  # pyright: ignore[reportArgumentType]
        assert result.is_ok()
        assert result.unwrap() == 20

    def test_or_else_receives_error_value(self) -> None:
        """Verify or_else function receives the actual error."""
        res: Result[int] = err_msg("404")
        # Pyright reports type error due to covariance: Ok(code * 10) returns Result[int],
        # but or_else expects Result[T_co]. This is a type system limitation when using
        # lambdas with inferred types. The runtime behavior is correct and matches Rust.
        result = res.or_else(lambda err: Ok(int(err.message) * 10))  # pyright: ignore[reportArgumentType]
        assert result.is_ok()
        assert result.unwrap() == 4040

    def test_or_else_can_return_new_error(self) -> None:
        """Verify or_else can transform error type."""
        res: Result[int] = err_msg("original")
        result = res.or_else(lambda e: err_msg(f"transformed: {e.message}"))
        assert result.is_err()
        assert result.unwrap_err().message == "transformed: original"

    def test_or_else_enables_error_recovery_chain(self) -> None:
        """Use case: try multiple recovery strategies."""

        def fetch_primary() -> Result[str]:
            return err_msg("primary failed")

        def try_secondary(_e: object) -> Result[str]:
            return err_msg("secondary failed")

        def use_default(_e: object) -> Result[str]:
            return Ok("default value")

        # Chain multiple or_else calls until one succeeds
        result = fetch_primary().or_else(try_secondary).or_else(use_default)
        assert result.is_ok()
        assert result.unwrap() == "default value"

    def test_or_else_function_not_called_on_ok(self) -> None:
        """Verify short-circuit behavior - function shouldn't be called for Ok."""
        called = False

        def recovery(_e: object) -> Result[int]:
            nonlocal called
            called = True
            return Ok(999)

        res: Result[int] = Ok(10)
        result = res.or_else(recovery)
        assert result.is_ok()
        assert result.unwrap() == 10
        assert called is False

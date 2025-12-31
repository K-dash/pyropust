"""Tests for Result and Option direct usage patterns (functional chaining).

These tests verify the README examples and cover methods not tested elsewhere:
- Result: map(), and_then(), map_err()
- Option: map(), unwrap_or()
"""

from __future__ import annotations

from pyropust import Err, None_, Ok, Option, Result, Some


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


class TestResultAndThen:
    """Test Result.and_then() for chaining operations that return Result."""

    def test_and_then_chains_ok_results(self) -> None:
        res = Ok(10).and_then(lambda x: Ok(x * 2))
        assert res.is_ok()
        assert res.unwrap() == 20

    def test_and_then_short_circuits_on_err(self) -> None:
        res: Result[int, str] = Err("first error").and_then(lambda x: Ok(x * 2))
        assert res.is_err()
        assert res.unwrap_err() == "first error"

    def test_and_then_propagates_inner_err(self) -> None:
        def get_ok() -> Result[int, str]:
            return Ok(10)

        def inner_err(_val: int) -> Result[int, str]:
            return Err("inner error")

        res = get_ok().and_then(inner_err)
        assert res.is_err()
        assert res.unwrap_err() == "inner error"

    def test_readme_example_functional_chaining(self) -> None:
        """Verify the README functional chaining example works."""
        res = Ok("123").map(int).map(lambda x: x * 2).and_then(lambda x: Ok(f"Value is {x}"))
        assert res.unwrap() == "Value is 246"


class TestResultMapErr:
    """Test Result.map_err() for transforming Err values."""

    def test_map_err_transforms_err_value(self) -> None:
        res: Result[int, str] = Err("error").map_err(lambda e: f"wrapped: {e}")
        assert res.is_err()
        assert res.unwrap_err() == "wrapped: error"

    def test_map_err_skips_on_ok(self) -> None:
        res = Ok(10).map_err(lambda e: f"wrapped: {e}")
        assert res.is_ok()
        assert res.unwrap() == 10


class TestOptionMap:
    """Test Option.map() for transforming Some values."""

    def test_map_transforms_some_value(self) -> None:
        opt = Some(10).map(lambda x: x * 2)
        assert opt.is_some()
        assert opt.unwrap() == 20

    def test_map_skips_on_none(self) -> None:
        opt: Option[int] = None_().map(lambda x: x * 2)
        assert opt.is_none()


class TestOptionUnwrapOr:
    """Test Option.unwrap_or() for providing default values."""

    def test_unwrap_or_returns_value_on_some(self) -> None:
        opt = Some("Alice")
        assert opt.unwrap_or("Guest") == "Alice"

    def test_unwrap_or_returns_default_on_none(self) -> None:
        opt: Option[str] = None_()
        assert opt.unwrap_or("Guest") == "Guest"

    def test_readme_example_option_usage(self) -> None:
        """Verify the README Option example works."""

        def find_user(user_id: int) -> Option[str]:
            return Some("Alice") if user_id == 1 else None_()

        # Found user
        name_opt = find_user(1)
        name = name_opt.unwrap_or("Guest")
        assert name == "Alice"

        # Not found user
        name_opt2 = find_user(999)
        name2 = name_opt2.unwrap_or("Guest")
        assert name2 == "Guest"


class TestResultManualHandling:
    """Test manual Result handling pattern from README."""

    def test_readme_example_divide_function(self) -> None:
        """Verify the README divide example works."""

        def divide(a: int, b: int) -> Result[float, str]:
            if b == 0:
                return Err("Division by zero")
            return Ok(a / b)

        # Success case
        res = divide(10, 2)
        assert res.is_ok()
        assert res.unwrap() == 5.0

        # Error case
        res_err = divide(10, 0)
        assert res_err.is_err()
        assert res_err.unwrap_err() == "Division by zero"

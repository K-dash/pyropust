"""Tests for Result query methods (is_ok_and, is_err_and).

Note: Type annotations are required when using Ok()/Err() constructors
because they have inferred types Result[T] and Result[Never].
This matches Rust's type system design. Use function return types or
intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

from pyropust import Err, Ok, Result


class TestResultIsOkAnd:
    """Test Result.is_ok_and() for conditional Ok checking."""

    def test_returns_true_when_ok_and_predicate_true(self) -> None:
        res = Ok(10)
        assert res.is_ok_and(lambda x: x > 5) is True

    def test_returns_false_when_ok_but_predicate_false(self) -> None:
        res = Ok(3)
        assert res.is_ok_and(lambda x: x > 5) is False

    def test_returns_false_when_err(self) -> None:
        res: Result[int] = Err("error")
        assert res.is_ok_and(lambda x: x > 5) is False

    def test_accepts_truthy_values(self) -> None:
        """Verify Python truthiness protocol works."""
        # Non-empty string is truthy
        assert Ok("hello").is_ok_and(lambda x: x) is True
        # Empty string is falsy
        assert Ok("").is_ok_and(lambda x: x) is False
        # Non-zero int is truthy
        assert Ok(42).is_ok_and(lambda x: x) is True
        # Zero is falsy
        assert Ok(0).is_ok_and(lambda x: x) is False

    def test_predicate_receives_ok_value(self) -> None:
        """Verify predicate gets the actual Ok value."""
        res = Ok([1, 2, 3])
        assert res.is_ok_and(lambda x: len(x) == 3) is True
        assert res.is_ok_and(lambda x: len(x) == 5) is False

    def test_predicate_not_called_when_err(self) -> None:
        """Verify short-circuit behavior - predicate shouldn't be called for Err."""
        called = False

        def side_effect_predicate(_x: int) -> bool:
            nonlocal called
            called = True
            return True

        res: Result[int] = Err("error")
        assert res.is_ok_and(side_effect_predicate) is False
        assert called is False


class TestResultIsErrAnd:
    """Test Result.is_err_and() for conditional Err checking."""

    def test_returns_true_when_err_and_predicate_true(self) -> None:
        res: Result[int] = Err("error")
        assert res.is_err_and(lambda e: "err" in e.message) is True

    def test_returns_false_when_err_but_predicate_false(self) -> None:
        res: Result[int] = Err("success")
        assert res.is_err_and(lambda e: "err" in e.message) is False

    def test_returns_false_when_ok(self) -> None:
        res: Result[int] = Ok(10)
        assert res.is_err_and(lambda e: "err" in e.message) is False

    def test_accepts_truthy_values(self) -> None:
        """Verify Python truthiness protocol works."""
        # Non-empty string is truthy
        res_err: Result[int] = Err("error")
        assert res_err.is_err_and(lambda e: e.message) is True
        # Empty string is falsy
        res_empty: Result[int] = Err("")
        assert res_empty.is_err_and(lambda e: e.message) is False

    def test_predicate_receives_err_value(self) -> None:
        """Verify predicate gets the actual Err value."""
        res: Result[int] = Err("404")
        assert res.is_err_and(lambda e: e.message == "404") is True
        assert res.is_err_and(lambda e: e.message == "500") is False

    def test_predicate_not_called_when_ok(self) -> None:
        """Verify short-circuit behavior - predicate shouldn't be called for Ok."""
        called = False

        def side_effect_predicate(_e: object) -> bool:
            nonlocal called
            called = True
            return True

        res: Result[int] = Ok(10)
        assert res.is_err_and(side_effect_predicate) is False
        assert called is False

"""Tests for Option composition methods (and_then, and_, or_).

Note: Type annotations are required when using Some()/None_() constructors
because they have inferred types. This matches Rust's type system design.
Use function return types or intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

from pyropust import None_, Option, Some


class TestOptionAndThen:
    """Test Option.and_then() for chaining operations that return Option."""

    def test_and_then_chains_some_options(self) -> None:
        opt = Some(10).and_then(lambda x: Some(x * 2))
        assert opt.is_some()
        assert opt.unwrap() == 20

    def test_and_then_short_circuits_on_none(self) -> None:
        opt: Option[int] = None_().and_then(lambda x: Some(x * 2))
        assert opt.is_none()

    def test_and_then_propagates_inner_none(self) -> None:
        def get_some() -> Option[int]:
            return Some(10)

        def inner_none(_val: int) -> Option[int]:
            return None_()

        opt = get_some().and_then(inner_none)
        assert opt.is_none()

    def test_and_then_chains_with_type_change(self) -> None:
        opt = Some(123).and_then(lambda x: Some(str(x)))
        assert opt.is_some()
        assert opt.unwrap() == "123"


class TestOptionAnd:
    """Test Option.and_() for combining Options."""

    def test_and_returns_other_on_some(self) -> None:
        opt1: Option[int] = Some(10)
        opt2: Option[str] = Some("value")
        result = opt1.and_(opt2)
        assert result.is_some()
        assert result.unwrap() == "value"

    def test_and_returns_none_when_first_is_none(self) -> None:
        opt1: Option[int] = None_()
        opt2: Option[str] = Some("value")
        result = opt1.and_(opt2)
        assert result.is_none()

    def test_and_returns_none_when_second_is_none(self) -> None:
        opt1: Option[int] = Some(10)
        opt2: Option[str] = None_()
        result = opt1.and_(opt2)
        assert result.is_none()

    def test_and_both_none_returns_none(self) -> None:
        opt1: Option[int] = None_()
        opt2: Option[str] = None_()
        result = opt1.and_(opt2)
        assert result.is_none()

    def test_and_enables_sequential_validation(self) -> None:
        """Test and_ for sequential validation where both must be Some."""

        def validate_positive(n: int) -> Option[int]:
            return Some(n) if n > 0 else None_()

        def validate_even(n: int) -> Option[int]:
            return Some(n) if n % 2 == 0 else None_()

        # Both validations pass
        opt1 = validate_positive(10)
        opt2 = validate_even(10)
        result = opt1.and_(opt2)
        assert result.is_some()

        # First validation fails
        opt1_fail = validate_positive(-5)
        opt2_pass = validate_even(10)
        result_fail = opt1_fail.and_(opt2_pass)
        assert result_fail.is_none()


class TestOptionOr:
    """Test Option.or_() for providing fallback Options."""

    def test_or_returns_self_on_some(self) -> None:
        opt1: Option[int] = Some(10)
        opt2: Option[int] = Some(20)
        result = opt1.or_(opt2)
        assert result.is_some()
        assert result.unwrap() == 10

    def test_or_returns_other_on_none(self) -> None:
        def none_val() -> Option[int]:
            return None_()

        def some_val() -> Option[int]:
            return Some(20)

        opt1 = none_val()
        opt2 = some_val()
        result = opt1.or_(opt2)
        assert result.is_some()
        assert result.unwrap() == 20

    def test_or_both_some_returns_first(self) -> None:
        opt1: Option[int] = Some(10)
        opt2: Option[int] = Some(20)
        result = opt1.or_(opt2)
        assert result.is_some()
        assert result.unwrap() == 10

    def test_or_both_none_returns_none(self) -> None:
        def none_val1() -> Option[int]:
            return None_()

        def none_val2() -> Option[int]:
            return None_()

        opt1 = none_val1()
        opt2 = none_val2()
        result = opt1.or_(opt2)
        assert result.is_none()

    def test_or_enables_fallback_chain(self) -> None:
        """Test or_ for trying multiple fallback sources."""

        def primary_source() -> Option[str]:
            return None_()

        def secondary_source() -> Option[str]:
            return None_()

        def tertiary_source() -> Option[str]:
            return Some("fallback value")

        result = primary_source().or_(secondary_source()).or_(tertiary_source())
        assert result.is_some()
        assert result.unwrap() == "fallback value"


class TestOptionOrElse:
    """Test Option.or_else() for fallback with computation."""

    def test_or_else_returns_self_on_some(self) -> None:
        opt: Option[int] = Some(10)
        result = opt.or_else(lambda: Some(20))
        assert result.is_some()
        assert result.unwrap() == 10

    def test_or_else_calls_function_on_none(self) -> None:
        def none_val() -> Option[int]:
            return None_()

        def fallback() -> Option[int]:
            return Some(20)

        opt = none_val()
        result = opt.or_else(fallback)
        assert result.is_some()
        assert result.unwrap() == 20

    def test_or_else_can_return_none(self) -> None:
        def none_val() -> Option[int]:
            return None_()

        def fallback() -> Option[int]:
            return None_()

        opt = none_val()
        result = opt.or_else(fallback)
        assert result.is_none()

    def test_or_else_enables_fallback_chain(self) -> None:
        """Test or_else for trying multiple fallback computations."""

        def primary() -> Option[str]:
            return None_()

        def secondary() -> Option[str]:
            return None_()

        def tertiary() -> Option[str]:
            return Some("fallback value")

        result = primary().or_else(secondary).or_else(tertiary)
        assert result.is_some()
        assert result.unwrap() == "fallback value"

    def test_or_else_function_not_called_on_some(self) -> None:
        """Verify or_else function is not called when Some."""
        called: list[bool] = []

        def fallback() -> Option[int]:
            called.append(True)
            return Some(99)

        opt: Option[int] = Some(10)
        result = opt.or_else(fallback)
        assert called == []
        assert result.is_some()
        assert result.unwrap() == 10


class TestOptionXor:
    """Test Option.xor() for exclusive or operation."""

    def test_xor_some_none_returns_some(self) -> None:
        opt1: Option[int] = Some(10)
        opt2: Option[int] = None_()
        result = opt1.xor(opt2)
        assert result.is_some()
        assert result.unwrap() == 10

    def test_xor_none_some_returns_some(self) -> None:
        def none_val() -> Option[int]:
            return None_()

        def some_val() -> Option[int]:
            return Some(20)

        opt1 = none_val()
        opt2 = some_val()
        result = opt1.xor(opt2)
        assert result.is_some()
        assert result.unwrap() == 20

    def test_xor_some_some_returns_none(self) -> None:
        opt1: Option[int] = Some(10)
        opt2: Option[int] = Some(20)
        result = opt1.xor(opt2)
        assert result.is_none()

    def test_xor_none_none_returns_none(self) -> None:
        def none_val1() -> Option[int]:
            return None_()

        def none_val2() -> Option[int]:
            return None_()

        opt1 = none_val1()
        opt2 = none_val2()
        result = opt1.xor(opt2)
        assert result.is_none()

    def test_xor_enables_exclusive_choice(self) -> None:
        """Test xor for choosing when exactly one is Some."""

        def from_cache() -> Option[str]:
            return None_()

        def from_default() -> Option[str]:
            return Some("default")

        # Exactly one source has a value
        result = from_cache().xor(from_default())
        assert result.is_some()
        assert result.unwrap() == "default"

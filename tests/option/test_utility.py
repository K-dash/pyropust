"""Tests for Option utility methods (flatten, transpose, zip, zip_with).

Note: Type annotations are required when using Some()/None_() constructors
because they have inferred types. This matches Rust's type system design.
Use function return types or intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

import pytest

from pyropust import Err, None_, Ok, Option, Result, Some


class TestOptionFlatten:
    """Test Option.flatten() for flattening nested Options."""

    def test_flatten_some_some(self) -> None:
        """Flatten Some(Some(value)) -> Some(value)."""

        def make_nested() -> Option[Option[int]]:
            return Some(Some(42))

        nested = make_nested()
        result = nested.flatten()
        assert result.is_some()
        assert result.unwrap() == 42

    def test_flatten_some_none(self) -> None:
        """Flatten Some(None) -> None."""

        def inner_none() -> Option[int]:
            return None_()

        nested: Option[Option[int]] = Some(inner_none())
        result = nested.flatten()
        assert result.is_none()

    def test_flatten_none(self) -> None:
        """Flatten None -> None."""
        nested: Option[Option[int]] = None_()
        result = nested.flatten()
        assert result.is_none()

    def test_flatten_requires_nested_option(self) -> None:
        """Verify flatten raises TypeError if Some value is not an Option."""
        opt: Option[int] = Some(42)
        with pytest.raises(TypeError, match="flatten requires Some value to be an Option"):
            opt.flatten()  # type: ignore[misc]

    def test_flatten_multiple_levels(self) -> None:
        """Verify flatten only removes one level of nesting."""

        def triple_nested() -> Option[Option[Option[int]]]:
            return Some(Some(Some(42)))

        nested = triple_nested()
        once_flattened = nested.flatten()
        assert once_flattened.is_some()

        # Still nested, need another flatten
        twice_flattened = once_flattened.flatten()
        assert twice_flattened.is_some()
        assert twice_flattened.unwrap() == 42


class TestOptionTranspose:
    """Test Option.transpose() for converting Option[Result] to Result[Option]."""

    def test_transpose_some_ok(self) -> None:
        """Transpose Some(Ok(value)) -> Ok(Some(value))."""

        def make_some_ok() -> Option[Result[int]]:
            return Some(Ok(42))

        opt = make_some_ok()
        result = opt.transpose()
        assert result.is_ok()
        unwrapped = result.unwrap()
        assert unwrapped.is_some()
        assert unwrapped.unwrap() == 42

    def test_transpose_some_err(self) -> None:
        """Transpose Some(Err(error)) -> Err(error)."""

        def make_err() -> Result[int]:
            return Err("error")

        opt: Option[Result[int]] = Some(make_err())
        result = opt.transpose()
        assert result.is_err()
        assert result.unwrap_err().message == "error"

    def test_transpose_none(self) -> None:
        """Transpose None -> Ok(None)."""
        opt: Option[Result[int]] = None_()
        result = opt.transpose()
        assert result.is_ok()
        unwrapped = result.unwrap()
        assert unwrapped.is_none()

    def test_transpose_requires_result(self) -> None:
        """Verify transpose raises TypeError if Some value is not a Result."""
        opt: Option[int] = Some(42)
        with pytest.raises(TypeError, match="transpose requires Some value to be a Result"):
            opt.transpose()  # type: ignore[misc]

    def test_transpose_round_trip_some(self) -> None:
        """Verify transpose is reversible for Some(Ok(value))."""

        def make_option() -> Option[Result[int]]:
            return Some(Ok(42))

        opt = make_option()
        # Option[Result[T]] -> Result[Option[T]]
        transposed = opt.transpose()
        assert transposed.is_ok()

        # Result[Option[T]] -> Option[Result[T]]
        back = transposed.transpose()
        assert back.is_some()
        inner_result = back.unwrap()
        assert inner_result.is_ok()
        assert inner_result.unwrap() == 42

    def test_transpose_round_trip_none(self) -> None:
        """Verify transpose is reversible for None."""

        def make_option() -> Option[Result[int]]:
            return None_()

        opt = make_option()
        # Option[Result[T]] -> Result[Option[T]]
        transposed = opt.transpose()
        assert transposed.is_ok()

        # Result[Option[T]] -> Option[Result[T]]
        back = transposed.transpose()
        assert back.is_none()


class TestOptionZip:
    """Test Option.zip() for combining two Options into a tuple."""

    def test_zip_some_some(self) -> None:
        """Zip Some(a) with Some(b) -> Some((a, b))."""
        opt1: Option[int] = Some(10)
        opt2: Option[str] = Some("hello")
        result = opt1.zip(opt2)
        assert result.is_some()
        value = result.unwrap()
        assert value == (10, "hello")

    def test_zip_some_none(self) -> None:
        """Zip Some(a) with None -> None."""
        opt1: Option[int] = Some(10)
        opt2: Option[str] = None_()
        result = opt1.zip(opt2)
        assert result.is_none()

    def test_zip_none_some(self) -> None:
        """Zip None with Some(b) -> None."""

        def none_val() -> Option[int]:
            return None_()

        def some_val() -> Option[str]:
            return Some("hello")

        opt1 = none_val()
        opt2 = some_val()
        result = opt1.zip(opt2)
        assert result.is_none()

    def test_zip_none_none(self) -> None:
        """Zip None with None -> None."""

        def none_val1() -> Option[int]:
            return None_()

        def none_val2() -> Option[str]:
            return None_()

        opt1 = none_val1()
        opt2 = none_val2()
        result = opt1.zip(opt2)
        assert result.is_none()

    def test_zip_different_types(self) -> None:
        """Verify zip works with different types."""
        opt1: Option[int] = Some(42)
        opt2: Option[list[str]] = Some(["a", "b", "c"])
        result = opt1.zip(opt2)
        assert result.is_some()
        assert result.unwrap() == (42, ["a", "b", "c"])


class TestOptionZipWith:
    """Test Option.zip_with() for combining Options with a function."""

    def test_zip_with_some_some(self) -> None:
        """Zip Some(a) with Some(b) using function -> Some(f(a, b))."""
        opt1: Option[int] = Some(10)
        opt2: Option[int] = Some(20)
        result = opt1.zip_with(opt2, lambda x, y: x + y)
        assert result.is_some()
        assert result.unwrap() == 30

    def test_zip_with_some_none(self) -> None:
        """Zip Some(a) with None using function -> None."""
        opt1: Option[int] = Some(10)
        opt2: Option[int] = None_()
        result = opt1.zip_with(opt2, lambda x, y: x + y)
        assert result.is_none()

    def test_zip_with_none_some(self) -> None:
        """Zip None with Some(b) using function -> None."""

        def none_val() -> Option[int]:
            return None_()

        def some_val() -> Option[int]:
            return Some(20)

        opt1 = none_val()
        opt2 = some_val()
        result = opt1.zip_with(opt2, lambda x, y: x + y)
        assert result.is_none()

    def test_zip_with_none_none(self) -> None:
        """Zip None with None using function -> None."""

        def none_val1() -> Option[int]:
            return None_()

        def none_val2() -> Option[int]:
            return None_()

        opt1 = none_val1()
        opt2 = none_val2()
        result = opt1.zip_with(opt2, lambda x, y: x + y)
        assert result.is_none()

    def test_zip_with_string_concatenation(self) -> None:
        """Verify zip_with with string concatenation."""
        opt1: Option[str] = Some("Hello")
        opt2: Option[str] = Some(" World")
        result = opt1.zip_with(opt2, lambda x, y: x + y)
        assert result.is_some()
        assert result.unwrap() == "Hello World"

    def test_zip_with_different_types(self) -> None:
        """Verify zip_with works with different input types."""
        opt1: Option[int] = Some(42)
        opt2: Option[str] = Some("items")
        result = opt1.zip_with(opt2, lambda count, item: f"{count} {item}")
        assert result.is_some()
        assert result.unwrap() == "42 items"

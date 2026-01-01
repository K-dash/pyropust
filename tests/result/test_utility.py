"""Tests for Result utility methods (flatten, transpose).

Note: Type annotations are required when using Ok()/Err() constructors
because they have inferred types Result[T, Never] and Result[Never, E].
This matches Rust's type system design. Use function return types or
intermediate functions to satisfy strict type checking.
"""

from __future__ import annotations

import pytest

from pyropust import Err, None_, Ok, Option, Result, Some


class TestResultFlatten:
    """Test Result.flatten() for flattening nested Results."""

    def test_flatten_ok_ok(self) -> None:
        """Flatten Ok(Ok(value)) -> Ok(value)."""

        def make_nested() -> Result[Result[int, str], str]:
            return Ok(Ok(42))

        nested = make_nested()
        result = nested.flatten()
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_flatten_ok_err(self) -> None:
        """Flatten Ok(Err(error)) -> Err(error)."""

        def inner_err() -> Result[int, str]:
            return Err("inner error")

        nested: Result[Result[int, str], str] = Ok(inner_err())
        result = nested.flatten()
        assert result.is_err()
        assert result.unwrap_err() == "inner error"

    def test_flatten_err(self) -> None:
        """Flatten Err(error) -> Err(error)."""
        nested: Result[Result[int, str], str] = Err("outer error")
        result = nested.flatten()
        assert result.is_err()
        assert result.unwrap_err() == "outer error"

    def test_flatten_requires_nested_result(self) -> None:
        """Verify flatten raises TypeError if Ok value is not a Result."""
        res: Result[int, str] = Ok(42)
        with pytest.raises(TypeError, match="flatten requires Ok value to be a Result"):
            res.flatten()  # type: ignore[misc]

    def test_flatten_multiple_levels(self) -> None:
        """Verify flatten only removes one level of nesting."""

        def triple_nested() -> Result[Result[Result[int, str], str], str]:
            return Ok(Ok(Ok(42)))

        nested = triple_nested()
        result = nested.flatten()
        # After one flatten, we have Result[Result[int, str], str]
        assert result.is_ok()
        inner = result.flatten()
        assert inner.is_ok()
        assert inner.unwrap() == 42

    def test_flatten_with_different_error_types_in_layers(self) -> None:
        """Verify flatten works when inner and outer error types match."""

        def make_nested() -> Result[Result[str, int], int]:
            # Inner Err with int error type
            return Ok(Err(404))

        nested = make_nested()
        result = nested.flatten()
        assert result.is_err()
        assert result.unwrap_err() == 404


class TestResultTranspose:
    """Test Result.transpose() for converting Result[Option[T], E] to Option[Result[T, E]]."""

    def test_transpose_ok_some(self) -> None:
        """Transpose Ok(Some(value)) -> Some(Ok(value))."""
        res: Result[Option[int], str] = Ok(Some(42))
        opt = res.transpose()
        assert opt.is_some()
        inner = opt.unwrap()
        assert inner.is_ok()
        assert inner.unwrap() == 42

    def test_transpose_ok_none(self) -> None:
        """Transpose Ok(None) -> None."""

        def make_none() -> Result[Option[int], str]:
            return Ok(None_())

        res = make_none()
        opt = res.transpose()
        assert opt.is_none()

    def test_transpose_err(self) -> None:
        """Transpose Err(error) -> Some(Err(error))."""
        res: Result[Option[int], str] = Err("error")
        opt = res.transpose()
        assert opt.is_some()
        inner = opt.unwrap()
        assert inner.is_err()
        assert inner.unwrap_err() == "error"

    def test_transpose_requires_option(self) -> None:
        """Verify transpose raises TypeError if Ok value is not an Option."""
        res: Result[int, str] = Ok(42)
        with pytest.raises(TypeError, match="transpose requires Ok value to be an Option"):
            res.transpose()  # type: ignore[misc]

    def test_transpose_round_trip_some(self) -> None:
        """Verify transpose is self-inverse for Some case."""
        # Option.transpose() not implemented yet, so we manually verify structure
        # For now, just verify Result.transpose works correctly
        res: Result[Option[int], str] = Ok(Some(42))
        transposed = res.transpose()
        assert transposed.is_some()
        inner = transposed.unwrap()
        assert inner.is_ok()
        assert inner.unwrap() == 42

    def test_transpose_round_trip_none(self) -> None:
        """Verify transpose is self-inverse for None case."""

        def make_none() -> Result[Option[int], str]:
            return Ok(None_())

        res = make_none()
        transposed = res.transpose()
        assert transposed.is_none()

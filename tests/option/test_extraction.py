"""Tests for Option extraction methods."""

from __future__ import annotations

import pytest

from pyropust import None_, Option, Some


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


class TestOptionExpect:
    """Test Option.expect() for extracting values with custom error messages."""

    def test_expect_returns_value_on_some(self) -> None:
        opt = Some("value")
        assert opt.expect("should have value") == "value"

    def test_expect_raises_on_none(self) -> None:
        opt: Option[str] = None_()
        with pytest.raises(RuntimeError, match="custom error"):
            opt.expect("custom error")


class TestOptionUnwrapOrElse:
    """Test Option.unwrap_or_else() for computing default values."""

    def test_unwrap_or_else_returns_value_on_some(self) -> None:
        opt = Some(10)
        assert opt.unwrap_or_else(lambda: 42) == 10

    def test_unwrap_or_else_computes_default_on_none(self) -> None:
        opt: Option[int] = None_()
        assert opt.unwrap_or_else(lambda: 42) == 42

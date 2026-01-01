"""Tests for Option methods (map, unwrap_or)."""

from __future__ import annotations

from pyropust import None_, Option, Some


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

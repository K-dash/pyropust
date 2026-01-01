"""Tests for Option transformation methods."""

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


class TestOptionMapOr:
    """Test Option.map_or() for transforming with default values."""

    def test_map_or_applies_function_on_some(self) -> None:
        opt = Some(5)
        result = opt.map_or(0, lambda x: x * 2)
        assert result == 10

    def test_map_or_returns_default_on_none(self) -> None:
        opt: Option[int] = None_()
        result = opt.map_or(0, lambda x: x * 2)
        assert result == 0


class TestOptionMapOrElse:
    """Test Option.map_or_else() for transforming with computed defaults."""

    def test_map_or_else_applies_function_on_some(self) -> None:
        opt = Some(5)
        result = opt.map_or_else(lambda: 0, lambda x: x * 2)
        assert result == 10

    def test_map_or_else_computes_default_on_none(self) -> None:
        opt: Option[int] = None_()
        result = opt.map_or_else(lambda: 42, lambda x: x * 2)
        assert result == 42


class TestOptionInspect:
    """Test Option.inspect() for side effects."""

    def test_inspect_calls_function_on_some(self) -> None:
        called: list[int] = []
        opt = Some(10)
        result = opt.inspect(lambda x: called.append(x))
        assert called == [10]
        assert result.is_some()
        assert result.unwrap() == 10

    def test_inspect_does_not_call_on_none(self) -> None:
        called: list[int] = []
        opt: Option[int] = None_()
        result = opt.inspect(lambda x: called.append(x))
        assert called == []
        assert result.is_none()


class TestOptionFilter:
    """Test Option.filter() for conditional filtering."""

    def test_filter_keeps_value_when_predicate_matches(self) -> None:
        opt = Some(10)
        result = opt.filter(lambda x: x > 5)
        assert result.is_some()
        assert result.unwrap() == 10

    def test_filter_returns_none_when_predicate_fails(self) -> None:
        opt = Some(3)
        result = opt.filter(lambda x: x > 5)
        assert result.is_none()

    def test_filter_returns_none_on_none(self) -> None:
        opt: Option[int] = None_()
        result = opt.filter(lambda x: x > 5)
        assert result.is_none()

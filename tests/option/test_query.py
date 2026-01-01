"""Tests for Option query methods."""

from __future__ import annotations

from pyropust import None_, Option, Some


class TestOptionQuery:
    """Test Option query methods."""

    def test_is_some_and_returns_true_when_predicate_matches(self) -> None:
        opt = Some(10)
        assert opt.is_some_and(lambda x: x > 5)

    def test_is_some_and_returns_false_when_predicate_fails(self) -> None:
        opt = Some(3)
        assert not opt.is_some_and(lambda x: x > 5)

    def test_is_some_and_returns_false_on_none(self) -> None:
        opt: Option[int] = None_()
        assert not opt.is_some_and(lambda x: x > 5)

    def test_is_none_or_returns_true_on_none(self) -> None:
        opt: Option[int] = None_()
        assert opt.is_none_or(lambda x: x > 5)

    def test_is_none_or_returns_true_when_predicate_matches(self) -> None:
        opt = Some(10)
        assert opt.is_none_or(lambda x: x > 5)

    def test_is_none_or_returns_false_when_predicate_fails(self) -> None:
        opt = Some(3)
        assert not opt.is_none_or(lambda x: x > 5)

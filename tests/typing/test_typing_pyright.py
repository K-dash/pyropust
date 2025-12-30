from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, assert_type

from pyrope import Blueprint, Ok, Op, Result, RopeError, do, run

if TYPE_CHECKING:

    @do
    def to_upper(
        value: str,
    ) -> Generator[Result[str, object], str, Result[str, object]]:
        text = yield Ok(value)
        return Ok(text.upper())

    # index returns object, not str
    bp = Blueprint.for_type(str).pipe(Op.split("@")).pipe(Op.index(1))
    assert_type(bp, Blueprint[str, object])
    assert_type(run(bp, "a@example.com"), Result[object, RopeError])

    # split returns list[str]
    guarded = Blueprint.any().guard_str().pipe(Op.split("@"))
    assert_type(guarded, Blueprint[object, list[str]])

    # Blueprint() with guard_str() to narrow object -> str before to_uppercase
    dynamic = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .guard_str()
        .pipe(Op.to_uppercase())
    )
    assert_type(dynamic, Blueprint[object, str])

    # Alternative: use expect_str() instead of guard_str()
    with_expect = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .pipe(Op.expect_str())
        .pipe(Op.to_uppercase())
    )
    assert_type(with_expect, Blueprint[object, str])

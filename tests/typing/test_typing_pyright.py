from __future__ import annotations

from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING, assert_type

from pyrope import Blueprint, Ok, Op, Result, RopeError, do, run

if TYPE_CHECKING:

    @do
    def to_upper(
        value: str,
    ) -> Generator[Result[str, object], str, Result[str, object]]:
        text = yield Ok(value)
        return Ok(text.upper())

    bp = Blueprint.for_type(str).pipe(Op.split("@")).pipe(Op.index(1))
    assert_type(bp, Blueprint[str, str])
    assert_type(run(bp, "a@example.com"), Result[str, RopeError])

    guarded = Blueprint.any().guard_str().pipe(Op.split("@"))
    assert_type(guarded, Blueprint[object, Sequence[str]])

    # Blueprint() 起点（assert_str で object → str に変換）
    dynamic = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .pipe(Op.to_uppercase())
    )
    assert_type(dynamic, Blueprint[object, str])

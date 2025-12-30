from __future__ import annotations

from collections.abc import Generator

from pyrope import Blueprint, ErrorKind, Ok, Op, Result, RopeError, do, run


def test_blueprint_execution() -> None:
    bp = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .pipe(Op.to_uppercase())
    )

    result = run(bp, "alice@example.com")
    assert result.is_ok()
    assert result.unwrap() == "EXAMPLE.COM"

    fail_result = run(bp, "invalid-email")
    assert fail_result.is_err()
    err = fail_result.unwrap_err()
    assert str(err.kind) == str(ErrorKind.NotFound)


def test_do_with_blueprint() -> None:
    bp = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
    )

    @do
    def workflow(raw: str) -> Generator[Result[str, RopeError], str, Result[str, RopeError]]:
        domain = yield run(bp, raw)
        return Ok(f"Processed: {domain}")

    ok = workflow("alice@example.com")
    assert ok.unwrap() == "Processed: example.com"

    err = workflow("bad")
    assert err.is_err()

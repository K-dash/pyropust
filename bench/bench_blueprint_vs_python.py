from __future__ import annotations

import os
import statistics
import sys
import timeit
from collections.abc import Callable
from dataclasses import dataclass

from pyropust import Blueprint, Op, run


@dataclass(frozen=True)
class Case:
    name: str
    build_bp: Callable[[], Blueprint[str, str]]
    py_fn: Callable[[str], str]


def _pipeline_py(input_text: str, pipe_count: int) -> str:
    value = input_text
    for _ in range(pipe_count):
        value = value.split(",")[0].upper()
    return value


def _pipeline_bp(pipe_count: int) -> Blueprint[str, str]:
    bp = Blueprint.for_type(str)
    for _ in range(pipe_count):
        bp = (
            bp.pipe(Op.text.split(","))
            .pipe(Op.seq.index(0))
            .pipe(Op.coerce.expect_str())
            .pipe(Op.text.to_uppercase())
        )
    return bp


def _tiny_py(input_text: str) -> str:
    return input_text.upper()


def _tiny_bp() -> Blueprint[str, str]:
    return Blueprint.for_type(str).pipe(Op.text.to_uppercase())


def _multi_run_py(input_text: str, pipe_count: int) -> str:
    value = input_text
    bp = (
        Blueprint.for_type(str)
        .pipe(Op.text.split(","))
        .pipe(Op.seq.index(0))
        .pipe(Op.coerce.expect_str())
        .pipe(Op.text.to_uppercase())
    )
    for _ in range(pipe_count):
        result = run(bp, value)
        if result.is_err():
            raise RuntimeError(f"Blueprint failed: {result.unwrap_err().message}")
        value = result.unwrap()
    return value


def _cases(pipe_count: int) -> list[Case]:
    return [
        Case(
            name="pipeline",
            build_bp=lambda: _pipeline_bp(pipe_count),
            py_fn=lambda s: _pipeline_py(s, pipe_count),
        ),
        Case(
            name="tiny_op",
            build_bp=_tiny_bp,
            py_fn=_tiny_py,
        ),
        Case(
            name="multi_run",
            build_bp=lambda: _pipeline_bp(pipe_count),
            py_fn=lambda s: _multi_run_py(s, pipe_count),
        ),
    ]


SIZES = {
    "small": "foo,bar,baz" * 8,  # ~88B
    "medium": "foo,bar,baz," * 400,  # ~4.8KB
    "large": "foo,bar,baz," * 8000,  # ~96KB
}

PIPE_COUNTS = [1, 5, 20]
REPEAT = 7
TARGET_TIME = 0.5


def _estimate_number(stmt: str, setup: str, globals_: dict[str, object], target_time: float) -> int:
    number = 10
    while True:
        elapsed = timeit.timeit(stmt, setup=setup, number=number, globals=globals_)
        if elapsed >= target_time:
            return number
        number *= 2


def _time_case(
    stmt: str, setup: str, globals_: dict[str, object], target_time: float, repeat: int
) -> tuple[float, int]:
    number = _estimate_number(stmt, setup, globals_, target_time)
    samples = timeit.repeat(stmt, setup=setup, number=number, repeat=repeat, globals=globals_)
    return statistics.median(samples), number


def _verify_output(py_fn: Callable[[str], str], bp: Blueprint[str, str], input_text: str) -> None:
    py_out = py_fn(input_text)
    bp_out = run(bp, input_text)
    if bp_out.is_err():
        raise RuntimeError(f"Blueprint failed: {bp_out.unwrap_err().message}")
    if py_out != bp_out.unwrap():
        raise AssertionError("Python and Blueprint outputs differ")


def _emit(line: str = "") -> None:
    sys.stdout.write(f"{line}\n")


def main() -> None:
    repeat = int(os.environ.get("BENCH_REPEAT", REPEAT))
    target_time = float(os.environ.get("BENCH_TARGET_TIME", TARGET_TIME))
    pipe_counts_raw = os.environ.get("BENCH_PIPE_COUNTS")
    if pipe_counts_raw:
        pipe_counts = [int(v) for v in pipe_counts_raw.split(",") if v.strip()]
    else:
        pipe_counts = PIPE_COUNTS
    sizes_raw = os.environ.get("BENCH_SIZES")
    if sizes_raw:
        size_names = [v.strip() for v in sizes_raw.split(",") if v.strip()]
    else:
        size_names = list(SIZES.keys())
    cases_raw = os.environ.get("BENCH_CASES")
    case_names = {v.strip() for v in cases_raw.split(",") if v.strip()} if cases_raw else None

    _emit("Blueprint vs Python (seconds, lower is better)")
    _emit(f"repeat={repeat}, target_time~{target_time}s per measurement")
    _emit("Blueprint is built in setup; timing measures run() only.")
    _emit()

    for size_name in size_names:
        input_text = SIZES[size_name]
        _emit(f"== {size_name} ==")
        for pipe_count in pipe_counts:
            _emit(f"-- pipe_count={pipe_count} --")
            for case in _cases(pipe_count):
                if case_names and case.name not in case_names:
                    continue
                bp = case.build_bp()
                _verify_output(case.py_fn, bp, input_text)

                globals_: dict[str, object] = {
                    "INPUT_TEXT": input_text,
                    "PIPE_COUNT": pipe_count,
                    "bp": bp,
                    "run": run,
                    "py_fn": case.py_fn,
                }

                setup_py = ""
                setup_bp = ""
                stmt_py = "py_fn(INPUT_TEXT)"
                stmt_bp = "run(bp, INPUT_TEXT)"

                py_time, py_number = _time_case(stmt_py, setup_py, globals_, target_time, repeat)
                bp_time, bp_number = _time_case(stmt_bp, setup_bp, globals_, target_time, repeat)
                ratio = bp_time / py_time if py_time else float("inf")

                _emit(
                    f"{case.name:>10} | python: {py_time:.6f}s (n={py_number}) | "
                    f"blueprint: {bp_time:.6f}s (n={bp_number}) | ratio: {ratio:.2f}x"
                )
            _emit()
        _emit()


if __name__ == "__main__":
    main()

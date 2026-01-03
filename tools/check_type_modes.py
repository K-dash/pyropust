"""Check type behavior for mode1/mode2/mode3 against a probe file.

Mode1: E自由 (Ok[T, E] -> Result[T, E])
Mode2: E非露出 (ResultT[T] = Result[T, Error[ErrorCode]])
Mode3: phantom Ok (Ok[T, CodeT] -> Result[T, Error[CodeT]])
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT_PYI = ROOT / "pyropust" / "__init__.pyi"
NATIVE_STUB = ROOT / "pyropust" / "pyropust_native.pyi"
PROBE = ROOT / "tests" / "typing" / "type_mode_probe.py"
PROBE_MODE2B = ROOT / "tests" / "typing" / "type_mode_probe_mode2b.py"


OK_MARKER = "def Ok"


def _run(cmd: list[str]) -> int:
    return subprocess.run(cmd, check=False).returncode  # noqa: S603


def _gen_native_stub() -> None:
    code = _run(["python3", str(ROOT / "tools" / "gen_native_stub.py")])
    if code != 0:
        raise SystemExit(code)


def _mode1(text: str) -> str:
    # Replace Ok overloads / signature with E-generic Ok.
    lines: list[str] = []
    src = text.splitlines()
    i = 0
    while i < len(src):
        line = src[i]
        if line.lstrip().startswith("@overload"):
            # Skip @overload if next non-empty line is def Ok
            j = i + 1
            while j < len(src) and src[j].strip() == "":
                j += 1
            if j < len(src) and src[j].lstrip().startswith("def Ok"):
                i += 1
                continue
        if line.lstrip().startswith("def Ok"):
            lines.append("def Ok[T, E](value: T) -> Result[T, E]: ...")
            i += 1
            continue
        lines.append(line)
        i += 1
    return "\n".join(lines) + "\n"


def _mode2(text: str) -> str:
    # Keep Result generic but add a public alias and pin Ok to it.
    lines: list[str] = []
    src = text.splitlines()
    inserted_alias = False
    i = 0
    while i < len(src):
        line = src[i]
        if line.lstrip().startswith("@overload"):
            # Skip @overload if next non-empty line is def Ok
            j = i + 1
            while j < len(src) and src[j].strip() == "":
                j += 1
            if j < len(src) and src[j].lstrip().startswith("def Ok"):
                i += 1
                continue
        if not inserted_alias and line.startswith("class Result"):
            lines.append("type ResultT[T] = Result[T, Error[ErrorCode]]")
            inserted_alias = True
        if line.lstrip().startswith("def Ok"):
            lines.append("def Ok[T](value: T) -> ResultT[T]: ...")
            i += 1
            continue
        lines.append(line)
        i += 1
    if not inserted_alias:
        lines.append("type ResultT[T] = Result[T, Error[ErrorCode]]")
    return "\n".join(lines) + "\n"


def _mode3(text: str) -> str:
    # Phantom generic Ok: infer CodeT from context (no _code_type param).
    lines: list[str] = []
    src = text.splitlines()
    i = 0
    while i < len(src):
        line = src[i]
        if line.lstrip().startswith("@overload"):
            # Skip @overload if next non-empty line is def Ok
            j = i + 1
            while j < len(src) and src[j].strip() == "":
                j += 1
            if j < len(src) and src[j].lstrip().startswith("def Ok"):
                i += 1
                continue
        if line.lstrip().startswith("def Ok"):
            lines.append("def Ok[T, CodeT: ErrorCode](value: T) -> Result[T, Error[CodeT]]: ...")
            i += 1
            continue
        lines.append(line)
        i += 1
    return "\n".join(lines) + "\n"


def _mode2b(text: str) -> str:
    # Error-only (non-generic) variant: Error has no CodeT.
    # Replace Error[CodeT] -> Error, and CodeT parameters -> str.
    out = text
    out = out.replace("class Error[CodeT: ErrorCode]:", "class Error:")
    out = out.replace("Error[CodeT]", "Error")
    out = out.replace("Error[ErrorCode]", "Error")
    out = out.replace("code: CodeT", "code: str")
    out = out.replace("code: CodeT | str", "code: str")
    out = out.replace("str | str", "str")
    out = out.replace("def Err[CodeT: ErrorCode](error: Error[CodeT])", "def Err(error: Error)")
    out = out.replace("def err[CodeT: ErrorCode](", "def err(")
    out = out.replace("def bail[CodeT: ErrorCode](", "def bail(")
    out = out.replace("def ensure[CodeT: ErrorCode](", "def ensure(")
    out = out.replace("-> Result[T_co, Error[CodeT]]", "-> Result[T_co, Error]")
    out = out.replace("-> Result[U, Error[CodeT]]", "-> Result[U, Error]")
    out = out.replace("-> Result[Option[U], Error[CodeT]]", "-> Result[Option[U], Error]")
    out = out.replace("Result[T_co, Error[CodeT]]", "Result[T_co, Error]")
    out = out.replace("Result[U, Error[CodeT]]", "Result[U, Error]")
    out = out.replace("Result[Option[U], Error[CodeT]]", "Result[Option[U], Error]")
    out = out.replace("Result[Never, Error[CodeT]]", "Result[Never, Error]")
    out = out.replace("Result[None, Error[CodeT]]", "Result[None, Error]")
    out = out.replace("-> Error[CodeT]", "-> Error")
    out = out.replace("Error[CodeT]", "Error")
    out = out.replace("Error[CodeT] | None", "Error | None")
    out = out.replace("Error[CodeT],", "Error,")
    out = out.replace("Error[CodeT])", "Error)")
    out = out.replace("CodeT: ErrorCode", "")
    # Clean up dangling type parameter lists like [U, ] after CodeT removal.
    out = re.sub(r"\[([A-Za-z0-9_]+),\s*\]", r"[\1]", out)
    out = re.sub(r"\[\s*,\s*([A-Za-z0-9_]+)\]", r"[\1]", out)
    out = re.sub(r"(def\s+[A-Za-z0-9_]+)\[\]\(", r"\1(", out)
    out = re.sub(r"(class\s+[A-Za-z0-9_]+)\[\]\:", r"\1:", out)
    return out  # noqa: RET504


def _write_probe_mode2b() -> None:
    # Create a probe variant that uses non-generic Error.
    text = PROBE.read_text()
    text = text.replace("Error[Code]", "Error")
    text = text.replace("Error[ErrorCode]", "Error")
    text = text.replace("Result[int, Error[Code]]", "Result[int, Error]")
    text = text.replace("Result[str, Error[Code]]", "Result[str, Error]")
    text = text.replace("Result[int, Error[ErrorCode]]", "Result[int, Error]")
    PROBE_MODE2B.write_text(text)


def _check(label: str, probe: Path) -> None:
    print(f"\n=== {label} ===")  # noqa: T201
    mypy_code = _run(["uv", "run", "mypy", "--strict", str(probe)])
    pyright_code = _run(["uv", "run", "pyright", str(probe)])
    print(f"[{label}] mypy exit: {mypy_code}, pyright exit: {pyright_code}")  # noqa: T201


def main() -> None:
    original = INIT_PYI.read_text()
    try:
        # Mode 1
        INIT_PYI.write_text(_mode1(original))
        _gen_native_stub()
        _check("mode1 (E自由)", PROBE)

        # Mode 2
        INIT_PYI.write_text(_mode2(original))
        _gen_native_stub()
        _check("mode2 (E非露出)", PROBE)

        # Mode 3 (phantom Ok)
        INIT_PYI.write_text(_mode3(original))
        _gen_native_stub()
        _check("mode3 (phantom Ok)", PROBE)

        # Mode 2b (Error only)
        INIT_PYI.write_text(_mode2b(original))
        _gen_native_stub()
        _write_probe_mode2b()
        _check("mode2b (Error only)", PROBE_MODE2B)
    finally:
        INIT_PYI.write_text(original)
        _gen_native_stub()
        if PROBE_MODE2B.exists():
            PROBE_MODE2B.unlink()


if __name__ == "__main__":
    main()

# pyrope

A proof-of-concept library that brings Rust's `Result` and `Option` types to Python, treating failures as values instead of exceptions.

The concept: "Drop a rope (type safety from Rust) into the dangerous freedom of Python."

## Why Not Exceptions?

1. **Explicit control flow**: Treat failures as values, not control flow jumps
2. **No implicit None**: Force explicit `unwrap()` or `is_some()` checks
3. **Rust-like short-circuiting**: Reproduce Rust's `?` operator in Python using generators

## Direct Usage

You can use `Result` and `Option` types directly for manual handling or functional chaining, just like in Rust.

### Manual Handling

```python
from pyrope import Ok, Err, Result

def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

res = divide(10, 2)
if res.is_ok():
    print(f"Success: {res.unwrap()}")  # Success: 5.0
else:
    print(f"Failure: {res.unwrap_err()}")
```

### Functional Chaining (`map`, `and_then`)

Avoid `if` checks by chaining operations.

```python
from pyrope import Ok

res = (
    Ok("123")
    .map(int)                # Result[int, E]
    .map(lambda x: x * 2)    # Result[int, E]
    .and_then(lambda x: Ok(f"Value is {x}"))
)
print(res.unwrap())  # "Value is 246"
```

> **Type Hint for `and_then`**: When using `and_then` with a callback that may return `Err`, define the initial `Result` with an explicit return type annotation. This ensures the error type is correctly inferred.
>
> ```python
> from pyrope import Ok, Err, Result
>
> def fetch_data() -> Result[int, str]:  # Declare error type here
>     return Ok(42)
>
> def validate(x: int) -> Result[int, str]:
>     return Err("invalid") if x < 0 else Ok(x)
>
> # Error type flows correctly through the chain
> result = fetch_data().and_then(validate)
> ```

### Option Type (Safe None Handling)

No more `AttributeError: 'NoneType' object has no attribute '...'`.

```python
from pyrope import Some, None_, Option

def find_user(user_id: int) -> Option[str]:
    return Some("Alice") if user_id == 1 else None_()

name_opt = find_user(1)
# You MUST check or unwrap explicitly
name = name_opt.unwrap_or("Guest")
print(f"Hello, {name}!")  # Hello, Alice!
```

## Blueprint (Batch Execution)

For performance-critical pipelines, use `Blueprint` to define a sequence of operations and execute them in a single Rust call. This reduces Python↔Rust boundary crossings, which can help in longer pipelines.

```python
from pyrope import Blueprint, Op, run

# Define a pipeline
bp = (
    Blueprint()
    .pipe(Op.split(","))
    .pipe(Op.index(0))
    .pipe(Op.expect_str())
    .pipe(Op.to_uppercase())
)

# Execute with type-safe error handling
result = run(bp, "hello,world")
if result.is_ok():
    print(result.unwrap())  # "HELLO"
else:
    print(f"Error: {result.unwrap_err().message}")
```

### Operators

Supported operators are listed in [docs](docs/operations.md).

`Op.json_decode()` enables a fast Rust JSON path when it is the first operator in a Blueprint. `Op.map_py(...)` runs a Python callback inside the pipeline (slower, but flexible). If the callback raises, the error becomes `RopeError` with code `py_exception`, and the traceback is stored in `err.metadata["py_traceback"]`.

Note: `Blueprint.for_type(...)` is a type-hinting helper for Python type checkers. It does not enforce runtime type checks.

### Benchmark (reproducible, no extra deps)

Run the included `timeit` benchmark to compare a pure-Python pipeline vs `Blueprint` in seconds. The benchmark builds the Blueprint in setup and measures `run()` only, reporting median timings:

```bash
uv run python bench/bench_blueprint_vs_python.py
```

Note: Small inputs or short pipelines may show little difference; multi-stage pipelines are where boundary reduction tends to help.

`multi_run` compares repeatedly calling `run()` on a single-op Blueprint vs a single `run()` over a multi-op Blueprint (measures boundary-crossing overhead).

Latest run (macOS arm64, Python 3.14.0, BENCH_TARGET_TIME=0.2, BENCH_REPEAT=5, BENCH_SIZES=medium,large, BENCH_PIPE_COUNTS=20, BENCH_CASES=pipeline,tiny_op,multi_run):

```
Blueprint vs Python (seconds, lower is better)
repeat=5, target_time~0.2s per measurement
Blueprint is built in setup; timing measures run() only.

== medium ==
-- pipe_count=20 --
  pipeline | python: 0.371662s (n=20480) | blueprint: 0.362132s (n=2560) | ratio: 0.97x
   tiny_op | python: 0.248113s (n=163840) | blueprint: 0.341658s (n=163840) | ratio: 1.38x
 multi_run | python: 0.253638s (n=1280) | blueprint: 0.344409s (n=2560) | ratio: 1.36x

== large ==
-- pipe_count=20 --
  pipeline | python: 0.215668s (n=640) | blueprint: 0.423312s (n=160) | ratio: 1.96x
   tiny_op | python: 0.286244s (n=10240) | blueprint: 0.262916s (n=20480) | ratio: 0.92x
 multi_run | python: 0.371366s (n=160) | blueprint: 0.182248s (n=80) | ratio: 0.49x
```

## Syntactic Sugar: `@do` Decorator

Generator-based short-circuiting reproduces Rust's `?` operator in Python.

```python
from pyrope import Ok, Result, do

@do
def process(value: str) -> Result[str, object]:
    text = yield Ok(value)  # Type checkers infer 'text' as str
    upper = yield Ok(text.upper())
    return Ok(f"Processed: {upper}")

print(process("hello").unwrap())  # "Processed: HELLO"
```

## Border Control: Exception Interoperability

Real-world Python code uses libraries like `requests`, `boto3`, and `sqlalchemy` that throw exceptions. pyrope provides tools to safely bridge between the "exception world" and the "Result world".

### Converting Exceptions to Results: `@catch`

Use `@catch` to wrap exception-throwing code and convert it into safe `Result` values.

```python
from pyrope import catch
import requests

# Wrap existing libraries that throw exceptions
@catch(requests.RequestException)
def fetch_data(url: str) -> dict:
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Now returns Result[dict, RopeError] instead of raising
result = fetch_data("https://api.example.com/data")
if result.is_ok():
    data = result.unwrap()
else:
    print(f"Failed to fetch: {result.unwrap_err().message}")
```

**When to use:**

- Wrapping third-party libraries that throw exceptions
- Creating safe boundaries around risky I/O operations
- Gradually introducing pyrope into existing codebases

You can also use `@catch` without arguments to catch all exceptions, or use `Result.attempt()` directly:

```python
from pyrope import Result

# Inline exception handling
result = Result.attempt(lambda: int("not-a-number"), ValueError)
# Returns Err(RopeError) instead of raising ValueError
```

### Converting Results to Exceptions: `unwrap_or_raise`

At the edges of your application (e.g., web framework endpoints), you may need to convert `Result` back into exceptions.

```python
from pyrope import Result, do, catch
from fastapi import FastAPI, HTTPException

app = FastAPI()

@catch(ValueError, KeyError)
def parse_user_input(data: dict) -> dict:
    return {
        "age": int(data["age"]),
        "name": data["name"],
    }

@app.post("/users")
def create_user(data: dict):
    result = parse_user_input(data)

    # Convert Result to exception at the framework boundary
    parsed = result.unwrap_or_raise(
        HTTPException(status_code=400, detail="Invalid input")
    )

    return {"user": parsed}
```

**When to use:**

- Framework endpoints (FastAPI, Flask, Django)
- CLI tools that need to exit with error codes
- Any boundary where exceptions are the expected error handling mechanism

## Type Checker Support

- **Pyright**: Primary focus - verifies that `yield` correctly infers types
- **MyPy**: Strict mode compatibility verified

## Installation

### Requirements

- Python 3.12+
- Rust toolchain (pinned via `rust-toolchain.toml`)
- [uv](https://github.com/astral-sh/uv)
- [cargo-make](https://github.com/sagiegurari/cargo-make)

### Setup

```bash
# Install dependencies and build extension
uv sync
makers dev

# Or run everything at once
makers ci
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code generation system, and testing guidelines.

## License

This is a proof-of-concept project and is not intended for production use.

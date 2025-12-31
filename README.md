# pyropust

A proof-of-concept library that brings Rust's `Result` and `Option` types to Python, treating failures as values instead of exceptions.

The concept: "A robust rope for your Python orchestration. Drop a Ropust into the dangerous freedom of Python."

## Who This Is For

Pyropust is for Python developers who want explicit, type-safe control over error flow and data transformations, especially when bridging Python and Rust or when pipelines become hard to reason about with exceptions alone.

Common problems it helps with:

- Making error propagation explicit and type-checked (Result/Option).
- Defining typed, composable pipelines with predictable failure modes (Blueprint).
- Keeping Python↔Rust boundaries safe without scattering try/except logic.

## Why Not Exceptions?

1. **Explicit control flow**: Treat failures as values, not control flow jumps.
2. **Error Locality**: Handle errors exactly where they happen, making the code easier to trace.
3. **No implicit None**: Force explicit `unwrap()` or `is_some()` checks.
4. **Railway Oriented**: Naturally build linear pipelines where data flows or short-circuits safely.using generators

## Quick Start

Start small and adopt features gradually:

1. Wrap exceptions with `@catch` to get `Result`.
2. Use `Result`/`Option` explicitly in Python code.
3. Use `@do` for short-circuiting chains.
4. Introduce `Blueprint` for typed pipelines.

## Direct Usage

You can use `Result` and `Option` types directly for manual handling or functional chaining, just like in Rust.

### Manual Handling

```python
from pyropust import Ok, Err, Result

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
from pyropust import Ok

res = (
    Ok("123")
    .map(int)                # Result[int, E]
    .map(lambda x: x * 2)    # Result[int, E]
    .and_then(lambda x: Ok(f"Value is {x}"))
)
print(res.unwrap())  # "Value is 246"
```

> [!TIP]
> **Type Hint for `and_then`**: When using `and_then` with a callback that may return `Err`, define the initial `Result` with an explicit return type annotation. This ensures the error type is correctly inferred.
>
> ```python
> from pyropust import Ok, Err, Result
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
from pyropust import Some, None_, Option

def find_user(user_id: int) -> Option[str]:
    return Some("Alice") if user_id == 1 else None_()

name_opt = find_user(1)
# You MUST check or unwrap explicitly
name = name_opt.unwrap_or("Guest")
print(f"Hello, {name}!")  # Hello, Alice!
```

## Blueprint (Typed Pipelines)

Use `Blueprint` to define a typed, composable pipeline with explicit error handling. The primary value is clarity and type-safety across a sequence of operations. Performance can improve in some cases, but it is not guaranteed and should be treated as a secondary benefit.

```python
from pyropust import Blueprint, Op, run

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

### Operators & Integration

Pyropust provides built-in operators to handle common data tasks safely in Rust, while allowing flexible escape hatches to Python.

#### Core Operators

- **`Op.json_decode()`**: Enables a **Turbo JSON Path** (high-performance Rust parsing) when used as the first operator in a Blueprint.
- **`Op.map_py(fn)`**: Runs a custom Python callback within the pipeline. It’s a "safety hatch"—if the callback raises an exception, it is caught and converted into a `RopustError` (code: `py_exception`) with the original traceback stored in `metadata["py_traceback"]`.
- **Built-in logic**: Includes `as_str()`, `as_int()`, `split()`, `index()`, `get()`, and `to_uppercase()`. See [docs/operations.md](docs/operations.md) for the full list.

#### Design Principles

- **Type-safe construction**: `Blueprint.for_type(T)` is a helper for static type checkers (Pyright/Mypy). It provides zero-runtime-overhead type hinting.
- **Exception Bridge**: Use `exception_to_ropust_error()` to normalize external exceptions (like `requests.Error`) into a consistent `RopustError` format.

> [!NOTE]
> **Why a shared error format?**
> By unifying errors into `RopustError`, you get a consistent interface across Python and Rust. You can reliably access fields like `path`, `expected`, and `got` without losing context (like Python tracebacks) during pipeline orchestration. See [docs/errors.md](docs/errors.md) for details.

## Syntactic Sugar: `@do` Decorator

Generator-based short-circuiting reproduces Rust's `?` operator in Python.

```python
from pyropust import Ok, Result, do

@do
def process(value: str) -> Result[str, object]:
    text = yield Ok(value)  # Type checkers infer 'text' as str
    upper = yield Ok(text.upper())
    return Ok(f"Processed: {upper}")

print(process("hello").unwrap())  # "Processed: HELLO"
```

## Border Control: Exception Interoperability

Real-world Python code uses libraries like `requests`, `boto3`, and `sqlalchemy` that throw exceptions. pyropust provides tools to safely bridge between the "exception world" and the "Result world".

### Converting Exceptions to Results: `@catch`

Use `@catch` to wrap exception-throwing code and convert it into safe `Result` values.

```python
from pyropust import catch
import requests

# Wrap existing libraries that throw exceptions
@catch(requests.RequestException)
def fetch_data(url: str) -> dict:
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Now returns Result[dict, RopustError] instead of raising
result = fetch_data("https://api.example.com/data")
if result.is_ok():
    data = result.unwrap()
else:
    print(f"Failed to fetch: {result.unwrap_err().message}")
```

**When to use:**

- Wrapping third-party libraries that throw exceptions
- Creating safe boundaries around risky I/O operations
- Gradually introducing pyropust into existing codebases

You can also use `@catch` without arguments to catch all exceptions, or use `Result.attempt()` directly:

```python
from pyropust import Result

# Inline exception handling
result = Result.attempt(lambda: int("not-a-number"), ValueError)
# Returns Err(RopustError) instead of raising ValueError
```

### Converting Results to Exceptions: `unwrap_or_raise`

At the edges of your application (e.g., web framework endpoints), you may need to convert `Result` back into exceptions.

```python
from pyropust import Result, do, catch
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

## Benchmarks

Performance is workload-dependent. The primary value of `Blueprint` is type-safety and composability, not guaranteed speedups.

Run the included benchmark:

```bash
uv run python bench/bench_blueprint_vs_python.py
```

Key findings:

- Performance varies by workload; some cases are slower, some are comparable, and some benefit from fewer boundary crossings.
- Larger pipelines and repeated runs can show improvements, but tiny operators can be slower.
- Treat benchmarks as measurements, not a promise of speedups.

**For detailed results and methodology, see [docs/benchmarks.md](docs/benchmarks.md).**

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025 K-dash

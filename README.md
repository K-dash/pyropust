# pyropust

[![Python versions](https://img.shields.io/pypi/pyversions/pyropust.svg)](https://pypi.org/project/pyropust/)
[![PyPI](https://img.shields.io/pypi/v/pyropust.svg?color=blue)](https://pypi.org/project/pyropust/)

**Rust-powered, type-safe pipelines for Python.**

pyropust bridges the messy, exception-heavy reality of Python with the explicit, composable world of Rust’s `Result / Option`.

This is **not just another Result library**.

pyropust is built around three core ideas:

- **Blueprints** — typed, declarative data-processing pipelines
- **Rust operators** — hot-path operations (e.g. JSON decoding) executed safely and efficiently in Rust
- **Exception boundaries** — explicit normalization of Python exceptions into `Result`

If you have ever thought:

> “I want Rust-like error flow, but I live in Python and can’t avoid exceptions”

pyropust is designed for you.

## Why pyropust exists

Python already has multiple `Result / Option` libraries. The problem is not representation — it is integration.

In real Python systems:

- Most libraries raise exceptions (`requests`, `boto3`, `sqlalchemy`, ...)
- Data transformation is written as long chains of `try/except`
- Type checkers lose track of what can fail and where

pyropust treats exceptions as an external reality and provides a structured boundary where they are captured, typed, and composed.

## Why not exceptions?

Exceptions are great for failures that should abort the current operation. They are less suitable for orchestration and pipelines:

- They hide control flow in call stacks
- They complicate typed composition across steps
- They are hard to make explicit at module boundaries

pyropust makes failures **values** so they can be composed, transformed, and tested like data.

## Adoption path

You do not need to switch everything at once. A realistic path is:

1. Wrap exceptions with `@catch`
2. Use `Result / Option` explicitly in Python code
3. Use `@do` for structured propagation
4. Introduce `Blueprint` for typed pipelines

## Key concepts

### 1) Result and Option

Rust-style `Result[T]` and `Option[T]` as first-class values.

```python
from pyropust import Ok, Err, Some, None_

value = Ok(10)
error = Err("boom")

maybe = Some(42)
empty = None_()
```

Result is explicit about failures. All failures are represented as `RopustError`. You can return it from functions and branch on `is_ok / is_err` without exceptions.
Note: `unwrap()` is intended for tests, examples, and application boundaries. Inside libraries and pipelines, prefer structured propagation (`@do`, `context`, `and_then`).

```python
from pyropust import Ok, Err, Result

def divide(a: int, b: int) -> Result[float]:
    if b == 0:
        return Err("division by zero")
    return Ok(a / b)

res = divide(10, 2)
if res.is_ok():
    value = res.unwrap()
else:
    error = res.unwrap_err()
    print(error.message)
```

This pattern is useful for explanation and testing. In real code, prefer structured propagation with `@do`, combinators, or boundary helpers.

Keep Option short and explicit: you must unwrap or provide defaults.

```python
from pyropust import Some, None_, Option

def find_user(user_id: int) -> Option[str]:
    return Some("alice") if user_id == 1 else None_()

user = find_user(1)
name = user.unwrap_or("guest")

missing = find_user(2)
name2 = missing.unwrap_or("guest")
```

Unlike `Optional[T]` (which is only a type hint), `Option[T]` is a runtime value that forces explicit handling.

#### Functional Chaining (`map`, `and_then`)

Avoid `if` checks by chaining operations.

```python
from pyropust import Ok

res = (
    Ok("123")
    .map(int)                # Result[int]
    .map(lambda x: x * 2)    # Result[int]
    .and_then(lambda x: Ok(f"Value is {x}"))
)
print(res.unwrap())  # "Value is 246"
```

When to use: `map/and_then` is best for small, expression-style transforms where each step is a function.

> [!TIP]
> **Type Hint for `and_then`**: When using `and_then` with a callback that may return `Err`, define the initial `Result` with an explicit return type annotation. This ensures the Ok type is correctly inferred.
>
> ```python
> from pyropust import Ok, Err, Result
>
> def fetch_data() -> Result[int]:  # Declare ok type here
>     return Ok(42)
>
> def validate(x: int) -> Result[int]:
>     return Err("invalid") if x < 0 else Ok(x)
>
> # Error type flows correctly through the chain
> result = fetch_data().and_then(validate)
> ```

#### Adding context and error codes

In real applications, errors often need additional context as they move up the stack.
pyropust provides helpers inspired by Rust’s `context` and error mapping patterns.

```python
from pyropust import Result, Err

def load_config(path: str) -> Result[str]:
    return Err("file not found")

result = load_config("/etc/app.toml").context(
    "failed to load application config",
    code="config.load",
)
```

- `context(...)` adds human-readable context while preserving the original cause
- The original error is kept as a structured cause chain

You can also modify error codes for classification and observability:

```python
result = load_config("/etc/app.toml").with_code("config.not_found")

result = load_config("/etc/app.toml").map_err_code("startup")
```

Error codes are stable, machine-facing identifiers.
Messages are for humans and may change; codes are for branching, testing, and observability.

These helpers make it easy to:

- Add meaning at higher layers
- Classify failures without losing detail
- Keep error handling explicit and testable

### 2) Blueprint: typed pipelines

A **Blueprint** is a declarative pipeline that describes what happens to data, not how it is wired together.

```python
from pyropust import Blueprint, Op

bp = (
    Blueprint.for_type(str)
    .pipe(Op.json_decode())
    .pipe(Op.get("user"))
    .pipe(Op.get("id"))
)
```

Characteristics:

- **Typed**: `Blueprint.for_type(T)` gives static analyzers a concrete starting point
- **Composable**: pipelines are values, not control flow
- **No runtime type checks**: types are for humans and tools, not runtime checks

Blueprints are the primary abstraction of pyropust.

Blueprints are inert definitions. Use `run(bp, value)` to execute them, typically inside an exception boundary.

Only a core set of basic operators is supported today; see the full list in [docs/operations.md](docs/operations.md).

### 3) Rust operators (hot paths)

Some operations are performance-critical and error-prone. pyropust implements these as Rust-backed operators:

- `Op.json_decode()`
- (future) `Op.base64_decode()`, `Op.url_parse()`, ...

Benefits:

- Faster execution for hot paths
- Consistent error semantics
- No Python-level exceptions leaking through the pipeline

You can always fall back to Python:

```python
bp = bp.pipe(Op.map_py(lambda x: x + 1))
```

Rust where it matters, Python where it’s convenient.

### 4) Exception boundaries (`@catch`)

Python exceptions are unavoidable. pyropust makes them explicit.

```python
from pyropust import Blueprint, Op, catch, run

bp = (
    Blueprint.for_type(str)
    .pipe(Op.json_decode())
    .pipe(Op.get("value"))
)

@catch
def load_value(payload: str):
    return run(bp, payload)
```

Inside the boundary:

- Exceptions are captured
- Normalized into `Err`
- Enriched with traceback metadata (`py_traceback`)

Outside the boundary:

- No hidden control flow
- Failures are values

This makes error flow visible, testable, and composable.

### 5) `@do`: Rust-like `?` for Python

The `@do` decorator enables linear, Rust-style propagation of `Result`.

```python
from pyropust import Ok, Result, do

@do
def process(data: str) -> Result[str]:
    text = yield Ok(data)
    return Ok(text.upper())
```

When to use: `@do` reads like imperative code and is better when you need intermediate variables, early returns, or mixed steps.
Prefer `context` for adding meaning instead of catching exceptions.

This is not syntax sugar over exceptions — it is structured propagation of `Result` values.

## Framework boundaries

You can safely use pyropust in frameworks that expect exceptions by converting `Result` back into exceptions at the boundary.

```python
from fastapi import FastAPI, HTTPException
from pyropust import Result, catch

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

## Installation

> pyropust is currently experimental.

```bash
pip install pyropust
```

Supported:

- Python 3.10+
- CPython (wheels provided)

Note: Some platforms may require a Rust toolchain to build from source.

## Minimal example (30 seconds)

```python
from pyropust import Blueprint, Op, catch, run

bp = (
    Blueprint.for_type(str)
    .pipe(Op.json_decode())
    .pipe(Op.get("value"))
)

@catch
def run_value(payload: str):
    return run(bp, payload)

result = run_value('{"value": 123}')
```

- No `try/except`
- Failures are explicit
- The pipeline is reusable and testable

## Documentation

- [Operators](docs/operations.md)
- [Errors](docs/errors.md)
- [Benchmarks](docs/benchmarks.md)

## Non-goals

pyropust intentionally does not aim to:

- Replace Python exceptions everywhere
- Be a general-purpose FP toolkit
- Hide Python’s dynamic nature

It is a boundary and pipeline tool, not a new language.

## Roadmap

- More Rust-backed operators
- Benchmark suite and published numbers
- Better IDE / type-checker ergonomics
- Stabilization of public APIs

## Stability

- APIs may change before 1.0
- Semantic versioning will start at 1.0
- Breaking changes will be documented

## License

MIT

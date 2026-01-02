# Contributing to pyropust

Thank you for your interest in contributing! This document provides guidelines and instructions for development.

## Development Setup

### Prerequisites

- Python 3.12+
- Rust toolchain (pinned via `rust-toolchain.toml`)
- [uv](https://github.com/astral-sh/uv) for Python package management
- [cargo-make](https://github.com/sagiegurari/cargo-make) for task automation

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/K-dash/pyropust.git
cd pyropust

# Install Python dependencies
uv sync

# Build the Rust extension
makers dev
```

## Development Commands

All development tasks are managed via `cargo-make`. In practice, contributors should use `makers` for nearly everything.

### Recommended workflow

```bash
makers                  # Full pipeline (gen + build + format + lint + test)
makers dev              # Faster dev build (maturin develop)
makers clean            # Clean build artifacts
```

If you need a specific task beyond the above, check `Makefile.toml` for the full list.

### Code Generation

The only generated artifact is the native stub:

```bash
makers gen-native-stub   # Generate pyropust_native.pyi from __init__.pyi
makers check-gen         # Verify generated code is up-to-date
```

## Type Safety Principles

1. **Prefer `@do` for structured propagation**: keep error flow explicit and typed
2. **Use `*_try` for exception-prone callbacks**: `map_try` / `and_then_try` are the boundary
3. **Keep error codes stable**: they are for branching/testing, messages are for humans

### Type Checker Tests

Located in `tests/typing/`, these tests verify that type checkers correctly infer types:

```python
from typing import assert_type
from pyropust import Error, ErrorCode, Ok, Result, err

class Code(ErrorCode):
    INVALID = "invalid"

def parse(value: str) -> Result[int, Error[Code]]:
    return Ok(int(value))

assert_type(parse("1"), Result[int, Error[Code]])
```

## CI Pipeline

CI runs the same `makers` pipeline used locally, so if it passes on your machine, it should pass in CI.

## Common Issues

### "Generated code is out of date"

Run `makers gen-native-stub` and commit the changes:

```bash
makers gen-native-stub
git add pyropust/pyropust_native.pyi
git commit -m "Update generated code"
```

### Build failures

```bash
# Clean and rebuild
makers clean
makers dev
```

## Questions?

Feel free to open an issue for any questions or suggestions!

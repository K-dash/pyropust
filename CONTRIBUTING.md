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
git clone https://github.com/USERNAME/rope.git
cd rope

# Install Python dependencies
uv sync

# Build the Rust extension
makers dev
```

## Development Commands

All development tasks are managed via `cargo-make`. Run `makers <task>` to execute a task.

### Build Tasks

```bash
makers dev               # Development build (maturin develop)
makers build             # Same as dev
makers build-release     # Build release wheel
makers clean             # Clean all build artifacts
```

### Code Generation

**Important**: This project uses automatic code generation for operators.

```bash
makers gen               # Generate Op class from src/ops/kind.rs
makers check-gen         # Verify generated code is up-to-date
```

The generator (`tools/gen_ops.py`) reads metadata from `src/ops/kind.rs` and generates:

1. `src/py/op_generated.rs` - Rust Op class implementation
2. `pyropust/__init__.pyi` - Python type stubs

**When adding a new operator:**

1. Add metadata to `src/ops/kind.rs`:

```rust
/// @op name=my_op py=my_op
/// @sig in=str out=int
/// @ns text
/// @param arg:str
MyOp { arg: String },
```

2. Add implementation to `src/ops/apply.rs`
3. Run `makers gen` to regenerate code
4. Run `makers all` to verify everything works

**When adding a new namespace (e.g., `@ns json`):**

1. Add operators with the new `@ns` tag in `src/ops/kind.rs`
2. Run `makers gen` - this automatically updates:
   - `src/py/op_generated.rs` (creates `OpJson` class)
   - `src/py/mod.rs` (adds export)
   - `src/lib.rs` (adds `m.add_class::<OpJson>()`)
   - `pyropust/__init__.pyi` (adds type stubs)
3. **Manual step**: Add `OpJson` to the `use py::{...}` import in `src/lib.rs`
4. Run `makers all` to verify everything works

### Formatting

```bash
makers rust-fmt          # Format Rust code
makers rust-fmt-check    # Check Rust formatting
makers ruff-fmt          # Format Python code
makers ruff-fmt-check    # Check Python formatting
makers fmt-all           # Format all code (Rust + Python)
```

### Linting

```bash
makers rust-clippy       # Run Rust linter (clippy)
makers ruff              # Run Python linter (ruff)
makers lint-all          # Run all linters
```

### Testing

```bash
makers rust-test         # Run Rust unit tests
makers pytest            # Run Python tests
makers mypy              # Run MyPy type checker (strict)
makers pyright           # Run Pyright type checker (strict)
makers test-all          # Run all tests (Rust + Python)
```

### CI/Complete Checks

```bash
makers check             # Run all checks (format, lint, test, gen)
makers all               # Run complete pipeline (gen + dev + check)
makers ci                # Same as all
```

## Code Generation System

The project uses a single source of truth (`src/ops/kind.rs`) for operator definitions.

### Metadata Format

```rust
/// @op name=<rust_name> py=<python_name>
/// @sig in=<input_type> out=<output_type>
/// @param <name>:<type>
OperatorVariant { field: RustType },
```

**Example:**

```rust
/// @op name=split py=split
/// @sig in=str out=list[str]
/// @param delim:str
Split { delim: String },
```

### What Gets Generated

1. **Rust (`src/py/op_generated.rs`)**:

```rust
#[pymethods]
impl Op {
    #[staticmethod]
    pub fn split(delim: String) -> Operator {
        Operator {
            kind: OperatorKind::Split { delim },
        }
    }
}
```

2. **Python Stub (`pyropust/__init__.pyi`)**:

```python
class Op:
    @staticmethod
    def split(delim: str) -> Operator[str, list[str]]: ...
```

### CI Integration

The CI automatically checks if generated code is up-to-date:

- `check-generated` job runs `makers gen` and verifies no diffs
- PRs that modify `kind.rs` without running `makers gen` will fail

## Project Structure

```
pyropust/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI
├── pyropust/                  # Python package
│   ├── __init__.py          # Public API
│   ├── __init__.pyi         # PEP 561 type stubs
│   ├── do.py                # @do decorator
│   ├── pyropust_native.pyi    # Internal native module stubs
│   └── py.typed             # PEP 561 marker
├── src/                     # Rust implementation
│   ├── lib.rs               # PyO3 module definition
│   ├── data/                # Value type and Python conversion
│   ├── ops/                 # Operator implementations
│   │   ├── kind.rs          # Operator metadata (SSOT)
│   │   ├── apply.rs         # Operator execution logic
│   │   └── error.rs         # Error handling
│   └── py/                  # PyO3 exposed classes
│       ├── blueprint.rs     # Blueprint class
│       ├── error.rs         # RopeError class
│       ├── op_generated.rs  # Generated Op class
│       ├── operator.rs      # Operator class
│       └── result.rs        # Result/Option classes
├── tests/
│   ├── test_blueprint.py    # Blueprint runtime tests
│   ├── test_runtime.py      # Result/Option tests
│   └── typing/              # Type checker tests
│       ├── test_typing_mypy.py
│       └── test_typing_pyright.py
├── tools/
│   └── gen_ops.py           # Code generator
├── Cargo.toml               # Rust dependencies
├── pyproject.toml           # Python project config
├── Makefile.toml            # cargo-make task definitions
└── rust-toolchain.toml      # Rust version pin
```

## Type Safety Principles

1. **`Op.assert_*` methods are validators, not converters**: They return `Err(RopeError)` if preconditions aren't met
2. **`Op.index` / `Op.get` return `object`**: Use `Op.expect_str()` or similar to narrow types
3. **`.pipe()` only connects compatible types**: Type checkers verify the pipeline at build time
4. **For dynamic input, use guards**: `Blueprint.any().guard_str()` explicitly narrows types

## Testing Guidelines

### Running Tests

```bash
# All tests
makers test-all

# Specific test suites
makers pytest              # Python runtime tests
makers mypy                # Type checking with MyPy
makers pyright             # Type checking with Pyright
makers rust-test           # Rust unit tests
```

### Type Checker Tests

Located in `tests/typing/`, these tests verify that type checkers correctly infer types:

```python
from typing import assert_type
from pyropust import Blueprint, Op

bp = Blueprint().pipe(Op.split(",")).pipe(Op.index(0))
assert_type(bp, Blueprint[str, object])
```

## CI Pipeline

The CI runs three parallel jobs:

1. **check-generated**: Verifies generated code is up-to-date
2. **rust**: Runs `cargo fmt`, `clippy`, and `test`
3. **python**: Runs Ruff, MyPy, Pyright, and Pytest

All jobs must pass for a PR to be merged.

## Common Issues

### "Generated code is out of date"

Run `makers gen` and commit the changes:

```bash
makers gen
git add src/py/op_generated.rs pyropust/__init__.pyi
git commit -m "Update generated code"
```

### Type checker errors after modifying operators

1. Ensure metadata in `src/ops/kind.rs` is correct
2. Run `makers gen` to regenerate stubs
3. Check that `pyropust/__init__.pyi` has the correct types

### Build failures

```bash
# Clean and rebuild
makers clean
makers dev
```

## Questions?

Feel free to open an issue for any questions or suggestions!

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
makers gen              # Regenerate operator bindings after editing kind.rs
makers clean            # Clean build artifacts
```

If you need a specific task beyond the above, check `Makefile.toml` for the full list.

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
4. Run `makers` to verify everything works

**When adding a new namespace (e.g., `@ns json`):**

1. Add operators with the new `@ns` tag in `src/ops/kind.rs`
2. Run `makers gen` - this automatically updates:
   - `src/py/op_generated.rs` (creates `OpJson` class)
   - `src/py/mod.rs` (adds export)
   - `src/lib.rs` (adds `m.add_class::<OpJson>()`)
   - `pyropust/__init__.pyi` (adds type stubs)
3. **Manual step**: Add `OpJson` to the `use py::{...}` import in `src/lib.rs`
4. Run `makers` to verify everything works

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

## Type Safety Principles

1. **`Op.assert_*` methods are validators, not converters**: They return `Err(RopustError)` if preconditions aren't met
2. **`Op.index` / `Op.get` return `object`**: Use `Op.expect_str()` or similar to narrow types
3. **`.pipe()` only connects compatible types**: Type checkers verify the pipeline at build time
4. **For dynamic input, use guards**: `Blueprint.any().guard_str()` explicitly narrows types

### Type Checker Tests

Located in `tests/typing/`, these tests verify that type checkers correctly infer types:

```python
from typing import assert_type
from pyropust import Blueprint, Op

bp = Blueprint().pipe(Op.split(",")).pipe(Op.index(0))
assert_type(bp, Blueprint[str, object])
```

## CI Pipeline

CI runs the same `makers` pipeline used locally, so if it passes on your machine, it should pass in CI.

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

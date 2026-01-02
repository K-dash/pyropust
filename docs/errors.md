# Error Format

This document defines the shared error format used by pyropust across Python and Rust boundaries. The goal is to make error exchange predictable between extensions and libraries.

## Dict Format

`Error.to_dict()` returns a dictionary with the following keys:

- `kind`: string
  - One of `"InvalidInput"`, `"NotFound"`, `"Internal"`.
- `code`: string
  - Stable, machine-readable error code (e.g., `"type_mismatch"`, `"py_exception"`).
  - Typically the `value` of an `ErrorCode` (`StrEnum`) in Python.
- `message`: string
  - Human-readable summary.
- `op`: string | None
  - Operation or context name when relevant.
- `path`: list[str | int]
  - Path to the failing location (keys or indexes).
- `expected`: string | None
- `got`: string | None
- `cause`: string | None
- `metadata`: dict[str, str]
  - Additional structured details.

Example:

```python
{
    "kind": "InvalidInput",
    "code": "type_mismatch",
    "message": "Type mismatch",
    "op": "AsInt",
    "path": ["user", 0],
    "expected": "int",
    "got": "str",
    "cause": None,
    "metadata": {
        "source": "my_extension",
    },
}
```

## Reserved Metadata Keys

These keys have standard meaning when present:

- `py_traceback`: Full Python traceback string when an exception is converted.
- `exception`: Python exception type name (e.g., `"ValueError"`).
- `source`: Identifier of the component/extension that produced the error.

Extensions may add additional keys, but should avoid collisions with the reserved ones.

## Conversion APIs

### `Error.to_dict()`
Returns the format above.

### `Error.from_dict(data)`
Creates an `Error` from a dict following the format.

### `exception_to_error(exc, code="py_exception")`
Normalizes a Python exception into `Error`.

- `code` defaults to `"py_exception"`.
- `metadata["py_traceback"]` is populated when available.

## Recommendations for Interop

- Treat `code` as the primary programmatic discriminator.
- Use `kind` for high-level classification.
- Keep `metadata` values string-only for portability.
- Document any custom `code` values your extension emits.

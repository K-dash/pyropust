# Supported Operations

This document lists the operators available in `Op` and their behavior. Operators are grouped by namespace. All operators are also available via the flat `Op.*` API for backward compatibility.

## Coerce

- `assert_str()`
  - Input: object
  - Output: str
  - Behavior: returns the input if it is a string; otherwise raises a type mismatch error.

- `expect_str()`
  - Input: object
  - Output: str
  - Behavior: same as `assert_str` (type narrowing helper).

- `as_str()`
  - Input: object
  - Output: str
  - Behavior: converts str/bytes/bool/int/float/datetime/null to string; bytes must be valid UTF-8.

- `as_int()`
  - Input: object
  - Output: int
  - Behavior: converts str/float/bool to int; fails on invalid strings.

- `as_float()`
  - Input: object
  - Output: float
  - Behavior: converts str/int to float; fails on invalid strings.

- `as_bool()`
  - Input: object
  - Output: bool
  - Behavior: converts str/int to bool using common truthy/falsy strings.

- `as_datetime(format: str)`
  - Input: object
  - Output: datetime
  - Behavior: parses datetime or date-only strings using the given format; returns UTC datetime.

- `json_decode()`
  - Input: str | bytes
  - Output: Mapping[str, object]
  - Behavior: parses JSON into internal values. If this is the first operator in a Blueprint, `run()` uses a fast Rust JSON path.

## Text

- `split(delim: str)`
  - Input: str
  - Output: list[str]
  - Behavior: splits on the given delimiter (must be non-empty).

- `trim()`
  - Input: str
  - Output: str
  - Behavior: trims leading and trailing whitespace.

- `lower()`
  - Input: str
  - Output: str
  - Behavior: lowercases the string.

- `replace(old: str, new: str)`
  - Input: str
  - Output: str
  - Behavior: replaces all occurrences of `old` with `new`.

- `to_uppercase()`
  - Input: str
  - Output: str
  - Behavior: uppercases the string.

## Sequence

- `index(idx: int)`
  - Input: Sequence[object]
  - Output: object
  - Behavior: returns the element at the given index.

- `slice(start: int, end: int)`
  - Input: Sequence[object]
  - Output: list[object]
  - Behavior: returns a slice in the range `[start, end)`; errors on invalid bounds.

- `first()`
  - Input: Sequence[object]
  - Output: object
  - Behavior: returns the first element; errors on empty sequences.

- `last()`
  - Input: Sequence[object]
  - Output: object
  - Behavior: returns the last element; errors on empty sequences.

## Map

- `get(key: str)`
  - Input: Mapping[str, object]
  - Output: object
  - Behavior: returns the value for the key; errors if missing.

- `get_or(key: str, default: object)`
  - Input: Mapping[str, object]
  - Output: object
  - Behavior: returns the value for the key, or the provided default if missing. The default is converted using the same rules as `run()` input conversion.

## Core

- `len()`
  - Input: object
  - Output: int
  - Behavior: works on str/bytes/list/map; errors on other types.

- `map_py(func: Callable[[T], U])`
  - Input: object
  - Output: object
  - Behavior: calls the Python function with the current value. Exceptions are converted to `RopeError` with code `py_exception` and traceback stored in `metadata["py_traceback"]`.

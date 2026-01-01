from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

from pyropust import Blueprint, ErrorKind, Ok, Op, Result, do, run


def test_blueprint_execution() -> None:
    bp = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .guard_str()
        .pipe(Op.to_uppercase())
    )

    result = run(bp, "alice@example.com")
    assert result.is_ok()
    assert result.unwrap() == "EXAMPLE.COM"

    fail_result = run(bp, "invalid-email")
    assert fail_result.is_err()
    err = fail_result.unwrap_err()
    assert str(err.kind) == str(ErrorKind.NotFound)


def test_do_with_blueprint() -> None:
    bp = Blueprint().pipe(Op.assert_str()).pipe(Op.split("@")).pipe(Op.index(1))

    @do
    def workflow(raw: str) -> Generator[Result[object], object, Result[str]]:
        domain = yield run(bp, raw)
        return Ok(f"Processed: {domain}")

    ok = workflow("alice@example.com")
    assert ok.unwrap() == "Processed: example.com"

    err = workflow("bad")
    assert err.is_err()


def test_expect_str_operator() -> None:
    """Test expect_str() as a type-narrowing operator after index/get."""
    bp = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .pipe(Op.expect_str())
        .pipe(Op.to_uppercase())
    )

    result = run(bp, "alice@example.com")
    assert result.is_ok()
    assert result.unwrap() == "EXAMPLE.COM"

    # Should fail if index returns non-string
    fail_bp = (
        Blueprint()
        .pipe(Op.assert_str())
        .pipe(Op.split(" "))
        .pipe(Op.index(10))  # Out of bounds -> returns error before expect_str
        .pipe(Op.expect_str())
    )
    fail_result = run(fail_bp, "hello world")
    assert fail_result.is_err()


def test_namespace_style_operators() -> None:
    """Test namespaced operators (Op.text.*, Op.seq.*, etc.)."""
    bp = (
        Blueprint()
        .pipe(Op.coerce.assert_str())  # Narrow type to str first
        .pipe(Op.text.split(","))
        .pipe(Op.seq.index(0))
        .pipe(Op.coerce.expect_str())
        .pipe(Op.text.to_uppercase())
    )

    result = run(bp, "hello,world")
    assert result.is_ok()
    assert result.unwrap() == "HELLO"


def test_namespace_and_flat_api_equivalence() -> None:
    """Test that namespace and flat API produce identical results."""
    # Namespace style
    bp_ns = (
        Blueprint()
        .pipe(Op.coerce.assert_str())  # Narrow type to str first
        .pipe(Op.text.split("@"))
        .pipe(Op.seq.index(1))
        .pipe(Op.coerce.expect_str())
        .pipe(Op.text.to_uppercase())
    )

    # Flat style (backward compatibility)
    bp_flat = (
        Blueprint()
        .pipe(Op.assert_str())  # Narrow type to str first
        .pipe(Op.split("@"))
        .pipe(Op.index(1))
        .pipe(Op.expect_str())
        .pipe(Op.to_uppercase())
    )

    input_data = "alice@example.com"
    result_ns = run(bp_ns, input_data)
    result_flat = run(bp_flat, input_data)

    assert result_ns.unwrap() == result_flat.unwrap() == "EXAMPLE.COM"


def test_len_operator_universal() -> None:
    """Test len() works on str, bytes, list, and map."""
    # String length
    bp_str = Blueprint().pipe(Op.coerce.assert_str()).pipe(Op.core.len())
    result = run(bp_str, "hello")
    assert result.is_ok()
    assert result.unwrap() == 5

    # List length
    bp_list = Blueprint().pipe(Op.core.len())
    result = run(bp_list, [1, 2, 3, 4])
    assert result.is_ok()
    assert result.unwrap() == 4

    # Map length
    result = run(bp_list, {"a": 1, "b": 2, "c": 3})
    assert result.is_ok()
    assert result.unwrap() == 3

    # Bytes length
    result = run(bp_list, b"hello world")
    assert result.is_ok()
    assert result.unwrap() == 11

    # len() should fail on unsupported types (int, bool, null)
    fail_result = run(bp_list, 42)
    assert fail_result.is_err()
    err = fail_result.unwrap_err()
    assert err.code == "type_mismatch"
    assert "str|bytes|list|map" in (err.expected or "")


def test_len_backward_compat_aliases() -> None:
    """Test that Op.len() and Op.text.len() are available as aliases."""
    bp_flat = Blueprint().pipe(Op.len())
    bp_text = Blueprint().pipe(Op.text.len())

    result_flat = run(bp_flat, "test")
    result_text = run(bp_text, "test")

    assert result_flat.unwrap() == result_text.unwrap() == 4


def test_as_int_conversion() -> None:
    """Test as_int() converts str/float/bool to int."""
    bp = Blueprint().pipe(Op.coerce.as_int())

    # String to int
    result = run(bp, "42")
    assert result.is_ok()
    assert result.unwrap() == 42

    # String with whitespace
    result = run(bp, "  -123  ")
    assert result.is_ok()
    assert result.unwrap() == -123

    # Float to int (truncation)
    result = run(bp, 3.7)
    assert result.is_ok()
    assert result.unwrap() == 3

    # Bool to int
    true_val: object = True
    result = run(bp, true_val)
    assert result.is_ok()
    assert result.unwrap() == 1

    false_val: object = False
    result = run(bp, false_val)
    assert result.is_ok()
    assert result.unwrap() == 0

    # Int passthrough
    result = run(bp, 99)
    assert result.is_ok()
    assert result.unwrap() == 99

    # Invalid string
    fail_result = run(bp, "not a number")
    assert fail_result.is_err()
    assert fail_result.unwrap_err().code == "parse_error"


def test_as_float_conversion() -> None:
    """Test as_float() converts str/int to float."""
    bp = Blueprint().pipe(Op.coerce.as_float())

    # String to float
    result = run(bp, "3.14")
    assert result.is_ok()
    assert abs(result.unwrap() - 3.14) < 0.001

    # Int to float
    result = run(bp, 42)
    assert result.is_ok()
    assert result.unwrap() == 42.0

    # Float passthrough
    result = run(bp, 2.718)
    assert result.is_ok()
    assert abs(result.unwrap() - 2.718) < 0.001

    # Invalid string
    fail_result = run(bp, "not a float")
    assert fail_result.is_err()
    assert fail_result.unwrap_err().code == "parse_error"


def test_as_bool_conversion() -> None:
    """Test as_bool() converts str/int to bool."""
    bp = Blueprint().pipe(Op.coerce.as_bool())

    # String truthy values
    for truthy in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
        result = run(bp, truthy)
        assert result.is_ok(), f"Failed for {truthy}"
        assert result.unwrap() is True, f"Expected True for {truthy}"

    # String falsy values
    for falsy in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF", ""]:
        result = run(bp, falsy)
        assert result.is_ok(), f"Failed for {falsy!r}"
        assert result.unwrap() is False, f"Expected False for {falsy!r}"

    # Int to bool
    result = run(bp, 1)
    assert result.is_ok()
    assert result.unwrap() is True

    result = run(bp, 0)
    assert result.is_ok()
    assert result.unwrap() is False

    result = run(bp, -5)
    assert result.is_ok()
    assert result.unwrap() is True  # Non-zero is truthy

    # Bool passthrough
    true_val: object = True
    result = run(bp, true_val)
    assert result.is_ok()
    assert result.unwrap() is True

    # Invalid string
    fail_result = run(bp, "maybe")
    assert fail_result.is_err()
    assert fail_result.unwrap_err().code == "parse_error"


def test_float_input_output() -> None:
    """Test that float values can be passed through Blueprint."""
    # Float passthrough via as_float
    bp_float = Blueprint().pipe(Op.coerce.as_float())
    result = run(bp_float, 3.14159)
    assert result.is_ok()
    assert abs(result.unwrap() - 3.14159) < 0.00001


def test_as_datetime_conversion() -> None:
    """Test as_datetime() parses string to datetime."""
    bp = Blueprint().pipe(Op.coerce.as_datetime("%Y-%m-%d %H:%M:%S"))

    # Valid datetime string
    result = run(bp, "2024-12-25 10:30:00")
    assert result.is_ok()
    dt = result.unwrap()
    assert isinstance(dt, datetime)
    assert dt.year == 2024
    assert dt.month == 12
    assert dt.day == 25
    assert dt.hour == 10
    assert dt.minute == 30
    assert dt.second == 0
    assert dt.tzinfo == UTC  # Converted to UTC

    # Different format
    bp_date_only = Blueprint().pipe(Op.coerce.as_datetime("%Y-%m-%d"))
    result = run(bp_date_only, "2023-06-15")
    assert result.is_ok()
    dt = result.unwrap()
    assert dt.year == 2023
    assert dt.month == 6
    assert dt.day == 15

    # Invalid format
    fail_result = run(bp, "not a date")
    assert fail_result.is_err()
    err = fail_result.unwrap_err()
    assert err.code == "parse_error"
    assert "datetime" in err.message.lower()

    # Wrong format
    fail_result = run(bp, "25/12/2024")  # Format doesn't match
    assert fail_result.is_err()


def test_datetime_input_passthrough() -> None:
    """Test that datetime values can be passed through Blueprint."""
    # Create a UTC datetime and pass it through as_datetime
    bp = Blueprint().pipe(Op.coerce.as_datetime("%Y-%m-%d"))
    input_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    result = run(bp, input_dt)
    assert result.is_ok()
    dt = result.unwrap()
    assert dt == input_dt


def test_turbo_json_path() -> None:
    bp = (
        Blueprint.for_type(str)
        .pipe(Op.json_decode())
        .pipe(Op.get("name"))
        .pipe(Op.expect_str())
        .pipe(Op.to_uppercase())
    )

    res = run(bp, '{"name": "alice", "age": 30}')
    assert res.is_ok()
    assert res.unwrap() == "ALICE"

    fail_res = run(bp, '{"name": "alice", ')
    assert fail_res.is_err()
    assert fail_res.unwrap_err().code == "json_parse_error"


def test_map_py_operator() -> None:
    def reverse_text(value: str) -> str:
        return "".join(reversed(value))

    bp = Blueprint.for_type(str).pipe(Op.map_py(reverse_text)).pipe(Op.to_uppercase())

    res = run(bp, "hello")
    assert res.is_ok()
    assert res.unwrap() == "OLLEH"

    def fail_fn(_: str) -> str:
        raise ValueError("boom")

    bp_fail = Blueprint.for_type(str).pipe(Op.map_py(fail_fn))
    fail_res = run(bp_fail, "hello")
    assert fail_res.is_err()
    err = fail_res.unwrap_err()
    assert err.code == "py_exception"
    assert "py_traceback" in err.metadata
    assert "ValueError" in err.metadata["py_traceback"]
    assert "boom" in err.metadata["py_traceback"]


def test_map_py_invalid_return() -> None:
    def bad_return(_: str) -> object:
        return object()

    bp = Blueprint.for_type(str).pipe(Op.map_py(bad_return))
    res = run(bp, "hello")
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "py_return_invalid"


def test_text_ops() -> None:
    bp = Blueprint.for_type(str).pipe(Op.trim()).pipe(Op.lower()).pipe(Op.replace(" ", "-"))
    res = run(bp, "  Hello World  ")
    assert res.is_ok()
    assert res.unwrap() == "hello-world"


def test_split_invalid_delim() -> None:
    bp = Blueprint.for_type(str).pipe(Op.split(""))
    res = run(bp, "a,b")
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "invalid_delim"
    assert err.op == "Split"
    assert err.expected == "non-empty string"
    assert err.got == "empty string"


def test_as_str_conversion() -> None:
    bp = Blueprint.for_type(object).pipe(Op.as_str())
    res = run(bp, 123)
    assert res.is_ok()
    assert res.unwrap() == "123"


def test_seq_slice_first_last() -> None:
    bp_slice = Blueprint.for_type(list[object]).pipe(Op.slice(1, 3))
    res_slice = run(bp_slice, [1, 2, 3, 4])
    assert res_slice.is_ok()
    assert res_slice.unwrap() == [2, 3]

    bp_first = Blueprint.for_type(list[object]).pipe(Op.first())
    res_first = run(bp_first, ["a", "b"])
    assert res_first.is_ok()
    assert res_first.unwrap() == "a"

    bp_last = Blueprint.for_type(list[object]).pipe(Op.last())
    res_last = run(bp_last, ["a", "b"])
    assert res_last.is_ok()
    assert res_last.unwrap() == "b"


def test_get_or_default() -> None:
    bp = Blueprint.for_type(dict[str, int]).pipe(Op.get_or("missing", 5))
    res = run(bp, {"present": 1})
    assert res.is_ok()
    assert res.unwrap() == 5


def test_map_keys_values() -> None:
    bp_keys = Blueprint.for_type(dict[str, object]).pipe(Op.keys())
    res_keys = run(bp_keys, {"a": 1, "b": 2})
    assert res_keys.is_ok()
    assert sorted(res_keys.unwrap()) == ["a", "b"]

    bp_values = Blueprint.for_type(dict[str, int]).pipe(Op.values())
    res_values = run(bp_values, {"a": 1, "b": 2})
    assert res_values.is_ok()
    values = res_values.unwrap()
    assert 1 in values
    assert 2 in values


def test_get_missing_key() -> None:
    bp = Blueprint.for_type(dict[str, int]).pipe(Op.get("missing"))
    res = run(bp, {"present": 1})
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "key_not_found"
    assert err.op == "GetKey"
    assert str(err.kind) == str(ErrorKind.NotFound)
    assert err.path == ["missing"]


def test_invalid_operator_in_pipeline() -> None:
    # NOTE: type-ignore is intentional: we want to exercise runtime error handling
    # for a pipeline that should be rejected by static type checking.
    bp = Blueprint.for_type(str).pipe(Op.get("name"))  # type: ignore[arg-type]
    res = run(bp, "not a map")
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "type_mismatch"
    assert err.op == "GetKey"
    assert err.expected == "map"
    assert err.got == "str"


def test_get_or_default_invalid() -> None:
    bp = Blueprint.for_type(dict[str, int]).pipe(
        # NOTE: type-ignore is intentional: default value is not convertible and
        # this test validates the runtime error path.
        Op.get_or("missing", object())  # type: ignore[arg-type]
    )
    res = run(bp, {"present": 1})
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "default_invalid"
    assert err.op == "GetOr"


def test_len_type_mismatch() -> None:
    bp = Blueprint.for_type(object).pipe(Op.len())
    res = run(bp, 123)
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "type_mismatch"
    assert err.op == "Len"
    assert err.expected == "str|bytes|list|map"
    assert err.got == "int"


def test_json_decode_invalid_input_type() -> None:
    # NOTE: type-ignore is intentional: json_decode expects str|bytes.
    bp = Blueprint.for_type(object).pipe(Op.json_decode())  # type: ignore[arg-type]
    res = run(bp, 123)
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "type_mismatch"
    assert err.op == "JsonDecode"
    assert err.expected == "str|bytes"
    assert err.got == "int"


def test_input_map_key_not_str() -> None:
    bp = Blueprint.for_type(dict[str, object]).pipe(Op.get("key"))
    res = run(bp, {1: "x"})
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "invalid_key"
    assert err.op == "Input"
    assert err.expected == "str"
    assert err.got == "non-str"


def test_input_unsupported_type() -> None:
    bp = Blueprint.for_type(object).pipe(Op.is_null())
    res = run(bp, {1, 2})  # set is unsupported
    assert res.is_err()
    err = res.unwrap_err()
    assert err.code == "unsupported_type"
    assert err.op == "Input"
    assert err.expected == "null/str/int/float/bool/bytes/datetime/list/map"
    assert err.got == "set"


def test_is_null_is_empty() -> None:
    bp_null = Blueprint.for_type(object).pipe(Op.is_null())
    res = run(bp_null, None)
    assert res.is_ok()
    assert res.unwrap() is True

    bp_empty = Blueprint.for_type(object).pipe(Op.is_empty())
    res = run(bp_empty, "")
    assert res.is_ok()
    assert res.unwrap() is True

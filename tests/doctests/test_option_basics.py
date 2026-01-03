"""Doctests for Option basic operations.

Tests examples from reference/option.md.
"""

from typing import TypedDict

from pyropust import ErrorCode, None_, Ok, Option, Result, Some, err


class Code(ErrorCode):
    MISSING = "missing"
    INVALID = "invalid"


class ConfigInput(TypedDict, total=False):
    host: str
    port: int
    debug: bool


class Config(TypedDict):
    host: str
    port: int
    debug: bool


class Address(TypedDict, total=False):
    city: str


class User(TypedDict, total=False):
    address: Address


class Root(TypedDict, total=False):
    user: User


class UserRecord(TypedDict, total=False):
    email: str
    age: int | str


class ValidUser(TypedDict):
    email: str
    age: int


def test_some_basic() -> None:
    """Test Some construction and queries."""
    option = Some(42)

    assert option.is_some()
    assert not option.is_none()
    assert option.unwrap() == 42


def test_none_basic() -> None:
    """Test None_ construction and queries."""
    option = None_()

    assert option.is_none()
    assert not option.is_some()

    # Unwrap with default
    assert option.unwrap_or(0) == 0


def test_is_some_and() -> None:
    """Test is_some_and predicate."""
    option = Some(42)
    assert option.is_some_and(lambda x: x > 40)
    assert not option.is_some_and(lambda x: x < 40)

    # None_ always returns False
    option = None_()
    assert not option.is_some_and(lambda _x: True)


def test_is_none_or() -> None:
    """Test is_none_or predicate."""
    option = Some(42)
    assert option.is_none_or(lambda x: x == 42)
    assert not option.is_none_or(lambda x: x < 40)

    # None_ always returns True
    option = None_()
    assert option.is_none_or(lambda _x: False)


def test_unwrap_or() -> None:
    """Test unwrap_or for default values."""
    assert Some(42).unwrap_or(0) == 42
    assert None_().unwrap_or(0) == 0


def test_unwrap_or_else() -> None:
    """Test unwrap_or_else for computed defaults."""
    assert Some(42).unwrap_or_else(lambda: 100) == 42
    assert None_().unwrap_or_else(lambda: 100) == 100


def test_map() -> None:
    """Test map transformation."""
    option = Some(5).map(lambda x: x * 2)
    assert option.unwrap() == 10

    # Map on None_ is no-op
    option = None_().map(lambda _x: 0)
    assert option.is_none()


def test_map_try() -> None:
    """Test map_try with exception handling."""
    # Success
    result = Some("123").map_try(int, code=Code.INVALID, message="invalid integer")
    assert result.is_ok()
    assert result.unwrap().unwrap() == 123

    # Exception caught
    result = Some("abc").map_try(int, code=Code.INVALID, message="invalid integer")
    assert result.is_err()

    # None_ stays None_
    result = None_().map_try(int, code=Code.INVALID, message="invalid integer")
    assert result.is_ok()
    assert result.unwrap().is_none()


def test_filter() -> None:
    """Test filter predicate."""
    # Predicate matches
    option = Some(42).filter(lambda x: x > 40)
    assert option.unwrap() == 42

    # Predicate doesn't match
    option = Some(42).filter(lambda x: x < 40)
    assert option.is_none()

    # None_ stays None_
    option = None_().filter(lambda _x: True)
    assert option.is_none()


def test_and_then() -> None:
    """Test and_then for chaining."""

    def parse_int(s: str) -> Option[int]:
        try:
            return Some(int(s))
        except ValueError:
            return None_()

    # Success
    option = Some("42").and_then(parse_int)
    assert option.unwrap() == 42

    # Failure
    option = Some("abc").and_then(parse_int)
    assert option.is_none()

    # None_ short-circuits
    option = None_().and_then(parse_int)
    assert option.is_none()


def test_or_() -> None:
    """Test or_ for fallback."""
    # First Some returned
    option = Some(1).or_(Some(2))
    assert option.unwrap() == 1

    # Fallback to second
    none_option: Option[int] = Some(1).filter(lambda _x: False)
    option = none_option.or_(Some(2))
    assert option.unwrap() == 2

    # Both None_
    none_option1: Option[int] = Some(1).filter(lambda _x: False)
    none_option2: Option[int] = Some(2).filter(lambda _x: False)
    option = none_option1.or_(none_option2)
    assert option.is_none()


def test_xor() -> None:
    """Test xor for exclusive or."""
    # Exactly one Some
    none_option1: Option[int] = Some(1).filter(lambda _x: False)
    option = Some(1).xor(none_option1)
    assert option.unwrap() == 1

    none_option2: Option[int] = Some(2).filter(lambda _x: False)
    option = none_option2.xor(Some(2))
    assert option.unwrap() == 2

    # Both Some -> None_
    option = Some(1).xor(Some(2))
    assert option.is_none()

    # Both None_ -> None_
    none_option3: Option[int] = Some(1).filter(lambda _x: False)
    none_option4: Option[int] = Some(2).filter(lambda _x: False)
    option = none_option3.xor(none_option4)
    assert option.is_none()


def test_ok_or() -> None:
    """Test ok_or conversion to Result."""
    # Some -> Ok
    result = Some(42).ok_or(Code.MISSING, "value not found")
    assert result.is_ok()
    assert result.unwrap() == 42

    # None_ -> Err
    result = None_().ok_or(Code.MISSING, "value not found")
    assert result.is_err()
    assert result.unwrap_err().code == Code.MISSING


def test_flatten() -> None:
    """Test flatten for nested Options."""
    nested = Some(Some(42))
    option = nested.flatten()
    assert option.unwrap() == 42

    nested = Some(None_())
    option = nested.flatten()
    assert option.is_none()


def test_transpose() -> None:
    """Test transpose Option[Result] to Result[Option]."""
    # Some(Ok) -> Ok(Some)
    option_ok: Option[Result[int]] = Some(Ok(42))
    result_ok = option_ok.transpose()
    assert result_ok.is_ok()
    assert result_ok.unwrap().unwrap() == 42

    # Some(Err) -> Err
    option_err = Some(err(Code.INVALID, "failed"))
    result_err = option_err.transpose()
    assert result_err.is_err()

    # None_ -> Ok(None_)
    option_none: Option[Result[int]] = None_()
    result_none = option_none.transpose()
    assert result_none.is_ok()
    assert result_none.unwrap().is_none()


def test_zip() -> None:
    """Test zip for combining Options."""
    # Both Some
    option = Some(1).zip(Some(2))
    assert option.unwrap() == (1, 2)

    # One None_
    none_option: Option[int] = None_()
    option = Some(1).zip(none_option)
    assert option.is_none()

    option = none_option.zip(Some(2))
    assert option.is_none()


def test_zip_with() -> None:
    """Test zip_with for combining with function."""
    option = Some(5).zip_with(Some(3), lambda a, b: a + b)
    assert option.unwrap() == 8

    none_option: Option[int] = None_()
    option = Some(5).zip_with(none_option, lambda a, b: a + b)
    assert option.is_none()


def test_optional_config_pattern() -> None:
    """Test optional config with defaults pattern."""

    def get_config(data: ConfigInput) -> Config:
        # Note: dict.get() returns None for missing keys
        # Some(None) is still Some, so we need to check for None explicitly
        debug_value = data.get("debug")
        return {
            "host": data.get("host") or "localhost",
            "port": data.get("port") or 8080,
            "debug": debug_value if debug_value is not None else False,
        }

    # Partial config
    config = get_config({"host": "example.com"})
    assert config["host"] == "example.com"
    assert config["port"] == 8080
    assert config["debug"] is False

    # Complete config
    config = get_config({"host": "example.com", "port": 3000, "debug": True})
    assert config["host"] == "example.com"
    assert config["port"] == 3000
    assert config["debug"] is True


def test_optional_chaining_pattern() -> None:
    """Test optional chaining pattern."""

    def get_user(root: Root) -> Option[User]:
        return None_() if "user" not in root else Some(root["user"])

    def get_address(user: User) -> Option[Address]:
        return None_() if "address" not in user else Some(user["address"])

    def get_city(address: Address) -> Option[str]:
        return None_() if "city" not in address else Some(address["city"])

    data: Root = {"user": {"address": {"city": "Tokyo"}}}

    # Success path
    city = get_user(data).and_then(get_address).and_then(get_city).unwrap_or("Unknown")
    assert city == "Tokyo"

    # Missing nested key
    data_incomplete: Root = {"user": {"address": {}}}
    city = get_user(data_incomplete).and_then(get_address).and_then(get_city).unwrap_or("Unknown")
    assert city == "Unknown"

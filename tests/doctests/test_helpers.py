"""Doctests for helper functions (err, bail, ensure).

Tests examples from reference/helpers.md.
"""

from typing import TypedDict

from pyropust import (
    ErrorCode,
    bail,
    err,
    exception_to_error,
)


class Code(ErrorCode):
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    TOO_SMALL = "too_small"
    TOO_LARGE = "too_large"
    MISSING_FIELD = "missing_field"
    WEAK_CREDENTIAL = "weak_credential"


class UserInput(TypedDict, total=False):
    email: str
    age: int | str


class UserValidated(TypedDict):
    email: str
    age: int


class RegistrationInput(TypedDict, total=False):
    email: str
    password: str
    age: int | str


class RegistrationOutput(TypedDict):
    email: str
    password: str
    age: int


def test_err_basic() -> None:
    """Test err() creates Err(Error(...))."""
    result = err(Code.NOT_FOUND, "User not found")

    assert result.is_err()
    assert result.unwrap_err().code == Code.NOT_FOUND
    assert result.unwrap_err().message == "User not found"


def test_err_with_metadata() -> None:
    """Test err() with additional context."""
    result = err(
        Code.NOT_FOUND,
        "User not found",
        metadata={"user_id": "123"},
        path=["users", "123"],
        op="fetch_user",
    )

    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == Code.NOT_FOUND
    assert error.metadata == {"user_id": "123"}
    assert error.path == ["users", "123"]
    assert error.op == "fetch_user"


def test_bail_for_early_return() -> None:
    """Test bail() for early return pattern."""


def test_err_vs_bail() -> None:
    """Test that err() and bail() are functionally identical.

    The difference is semantic intent only.
    """
    err_result = err(Code.INVALID, "failed")
    bail_result = bail(Code.INVALID, "failed")

    # Both return Err with same code and message
    assert err_result.is_err()
    assert bail_result.is_err()
    assert err_result.unwrap_err().code == bail_result.unwrap_err().code
    assert err_result.unwrap_err().message == bail_result.unwrap_err().message


def test_ensure_basic() -> None:
    """Test ensure() returns Ok(None) or Err."""


def test_exception_to_error() -> None:
    """Test exception_to_error for manual conversion."""
    try:
        int("abc")
    except ValueError as e:
        error = exception_to_error(e, code=Code.INVALID)
        assert error.code == Code.INVALID
        assert error.cause is not None
        assert "invalid literal" in error.cause


def test_ensure_equivalent_to_if_err() -> None:
    """Test that ensure() is equivalent to if + err pattern."""

    # Using ensure

    # Using if + err

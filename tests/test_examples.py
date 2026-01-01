"""Tests for README examples and manual handling patterns."""

from __future__ import annotations

from pyropust import Err, Ok, Result


class TestResultManualHandling:
    """Test manual Result handling pattern from README."""

    def test_readme_example_divide_function(self) -> None:
        """Verify the README divide example works."""

        def divide(a: int, b: int) -> Result[float]:
            if b == 0:
                return Err("Division by zero")
            return Ok(a / b)

        # Success case
        res = divide(10, 2)
        assert res.is_ok()
        assert res.unwrap() == 5.0

        # Error case
        res_err = divide(10, 0)
        assert res_err.is_err()
        assert res_err.unwrap_err().message == "Division by zero"

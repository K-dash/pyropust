from __future__ import annotations

from collections.abc import Sequence

from .pyrope_native import (
    Operator,
    _op_assert_str,
    _op_get_key,
    _op_index,
    _op_split,
    _op_to_uppercase,
)


class Op:
    @staticmethod
    def assert_str() -> Operator[object, str]:
        return _op_assert_str()

    @staticmethod
    def split(delim: str) -> Operator[str, Sequence[str]]:
        return _op_split(delim)

    @staticmethod
    def index(idx: int) -> Operator[list[object], object]:
        return _op_index(idx)

    @staticmethod
    def get(key: str) -> Operator[dict[str, object], object]:
        return _op_get_key(key)

    @staticmethod
    def to_uppercase() -> Operator[str, str]:
        return _op_to_uppercase()

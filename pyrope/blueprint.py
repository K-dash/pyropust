from __future__ import annotations

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
    def assert_str() -> Operator:
        return _op_assert_str()

    @staticmethod
    def split(delim: str) -> Operator:
        return _op_split(delim)

    @staticmethod
    def index(idx: int) -> Operator:
        return _op_index(idx)

    @staticmethod
    def get(key: str) -> Operator:
        return _op_get_key(key)

    @staticmethod
    def to_uppercase() -> Operator:
        return _op_to_uppercase()

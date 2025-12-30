use crate::ops::OperatorKind;
use crate::py::operator::Operator;
use pyo3::prelude::*;

/// Static factory class for creating Operators
#[pyclass(frozen, name = "Op")]
pub struct Op;

#[pymethods]
impl Op {
    /// Assert that the input is a string
    #[staticmethod]
    fn assert_str() -> Operator {
        Operator {
            kind: OperatorKind::AssertStr,
        }
    }

    /// Type-narrowing operator that asserts the input is a string
    ///
    /// Alias for assert_str() for use after operations that return object.
    ///
    /// Usage:
    ///     Blueprint().pipe(Op.index(0)).pipe(Op.expect_str()).pipe(Op.to_uppercase())
    #[staticmethod]
    fn expect_str() -> Operator {
        Operator {
            kind: OperatorKind::AssertStr,
        }
    }

    /// Split a string by delimiter
    #[staticmethod]
    fn split(delim: String) -> Operator {
        Operator {
            kind: OperatorKind::Split { delim },
        }
    }

    /// Index into a sequence
    #[staticmethod]
    fn index(idx: usize) -> Operator {
        Operator {
            kind: OperatorKind::Index { idx },
        }
    }

    /// Get a value from a mapping by key
    #[staticmethod]
    fn get(key: String) -> Operator {
        Operator {
            kind: OperatorKind::GetKey { key },
        }
    }

    /// Convert a string to uppercase
    #[staticmethod]
    fn to_uppercase() -> Operator {
        Operator {
            kind: OperatorKind::ToUppercase,
        }
    }
}

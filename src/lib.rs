mod data;
mod ops;
mod py;

use py::{
    op_assert_str, op_get_key, op_index, op_split, op_to_uppercase, py_err, py_none, py_ok,
    py_some, run, Blueprint, ErrorKindObj, Op, Operator, OptionObj, ResultObj, RopeError,
};
use pyo3::prelude::*;
use pyo3::types::PyModule;
use pyo3::wrap_pyfunction;

#[pymodule]
fn pyrope_native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ResultObj>()?;
    m.add_class::<OptionObj>()?;
    m.add_class::<ErrorKindObj>()?;
    m.add_class::<RopeError>()?;
    m.add_class::<Operator>()?;
    m.add_class::<Blueprint>()?;
    m.add_class::<Op>()?;
    m.add_function(wrap_pyfunction!(py_ok, m)?)?;
    m.add_function(wrap_pyfunction!(py_err, m)?)?;
    m.add_function(wrap_pyfunction!(py_some, m)?)?;
    m.add_function(wrap_pyfunction!(py_none, m)?)?;
    m.add_function(wrap_pyfunction!(run, m)?)?;
    m.add_function(wrap_pyfunction!(op_assert_str, m)?)?;
    m.add_function(wrap_pyfunction!(op_split, m)?)?;
    m.add_function(wrap_pyfunction!(op_index, m)?)?;
    m.add_function(wrap_pyfunction!(op_get_key, m)?)?;
    m.add_function(wrap_pyfunction!(op_to_uppercase, m)?)?;

    m.add(
        "__all__",
        vec![
            "Result",
            "Option",
            "Ok",
            "Err",
            "Some",
            "None_",
            "RopeError",
            "ErrorKind",
            "Operator",
            "Blueprint",
            "Op",
            "run",
        ],
    )?;

    Ok(())
}

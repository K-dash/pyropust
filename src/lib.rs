mod interop;
mod ops;
mod py;

use py::{
    exception_to_ropust_error, py_err, py_none, py_ok, py_some, run, Blueprint, ErrorKindObj, Op,
    OpCoerce, OpCore, OpMap, OpSeq, OpText, Operator, OptionObj, ResultObj, RopustError,
};
use pyo3::prelude::*;
use pyo3::types::PyModule;
use pyo3::wrap_pyfunction;

#[pymodule]
fn pyropust_native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ResultObj>()?;
    m.add_class::<OptionObj>()?;
    m.add_class::<ErrorKindObj>()?;
    m.add_class::<RopustError>()?;
    m.add_class::<Operator>()?;
    m.add_class::<Blueprint>()?;
    // BEGIN GENERATED CLASSES
    m.add_class::<Op>()?;
    m.add_class::<OpCoerce>()?;
    m.add_class::<OpCore>()?;
    m.add_class::<OpMap>()?;
    m.add_class::<OpSeq>()?;
    m.add_class::<OpText>()?;
    // END GENERATED CLASSES
    m.add_function(wrap_pyfunction!(py_ok, m)?)?;
    m.add_function(wrap_pyfunction!(py_err, m)?)?;
    m.add_function(wrap_pyfunction!(py_some, m)?)?;
    m.add_function(wrap_pyfunction!(py_none, m)?)?;
    m.add_function(wrap_pyfunction!(run, m)?)?;
    m.add_function(wrap_pyfunction!(exception_to_ropust_error, m)?)?;

    m.add(
        "__all__",
        vec![
            "Result",
            "Option",
            "Ok",
            "Err",
            "Some",
            "None_",
            "RopustError",
            "ErrorKind",
            "Operator",
            "Blueprint",
            "Op",
            "run",
        ],
    )?;

    Ok(())
}

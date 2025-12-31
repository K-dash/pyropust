use pyo3::exceptions::{PyBaseException, PyRuntimeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyTuple, PyType};
use pyo3::Bound;
use std::collections::HashMap;

use super::error::{ErrorKind, RopeError};

#[pyclass(name = "Result")]
pub struct ResultObj {
    pub is_ok: bool,
    pub ok: Option<Py<PyAny>>,
    pub err: Option<Py<PyAny>>,
}

#[pymethods]
impl ResultObj {
    fn is_ok(&self) -> bool {
        self.is_ok
    }

    fn is_err(&self) -> bool {
        !self.is_ok
    }

    fn unwrap(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            Ok(self.ok.as_ref().expect("ok value").clone_ref(py))
        } else {
            Err(PyRuntimeError::new_err("called unwrap() on Err"))
        }
    }

    fn unwrap_err(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            Err(PyRuntimeError::new_err("called unwrap_err() on Ok"))
        } else {
            Ok(self.err.as_ref().expect("err value").clone_ref(py))
        }
    }

    fn map(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            let mapped = f.call1((value.clone_ref(py),))?;
            Ok(ok(mapped.into()))
        } else {
            Ok(err(self.err.as_ref().expect("err value").clone_ref(py)))
        }
    }

    fn map_err(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_ok {
            Ok(ok(self.ok.as_ref().expect("ok value").clone_ref(py)))
        } else {
            let value = self.err.as_ref().expect("err value");
            let mapped = f.call1((value.clone_ref(py),))?;
            Ok(err(mapped.into()))
        }
    }

    fn and_then(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            let out = f.call1((value.clone_ref(py),))?;
            let result_type = py.get_type::<ResultObj>();
            if !out.is_instance(result_type.as_any())? {
                return Err(PyTypeError::new_err("and_then callback must return Result"));
            }
            let out_ref: PyRef<'_, ResultObj> = out.extract()?;
            Ok(clone_result(py, &out_ref))
        } else {
            Ok(err(self.err.as_ref().expect("err value").clone_ref(py)))
        }
    }

    #[classmethod]
    #[pyo3(signature = (f, *exceptions))]
    fn attempt(
        _cls: &Bound<'_, PyType>,
        py: Python<'_>,
        f: Bound<'_, PyAny>,
        exceptions: &Bound<'_, PyTuple>,
    ) -> PyResult<Self> {
        match f.call0() {
            Ok(value) => {
                let result_type = py.get_type::<ResultObj>();
                if value.is_instance(result_type.as_any())? {
                    let out_ref: PyRef<'_, ResultObj> = value.extract()?;
                    Ok(clone_result(py, &out_ref))
                } else {
                    Ok(ok(value.into()))
                }
            }
            Err(err) => {
                if should_catch(py, &err, exceptions)? {
                    Ok(rope_error_from_exception(py, err))
                } else {
                    Err(err)
                }
            }
        }
    }

    fn unwrap_or_raise(&self, py: Python<'_>, exc: Py<PyAny>) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            Ok(self.ok.as_ref().expect("ok value").clone_ref(py))
        } else {
            let exc_ref = exc.bind(py);
            let base_exc = py.get_type::<PyBaseException>();
            if !exc_ref.is_instance(base_exc.as_any())? {
                return Err(PyTypeError::new_err(
                    "unwrap_or_raise expects an exception instance",
                ));
            }
            Err(PyErr::from_value(exc_ref.clone()))
        }
    }
}

// Python-facing constructor functions
#[pyfunction(name = "Ok")]
pub fn py_ok(value: Py<PyAny>) -> ResultObj {
    ok(value)
}

#[pyfunction(name = "Err")]
pub fn py_err(error: Py<PyAny>) -> ResultObj {
    err(error)
}

// Internal constructor functions
pub fn ok(value: Py<PyAny>) -> ResultObj {
    ResultObj {
        is_ok: true,
        ok: Some(value),
        err: None,
    }
}

pub fn err(error: Py<PyAny>) -> ResultObj {
    ResultObj {
        is_ok: false,
        ok: None,
        err: Some(error),
    }
}

fn clone_result(py: Python<'_>, out_ref: &PyRef<'_, ResultObj>) -> ResultObj {
    ResultObj {
        is_ok: out_ref.is_ok,
        ok: out_ref.ok.as_ref().map(|v| v.clone_ref(py)),
        err: out_ref.err.as_ref().map(|v| v.clone_ref(py)),
    }
}

fn should_catch(py: Python<'_>, err: &PyErr, exceptions: &Bound<'_, PyTuple>) -> PyResult<bool> {
    if exceptions.is_empty() {
        let base_exc = py.get_type::<pyo3::exceptions::PyException>();
        return Ok(err.matches(py, base_exc.as_any()).unwrap());
    }
    for exc in exceptions.iter() {
        if err.matches(py, exc)? {
            return Ok(true);
        }
    }
    Ok(false)
}

fn rope_error_from_exception(py: Python<'_>, py_err: PyErr) -> ResultObj {
    let mut metadata = HashMap::new();
    if let Ok(name) = py_err.get_type(py).name() {
        metadata.insert("exception".to_string(), name.to_string());
    }
    let cause = py_err
        .value(py)
        .repr()
        .ok()
        .and_then(|s| s.to_str().ok().map(|v| v.to_string()));
    let err_obj = Py::new(
        py,
        RopeError {
            kind: ErrorKind::Internal,
            code: "exception".to_string(),
            message: py_err.to_string(),
            metadata,
            op: None,
            path: Vec::new(),
            expected: None,
            got: None,
            cause,
        },
    )
    .expect("rope error alloc");
    err(err_obj.into())
}

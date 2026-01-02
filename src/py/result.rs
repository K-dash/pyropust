use pyo3::exceptions::{PyBaseException, PyRuntimeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList, PyString, PyTuple, PyType};
use pyo3::Bound;
use std::collections::HashMap;

use super::error::{build_error_from_parts, build_error_from_pyerr, Error, PathItem};
use super::option::{none_, some, OptionObj};

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

    fn expect(&self, py: Python<'_>, msg: &str) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            Ok(self.ok.as_ref().expect("ok value").clone_ref(py))
        } else {
            Err(PyRuntimeError::new_err(msg.to_string()))
        }
    }

    fn expect_err(&self, py: Python<'_>, msg: &str) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            Err(PyRuntimeError::new_err(msg.to_string()))
        } else {
            Ok(self.err.as_ref().expect("err value").clone_ref(py))
        }
    }

    fn unwrap_or(&self, py: Python<'_>, default: Py<PyAny>) -> Py<PyAny> {
        if self.is_ok {
            self.ok.as_ref().expect("ok value").clone_ref(py)
        } else {
            default
        }
    }

    fn unwrap_or_else(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            Ok(self.ok.as_ref().expect("ok value").clone_ref(py))
        } else {
            let err_value = self.err.as_ref().expect("err value");
            let result = f.call1((err_value.clone_ref(py),))?;
            Ok(result.into())
        }
    }

    fn ok(&self, py: Python<'_>) -> OptionObj {
        if self.is_ok {
            some(self.ok.as_ref().expect("ok value").clone_ref(py))
        } else {
            none_()
        }
    }

    fn err(&self, py: Python<'_>) -> OptionObj {
        if self.is_ok {
            none_()
        } else {
            some(self.err.as_ref().expect("err value").clone_ref(py))
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

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (f, *, code, message, kind = None, metadata = None, op = None, path = None, expected = None, got = None))]
    fn map_try(
        &self,
        py: Python<'_>,
        f: Bound<'_, PyAny>,
        code: Py<PyAny>,
        message: String,
        kind: Option<Py<PyAny>>,
        metadata: Option<Py<PyAny>>,
        op: Option<String>,
        path: Option<Py<PyAny>>,
        expected: Option<String>,
        got: Option<String>,
    ) -> PyResult<Self> {
        if !self.is_ok {
            return Ok(err(self.err.as_ref().expect("err value").clone_ref(py)));
        }

        let value = self.ok.as_ref().expect("ok value");
        match f.call1((value.clone_ref(py),)) {
            Ok(mapped) => Ok(ok(mapped.into())),
            Err(py_err) => {
                let cause_obj = build_error_from_pyerr(py, py_err, "py_exception");
                let cause_ref = cause_obj.bind(py).extract::<PyRef<'_, Error>>()?;

                let mut merged_metadata = extract_metadata(py, metadata)?;
                if !merged_metadata.contains_key("cause_exception") {
                    if let Some(value) = cause_ref.metadata.get("exception") {
                        merged_metadata.insert("cause_exception".to_string(), value.to_string());
                    }
                }
                if !merged_metadata.contains_key("cause_py_traceback") {
                    if let Some(value) = cause_ref.metadata.get("py_traceback") {
                        merged_metadata.insert("cause_py_traceback".to_string(), value.to_string());
                    }
                }

                let metadata_value = if merged_metadata.is_empty() {
                    None
                } else {
                    let dict = PyDict::new(py);
                    for (k, v) in merged_metadata {
                        dict.set_item(k, v)?;
                    }
                    Some(dict.into())
                };

                let kind = kind.or_else(|| Some(PyString::new(py, "Internal").into()));

                let new_err = build_error_from_parts(
                    py,
                    code,
                    &message,
                    kind,
                    metadata_value,
                    op,
                    path,
                    expected,
                    got,
                    Some(error_repr(&cause_ref)),
                )?;
                Ok(err(Py::new(py, new_err)?.into()))
            }
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

    fn map_or(
        &self,
        py: Python<'_>,
        default: Py<PyAny>,
        f: Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            let result = f.call1((value.clone_ref(py),))?;
            Ok(result.into())
        } else {
            Ok(default)
        }
    }

    fn map_or_else(
        &self,
        py: Python<'_>,
        default_f: Bound<'_, PyAny>,
        f: Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            let result = f.call1((value.clone_ref(py),))?;
            Ok(result.into())
        } else {
            let err_value = self.err.as_ref().expect("err value");
            let result = default_f.call1((err_value.clone_ref(py),))?;
            Ok(result.into())
        }
    }

    fn inspect(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            f.call1((value.clone_ref(py),))?;
        }
        Ok(ResultObj {
            is_ok: self.is_ok,
            ok: self.ok.as_ref().map(|v| v.clone_ref(py)),
            err: self.err.as_ref().map(|v| v.clone_ref(py)),
        })
    }

    fn inspect_err(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if !self.is_ok {
            let value = self.err.as_ref().expect("err value");
            f.call1((value.clone_ref(py),))?;
        }
        Ok(ResultObj {
            is_ok: self.is_ok,
            ok: self.ok.as_ref().map(|v| v.clone_ref(py)),
            err: self.err.as_ref().map(|v| v.clone_ref(py)),
        })
    }

    fn and_(&self, py: Python<'_>, other: &Self) -> Self {
        if self.is_ok {
            ResultObj {
                is_ok: other.is_ok,
                ok: other.ok.as_ref().map(|v| v.clone_ref(py)),
                err: other.err.as_ref().map(|v| v.clone_ref(py)),
            }
        } else {
            ResultObj {
                is_ok: self.is_ok,
                ok: self.ok.as_ref().map(|v| v.clone_ref(py)),
                err: self.err.as_ref().map(|v| v.clone_ref(py)),
            }
        }
    }

    fn or_(&self, py: Python<'_>, other: &Self) -> Self {
        if self.is_ok {
            ResultObj {
                is_ok: self.is_ok,
                ok: self.ok.as_ref().map(|v| v.clone_ref(py)),
                err: self.err.as_ref().map(|v| v.clone_ref(py)),
            }
        } else {
            ResultObj {
                is_ok: other.is_ok,
                ok: other.ok.as_ref().map(|v| v.clone_ref(py)),
                err: other.err.as_ref().map(|v| v.clone_ref(py)),
            }
        }
    }

    fn or_else(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_ok {
            Ok(ResultObj {
                is_ok: self.is_ok,
                ok: self.ok.as_ref().map(|v| v.clone_ref(py)),
                err: self.err.as_ref().map(|v| v.clone_ref(py)),
            })
        } else {
            let err_value = self.err.as_ref().expect("err value");
            let out = f.call1((err_value.clone_ref(py),))?;
            let result_type = py.get_type::<ResultObj>();
            if !out.is_instance(result_type.as_any())? {
                return Err(PyTypeError::new_err("or_else callback must return Result"));
            }
            let out_ref: PyRef<'_, ResultObj> = out.extract()?;
            Ok(clone_result(py, &out_ref))
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

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (f, *, code, message, kind = None, metadata = None, op = None, path = None, expected = None, got = None))]
    fn and_then_try(
        &self,
        py: Python<'_>,
        f: Bound<'_, PyAny>,
        code: Py<PyAny>,
        message: String,
        kind: Option<Py<PyAny>>,
        metadata: Option<Py<PyAny>>,
        op: Option<String>,
        path: Option<Py<PyAny>>,
        expected: Option<String>,
        got: Option<String>,
    ) -> PyResult<Self> {
        if !self.is_ok {
            return Ok(err(self.err.as_ref().expect("err value").clone_ref(py)));
        }

        let value = self.ok.as_ref().expect("ok value");
        let out = f.call1((value.clone_ref(py),));
        let out = match out {
            Ok(out) => out,
            Err(py_err) => {
                let cause_obj = build_error_from_pyerr(py, py_err, "py_exception");
                let cause_ref = cause_obj.bind(py).extract::<PyRef<'_, Error>>()?;

                let mut merged_metadata = extract_metadata(py, metadata)?;
                if !merged_metadata.contains_key("cause_exception") {
                    if let Some(value) = cause_ref.metadata.get("exception") {
                        merged_metadata.insert("cause_exception".to_string(), value.to_string());
                    }
                }
                if !merged_metadata.contains_key("cause_py_traceback") {
                    if let Some(value) = cause_ref.metadata.get("py_traceback") {
                        merged_metadata.insert("cause_py_traceback".to_string(), value.to_string());
                    }
                }

                let metadata_value = if merged_metadata.is_empty() {
                    None
                } else {
                    let dict = PyDict::new(py);
                    for (k, v) in merged_metadata {
                        dict.set_item(k, v)?;
                    }
                    Some(dict.into())
                };

                let kind = kind.or_else(|| Some(PyString::new(py, "Internal").into()));

                let new_err = build_error_from_parts(
                    py,
                    code,
                    &message,
                    kind,
                    metadata_value,
                    op,
                    path,
                    expected,
                    got,
                    Some(error_repr(&cause_ref)),
                )?;
                return Ok(err(Py::new(py, new_err)?.into()));
            }
        };

        let result_type = py.get_type::<ResultObj>();
        if !out.is_instance(result_type.as_any())? {
            return Err(PyTypeError::new_err(
                "and_then_try callback must return Result",
            ));
        }
        let out_ref: PyRef<'_, ResultObj> = out.extract()?;
        Ok(clone_result(py, &out_ref))
    }

    fn is_ok_and(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<bool> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            let result = f.call1((value.clone_ref(py),))?;
            result.is_truthy()
        } else {
            Ok(false)
        }
    }

    fn is_err_and(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<bool> {
        if self.is_ok {
            Ok(false)
        } else {
            let value = self.err.as_ref().expect("err value");
            let result = f.call1((value.clone_ref(py),))?;
            result.is_truthy()
        }
    }

    fn flatten(&self, py: Python<'_>) -> PyResult<Self> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            let result_type = py.get_type::<ResultObj>();
            if !value.bind(py).is_instance(result_type.as_any())? {
                return Err(PyTypeError::new_err(
                    "flatten requires Ok value to be a Result",
                ));
            }
            let inner_ref: PyRef<'_, ResultObj> = value.extract(py)?;
            Ok(clone_result(py, &inner_ref))
        } else {
            Ok(err(self.err.as_ref().expect("err value").clone_ref(py)))
        }
    }

    fn transpose(&self, py: Python<'_>) -> PyResult<OptionObj> {
        if self.is_ok {
            let value = self.ok.as_ref().expect("ok value");
            let option_type = py.get_type::<OptionObj>();
            if !value.bind(py).is_instance(option_type.as_any())? {
                return Err(PyTypeError::new_err(
                    "transpose requires Ok value to be an Option",
                ));
            }
            let opt_ref: PyRef<'_, OptionObj> = value.extract(py)?;
            if opt_ref.is_some {
                let inner_value = opt_ref.value.as_ref().expect("some value").clone_ref(py);
                let result_obj = ok(inner_value);
                let py_result = Py::new(py, result_obj)?;
                Ok(some(py_result.into()))
            } else {
                Ok(none_())
            }
        } else {
            let err_value = self.err.as_ref().expect("err value").clone_ref(py);
            let result_obj = err(err_value);
            let py_result = Py::new(py, result_obj)?;
            Ok(some(py_result.into()))
        }
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (message, *, code = "context", metadata = None, op = None, path = None, expected = None, got = None))]
    fn context(
        &self,
        py: Python<'_>,
        message: &str,
        code: &str,
        metadata: Option<Py<PyAny>>,
        op: Option<String>,
        path: Option<Py<PyAny>>,
        expected: Option<String>,
        got: Option<String>,
    ) -> PyResult<Self> {
        if self.is_ok {
            return Ok(clone_result_value(py, self));
        }

        let err_value = self.err.as_ref().expect("err value").clone_ref(py);
        let err_ref = err_value.bind(py).extract::<PyRef<'_, Error>>()?;

        let mut merged_metadata = err_ref.metadata.clone();
        let extra_metadata = extract_metadata(py, metadata)?;
        merged_metadata.extend(extra_metadata);

        let path = match path {
            Some(path_value) => extract_path(py, path_value)?,
            None => err_ref.path.clone(),
        };

        let new_err = Error {
            kind: err_ref.kind,
            code: code.to_string(),
            message: message.to_string(),
            metadata: merged_metadata,
            op: op.or_else(|| err_ref.op.clone()),
            path,
            expected: expected.or_else(|| err_ref.expected.clone()),
            got: got.or_else(|| err_ref.got.clone()),
            cause: Some(error_repr(&err_ref)),
        };
        Ok(err(Py::new(py, new_err)?.into()))
    }

    fn with_code(&self, py: Python<'_>, code: &str) -> PyResult<Self> {
        if self.is_ok {
            return Ok(clone_result_value(py, self));
        }
        let err_value = self.err.as_ref().expect("err value").clone_ref(py);
        let err_ref = err_value.bind(py).extract::<PyRef<'_, Error>>()?;
        let mut new_err = err_ref.clone();
        new_err.code = code.to_string();
        Ok(err(Py::new(py, new_err)?.into()))
    }

    fn map_err_code(&self, py: Python<'_>, prefix: &str) -> PyResult<Self> {
        if self.is_ok {
            return Ok(clone_result_value(py, self));
        }
        let err_value = self.err.as_ref().expect("err value").clone_ref(py);
        let err_ref = err_value.bind(py).extract::<PyRef<'_, Error>>()?;
        let mut new_err = err_ref.clone();
        let prefix_dot = format!("{prefix}.");
        if new_err.code.is_empty() {
            new_err.code = prefix.to_string();
        } else if !new_err.code.starts_with(&prefix_dot) {
            new_err.code = format!("{prefix}.{}", new_err.code);
        }
        Ok(err(Py::new(py, new_err)?.into()))
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
                    Ok(error_from_exception(py, err))
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
pub fn py_err(py: Python<'_>, error: Py<PyAny>) -> PyResult<ResultObj> {
    let error_ref = error.bind(py);
    let error_type = py.get_type::<Error>();
    if !error_ref.is_instance(error_type.as_any())? {
        return Err(PyTypeError::new_err("Err expects Error"));
    }
    Ok(err(error))
}

#[allow(clippy::too_many_arguments)]
#[pyfunction(name = "err")]
#[pyo3(signature = (code, message, *, kind = None, metadata = None, op = None, path = None, expected = None, got = None, cause = None))]
pub fn py_err_from_parts(
    py: Python<'_>,
    code: Py<PyAny>,
    message: &str,
    kind: Option<Py<PyAny>>,
    metadata: Option<Py<PyAny>>,
    op: Option<String>,
    path: Option<Py<PyAny>>,
    expected: Option<String>,
    got: Option<String>,
    cause: Option<String>,
) -> PyResult<ResultObj> {
    let error = build_error_from_parts(
        py, code, message, kind, metadata, op, path, expected, got, cause,
    )?;
    Ok(err(Py::new(py, error)?.into()))
}

#[allow(clippy::too_many_arguments)]
#[pyfunction(name = "bail")]
#[pyo3(signature = (code, message, *, kind = None, metadata = None, op = None, path = None, expected = None, got = None, cause = None))]
pub fn py_bail_from_parts(
    py: Python<'_>,
    code: Py<PyAny>,
    message: &str,
    kind: Option<Py<PyAny>>,
    metadata: Option<Py<PyAny>>,
    op: Option<String>,
    path: Option<Py<PyAny>>,
    expected: Option<String>,
    got: Option<String>,
    cause: Option<String>,
) -> PyResult<ResultObj> {
    let error = build_error_from_parts(
        py, code, message, kind, metadata, op, path, expected, got, cause,
    )?;
    Ok(err(Py::new(py, error)?.into()))
}

#[allow(clippy::too_many_arguments)]
#[pyfunction(name = "ensure")]
#[pyo3(signature = (condition, code, message, *, kind = None, metadata = None, op = None, path = None, expected = None, got = None, cause = None))]
pub fn py_ensure(
    py: Python<'_>,
    condition: Bound<'_, PyAny>,
    code: Py<PyAny>,
    message: &str,
    kind: Option<Py<PyAny>>,
    metadata: Option<Py<PyAny>>,
    op: Option<String>,
    path: Option<Py<PyAny>>,
    expected: Option<String>,
    got: Option<String>,
    cause: Option<String>,
) -> PyResult<ResultObj> {
    if condition.is_truthy()? {
        Ok(ok(py.None()))
    } else {
        let error = build_error_from_parts(
            py, code, message, kind, metadata, op, path, expected, got, cause,
        )?;
        Ok(err(Py::new(py, error)?.into()))
    }
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

fn clone_result_value(py: Python<'_>, out_ref: &ResultObj) -> ResultObj {
    ResultObj {
        is_ok: out_ref.is_ok,
        ok: out_ref.ok.as_ref().map(|v| v.clone_ref(py)),
        err: out_ref.err.as_ref().map(|v| v.clone_ref(py)),
    }
}

fn error_repr(err: &Error) -> String {
    format!(
        "Error(kind=ErrorKind.{}, code='{}', message='{}')",
        err.kind.as_str(),
        err.code,
        err.message
    )
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

fn error_from_exception(py: Python<'_>, py_err: PyErr) -> ResultObj {
    let err_obj = build_error_from_pyerr(py, py_err, "py_exception");
    err(err_obj.into())
}

fn extract_metadata(
    py: Python<'_>,
    metadata: Option<Py<PyAny>>,
) -> PyResult<HashMap<String, String>> {
    let mut data = HashMap::new();
    let Some(meta_value) = metadata else {
        return Ok(data);
    };
    let meta_dict = meta_value.bind(py).cast_exact::<PyDict>()?;
    for (k, v) in meta_dict.iter() {
        let key = k.extract::<String>()?;
        let value = v.extract::<String>()?;
        data.insert(key, value);
    }
    Ok(data)
}

fn extract_path(py: Python<'_>, path: Py<PyAny>) -> PyResult<Vec<PathItem>> {
    let path_value = path.bind(py);
    let list = path_value.cast_exact::<PyList>()?;
    let mut path = Vec::new();
    for item in list.iter() {
        if let Ok(key) = item.extract::<String>() {
            path.push(PathItem::Key(key));
        } else if let Ok(index) = item.extract::<usize>() {
            path.push(PathItem::Index(index));
        } else {
            return Err(PyTypeError::new_err(
                "invalid path element (expected str or int)",
            ));
        }
    }
    Ok(path)
}

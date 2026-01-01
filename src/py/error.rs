use pyo3::exceptions::{PyBaseException, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList, PyString, PyType};
use std::collections::HashMap;

// Re-export from ops to avoid duplication
pub use crate::ops::{ErrorKind, PathItem};

#[pyclass(frozen, name = "ErrorKind")]
#[derive(Clone)]
pub struct ErrorKindObj {
    pub kind: ErrorKind,
}

#[pymethods]
#[allow(non_snake_case)]
impl ErrorKindObj {
    #[classattr]
    fn InvalidInput(py: Python<'_>) -> Py<ErrorKindObj> {
        Py::new(
            py,
            ErrorKindObj {
                kind: ErrorKind::InvalidInput,
            },
        )
        .expect("ErrorKind alloc")
    }

    #[classattr]
    fn NotFound(py: Python<'_>) -> Py<ErrorKindObj> {
        Py::new(
            py,
            ErrorKindObj {
                kind: ErrorKind::NotFound,
            },
        )
        .expect("ErrorKind alloc")
    }

    #[classattr]
    fn Internal(py: Python<'_>) -> Py<ErrorKindObj> {
        Py::new(
            py,
            ErrorKindObj {
                kind: ErrorKind::Internal,
            },
        )
        .expect("ErrorKind alloc")
    }

    fn __repr__(&self) -> String {
        format!("ErrorKind.{}", self.kind.as_str())
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }

    fn __eq__(&self, other: PyRef<'_, ErrorKindObj>) -> bool {
        self.kind.as_str() == other.kind.as_str()
    }
}

#[pyclass(frozen)]
#[derive(Clone)]
pub struct RopustError {
    pub kind: ErrorKind,
    pub code: String,
    pub message: String,
    pub metadata: HashMap<String, String>,
    pub op: Option<String>,
    pub path: Vec<PathItem>,
    pub expected: Option<String>,
    pub got: Option<String>,
    pub cause: Option<String>,
}

#[pymethods]
impl RopustError {
    #[getter]
    fn kind(&self, py: Python<'_>) -> Py<ErrorKindObj> {
        Py::new(py, ErrorKindObj { kind: self.kind }).expect("ErrorKind alloc")
    }

    #[getter]
    fn code(&self) -> String {
        self.code.clone()
    }

    #[getter]
    fn message(&self) -> String {
        self.message.clone()
    }

    #[getter]
    fn metadata(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new(py);
        for (k, v) in &self.metadata {
            dict.set_item(k, v)?;
        }
        Ok(dict.into())
    }

    #[getter]
    fn op(&self) -> Option<String> {
        self.op.clone()
    }

    #[getter]
    fn path(&self, py: Python<'_>) -> Py<PyAny> {
        let list = PyList::empty(py);
        for item in &self.path {
            match item {
                PathItem::Key(value) => {
                    list.append(PyString::new(py, value)).expect("path key");
                }
                PathItem::Index(value) => {
                    list.append(*value).expect("path index");
                }
            }
        }
        list.unbind().into()
    }

    #[getter]
    fn expected(&self) -> Option<String> {
        self.expected.clone()
    }

    #[getter]
    fn got(&self) -> Option<String> {
        self.got.clone()
    }

    #[getter]
    fn cause(&self) -> Option<String> {
        self.cause.clone()
    }

    fn __repr__(&self) -> String {
        format!(
            "RopustError(kind=ErrorKind.{}, code='{}', message='{}')",
            self.kind.as_str(),
            self.code,
            self.message
        )
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }

    #[classmethod]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (code, message, *, kind = None, op = None, path = None, expected = None, got = None, metadata = None))]
    fn new(
        _cls: &Bound<'_, PyType>,
        py: Python<'_>,
        code: String,
        message: String,
        kind: Option<Py<PyAny>>,
        op: Option<String>,
        path: Option<Py<PyAny>>,
        expected: Option<String>,
        got: Option<String>,
        metadata: Option<Py<PyAny>>,
    ) -> PyResult<Self> {
        let kind = extract_kind(py, kind, ErrorKind::InvalidInput)?;
        let path = extract_path(py, path)?;
        let metadata = extract_metadata(py, metadata)?;

        Ok(RopustError {
            kind,
            code,
            message,
            metadata,
            op,
            path,
            expected,
            got,
            cause: None,
        })
    }

    #[classmethod]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (err, *, code, message, kind = None, op = None, path = None, expected = None, got = None, metadata = None))]
    fn wrap(
        _cls: &Bound<'_, PyType>,
        py: Python<'_>,
        err: Py<PyAny>,
        code: String,
        message: String,
        kind: Option<Py<PyAny>>,
        op: Option<String>,
        path: Option<Py<PyAny>>,
        expected: Option<String>,
        got: Option<String>,
        metadata: Option<Py<PyAny>>,
    ) -> PyResult<Self> {
        let err_ref = err.bind(py);
        if err_ref.is_none() {
            return Err(PyTypeError::new_err(
                "wrap expects an exception or RopustError",
            ));
        }

        let mut metadata = extract_metadata(py, metadata)?;

        let cause = if let Ok(cause_ref) = err_ref.extract::<PyRef<'_, RopustError>>() {
            Some(cause_ref.__repr__())
        } else {
            let base_exc = py.get_type::<PyBaseException>();
            if !err_ref.is_instance(base_exc.as_any())? {
                return Err(PyTypeError::new_err(
                    "wrap expects an exception or RopustError",
                ));
            }
            let py_err = PyErr::from_value(err_ref.clone());
            let cause_obj = build_ropust_error_from_pyerr(py, py_err, "py_exception");
            let cause_ref = cause_obj.bind(py).extract::<PyRef<'_, RopustError>>()?;
            if !metadata.contains_key("cause_exception") {
                if let Some(value) = cause_ref.metadata.get("exception") {
                    metadata.insert("cause_exception".to_string(), value.to_string());
                }
            }
            if !metadata.contains_key("cause_py_traceback") {
                if let Some(value) = cause_ref.metadata.get("py_traceback") {
                    metadata.insert("cause_py_traceback".to_string(), value.to_string());
                }
            }
            Some(cause_ref.__repr__())
        };

        let kind = extract_kind(py, kind, ErrorKind::Internal)?;
        let path = extract_path(py, path)?;

        Ok(RopustError {
            kind,
            code,
            message,
            metadata,
            op,
            path,
            expected,
            got,
            cause,
        })
    }

    fn to_dict(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new(py);
        dict.set_item("kind", self.kind.as_str())?;
        dict.set_item("code", self.code.clone())?;
        dict.set_item("message", self.message.clone())?;
        dict.set_item("op", self.op.clone())?;

        let path_list = PyList::empty(py);
        for item in &self.path {
            match item {
                PathItem::Key(value) => path_list.append(PyString::new(py, value))?,
                PathItem::Index(value) => path_list.append(*value)?,
            }
        }
        dict.set_item("path", path_list)?;

        dict.set_item("expected", self.expected.clone())?;
        dict.set_item("got", self.got.clone())?;
        dict.set_item("cause", self.cause.clone())?;

        let metadata_dict = PyDict::new(py);
        for (k, v) in &self.metadata {
            metadata_dict.set_item(k, v)?;
        }
        dict.set_item("metadata", metadata_dict)?;

        Ok(dict.into())
    }

    #[classmethod]
    fn from_dict(
        _cls: &Bound<'_, PyType>,
        _py: Python<'_>,
        data: Bound<'_, PyAny>,
    ) -> PyResult<Self> {
        let dict = data.cast_exact::<PyDict>()?;

        let kind_value = dict
            .get_item("kind")?
            .ok_or_else(|| PyTypeError::new_err("missing 'kind' field"))?;
        let kind = if let Ok(kind_obj) = kind_value.extract::<PyRef<'_, ErrorKindObj>>() {
            kind_obj.kind
        } else {
            let kind_str = kind_value.extract::<String>()?;
            match kind_str.as_str() {
                "InvalidInput" => ErrorKind::InvalidInput,
                "NotFound" => ErrorKind::NotFound,
                "Internal" => ErrorKind::Internal,
                _ => {
                    return Err(PyTypeError::new_err(
                        "invalid 'kind' field (expected ErrorKind or string)",
                    ))
                }
            }
        };

        let code = dict
            .get_item("code")?
            .ok_or_else(|| PyTypeError::new_err("missing 'code' field"))?
            .extract::<String>()?;
        let message = dict
            .get_item("message")?
            .ok_or_else(|| PyTypeError::new_err("missing 'message' field"))?
            .extract::<String>()?;

        let op = get_optional_string(dict, "op")?;
        let expected = get_optional_string(dict, "expected")?;
        let got = get_optional_string(dict, "got")?;
        let cause = get_optional_string(dict, "cause")?;

        let mut path = Vec::new();
        if let Some(path_value) = dict.get_item("path")? {
            let list = path_value.cast_exact::<PyList>()?;
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
        }

        let mut metadata = HashMap::new();
        if let Some(meta_value) = dict.get_item("metadata")? {
            let meta_dict = meta_value.cast_exact::<PyDict>()?;
            for (k, v) in meta_dict.iter() {
                let key = k.extract::<String>()?;
                let value = v.extract::<String>()?;
                metadata.insert(key, value);
            }
        }

        Ok(RopustError {
            kind,
            code,
            message,
            metadata,
            op,
            path,
            expected,
            got,
            cause,
        })
    }
}

#[pyfunction]
#[pyo3(signature = (exc, code = "py_exception"))]
pub fn exception_to_ropust_error(
    py: Python<'_>,
    exc: Py<PyAny>,
    code: &str,
) -> PyResult<Py<RopustError>> {
    let exc_ref = exc.bind(py);
    let base_exc = py.get_type::<PyBaseException>();
    if !exc_ref.is_instance(base_exc.as_any())? {
        return Err(PyTypeError::new_err(
            "exception_to_ropust_error expects an exception instance",
        ));
    }
    let py_err = PyErr::from_value(exc_ref.clone());
    Ok(build_ropust_error_from_pyerr(py, py_err, code))
}

pub fn build_ropust_error_from_pyerr(py: Python<'_>, py_err: PyErr, code: &str) -> Py<RopustError> {
    let mut metadata = HashMap::new();
    if let Ok(name) = py_err.get_type(py).name() {
        metadata.insert("exception".to_string(), name.to_string());
    }
    if let Some(traceback) = format_traceback(py, &py_err) {
        metadata.insert("py_traceback".to_string(), traceback);
    }
    let cause = py_err
        .value(py)
        .repr()
        .ok()
        .and_then(|s| s.to_str().ok().map(|v| v.to_string()));
    Py::new(
        py,
        RopustError {
            kind: ErrorKind::Internal,
            code: code.to_string(),
            message: py_err.to_string(),
            metadata,
            op: None,
            path: Vec::new(),
            expected: None,
            got: None,
            cause,
        },
    )
    .expect("ropust error alloc")
}

fn format_traceback(py: Python<'_>, py_err: &PyErr) -> Option<String> {
    let traceback_mod = py.import("traceback").ok()?;
    let tb = py_err.traceback(py);
    let formatted = traceback_mod
        .call_method1(
            "format_exception",
            (py_err.get_type(py), py_err.value(py), tb),
        )
        .ok()?
        .extract::<Vec<String>>()
        .ok()?;
    Some(formatted.concat())
}

fn extract_kind(
    py: Python<'_>,
    kind: Option<Py<PyAny>>,
    default_kind: ErrorKind,
) -> PyResult<ErrorKind> {
    let Some(kind_value) = kind else {
        return Ok(default_kind);
    };
    let kind_value = kind_value.bind(py);
    if let Ok(kind_obj) = kind_value.extract::<PyRef<'_, ErrorKindObj>>() {
        return Ok(kind_obj.kind);
    }
    let kind_str = kind_value.extract::<String>()?;
    match kind_str.as_str() {
        "InvalidInput" => Ok(ErrorKind::InvalidInput),
        "NotFound" => Ok(ErrorKind::NotFound),
        "Internal" => Ok(ErrorKind::Internal),
        _ => Err(PyTypeError::new_err(
            "invalid 'kind' field (expected ErrorKind or string)",
        )),
    }
}

fn extract_path(py: Python<'_>, path: Option<Py<PyAny>>) -> PyResult<Vec<PathItem>> {
    let Some(path_value) = path else {
        return Ok(Vec::new());
    };
    let path_value = path_value.bind(py);
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

fn get_optional_string(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<Option<String>> {
    if let Some(value) = dict.get_item(key)? {
        value.extract::<Option<String>>()
    } else {
        Ok(None)
    }
}

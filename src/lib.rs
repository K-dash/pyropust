mod data;
mod ops;

use data::{py_to_value, value_to_py};
use ops::{apply, OpError, OpErrorKind, OperatorKind};
use pyo3::exceptions::{PyRuntimeError, PyTypeError};
use pyo3::prelude::{PyAnyMethods, *};
use pyo3::types::{PyAny, PyDict, PyList, PyModule, PyString, PyType};
use pyo3::Bound;
use std::collections::HashMap;

#[pyclass(name = "Result")]
struct ResultObj {
    is_ok: bool,
    ok: Option<Py<PyAny>>,
    err: Option<Py<PyAny>>,
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
                return Err(PyTypeError::new_err(
                    "and_then callback must return Result",
                ));
            }
            let out_ref: PyRef<'_, ResultObj> = out.extract()?;
            Ok(ResultObj {
                is_ok: out_ref.is_ok,
                ok: out_ref.ok.as_ref().map(|v| v.clone_ref(py)),
                err: out_ref.err.as_ref().map(|v| v.clone_ref(py)),
            })
        } else {
            Ok(err(self.err.as_ref().expect("err value").clone_ref(py)))
        }
    }
}

#[pyclass(name = "Option")]
struct OptionObj {
    is_some: bool,
    value: Option<Py<PyAny>>,
}

#[pymethods]
impl OptionObj {
    fn is_some(&self) -> bool {
        self.is_some
    }

    fn is_none(&self) -> bool {
        !self.is_some
    }

    fn unwrap(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        if self.is_some {
            Ok(self.value.as_ref().expect("some value").clone_ref(py))
        } else {
            Err(PyRuntimeError::new_err("called unwrap() on None_"))
        }
    }

    fn map(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let mapped = f.call1((value.clone_ref(py),))?;
            Ok(some(mapped.into()))
        } else {
            Ok(none_())
        }
    }

    fn unwrap_or(&self, py: Python<'_>, default: Py<PyAny>) -> PyResult<Py<PyAny>> {
        if self.is_some {
            Ok(self.value.as_ref().expect("some value").clone_ref(py))
        } else {
            Ok(default.clone_ref(py))
        }
    }
}

#[pyfunction(name = "Ok")]
fn py_ok(value: Py<PyAny>) -> ResultObj {
    ok(value)
}

#[pyfunction(name = "Err")]
fn py_err(error: Py<PyAny>) -> ResultObj {
    err(error)
}

#[pyfunction(name = "Some")]
fn py_some(value: Py<PyAny>) -> OptionObj {
    some(value)
}

#[pyfunction(name = "None_")]
fn py_none() -> OptionObj {
    none_()
}

fn ok(value: Py<PyAny>) -> ResultObj {
    ResultObj {
        is_ok: true,
        ok: Some(value),
        err: None,
    }
}

fn err(error: Py<PyAny>) -> ResultObj {
    ResultObj {
        is_ok: false,
        ok: None,
        err: Some(error),
    }
}

fn some(value: Py<PyAny>) -> OptionObj {
    OptionObj {
        is_some: true,
        value: Some(value),
    }
}

fn none_() -> OptionObj {
    OptionObj {
        is_some: false,
        value: None,
    }
}


#[derive(Clone, Debug)]
enum PathItem {
    Key(String),
    Index(usize),
}

#[derive(Clone, Copy, Debug)]
enum ErrorKind {
    InvalidInput,
    NotFound,
    Internal,
}

impl ErrorKind {
    fn as_str(&self) -> &'static str {
        match self {
            ErrorKind::InvalidInput => "InvalidInput",
            ErrorKind::NotFound => "NotFound",
            ErrorKind::Internal => "Internal",
        }
    }
}

#[pyclass(frozen, name = "ErrorKind")]
#[derive(Clone)]
struct ErrorKindObj {
    kind: ErrorKind,
}

#[pymethods]
#[allow(non_snake_case)]
impl ErrorKindObj {
    #[classattr]
    fn InvalidInput(py: Python<'_>) -> Py<ErrorKindObj> {
        Py::new(py, ErrorKindObj { kind: ErrorKind::InvalidInput }).expect("ErrorKind alloc")
    }

    #[classattr]
    fn NotFound(py: Python<'_>) -> Py<ErrorKindObj> {
        Py::new(py, ErrorKindObj { kind: ErrorKind::NotFound }).expect("ErrorKind alloc")
    }

    #[classattr]
    fn Internal(py: Python<'_>) -> Py<ErrorKindObj> {
        Py::new(py, ErrorKindObj { kind: ErrorKind::Internal }).expect("ErrorKind alloc")
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
struct RopeError {
    kind: ErrorKind,
    code: String,
    message: String,
    metadata: HashMap<String, String>,
    op: Option<String>,
    path: Vec<PathItem>,
    expected: Option<String>,
    got: Option<String>,
    cause: Option<String>,
}

#[pymethods]
impl RopeError {
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
            "RopeError(kind=ErrorKind.{}, code='{}', message='{}')",
            self.kind.as_str(),
            self.code,
            self.message
        )
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

#[pyclass(frozen)]
#[derive(Clone)]
struct Operator {
    kind: OperatorKind,
}

#[pymethods]
impl Operator {
    fn __repr__(&self) -> String {
        format!("Operator.{}", self.kind.name())
    }
}

#[pyclass]
#[derive(Clone)]
struct Blueprint {
    ops: Vec<OperatorKind>,
}

#[pymethods]
impl Blueprint {
    #[new]
    fn new() -> Self {
        Blueprint { ops: Vec::new() }
    }

    #[classmethod]
    fn for_type(_cls: &Bound<'_, PyType>, _ty: &Bound<'_, PyAny>) -> Self {
        Blueprint { ops: Vec::new() }
    }

    #[classmethod]
    fn any(_cls: &Bound<'_, PyType>) -> Self {
        Blueprint { ops: Vec::new() }
    }

    fn pipe(&self, op: PyRef<'_, Operator>) -> Self {
        let mut ops = self.ops.clone();
        ops.push(op.kind.clone());
        Blueprint { ops }
    }

    fn guard_str(&self) -> Self {
        let mut ops = self.ops.clone();
        ops.push(OperatorKind::AssertStr);
        Blueprint { ops }
    }

    fn __repr__(&self) -> String {
        format!("Blueprint(ops={})", self.ops.len())
    }
}

#[pyfunction]
fn run(py: Python<'_>, blueprint: PyRef<'_, Blueprint>, input: Py<PyAny>) -> ResultObj {
    let mut current = match py_to_value(input.bind(py)) {
        Ok(value) => value,
        Err(e) => {
            return rope_error(
                py,
                ErrorKind::InvalidInput,
                e.code,
                e.message,
                None,
                Some("Input".to_string()),
                Vec::new(),
                Some(e.expected.to_string()),
                Some(e.got),
                None,
            )
        }
    };
    for op in &blueprint.ops {
        match apply(op, current) {
            Ok(value) => current = value,
            Err(e) => return op_error_to_result(py, e),
        }
    }
    ok(value_to_py(py, current))
}

fn op_error_to_result(py: Python<'_>, e: OpError) -> ResultObj {
    let kind = match e.kind {
        OpErrorKind::InvalidInput => ErrorKind::InvalidInput,
        OpErrorKind::NotFound => ErrorKind::NotFound,
    };
    let path: Vec<PathItem> = e
        .path
        .into_iter()
        .map(|p| match p {
            ops::PathItem::Key(k) => PathItem::Key(k),
            ops::PathItem::Index(i) => PathItem::Index(i),
        })
        .collect();
    rope_error(
        py,
        kind,
        e.code,
        e.message,
        None,
        Some(e.op.to_string()),
        path,
        e.expected.map(|s| s.to_string()),
        e.got,
        None,
    )
}

#[pyfunction(name = "_op_assert_str")]
fn op_assert_str() -> Operator {
    Operator {
        kind: OperatorKind::AssertStr,
    }
}

#[pyfunction(name = "_op_split")]
fn op_split(delim: String) -> Operator {
    Operator {
        kind: OperatorKind::Split { delim },
    }
}

#[pyfunction(name = "_op_index")]
fn op_index(idx: usize) -> Operator {
    Operator {
        kind: OperatorKind::Index { idx },
    }
}

#[pyfunction(name = "_op_get_key")]
fn op_get_key(key: String) -> Operator {
    Operator {
        kind: OperatorKind::GetKey { key },
    }
}

#[pyfunction(name = "_op_to_uppercase")]
fn op_to_uppercase() -> Operator {
    Operator {
        kind: OperatorKind::ToUppercase,
    }
}

fn rope_error(
    py: Python<'_>,
    kind: ErrorKind,
    code: &str,
    message: &str,
    metadata: Option<HashMap<String, String>>,
    op: Option<String>,
    path: Vec<PathItem>,
    expected: Option<String>,
    got: Option<String>,
    cause: Option<String>,
) -> ResultObj {
    let err_obj = Py::new(
        py,
        RopeError {
            kind,
            code: code.to_string(),
            message: message.to_string(),
            metadata: metadata.unwrap_or_default(),
            op,
            path,
            expected,
            got,
            cause,
        },
    )
    .expect("rope error alloc");
    err(err_obj.into())
}

#[pymodule]
fn pyrope_native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ResultObj>()?;
    m.add_class::<OptionObj>()?;
    m.add_class::<ErrorKindObj>()?;
    m.add_class::<RopeError>()?;
    m.add_class::<Operator>()?;
    m.add_class::<Blueprint>()?;
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
            "run",
        ],
    )?;

    Ok(())
}

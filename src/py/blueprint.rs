use super::error::{ErrorKind, RopeError};
use super::operator::Operator;
use super::result::{err, ok, ResultObj};
use crate::data::{py_to_value, serde_to_value, value_to_py, Value};
use crate::ops::PathItem;
use crate::ops::{apply, OpError, OperatorKind};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBytes, PyType};
use std::collections::HashMap;

#[pyclass]
#[derive(Clone)]
pub struct Blueprint {
    pub ops: Vec<OperatorKind>,
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

    /// Convenience method equivalent to `.pipe(Op.coerce.assert_str())`.
    /// Narrows the output type to `str` by asserting the value is a string.
    ///
    /// Note: If more guard methods are needed (e.g., guard_int, guard_list),
    /// consider generating them via gen_ops.py based on @ns coerce operators.
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
pub fn run(py: Python<'_>, blueprint: PyRef<'_, Blueprint>, input: Py<PyAny>) -> ResultObj {
    let mut current = if matches!(blueprint.ops.first(), Some(OperatorKind::JsonDecode)) {
        let input_any = input.bind(py);
        let parsed = if let Ok(text) = input_any.extract::<String>() {
            serde_json::from_str(&text)
        } else if let Ok(bytes) = input_any.cast_exact::<PyBytes>() {
            serde_json::from_slice(bytes.as_bytes())
        } else {
            let type_name = input_any
                .get_type()
                .name()
                .and_then(|name| name.to_str().map(|s| s.to_string()))
                .unwrap_or_else(|_| "unknown".to_string());
            return rope_error(
                py,
                ErrorKind::InvalidInput,
                "type_mismatch",
                "JSON input must be str or bytes",
                None,
                Some("JsonDecode".to_string()),
                Vec::new(),
                Some("str|bytes".to_string()),
                Some(type_name),
                None,
            );
        };

        match parsed {
            Ok(value) => serde_to_value(value),
            Err(err) => {
                return rope_error(
                    py,
                    ErrorKind::InvalidInput,
                    "json_parse_error",
                    "Failed to parse JSON",
                    None,
                    Some("JsonDecode".to_string()),
                    Vec::new(),
                    Some("valid JSON".to_string()),
                    Some(err.to_string()),
                    None,
                )
            }
        }
    } else {
        match py_to_value(input.bind(py)) {
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
        }
    };

    if matches!(blueprint.ops.first(), Some(OperatorKind::JsonDecode)) {
        for op in blueprint.ops.iter().skip(1) {
            match op {
                OperatorKind::MapPy { func } => match apply_map_py(py, func, current) {
                    Ok(value) => current = value,
                    Err(err) => return err,
                },
                _ => match apply(op, current) {
                    Ok(value) => current = value,
                    Err(e) => return op_error_to_result(py, e),
                },
            }
        }
    } else {
        for op in &blueprint.ops {
            match op {
                OperatorKind::MapPy { func } => match apply_map_py(py, func, current) {
                    Ok(value) => current = value,
                    Err(err) => return err,
                },
                _ => match apply(op, current) {
                    Ok(value) => current = value,
                    Err(e) => return op_error_to_result(py, e),
                },
            }
        }
    }

    ok(value_to_py(py, current))
}

fn apply_map_py(py: Python<'_>, func: &Py<PyAny>, value: Value) -> Result<Value, ResultObj> {
    let arg = value_to_py(py, value);
    let result = func.call1(py, (arg,)).map_err(|err| {
        let mut metadata = HashMap::new();
        if let Ok(traceback_mod) = py.import("traceback") {
            let tb = err.traceback(py);
            if let Ok(formatted) = traceback_mod
                .call_method1("format_exception", (err.get_type(py), err.value(py), tb))
                .and_then(|obj| obj.extract::<Vec<String>>())
            {
                metadata.insert("py_traceback".to_string(), formatted.concat());
            }
        }
        rope_error(
            py,
            ErrorKind::Internal,
            "py_exception",
            "Python callback raised an exception",
            if metadata.is_empty() {
                None
            } else {
                Some(metadata)
            },
            Some("MapPy".to_string()),
            Vec::new(),
            None,
            None,
            Some(err.to_string()),
        )
    })?;

    match py_to_value(result.bind(py)) {
        Ok(value) => Ok(value),
        Err(err) => Err(rope_error(
            py,
            ErrorKind::Internal,
            "py_return_invalid",
            "Python callback returned unsupported value",
            None,
            Some("MapPy".to_string()),
            Vec::new(),
            Some(err.expected.to_string()),
            Some(err.got),
            Some(err.message.to_string()),
        )),
    }
}

fn op_error_to_result(py: Python<'_>, e: OpError) -> ResultObj {
    rope_error(
        py,
        e.kind, // No conversion needed - same ErrorKind type
        e.code,
        e.message,
        None,
        Some(e.op.to_string()),
        e.path,
        e.expected.map(|s| s.to_string()),
        e.got,
        None,
    )
}

#[allow(clippy::too_many_arguments)]
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

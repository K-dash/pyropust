use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyBytes, PyDict, PyFloat, PyInt, PyList, PyString};
use std::collections::HashMap;

use super::Value;

/// Check if a Python object is a datetime instance
fn is_datetime(obj: &Bound<'_, PyAny>) -> bool {
    obj.get_type()
        .name()
        .map(|name| name == "datetime")
        .unwrap_or(false)
}

#[derive(Debug)]
pub struct ConvertError {
    pub code: &'static str,
    pub message: &'static str,
    pub expected: &'static str,
    pub got: String,
}

pub fn py_to_value(obj: &Bound<'_, PyAny>) -> Result<Value, ConvertError> {
    if obj.is_none() {
        return Ok(Value::Null);
    }
    if let Ok(value) = obj.extract::<bool>() {
        return Ok(Value::Bool(value));
    }
    // Check for exact int type first (before float, since int can be extracted as float)
    if obj.is_instance_of::<PyInt>() {
        if let Ok(value) = obj.extract::<i64>() {
            return Ok(Value::Int(value));
        }
    }
    // Check for exact float type
    if obj.is_instance_of::<PyFloat>() {
        if let Ok(value) = obj.extract::<f64>() {
            return Ok(Value::Float(value));
        }
    }
    // Fallback for numeric types
    if let Ok(value) = obj.extract::<i64>() {
        return Ok(Value::Int(value));
    }
    if let Ok(value) = obj.extract::<f64>() {
        return Ok(Value::Float(value));
    }
    if let Ok(value) = obj.extract::<String>() {
        return Ok(Value::Str(value));
    }
    if let Ok(bytes) = obj.cast_exact::<PyBytes>() {
        return Ok(Value::Bytes(bytes.as_bytes().to_vec()));
    }
    if let Ok(list) = obj.cast_exact::<PyList>() {
        let mut out = Vec::with_capacity(list.len());
        for item in list.iter() {
            out.push(py_to_value(&item)?);
        }
        return Ok(Value::List(out));
    }
    if let Ok(dict) = obj.cast_exact::<PyDict>() {
        let mut map = HashMap::new();
        for (k, v) in dict.iter() {
            let key = match k.extract::<String>() {
                Ok(value) => value,
                Err(_) => {
                    return Err(ConvertError {
                        code: "invalid_key",
                        message: "Map keys must be strings",
                        expected: "str",
                        got: "non-str".to_string(),
                    });
                }
            };
            let value = py_to_value(&v)?;
            map.insert(key, value);
        }
        return Ok(Value::Map(map));
    }
    // Check for datetime (must be before generic extraction attempts)
    if is_datetime(obj) {
        if let Ok(dt) = obj.extract::<DateTime<Utc>>() {
            return Ok(Value::DateTime(dt));
        }
    }
    let type_name = obj
        .get_type()
        .name()
        .and_then(|name| name.to_str().map(|s| s.to_string()))
        .unwrap_or_else(|_| "unknown".to_string());
    Err(ConvertError {
        code: "unsupported_type",
        message: "Unsupported input type",
        expected: "null/str/int/float/bool/bytes/datetime/list/map",
        got: type_name,
    })
}

pub fn value_to_py(py: Python<'_>, value: Value) -> Py<PyAny> {
    match value {
        Value::Null => py.None(),
        Value::Str(value) => PyString::new(py, &value).unbind().into(),
        Value::Int(value) => PyInt::new(py, value).unbind().into(),
        Value::Float(value) => PyFloat::new(py, value).unbind().into(),
        Value::Bool(value) => PyBool::new(py, value).to_owned().unbind().into(),
        Value::Bytes(value) => PyBytes::new(py, &value).unbind().into(),
        Value::DateTime(dt) => dt.into_pyobject(py).expect("datetime").unbind().into(),
        Value::List(values) => {
            let list = PyList::empty(py);
            for item in values {
                list.append(value_to_py(py, item)).expect("list append");
            }
            list.unbind().into()
        }
        Value::Map(map) => {
            let dict = PyDict::new(py);
            for (k, v) in map {
                dict.set_item(k, value_to_py(py, v)).expect("dict set");
            }
            dict.unbind().into()
        }
    }
}

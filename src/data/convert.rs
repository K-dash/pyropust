use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyBytes, PyDict, PyFloat, PyInt, PyList, PyString};
use serde_json::Value as SerdeValue;
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

pub fn serde_to_value(value: SerdeValue) -> Value {
    match value {
        SerdeValue::Null => Value::Null,
        SerdeValue::Bool(b) => Value::Bool(b),
        SerdeValue::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Int(i)
            } else if let Some(u) = n.as_u64() {
                Value::Float(u as f64)
            } else {
                Value::Float(n.as_f64().unwrap_or(0.0))
            }
        }
        SerdeValue::String(s) => Value::Str(s),
        SerdeValue::Array(items) => Value::List(items.into_iter().map(serde_to_value).collect()),
        SerdeValue::Object(obj) => {
            let mut map = HashMap::new();
            for (k, v) in obj {
                map.insert(k, serde_to_value(v));
            }
            Value::Map(map)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::serde_to_value;
    use crate::data::Value;
    use serde_json::json;

    #[test]
    fn serde_to_value_nested_structure() {
        let input = json!({
            "a": 1,
            "b": [true, null, 3.5],
        });

        let value = serde_to_value(input);
        let Value::Map(map) = value else {
            panic!("expected map");
        };

        match map.get("a") {
            Some(Value::Int(n)) => assert_eq!(*n, 1),
            other => panic!("unexpected a value: {:?}", other),
        }

        match map.get("b") {
            Some(Value::List(items)) => {
                assert!(matches!(items.first(), Some(Value::Bool(true))));
                assert!(matches!(items.get(1), Some(Value::Null)));
                match items.get(2) {
                    Some(Value::Float(f)) => assert!((*f - 3.5).abs() < 0.0001),
                    other => panic!("unexpected b[2]: {:?}", other),
                }
            }
            other => panic!("unexpected b value: {:?}", other),
        }
    }
}

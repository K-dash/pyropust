use crate::data::Value;

use super::super::error::OpError;

pub(super) fn len(op: &'static str, value: Value) -> Result<Value, OpError> {
    match value {
        Value::Str(s) => Ok(Value::Int(s.len() as i64)),
        Value::Bytes(b) => Ok(Value::Int(b.len() as i64)),
        Value::List(v) => Ok(Value::Int(v.len() as i64)),
        Value::Map(m) => Ok(Value::Int(m.len() as i64)),
        other => Err(OpError::type_mismatch(
            op,
            "str|bytes|list|map",
            other.type_name().to_string(),
        )),
    }
}

pub(super) fn is_null(_op: &'static str, value: Value) -> Result<Value, OpError> {
    Ok(Value::Bool(matches!(value, Value::Null)))
}

pub(super) fn is_empty(op: &'static str, value: Value) -> Result<Value, OpError> {
    match value {
        Value::Str(s) => Ok(Value::Bool(s.is_empty())),
        Value::Bytes(b) => Ok(Value::Bool(b.is_empty())),
        Value::List(v) => Ok(Value::Bool(v.is_empty())),
        Value::Map(m) => Ok(Value::Bool(m.is_empty())),
        other => Err(OpError::type_mismatch(
            op,
            "str|bytes|list|map",
            other.type_name().to_string(),
        )),
    }
}

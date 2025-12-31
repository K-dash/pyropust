use crate::data::Value;

use super::super::error::{ErrorKind, OpError};
use super::expect_str_value;

pub(super) fn split(op: &'static str, value: Value, delim: &str) -> Result<Value, OpError> {
    if delim.is_empty() {
        return Err(OpError {
            kind: ErrorKind::InvalidInput,
            code: "invalid_delim",
            message: "Split delimiter must not be empty",
            op,
            path: Vec::new(),
            expected: Some("non-empty string"),
            got: Some("empty string".to_string()),
        });
    }
    let text = expect_str_value(op, value)?;
    Ok(Value::List(
        text.split(delim)
            .map(|part| Value::Str(part.to_string()))
            .collect(),
    ))
}

pub(super) fn trim(op: &'static str, value: Value) -> Result<Value, OpError> {
    let text = expect_str_value(op, value)?;
    Ok(Value::Str(text.trim().to_string()))
}

pub(super) fn lower(op: &'static str, value: Value) -> Result<Value, OpError> {
    let text = expect_str_value(op, value)?;
    Ok(Value::Str(text.to_lowercase()))
}

pub(super) fn replace(
    op: &'static str,
    value: Value,
    old: &str,
    new: &str,
) -> Result<Value, OpError> {
    let text = expect_str_value(op, value)?;
    Ok(Value::Str(text.replace(old, new)))
}

pub(super) fn to_uppercase(op: &'static str, value: Value) -> Result<Value, OpError> {
    let text = expect_str_value(op, value)?;
    Ok(Value::Str(text.to_uppercase()))
}

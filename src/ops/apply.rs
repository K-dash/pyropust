use std::collections::HashMap;

use crate::data::Value;

use super::error::{OpError, OpErrorKind, PathItem};
use super::kind::OperatorKind;

pub fn apply(op: &OperatorKind, value: Value) -> Result<Value, OpError> {
    match op {
        OperatorKind::AssertStr => {
            let text = expect_str("AssertStr", value)?;
            Ok(Value::Str(text))
        }
        OperatorKind::Split { delim } => {
            if delim.is_empty() {
                return Err(OpError {
                    kind: OpErrorKind::InvalidInput,
                    code: "invalid_delim",
                    message: "Split delimiter must not be empty",
                    op: "Split",
                    path: Vec::new(),
                    expected: Some("non-empty string"),
                    got: Some("empty string".to_string()),
                });
            }
            let text = expect_str("Split", value)?;
            Ok(Value::List(
                text.split(delim)
                    .map(|part| Value::Str(part.to_string()))
                    .collect(),
            ))
        }
        OperatorKind::Index { idx } => {
            let items = expect_list("Index", value)?;
            items.get(*idx).cloned().ok_or_else(|| OpError {
                kind: OpErrorKind::NotFound,
                code: "index_out_of_range",
                message: "Index out of range",
                op: "Index",
                path: vec![PathItem::Index(*idx)],
                expected: None,
                got: None,
            })
        }
        OperatorKind::GetKey { key } => {
            let map = expect_map("GetKey", value)?;
            map.get(key).cloned().ok_or_else(|| OpError {
                kind: OpErrorKind::NotFound,
                code: "key_not_found",
                message: "Key not found",
                op: "GetKey",
                path: vec![PathItem::Key(key.clone())],
                expected: None,
                got: None,
            })
        }
        OperatorKind::ToUppercase => {
            let text = expect_str("ToUppercase", value)?;
            Ok(Value::Str(text.to_uppercase()))
        }
    }
}

fn expect_str(op: &'static str, value: Value) -> Result<String, OpError> {
    match value {
        Value::Str(text) => Ok(text),
        other => Err(OpError::type_mismatch(
            op,
            "str",
            other.type_name().to_string(),
        )),
    }
}

fn expect_list(op: &'static str, value: Value) -> Result<Vec<Value>, OpError> {
    match value {
        Value::List(items) => Ok(items),
        other => Err(OpError::type_mismatch(
            op,
            "list",
            other.type_name().to_string(),
        )),
    }
}

fn expect_map(op: &'static str, value: Value) -> Result<HashMap<String, Value>, OpError> {
    match value {
        Value::Map(map) => Ok(map),
        other => Err(OpError::type_mismatch(
            op,
            "map",
            other.type_name().to_string(),
        )),
    }
}

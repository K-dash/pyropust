use std::collections::HashMap;

use crate::interop::Value;

use super::error::{ErrorKind, OpError};
use super::kind::OperatorKind;

mod coerce;
mod core;
mod map;
mod seq;
mod text;

pub fn apply(op: &OperatorKind, value: Value) -> Result<Value, OpError> {
    let op_name = op.name();
    match op {
        OperatorKind::AssertStr => coerce::assert_str(op_name, value),
        OperatorKind::ExpectStr => coerce::expect_str(op_name, value),
        OperatorKind::AsStr => coerce::as_str(op_name, value),
        OperatorKind::AsInt => coerce::as_int(op_name, value),
        OperatorKind::AsFloat => coerce::as_float(op_name, value),
        OperatorKind::AsBool => coerce::as_bool(op_name, value),
        OperatorKind::AsDatetime { format } => coerce::as_datetime(op_name, value, format),
        OperatorKind::JsonDecode => coerce::json_decode(op_name, value),
        OperatorKind::MapPy { .. } => Err(OpError {
            kind: ErrorKind::Internal,
            code: "map_py_runtime",
            message: "map_py is only supported inside run()",
            op: op_name,
            path: Vec::new(),
            expected: None,
            got: None,
        }),
        OperatorKind::Split { delim } => text::split(op_name, value, delim),
        OperatorKind::Trim => text::trim(op_name, value),
        OperatorKind::Lower => text::lower(op_name, value),
        OperatorKind::Replace { old, new } => text::replace(op_name, value, old, new),
        OperatorKind::ToUppercase => text::to_uppercase(op_name, value),
        OperatorKind::Index { idx } => seq::index(op_name, value, *idx),
        OperatorKind::Slice { start, end } => seq::slice(op_name, value, *start, *end),
        OperatorKind::First => seq::first(op_name, value),
        OperatorKind::Last => seq::last(op_name, value),
        OperatorKind::GetKey { key } => map::get_key(op_name, value, key),
        OperatorKind::Keys => map::keys(op_name, value),
        OperatorKind::Values => map::values(op_name, value),
        OperatorKind::GetOr { .. } => Err(OpError {
            kind: ErrorKind::Internal,
            code: "get_or_runtime",
            message: "get_or is only supported inside run()",
            op: op_name,
            path: Vec::new(),
            expected: None,
            got: None,
        }),
        OperatorKind::IsNull => core::is_null(op_name, value),
        OperatorKind::IsEmpty => core::is_empty(op_name, value),
        OperatorKind::Len => core::len(op_name, value),
    }
}

fn expect_str_value(op: &'static str, value: Value) -> Result<String, OpError> {
    match value {
        Value::Str(text) => Ok(text),
        other => Err(OpError::type_mismatch(
            op,
            "str",
            other.type_name().to_string(),
        )),
    }
}

fn expect_list_value(op: &'static str, value: Value) -> Result<Vec<Value>, OpError> {
    match value {
        Value::List(items) => Ok(items),
        other => Err(OpError::type_mismatch(
            op,
            "list",
            other.type_name().to_string(),
        )),
    }
}

fn expect_map_value(op: &'static str, value: Value) -> Result<HashMap<String, Value>, OpError> {
    match value {
        Value::Map(map) => Ok(map),
        other => Err(OpError::type_mismatch(
            op,
            "map",
            other.type_name().to_string(),
        )),
    }
}

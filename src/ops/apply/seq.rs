use crate::data::Value;

use super::super::error::{ErrorKind, OpError, PathItem};
use super::expect_list_value;

pub(super) fn index(op: &'static str, value: Value, idx: usize) -> Result<Value, OpError> {
    let items = expect_list_value(op, value)?;
    items.get(idx).cloned().ok_or_else(|| OpError {
        kind: ErrorKind::NotFound,
        code: "index_out_of_range",
        message: "Index out of range",
        op,
        path: vec![PathItem::Index(idx)],
        expected: None,
        got: None,
    })
}

pub(super) fn slice(
    op: &'static str,
    value: Value,
    start: usize,
    end: usize,
) -> Result<Value, OpError> {
    let items = expect_list_value(op, value)?;
    if start > end || end > items.len() {
        return Err(OpError {
            kind: ErrorKind::InvalidInput,
            code: "slice_out_of_range",
            message: "Slice out of range",
            op,
            path: Vec::new(),
            expected: Some("valid slice bounds"),
            got: None,
        });
    }
    Ok(Value::List(items[start..end].to_vec()))
}

pub(super) fn first(op: &'static str, value: Value) -> Result<Value, OpError> {
    let items = expect_list_value(op, value)?;
    items.first().cloned().ok_or_else(|| OpError {
        kind: ErrorKind::NotFound,
        code: "empty_sequence",
        message: "Sequence is empty",
        op,
        path: Vec::new(),
        expected: None,
        got: None,
    })
}

pub(super) fn last(op: &'static str, value: Value) -> Result<Value, OpError> {
    let items = expect_list_value(op, value)?;
    items.last().cloned().ok_or_else(|| OpError {
        kind: ErrorKind::NotFound,
        code: "empty_sequence",
        message: "Sequence is empty",
        op,
        path: Vec::new(),
        expected: None,
        got: None,
    })
}

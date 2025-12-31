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

use crate::data::Value;

use super::super::error::{ErrorKind, OpError, PathItem};
use super::expect_map_value;

pub(super) fn get_key(op: &'static str, value: Value, key: &str) -> Result<Value, OpError> {
    let map = expect_map_value(op, value)?;
    map.get(key).cloned().ok_or_else(|| OpError {
        kind: ErrorKind::NotFound,
        code: "key_not_found",
        message: "Key not found",
        op,
        path: vec![PathItem::Key(key.to_string())],
        expected: None,
        got: None,
    })
}

use chrono::{NaiveDate, NaiveDateTime, NaiveTime, TimeZone, Utc};

use crate::data::Value;

use super::super::error::{ErrorKind, OpError};
use super::expect_str_value;

pub(super) fn assert_str(op: &'static str, value: Value) -> Result<Value, OpError> {
    let text = expect_str_value(op, value)?;
    Ok(Value::Str(text))
}

pub(super) fn expect_str(op: &'static str, value: Value) -> Result<Value, OpError> {
    let text = expect_str_value(op, value)?;
    Ok(Value::Str(text))
}

pub(super) fn as_int(op: &'static str, value: Value) -> Result<Value, OpError> {
    match value {
        Value::Int(n) => Ok(Value::Int(n)),
        Value::Float(f) => Ok(Value::Int(f as i64)),
        Value::Bool(b) => Ok(Value::Int(if b { 1 } else { 0 })),
        Value::Str(s) => s
            .trim()
            .parse::<i64>()
            .map(Value::Int)
            .map_err(|_| OpError {
                kind: ErrorKind::InvalidInput,
                code: "parse_error",
                message: "Failed to parse as int",
                op,
                path: Vec::new(),
                expected: Some("integer string"),
                got: Some(s),
            }),
        other => Err(OpError::type_mismatch(
            op,
            "str|int|float|bool",
            other.type_name().to_string(),
        )),
    }
}

pub(super) fn as_float(op: &'static str, value: Value) -> Result<Value, OpError> {
    match value {
        Value::Float(f) => Ok(Value::Float(f)),
        Value::Int(n) => Ok(Value::Float(n as f64)),
        Value::Str(s) => s
            .trim()
            .parse::<f64>()
            .map(Value::Float)
            .map_err(|_| OpError {
                kind: ErrorKind::InvalidInput,
                code: "parse_error",
                message: "Failed to parse as float",
                op,
                path: Vec::new(),
                expected: Some("numeric string"),
                got: Some(s),
            }),
        other => Err(OpError::type_mismatch(
            op,
            "str|int|float",
            other.type_name().to_string(),
        )),
    }
}

pub(super) fn as_bool(op: &'static str, value: Value) -> Result<Value, OpError> {
    match value {
        Value::Bool(b) => Ok(Value::Bool(b)),
        Value::Int(n) => Ok(Value::Bool(n != 0)),
        Value::Str(s) => {
            let lower = s.trim().to_lowercase();
            match lower.as_str() {
                "true" | "1" | "yes" | "on" => Ok(Value::Bool(true)),
                "false" | "0" | "no" | "off" | "" => Ok(Value::Bool(false)),
                _ => Err(OpError {
                    kind: ErrorKind::InvalidInput,
                    code: "parse_error",
                    message: "Failed to parse as bool",
                    op,
                    path: Vec::new(),
                    expected: Some("true/false/1/0/yes/no"),
                    got: Some(s),
                }),
            }
        }
        other => Err(OpError::type_mismatch(
            op,
            "str|int|bool",
            other.type_name().to_string(),
        )),
    }
}

pub(super) fn as_datetime(op: &'static str, value: Value, format: &str) -> Result<Value, OpError> {
    match value {
        Value::Str(s) => {
            let trimmed = s.trim();
            if let Ok(naive_dt) = NaiveDateTime::parse_from_str(trimmed, format) {
                return Ok(Value::DateTime(Utc.from_utc_datetime(&naive_dt)));
            }
            if let Ok(naive_date) = NaiveDate::parse_from_str(trimmed, format) {
                let naive_dt = naive_date.and_time(NaiveTime::MIN);
                return Ok(Value::DateTime(Utc.from_utc_datetime(&naive_dt)));
            }
            Err(OpError {
                kind: ErrorKind::InvalidInput,
                code: "parse_error",
                message: "Failed to parse as datetime",
                op,
                path: Vec::new(),
                expected: Some("datetime string matching format"),
                got: Some(s),
            })
        }
        Value::DateTime(dt) => Ok(Value::DateTime(dt)),
        other => Err(OpError::type_mismatch(
            op,
            "str|datetime",
            other.type_name().to_string(),
        )),
    }
}

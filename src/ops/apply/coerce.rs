use chrono::{NaiveDate, NaiveDateTime, NaiveTime, TimeZone, Utc};

use crate::interop::{serde_to_value, Value};

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

pub(super) fn as_str(op: &'static str, value: Value) -> Result<Value, OpError> {
    let text = match value {
        Value::Str(s) => s,
        Value::Bytes(bytes) => String::from_utf8(bytes).map_err(|_| OpError {
            kind: ErrorKind::InvalidInput,
            code: "invalid_utf8",
            message: "Failed to decode bytes as UTF-8",
            op,
            path: Vec::new(),
            expected: Some("utf-8 bytes"),
            got: None,
        })?,
        Value::Bool(b) => b.to_string(),
        Value::Int(n) => n.to_string(),
        Value::Float(f) => f.to_string(),
        Value::DateTime(dt) => dt.to_rfc3339(),
        Value::Null => "null".to_string(),
        other => {
            return Err(OpError::type_mismatch(
                op,
                "str|bytes|bool|int|float|datetime|null",
                other.type_name().to_string(),
            ))
        }
    };
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

pub(super) fn json_decode(op: &'static str, value: Value) -> Result<Value, OpError> {
    let parsed = match value {
        Value::Str(s) => serde_json::from_str(&s).map_err(|err| OpError {
            kind: ErrorKind::InvalidInput,
            code: "json_parse_error",
            message: "Failed to parse JSON",
            op,
            path: Vec::new(),
            expected: Some("valid JSON string"),
            got: Some(err.to_string()),
        })?,
        Value::Bytes(bytes) => serde_json::from_slice(&bytes).map_err(|err| OpError {
            kind: ErrorKind::InvalidInput,
            code: "json_parse_error",
            message: "Failed to parse JSON",
            op,
            path: Vec::new(),
            expected: Some("valid JSON bytes"),
            got: Some(err.to_string()),
        })?,
        other => {
            return Err(OpError::type_mismatch(
                op,
                "str|bytes",
                other.type_name().to_string(),
            ))
        }
    };

    Ok(serde_to_value(parsed))
}

#[cfg(test)]
mod tests {
    use super::as_str;
    use crate::interop::Value;
    use crate::ops::ErrorKind;

    #[test]
    fn as_str_invalid_utf8() {
        let value = Value::Bytes(vec![0xff, 0xfe]);
        let err = as_str("AsStr", value).unwrap_err();
        assert!(matches!(err.kind, ErrorKind::InvalidInput));
        assert_eq!(err.code, "invalid_utf8");
    }
}

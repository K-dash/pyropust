use std::collections::HashMap;

use chrono::{DateTime, Utc};

#[derive(Clone, Debug)]
pub enum Value {
    Null,
    Str(String),
    Int(i64),
    Float(f64),
    Bool(bool),
    Bytes(Vec<u8>),
    DateTime(DateTime<Utc>),
    List(Vec<Value>),
    Map(HashMap<String, Value>),
}

impl Value {
    pub fn type_name(&self) -> &'static str {
        match self {
            Value::Null => "null",
            Value::Str(_) => "str",
            Value::Int(_) => "int",
            Value::Float(_) => "float",
            Value::Bool(_) => "bool",
            Value::Bytes(_) => "bytes",
            Value::DateTime(_) => "datetime",
            Value::List(_) => "list",
            Value::Map(_) => "map",
        }
    }
}

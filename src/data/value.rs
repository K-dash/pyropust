use std::collections::HashMap;

#[derive(Clone, Debug)]
pub enum Value {
    Null,
    Str(String),
    Int(i64),
    Bool(bool),
    Bytes(Vec<u8>),
    List(Vec<Value>),
    Map(HashMap<String, Value>),
}

impl Value {
    pub fn type_name(&self) -> &'static str {
        match self {
            Value::Null => "null",
            Value::Str(_) => "str",
            Value::Int(_) => "int",
            Value::Bool(_) => "bool",
            Value::Bytes(_) => "bytes",
            Value::List(_) => "list",
            Value::Map(_) => "map",
        }
    }
}

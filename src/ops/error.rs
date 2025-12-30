#[derive(Debug, Clone, Copy)]
pub enum OpErrorKind {
    InvalidInput,
    NotFound,
}

#[derive(Debug)]
pub enum PathItem {
    Key(String),
    Index(usize),
}

#[derive(Debug)]
pub struct OpError {
    pub kind: OpErrorKind,
    pub code: &'static str,
    pub message: &'static str,
    pub op: &'static str,
    pub path: Vec<PathItem>,
    pub expected: Option<&'static str>,
    pub got: Option<String>,
}

impl OpError {
    pub fn type_mismatch(op: &'static str, expected: &'static str, got: String) -> Self {
        OpError {
            kind: OpErrorKind::InvalidInput,
            code: "type_mismatch",
            message: "Type mismatch",
            op,
            path: Vec::new(),
            expected: Some(expected),
            got: Some(got),
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub enum ErrorKind {
    InvalidInput,
    NotFound,
    Internal,
}

impl ErrorKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            ErrorKind::InvalidInput => "InvalidInput",
            ErrorKind::NotFound => "NotFound",
            ErrorKind::Internal => "Internal",
        }
    }
}

#[derive(Debug, Clone)]
pub enum PathItem {
    Key(String),
    Index(usize),
}

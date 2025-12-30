#[derive(Clone, Debug)]
pub enum OperatorKind {
    AssertStr,
    Split { delim: String },
    Index { idx: usize },
    GetKey { key: String },
    ToUppercase,
}

impl OperatorKind {
    pub fn name(&self) -> &'static str {
        match self {
            OperatorKind::AssertStr => "AssertStr",
            OperatorKind::Split { .. } => "Split",
            OperatorKind::Index { .. } => "Index",
            OperatorKind::GetKey { .. } => "GetKey",
            OperatorKind::ToUppercase => "ToUppercase",
        }
    }
}

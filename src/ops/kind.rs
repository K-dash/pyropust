#[derive(Clone, Debug)]
pub enum OperatorKind {
    /// @op name=assert_str py=assert_str
    /// @sig in=object out=str
    /// @ns coerce
    AssertStr,

    /// @op name=expect_str py=expect_str
    /// @sig in=object out=str
    /// @ns coerce
    ExpectStr,

    /// @op name=as_int py=as_int
    /// @sig in=object out=int
    /// @ns coerce
    AsInt,

    /// @op name=as_float py=as_float
    /// @sig in=object out=float
    /// @ns coerce
    AsFloat,

    /// @op name=as_bool py=as_bool
    /// @sig in=object out=bool
    /// @ns coerce
    AsBool,

    /// @op name=as_datetime py=as_datetime
    /// @sig in=object out=datetime
    /// @ns coerce
    /// @param format:str
    AsDatetime { format: String },

    /// @op name=split py=split
    /// @sig in=str out=list[str]
    /// @ns text
    /// @param delim:str
    Split { delim: String },

    /// @op name=index py=index
    /// @sig in=Sequence[object] out=object
    /// @ns seq
    /// @param idx:int
    Index { idx: usize },

    /// @op name=get py=get
    /// @sig in=Mapping[str, object] out=object
    /// @ns map
    /// @param key:str
    GetKey { key: String },

    /// @op name=to_uppercase py=to_uppercase
    /// @sig in=str out=str
    /// @ns text
    ToUppercase,

    /// @op name=len py=len
    /// @sig in=object out=int
    /// @ns core
    /// @alias text
    Len,
}

impl OperatorKind {
    pub fn name(&self) -> &'static str {
        match self {
            OperatorKind::AssertStr => "AssertStr",
            OperatorKind::ExpectStr => "ExpectStr",
            OperatorKind::AsInt => "AsInt",
            OperatorKind::AsFloat => "AsFloat",
            OperatorKind::AsBool => "AsBool",
            OperatorKind::AsDatetime { .. } => "AsDatetime",
            OperatorKind::Split { .. } => "Split",
            OperatorKind::Index { .. } => "Index",
            OperatorKind::GetKey { .. } => "GetKey",
            OperatorKind::ToUppercase => "ToUppercase",
            OperatorKind::Len => "Len",
        }
    }
}

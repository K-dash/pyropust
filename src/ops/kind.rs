use pyo3::prelude::*;

pub enum OperatorKind {
    /// @op name=assert_str py=assert_str
    /// @sig in=object out=str
    /// @ns coerce
    AssertStr,

    /// @op name=expect_str py=expect_str
    /// @sig in=object out=str
    /// @ns coerce
    ExpectStr,

    /// @op name=as_str py=as_str
    /// @sig in=object out=str
    /// @ns coerce
    AsStr,

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

    /// @op name=json_decode py=json_decode
    /// @sig in=str | bytes out=Mapping[str, object]
    /// @ns coerce
    JsonDecode,

    /// @op name=map_py py=map_py
    /// @sig in=object out=object
    /// @ns core
    /// @param func:callable
    MapPy { func: Py<PyAny> },

    /// @op name=split py=split
    /// @sig in=str out=list[str]
    /// @ns text
    /// @param delim:str
    Split { delim: String },

    /// @op name=trim py=trim
    /// @sig in=str out=str
    /// @ns text
    Trim,

    /// @op name=lower py=lower
    /// @sig in=str out=str
    /// @ns text
    Lower,

    /// @op name=replace py=replace
    /// @sig in=str out=str
    /// @ns text
    /// @param old:str
    /// @param new:str
    Replace { old: String, new: String },

    /// @op name=index py=index
    /// @sig in=Sequence[object] out=object
    /// @ns seq
    /// @param idx:int
    Index { idx: usize },

    /// @op name=slice py=slice
    /// @sig in=Sequence[object] out=list[object]
    /// @ns seq
    /// @param start:int
    /// @param end:int
    Slice { start: usize, end: usize },

    /// @op name=first py=first
    /// @sig in=Sequence[object] out=object
    /// @ns seq
    First,

    /// @op name=last py=last
    /// @sig in=Sequence[object] out=object
    /// @ns seq
    Last,

    /// @op name=get py=get
    /// @sig in=Mapping[str, object] out=object
    /// @ns map
    /// @param key:str
    GetKey { key: String },

    /// @op name=get_or py=get_or
    /// @sig in=Mapping[str, object] out=object
    /// @ns map
    /// @param key:str
    /// @param default:object
    GetOr { key: String, default: Py<PyAny> },

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

impl Clone for OperatorKind {
    fn clone(&self) -> Self {
        match self {
            OperatorKind::AssertStr => OperatorKind::AssertStr,
            OperatorKind::ExpectStr => OperatorKind::ExpectStr,
            OperatorKind::AsStr => OperatorKind::AsStr,
            OperatorKind::AsInt => OperatorKind::AsInt,
            OperatorKind::AsFloat => OperatorKind::AsFloat,
            OperatorKind::AsBool => OperatorKind::AsBool,
            OperatorKind::AsDatetime { format } => OperatorKind::AsDatetime {
                format: format.clone(),
            },
            OperatorKind::JsonDecode => OperatorKind::JsonDecode,
            OperatorKind::MapPy { func } => Python::attach(|py| OperatorKind::MapPy {
                func: func.clone_ref(py),
            }),
            OperatorKind::Split { delim } => OperatorKind::Split {
                delim: delim.clone(),
            },
            OperatorKind::Trim => OperatorKind::Trim,
            OperatorKind::Lower => OperatorKind::Lower,
            OperatorKind::Replace { old, new } => OperatorKind::Replace {
                old: old.clone(),
                new: new.clone(),
            },
            OperatorKind::Index { idx } => OperatorKind::Index { idx: *idx },
            OperatorKind::Slice { start, end } => OperatorKind::Slice {
                start: *start,
                end: *end,
            },
            OperatorKind::First => OperatorKind::First,
            OperatorKind::Last => OperatorKind::Last,
            OperatorKind::GetKey { key } => OperatorKind::GetKey { key: key.clone() },
            OperatorKind::GetOr { key, default } => Python::attach(|py| OperatorKind::GetOr {
                key: key.clone(),
                default: default.clone_ref(py),
            }),
            OperatorKind::ToUppercase => OperatorKind::ToUppercase,
            OperatorKind::Len => OperatorKind::Len,
        }
    }
}

impl OperatorKind {
    pub fn name(&self) -> &'static str {
        match self {
            OperatorKind::AssertStr => "AssertStr",
            OperatorKind::ExpectStr => "ExpectStr",
            OperatorKind::AsStr => "AsStr",
            OperatorKind::AsInt => "AsInt",
            OperatorKind::AsFloat => "AsFloat",
            OperatorKind::AsBool => "AsBool",
            OperatorKind::AsDatetime { .. } => "AsDatetime",
            OperatorKind::JsonDecode => "JsonDecode",
            OperatorKind::MapPy { .. } => "MapPy",
            OperatorKind::Split { .. } => "Split",
            OperatorKind::Trim => "Trim",
            OperatorKind::Lower => "Lower",
            OperatorKind::Replace { .. } => "Replace",
            OperatorKind::Index { .. } => "Index",
            OperatorKind::Slice { .. } => "Slice",
            OperatorKind::First => "First",
            OperatorKind::Last => "Last",
            OperatorKind::GetKey { .. } => "GetKey",
            OperatorKind::GetOr { .. } => "GetOr",
            OperatorKind::ToUppercase => "ToUppercase",
            OperatorKind::Len => "Len",
        }
    }
}

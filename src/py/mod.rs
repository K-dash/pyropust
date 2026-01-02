mod error;
mod option;
mod result;

pub use error::{exception_to_error, Error, ErrorKindObj};
pub use option::{py_none, py_some, OptionObj};
pub use result::{py_bail_from_parts, py_ensure, py_err, py_err_from_parts, py_ok, ResultObj};

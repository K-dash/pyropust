use pyo3::exceptions::{PyRuntimeError, PyTypeError};
use pyo3::prelude::*;

#[pyclass(name = "Option")]
pub struct OptionObj {
    pub is_some: bool,
    pub value: Option<Py<PyAny>>,
}

#[pymethods]
impl OptionObj {
    fn is_some(&self) -> bool {
        self.is_some
    }

    fn is_none(&self) -> bool {
        !self.is_some
    }

    fn unwrap(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        if self.is_some {
            Ok(self.value.as_ref().expect("some value").clone_ref(py))
        } else {
            Err(PyRuntimeError::new_err("called unwrap() on None_"))
        }
    }

    fn map(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let mapped = f.call1((value.clone_ref(py),))?;
            Ok(some(mapped.into()))
        } else {
            Ok(none_())
        }
    }

    fn unwrap_or(&self, py: Python<'_>, default: Py<PyAny>) -> PyResult<Py<PyAny>> {
        if self.is_some {
            Ok(self.value.as_ref().expect("some value").clone_ref(py))
        } else {
            Ok(default.clone_ref(py))
        }
    }

    // Query methods
    fn is_some_and(&self, py: Python<'_>, predicate: Bound<'_, PyAny>) -> PyResult<bool> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let result = predicate.call1((value.clone_ref(py),))?;
            result.is_truthy()
        } else {
            Ok(false)
        }
    }

    fn is_none_or(&self, py: Python<'_>, predicate: Bound<'_, PyAny>) -> PyResult<bool> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let result = predicate.call1((value.clone_ref(py),))?;
            result.is_truthy()
        } else {
            Ok(true)
        }
    }

    // Extraction methods
    fn expect(&self, py: Python<'_>, msg: &str) -> PyResult<Py<PyAny>> {
        if self.is_some {
            Ok(self.value.as_ref().expect("some value").clone_ref(py))
        } else {
            Err(PyRuntimeError::new_err(msg.to_string()))
        }
    }

    fn unwrap_or_else(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        if self.is_some {
            Ok(self.value.as_ref().expect("some value").clone_ref(py))
        } else {
            let result = f.call0()?;
            Ok(result.into())
        }
    }

    // Transformation methods
    fn map_or(
        &self,
        py: Python<'_>,
        default: Py<PyAny>,
        f: Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let result = f.call1((value.clone_ref(py),))?;
            Ok(result.into())
        } else {
            Ok(default)
        }
    }

    fn map_or_else(
        &self,
        py: Python<'_>,
        default_f: Bound<'_, PyAny>,
        f: Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let result = f.call1((value.clone_ref(py),))?;
            Ok(result.into())
        } else {
            let result = default_f.call0()?;
            Ok(result.into())
        }
    }

    fn inspect(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            f.call1((value.clone_ref(py),))?;
        }
        Ok(OptionObj {
            is_some: self.is_some,
            value: self.value.as_ref().map(|v| v.clone_ref(py)),
        })
    }

    fn filter(&self, py: Python<'_>, predicate: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let result = predicate.call1((value.clone_ref(py),))?;
            if result.is_truthy()? {
                Ok(some(value.clone_ref(py)))
            } else {
                Ok(none_())
            }
        } else {
            Ok(none_())
        }
    }

    // Composition methods
    fn and_(&self, py: Python<'_>, other: &Self) -> Self {
        if self.is_some {
            OptionObj {
                is_some: other.is_some,
                value: other.value.as_ref().map(|v| v.clone_ref(py)),
            }
        } else {
            none_()
        }
    }

    fn and_then(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_some {
            let value = self.value.as_ref().expect("some value");
            let out = f.call1((value.clone_ref(py),))?;
            let option_type = py.get_type::<OptionObj>();
            if !out.is_instance(option_type.as_any())? {
                return Err(PyTypeError::new_err("and_then callback must return Option"));
            }
            let out_ref: PyRef<'_, OptionObj> = out.extract()?;
            Ok(clone_option(py, &out_ref))
        } else {
            Ok(none_())
        }
    }

    fn or_(&self, py: Python<'_>, other: &Self) -> Self {
        if self.is_some {
            OptionObj {
                is_some: self.is_some,
                value: self.value.as_ref().map(|v| v.clone_ref(py)),
            }
        } else {
            OptionObj {
                is_some: other.is_some,
                value: other.value.as_ref().map(|v| v.clone_ref(py)),
            }
        }
    }

    fn or_else(&self, py: Python<'_>, f: Bound<'_, PyAny>) -> PyResult<Self> {
        if self.is_some {
            Ok(OptionObj {
                is_some: self.is_some,
                value: self.value.as_ref().map(|v| v.clone_ref(py)),
            })
        } else {
            let out = f.call0()?;
            let option_type = py.get_type::<OptionObj>();
            if !out.is_instance(option_type.as_any())? {
                return Err(PyTypeError::new_err("or_else callback must return Option"));
            }
            let out_ref: PyRef<'_, OptionObj> = out.extract()?;
            Ok(clone_option(py, &out_ref))
        }
    }

    fn xor(&self, py: Python<'_>, other: &Self) -> Self {
        match (self.is_some, other.is_some) {
            (true, false) => OptionObj {
                is_some: true,
                value: self.value.as_ref().map(|v| v.clone_ref(py)),
            },
            (false, true) => OptionObj {
                is_some: true,
                value: other.value.as_ref().map(|v| v.clone_ref(py)),
            },
            _ => none_(),
        }
    }
}

// Python-facing constructor functions
#[pyfunction(name = "Some")]
pub fn py_some(value: Py<PyAny>) -> OptionObj {
    some(value)
}

#[pyfunction(name = "None_")]
pub fn py_none() -> OptionObj {
    none_()
}

// Internal constructor functions
pub fn some(value: Py<PyAny>) -> OptionObj {
    OptionObj {
        is_some: true,
        value: Some(value),
    }
}

pub fn none_() -> OptionObj {
    OptionObj {
        is_some: false,
        value: None,
    }
}

fn clone_option(py: Python<'_>, out_ref: &PyRef<'_, OptionObj>) -> OptionObj {
    OptionObj {
        is_some: out_ref.is_some,
        value: out_ref.value.as_ref().map(|v| v.clone_ref(py)),
    }
}

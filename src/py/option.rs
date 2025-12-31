use pyo3::exceptions::PyRuntimeError;
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

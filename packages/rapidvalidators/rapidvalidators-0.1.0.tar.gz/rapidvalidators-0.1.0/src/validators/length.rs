//! Length validation module

use super::validation_result;
use pyo3::prelude::*;

pub fn validate_length(value: &str, min_val: Option<usize>, max_val: Option<usize>) -> bool {
    let len = value.len();
    if let Some(m) = min_val {
        if len < m {
            return false;
        }
    }
    if let Some(m) = max_val {
        if len > m {
            return false;
        }
    }
    true
}

#[pyfunction]
#[pyo3(name = "length", signature = (value, /, *, min_val=None, max_val=None))]
pub fn py_length(
    py: Python<'_>,
    value: &str,
    min_val: Option<usize>,
    max_val: Option<usize>,
) -> PyResult<PyObject> {
    validation_result(
        py,
        validate_length(value, min_val, max_val),
        "length",
        value,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_length() {
        assert!(validate_length("hello", Some(1), Some(10)));
        assert!(!validate_length("hello", Some(10), None)); // too short
        assert!(!validate_length("hello", None, Some(3))); // too long
        assert!(validate_length("hello", None, None)); // no limits
    }
}

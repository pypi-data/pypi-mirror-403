//! Between validation module

use pyo3::prelude::*;
use pyo3::types::PyDict;

pub fn validate_between(value: f64, min_val: Option<f64>, max_val: Option<f64>) -> bool {
    if let Some(min) = min_val {
        if value < min {
            return false;
        }
    }
    if let Some(max) = max_val {
        if value > max {
            return false;
        }
    }
    true
}

#[pyfunction]
#[pyo3(name = "between", signature = (value, /, *, min_val=None, max_val=None))]
pub fn py_between(
    py: Python<'_>,
    value: f64,
    min_val: Option<f64>,
    max_val: Option<f64>,
) -> PyResult<PyObject> {
    if validate_between(value, min_val, max_val) {
        Ok(true.to_object(py))
    } else {
        let ve = py.get_type_bound::<crate::PyValidationError>();
        let args = PyDict::new_bound(py);
        args.set_item("value", value)?;
        if let Some(min) = min_val {
            args.set_item("min_val", min)?;
        }
        if let Some(max) = max_val {
            args.set_item("max_val", max)?;
        }
        Ok(ve.call1(("between", args.to_object(py), ""))?.to_object(py))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_between() {
        assert!(validate_between(5.0, Some(1.0), Some(10.0)));
        assert!(!validate_between(0.0, Some(1.0), Some(10.0)));
        // Test with no limits
        assert!(validate_between(5.0, None, None));
        assert!(validate_between(5.0, Some(1.0), None));
        assert!(validate_between(5.0, None, Some(10.0)));
    }
}

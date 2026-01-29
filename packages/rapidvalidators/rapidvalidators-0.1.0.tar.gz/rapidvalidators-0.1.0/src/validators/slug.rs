//! Slug validation module

use super::validation_result;
use once_cell::sync::Lazy;
use pyo3::prelude::*;
use regex::Regex;

static SLUG_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[a-z0-9]+(?:-[a-z0-9]+)*$").unwrap());

pub fn validate_slug(value: &str) -> bool {
    !value.is_empty() && SLUG_PATTERN.is_match(value)
}

#[pyfunction]
#[pyo3(name = "slug", signature = (value, /))]
pub fn py_slug(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    validation_result(py, validate_slug(value), "slug", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_slug() {
        assert!(validate_slug("hello-world"));
        assert!(!validate_slug("Hello-World"));
    }
}

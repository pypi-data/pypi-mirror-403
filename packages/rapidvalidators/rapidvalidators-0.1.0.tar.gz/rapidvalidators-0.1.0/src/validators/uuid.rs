//! UUID validation module

use super::validation_result;
use once_cell::sync::Lazy;
use pyo3::prelude::*;
use regex::Regex;

// UUID with dashes: 8-4-4-4-12 format
static UUID_DASHED_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        .unwrap()
});

// UUID without dashes: 32 hex characters
static UUID_NO_DASHES_PATTERN: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^[0-9a-fA-F]{32}$").unwrap());

pub fn validate_uuid(value: &str) -> bool {
    !value.is_empty()
        && (UUID_DASHED_PATTERN.is_match(value) || UUID_NO_DASHES_PATTERN.is_match(value))
}

#[pyfunction]
#[pyo3(name = "uuid", signature = (value, /))]
pub fn py_uuid(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    validation_result(py, validate_uuid(value), "uuid", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_uuid() {
        // With dashes
        assert!(validate_uuid("2bc1c94f-0deb-43e9-92a1-4775189ec9f8"));
        // Without dashes (32 hex chars)
        assert!(validate_uuid("2bc1c94f0deb43e992a14775189ec9f8"));
        // Invalid
        assert!(!validate_uuid("not-a-uuid"));
        assert!(!validate_uuid(""));
    }
}

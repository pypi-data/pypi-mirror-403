//! Encoding validators

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;

static BASE16_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9A-Fa-f]+$").unwrap());
static BASE32_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[A-Z2-7]+=*$").unwrap());
static BASE58_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+$").unwrap()
});
static BASE64_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[A-Za-z0-9+/]*={0,2}$").unwrap());
static BASE64_URL: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[A-Za-z0-9_-]*={0,2}$").unwrap());

pub fn validate_base16(value: &str) -> bool {
    !value.is_empty() && BASE16_PATTERN.is_match(value)
}
pub fn validate_base32(value: &str) -> bool {
    !value.is_empty() && BASE32_PATTERN.is_match(value)
}
pub fn validate_base58(value: &str) -> bool {
    !value.is_empty() && BASE58_PATTERN.is_match(value)
}
pub fn validate_base64(value: &str, url_safe: bool) -> bool {
    if value.is_empty() {
        return false;
    }
    let padding = value.chars().rev().take_while(|&c| c == '=').count();
    if padding > 2 {
        return false;
    }
    if url_safe {
        BASE64_URL.is_match(value)
    } else {
        BASE64_PATTERN.is_match(value)
    }
}

fn simple_result(py: Python<'_>, valid: bool, name: &str, value: &str) -> PyResult<PyObject> {
    if valid {
        Ok(true.to_object(py))
    } else {
        let ve = py.get_type_bound::<crate::PyValidationError>();
        let args = PyDict::new_bound(py);
        args.set_item("value", value)?;
        Ok(ve.call1((name, args.to_object(py), ""))?.to_object(py))
    }
}

#[pyfunction]
#[pyo3(name = "base16", signature = (value, /))]
pub fn py_base16(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    simple_result(py, validate_base16(value), "base16", value)
}

#[pyfunction]
#[pyo3(name = "base32", signature = (value, /))]
pub fn py_base32(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    simple_result(py, validate_base32(value), "base32", value)
}

#[pyfunction]
#[pyo3(name = "base58", signature = (value, /))]
pub fn py_base58(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    simple_result(py, validate_base58(value), "base58", value)
}

#[pyfunction]
#[pyo3(name = "base64", signature = (value, /, *, url_safe=false))]
pub fn py_base64(py: Python<'_>, value: &str, url_safe: bool) -> PyResult<PyObject> {
    simple_result(py, validate_base64(value, url_safe), "base64", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_base16() {
        assert!(validate_base16("deadbeef"));
        assert!(validate_base16("abc"));
    }
    #[test]
    fn test_base58() {
        assert!(validate_base58("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"));
    }
    #[test]
    fn test_base64() {
        assert!(validate_base64("SGVsbG8=", false));
    }
}

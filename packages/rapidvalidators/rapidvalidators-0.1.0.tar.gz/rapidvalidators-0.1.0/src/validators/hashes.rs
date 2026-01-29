//! Hash validators

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;

static MD5: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9a-fA-F]{32}$").unwrap());
static SHA1: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9a-fA-F]{40}$").unwrap());
static SHA224: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9a-fA-F]{56}$").unwrap());
static SHA256: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9a-fA-F]{64}$").unwrap());
static SHA384: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9a-fA-F]{96}$").unwrap());
static SHA512: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9a-fA-F]{128}$").unwrap());

pub fn validate_md5(v: &str) -> bool {
    !v.is_empty() && MD5.is_match(v)
}
pub fn validate_sha1(v: &str) -> bool {
    !v.is_empty() && SHA1.is_match(v)
}
pub fn validate_sha224(v: &str) -> bool {
    !v.is_empty() && SHA224.is_match(v)
}
pub fn validate_sha256(v: &str) -> bool {
    !v.is_empty() && SHA256.is_match(v)
}
pub fn validate_sha384(v: &str) -> bool {
    !v.is_empty() && SHA384.is_match(v)
}
pub fn validate_sha512(v: &str) -> bool {
    !v.is_empty() && SHA512.is_match(v)
}

fn hash_result(py: Python<'_>, valid: bool, name: &str, value: &str) -> PyResult<PyObject> {
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
#[pyo3(name = "md5", signature = (value, /))]
pub fn py_md5(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    hash_result(py, validate_md5(value), "md5", value)
}
#[pyfunction]
#[pyo3(name = "sha1", signature = (value, /))]
pub fn py_sha1(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    hash_result(py, validate_sha1(value), "sha1", value)
}
#[pyfunction]
#[pyo3(name = "sha224", signature = (value, /))]
pub fn py_sha224(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    hash_result(py, validate_sha224(value), "sha224", value)
}
#[pyfunction]
#[pyo3(name = "sha256", signature = (value, /))]
pub fn py_sha256(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    hash_result(py, validate_sha256(value), "sha256", value)
}
#[pyfunction]
#[pyo3(name = "sha384", signature = (value, /))]
pub fn py_sha384(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    hash_result(py, validate_sha384(value), "sha384", value)
}
#[pyfunction]
#[pyo3(name = "sha512", signature = (value, /))]
pub fn py_sha512(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    hash_result(py, validate_sha512(value), "sha512", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_hashes() {
        assert!(validate_md5("d41d8cd98f00b204e9800998ecf8427e"));
        assert!(validate_sha256(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ));
    }
}

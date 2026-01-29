//! MAC address validation module

use super::validation_result;
use pyo3::prelude::*;

/// Validate MAC address - matches original validators library behavior
/// Accepts: colon-separated, hyphen-separated, dot-separated, and mixed colon/hyphen
/// Rejects: plain format without separators
pub fn validate_mac_address(value: &str) -> bool {
    // Must be exactly 17 characters for separated format (with : or -)
    // or exactly 14 characters for dot format (xxxx.xxxx.xxxx)
    let len = value.len();

    if len == 17 {
        // Check for colon, hyphen, or mixed format (original accepts mixed!)
        let bytes = value.as_bytes();
        for (i, &b) in bytes.iter().enumerate() {
            match i % 3 {
                0 | 1 => {
                    if !b.is_ascii_hexdigit() {
                        return false;
                    }
                }
                2 => {
                    // Accept either colon or hyphen as separator (mixed allowed)
                    if b != b':' && b != b'-' {
                        return false;
                    }
                }
                _ => unreachable!(),
            }
        }
        true
    } else if len == 14 {
        // Dot format: xxxx.xxxx.xxxx
        let bytes = value.as_bytes();
        for (i, &b) in bytes.iter().enumerate() {
            match i {
                4 | 9 => {
                    if b != b'.' {
                        return false;
                    }
                }
                _ => {
                    if !b.is_ascii_hexdigit() {
                        return false;
                    }
                }
            }
        }
        true
    } else {
        // Reject plain format (12 chars without separators) and other lengths
        false
    }
}

#[pyfunction]
#[pyo3(name = "mac_address", signature = (value, /))]
pub fn py_mac_address(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    validation_result(py, validate_mac_address(value), "mac_address", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_mac() {
        assert!(validate_mac_address("00:11:22:33:44:55"));
        assert!(validate_mac_address("00-11-22-33-44-55"));
        assert!(!validate_mac_address("invalid"));
    }
}

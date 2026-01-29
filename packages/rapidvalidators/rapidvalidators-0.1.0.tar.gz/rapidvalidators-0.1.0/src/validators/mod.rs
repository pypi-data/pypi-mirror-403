//! Validators module

pub mod between;
pub mod card;
pub mod country;
pub mod cron;
pub mod crypto_address;
pub mod domain;
pub mod email;
pub mod encoding;
pub mod finance;
pub mod hashes;
pub mod hostname;
pub mod i18n;
pub mod ip_address;
pub mod length;
pub mod mac_address;
pub mod slug;
pub mod url;
pub mod uuid;

use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Helper to create validation result - returns True or ValidationError
pub fn validation_result(
    py: Python<'_>,
    valid: bool,
    func_name: &str,
    value: &str,
) -> PyResult<PyObject> {
    if valid {
        Ok(true.to_object(py))
    } else {
        let ve_type = py.get_type_bound::<crate::PyValidationError>();
        let args = PyDict::new_bound(py);
        args.set_item("value", value)?;
        let error = ve_type.call1((func_name, args.to_object(py), ""))?;
        Ok(error.to_object(py))
    }
}

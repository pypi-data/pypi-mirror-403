//! Card validators

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;

// Visa: starts with 4, 16 or 19 digits (NOT 13 - original library rejects 13-digit)
static VISA: Lazy<Regex> = Lazy::new(|| Regex::new(r"^4\d{15}(?:\d{3})?$").unwrap());
static MC: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^(?:5[1-5]\d{2}|222[1-9]|22[3-9]\d|2[3-6]\d{2}|27[01]\d|2720)\d{12}$").unwrap()
});
static AMEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^3[47]\d{13}$").unwrap());
static DISC: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^(?:6011|65\d{2}|64[4-9]\d)\d{12}(?:\d{3})?$").unwrap());
static DINERS: Lazy<Regex> = Lazy::new(|| Regex::new(r"^3(?:0[0-5]|[68]\d)\d{11,16}$").unwrap());
static JCB: Lazy<Regex> = Lazy::new(|| Regex::new(r"^(?:2131|1800|35\d{3})\d{11,16}$").unwrap());
static MIR: Lazy<Regex> = Lazy::new(|| Regex::new(r"^220[0-4]\d{12}$").unwrap());
static UNION: Lazy<Regex> = Lazy::new(|| Regex::new(r"^62\d{14,17}$").unwrap());

fn luhn(s: &str) -> bool {
    let d: Vec<u32> = s
        .chars()
        .filter(|c| c.is_ascii_digit())
        .map(|c| c.to_digit(10).unwrap())
        .collect();
    if d.is_empty() {
        return false;
    }
    let sum: u32 = d
        .iter()
        .rev()
        .enumerate()
        .map(|(i, &x)| {
            if i % 2 == 1 {
                let y = x * 2;
                if y > 9 {
                    y - 9
                } else {
                    y
                }
            } else {
                x
            }
        })
        .sum();
    sum % 10 == 0
}
fn norm(v: &str) -> String {
    v.chars().filter(|c| c.is_ascii_digit()).collect()
}

pub fn validate_card_number(v: &str) -> bool {
    let n = norm(v);
    n.len() >= 12 && n.len() <= 19 && luhn(&n)
}
pub fn validate_visa(v: &str) -> bool {
    let n = norm(v);
    VISA.is_match(&n) && luhn(&n)
}
pub fn validate_mastercard(v: &str) -> bool {
    let n = norm(v);
    MC.is_match(&n) && luhn(&n)
}
pub fn validate_amex(v: &str) -> bool {
    let n = norm(v);
    AMEX.is_match(&n) && luhn(&n)
}
pub fn validate_discover(v: &str) -> bool {
    let n = norm(v);
    DISC.is_match(&n) && luhn(&n)
}
pub fn validate_diners(v: &str) -> bool {
    let n = norm(v);
    DINERS.is_match(&n) && luhn(&n)
}
pub fn validate_jcb(v: &str) -> bool {
    let n = norm(v);
    JCB.is_match(&n) && luhn(&n)
}
pub fn validate_mir(v: &str) -> bool {
    let n = norm(v);
    MIR.is_match(&n) && luhn(&n)
}
pub fn validate_unionpay(v: &str) -> bool {
    let n = norm(v);
    UNION.is_match(&n) && luhn(&n)
}

fn card_result(py: Python<'_>, valid: bool, name: &str, value: &str) -> PyResult<PyObject> {
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
#[pyo3(name = "card_number", signature = (value, /))]
pub fn py_card_number(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_card_number(value), "card_number", value)
}
#[pyfunction]
#[pyo3(name = "visa", signature = (value, /))]
pub fn py_visa(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_visa(value), "visa", value)
}
#[pyfunction]
#[pyo3(name = "mastercard", signature = (value, /))]
pub fn py_mastercard(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_mastercard(value), "mastercard", value)
}
#[pyfunction]
#[pyo3(name = "amex", signature = (value, /))]
pub fn py_amex(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_amex(value), "amex", value)
}
#[pyfunction]
#[pyo3(name = "discover", signature = (value, /))]
pub fn py_discover(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_discover(value), "discover", value)
}
#[pyfunction]
#[pyo3(name = "diners", signature = (value, /))]
pub fn py_diners(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_diners(value), "diners", value)
}
#[pyfunction]
#[pyo3(name = "jcb", signature = (value, /))]
pub fn py_jcb(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_jcb(value), "jcb", value)
}
#[pyfunction]
#[pyo3(name = "mir", signature = (value, /))]
pub fn py_mir(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_mir(value), "mir", value)
}
#[pyfunction]
#[pyo3(name = "unionpay", signature = (value, /))]
pub fn py_unionpay(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    card_result(py, validate_unionpay(value), "unionpay", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_cards() {
        assert!(validate_visa("4532015112830366"));
        assert!(validate_mastercard("5425233430109903"));
    }
}

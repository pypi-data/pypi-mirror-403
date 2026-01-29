//! Finance validators

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;

static CUSIP_PAT: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[0-9A-Z]{9}$").unwrap());
static ISIN_PAT: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[A-Z]{2}[A-Z0-9]{9}\d$").unwrap());
static SEDOL_PAT: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^[0-9BCDFGHJKLMNPQRSTVWXYZ]{7}$").unwrap());

fn luhn(s: &str) -> bool {
    let d: Vec<u32> = s.chars().filter_map(|c| c.to_digit(10)).collect();
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

/// IBAN validator - matches original validators library behavior exactly
/// The original library does NOT normalize case or remove spaces
/// It requires the IBAN to be uppercase with no spaces
pub fn validate_iban(v: &str) -> bool {
    // Original library requires exact format: no spaces, uppercase only
    let len = v.len();
    if len < 15 || len > 34 {
        return false;
    }

    // Validate all characters are uppercase letters or digits (no spaces, no lowercase)
    let bytes = v.as_bytes();
    for &b in bytes {
        match b {
            b'A'..=b'Z' | b'0'..=b'9' => {}
            _ => return false, // Reject spaces, lowercase, dashes, etc.
        }
    }

    // Validate format: 2 letters + 2 digits + alphanumeric
    if !bytes[0].is_ascii_uppercase() || !bytes[1].is_ascii_uppercase() {
        return false;
    }
    if !bytes[2].is_ascii_digit() || !bytes[3].is_ascii_digit() {
        return false;
    }

    // Calculate mod97 on rearranged IBAN (move first 4 chars to end)
    // For each letter A=10, B=11, etc. For digits, use digit value
    let mut remainder: u64 = 0;

    // Process bytes[4..] first, then bytes[0..4]
    for &b in bytes[4..].iter().chain(bytes[0..4].iter()) {
        if b.is_ascii_digit() {
            remainder = (remainder * 10 + (b - b'0') as u64) % 97;
        } else {
            let val = (b - b'A' + 10) as u64;
            remainder = (remainder * 100 + val) % 97;
        }
    }

    remainder == 1
}
pub fn validate_cusip(v: &str) -> bool {
    let v = v.to_uppercase();
    if !CUSIP_PAT.is_match(&v) {
        return false;
    }
    let c: Vec<char> = v.chars().collect();
    let mut sum = 0u32;
    for (i, &ch) in c[..8].iter().enumerate() {
        let mut val = if ch.is_ascii_digit() {
            ch.to_digit(10).unwrap()
        } else {
            (ch as u32) - ('A' as u32) + 10
        };
        if i % 2 == 1 {
            val *= 2;
        }
        sum += val / 10 + val % 10;
    }
    c[8].to_digit(10) == Some((10 - (sum % 10)) % 10)
}
pub fn validate_isin(v: &str) -> bool {
    let v = v.to_uppercase();
    if !ISIN_PAT.is_match(&v) {
        return false;
    }
    let n: String = v
        .chars()
        .map(|c| {
            if c.is_ascii_digit() {
                c.to_string()
            } else {
                ((c as u32) - ('A' as u32) + 10).to_string()
            }
        })
        .collect();
    luhn(&n)
}
pub fn validate_sedol(v: &str) -> bool {
    let v = v.to_uppercase();
    if !SEDOL_PAT.is_match(&v) {
        return false;
    }
    let w = [1u32, 3, 1, 7, 3, 9, 1];
    let c: Vec<char> = v.chars().collect();
    let sum: u32 = c
        .iter()
        .zip(w.iter())
        .map(|(&ch, &wt)| {
            let val = if ch.is_ascii_digit() {
                ch.to_digit(10).unwrap()
            } else {
                (ch as u32) - ('A' as u32) + 10
            };
            val * wt
        })
        .sum();
    sum % 10 == 0
}

fn fin_result(py: Python<'_>, valid: bool, name: &str, value: &str) -> PyResult<PyObject> {
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
#[pyo3(name = "iban", signature = (value, /))]
pub fn py_iban(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    fin_result(py, validate_iban(value), "iban", value)
}
#[pyfunction]
#[pyo3(name = "cusip", signature = (value, /))]
pub fn py_cusip(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    fin_result(py, validate_cusip(value), "cusip", value)
}
#[pyfunction]
#[pyo3(name = "isin", signature = (value, /))]
pub fn py_isin(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    fin_result(py, validate_isin(value), "isin", value)
}
#[pyfunction]
#[pyo3(name = "sedol", signature = (value, /))]
pub fn py_sedol(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    fin_result(py, validate_sedol(value), "sedol", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_finance() {
        assert!(validate_iban("GB82WEST12345698765432"));
        assert!(validate_isin("US0378331005"));
    }
}

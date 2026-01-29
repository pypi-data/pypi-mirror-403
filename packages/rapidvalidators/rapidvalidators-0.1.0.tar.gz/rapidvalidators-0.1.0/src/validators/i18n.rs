//! International ID validators

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;

static ES_NIF: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\d{8}[A-Z]$").unwrap());
static ES_NIE: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[XYZ]\d{7}[A-Z]$").unwrap());
static ES_CIF: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]$").unwrap());
static FI_BID: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\d{7}-\d$").unwrap());
static IND_AADHAR: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\d{4}\s?\d{4}\s?\d{4}$").unwrap());
static IND_PAN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[A-Z]{5}\d{4}[A-Z]$").unwrap());

pub fn validate_es_nif(v: &str) -> bool {
    let v = v.to_uppercase();
    if !ES_NIF.is_match(&v) {
        return false;
    }
    let letters = "TRWAGMYFPDXBNJZSQVHLCKE";
    let num: u32 = v[..8].parse().unwrap_or(0);
    v.chars().last() == letters.chars().nth((num % 23) as usize)
}
pub fn validate_es_nie(v: &str) -> bool {
    let v = v.to_uppercase();
    if !ES_NIE.is_match(&v) {
        return false;
    }
    let prefix = match v.chars().next() {
        Some('X') => "0",
        Some('Y') => "1",
        Some('Z') => "2",
        _ => return false,
    };
    let num: u32 = format!("{}{}", prefix, &v[1..8]).parse().unwrap_or(0);
    let letters = "TRWAGMYFPDXBNJZSQVHLCKE";
    v.chars().last() == letters.chars().nth((num % 23) as usize)
}
pub fn validate_es_cif(v: &str) -> bool {
    ES_CIF.is_match(&v.to_uppercase())
}
pub fn validate_es_doi(v: &str) -> bool {
    validate_es_nif(v) || validate_es_nie(v) || validate_es_cif(v)
}
pub fn validate_fi_business_id(v: &str) -> bool {
    if !FI_BID.is_match(v) {
        return false;
    }
    let d: Vec<u32> = v
        .replace('-', "")
        .chars()
        .filter_map(|c| c.to_digit(10))
        .collect();
    if d.len() != 8 {
        return false;
    }
    let w = [7u32, 9, 10, 5, 8, 4, 2];
    let sum: u32 = d[..7].iter().zip(w.iter()).map(|(x, y)| x * y).sum();
    let check = (11 - (sum % 11)) % 11;
    check < 10 && d[7] == check
}
pub fn validate_fi_ssn(v: &str) -> bool {
    v.len() == 11
}
pub fn validate_fr_department(v: &str) -> bool {
    if v == "2A" || v == "2B" {
        return true;
    }
    let num: u32 = v.parse().unwrap_or(0);
    (1..=95).contains(&num) || (971..=976).contains(&num)
}
pub fn validate_fr_ssn(v: &str) -> bool {
    v.chars().filter(|c| c.is_ascii_digit()).count() == 15
}
pub fn validate_ind_aadhar(v: &str) -> bool {
    let d: String = v.chars().filter(|c| c.is_ascii_digit()).collect();
    d.len() == 12 && !d.starts_with('0') && !d.starts_with('1')
}
pub fn validate_ind_pan(v: &str) -> bool {
    IND_PAN.is_match(&v.to_uppercase())
}
pub fn validate_ru_inn(v: &str) -> bool {
    let d: Vec<_> = v.chars().filter(|c| c.is_ascii_digit()).collect();
    matches!(d.len(), 10 | 12)
}

fn i18n_result(py: Python<'_>, valid: bool, name: &str, value: &str) -> PyResult<PyObject> {
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
#[pyo3(name = "es_cif", signature = (value, /))]
pub fn py_es_cif(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_es_cif(value), "es_cif", value)
}
#[pyfunction]
#[pyo3(name = "es_doi", signature = (value, /))]
pub fn py_es_doi(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_es_doi(value), "es_doi", value)
}
#[pyfunction]
#[pyo3(name = "es_nie", signature = (value, /))]
pub fn py_es_nie(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_es_nie(value), "es_nie", value)
}
#[pyfunction]
#[pyo3(name = "es_nif", signature = (value, /))]
pub fn py_es_nif(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_es_nif(value), "es_nif", value)
}
#[pyfunction]
#[pyo3(name = "fi_business_id", signature = (value, /))]
pub fn py_fi_business_id(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_fi_business_id(value), "fi_business_id", value)
}
#[pyfunction]
#[pyo3(name = "fi_ssn", signature = (value, /))]
pub fn py_fi_ssn(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_fi_ssn(value), "fi_ssn", value)
}
#[pyfunction]
#[pyo3(name = "fr_department", signature = (value, /))]
pub fn py_fr_department(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_fr_department(value), "fr_department", value)
}
#[pyfunction]
#[pyo3(name = "fr_ssn", signature = (value, /))]
pub fn py_fr_ssn(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_fr_ssn(value), "fr_ssn", value)
}
#[pyfunction]
#[pyo3(name = "ind_aadhar", signature = (value, /))]
pub fn py_ind_aadhar(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_ind_aadhar(value), "ind_aadhar", value)
}
#[pyfunction]
#[pyo3(name = "ind_pan", signature = (value, /))]
pub fn py_ind_pan(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_ind_pan(value), "ind_pan", value)
}
#[pyfunction]
#[pyo3(name = "ru_inn", signature = (value, /))]
pub fn py_ru_inn(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    i18n_result(py, validate_ru_inn(value), "ru_inn", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_i18n() {
        assert!(validate_ind_pan("ABCDE1234F"));
    }
}

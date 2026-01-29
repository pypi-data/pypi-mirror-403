//! Country validators

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashSet;

static COUNTRIES: Lazy<HashSet<&'static str>> = Lazy::new(|| {
    [
        "AF", "AL", "DZ", "US", "GB", "DE", "FR", "IT", "ES", "PT", "NL", "BE", "AT", "CH", "SE",
        "NO", "DK", "FI", "PL", "CZ", "SK", "HU", "RO", "BG", "GR", "TR", "RU", "UA", "BY", "CN",
        "JP", "KR", "IN", "AU", "CA", "MX", "BR", "AR", "ZA", "EG", "NG", "KE", "SA", "AE", "IL",
        "SG", "MY", "TH", "ID", "PH", "VN", "NZ", "IE", "HK", "TW",
    ]
    .iter()
    .copied()
    .collect()
});
static CURRENCIES: Lazy<HashSet<&'static str>> = Lazy::new(|| {
    [
        "USD", "EUR", "GBP", "JPY", "CNY", "INR", "AUD", "CAD", "CHF", "HKD", "SGD", "SEK", "NOK",
        "DKK", "NZD", "ZAR", "MXN", "BRL", "KRW", "RUB", "TRY", "PLN", "THB", "IDR", "MYR", "PHP",
        "CZK", "HUF", "ILS", "CLP", "AED", "SAR", "TWD", "ARS", "COP", "EGP", "VND", "BDT", "PKR",
        "NGN",
    ]
    .iter()
    .copied()
    .collect()
});
static CALLING: Lazy<HashSet<&'static str>> = Lazy::new(|| {
    [
        "1", "7", "20", "27", "30", "31", "32", "33", "34", "36", "39", "40", "41", "43", "44",
        "45", "46", "47", "48", "49", "51", "52", "53", "54", "55", "56", "57", "58", "60", "61",
        "62", "63", "64", "65", "66", "81", "82", "84", "86", "90", "91", "92", "93", "94", "95",
        "98",
    ]
    .iter()
    .copied()
    .collect()
});

pub fn validate_country_code(v: &str) -> bool {
    COUNTRIES.contains(v.to_uppercase().as_str())
}
pub fn validate_currency(v: &str) -> bool {
    CURRENCIES.contains(v.to_uppercase().as_str())
}
pub fn validate_calling_code(v: &str) -> bool {
    CALLING.contains(v.trim_start_matches('+'))
}

fn country_result(py: Python<'_>, valid: bool, name: &str, value: &str) -> PyResult<PyObject> {
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
#[pyo3(name = "country_code", signature = (value, /))]
pub fn py_country_code(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    country_result(py, validate_country_code(value), "country_code", value)
}
#[pyfunction]
#[pyo3(name = "currency", signature = (value, /))]
pub fn py_currency(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    country_result(py, validate_currency(value), "currency", value)
}
#[pyfunction]
#[pyo3(name = "calling_code", signature = (value, /))]
pub fn py_calling_code(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    country_result(py, validate_calling_code(value), "calling_code", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_country() {
        assert!(validate_country_code("US"));
        assert!(validate_currency("USD"));
    }
}

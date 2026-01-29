//! RapidValidators - High-performance validators implemented in Rust

use pyo3::prelude::*;

mod validators;

use validators::{
    between, card, country, cron, crypto_address, domain, email, encoding, finance, hashes,
    hostname, i18n, ip_address, length, mac_address, slug, url, uuid,
};

/// ValidationError class for Python - behaves as falsy
#[pyclass(name = "ValidationError")]
pub struct PyValidationError {
    #[pyo3(get)]
    pub func: String,
    #[pyo3(get)]
    pub message: String,
}

#[pymethods]
impl PyValidationError {
    #[new]
    #[pyo3(signature = (func, _args, message=""))]
    fn new(func: String, _args: PyObject, message: &str) -> Self {
        PyValidationError {
            func,
            message: message.to_string(),
        }
    }

    fn __bool__(&self) -> bool {
        false
    }

    fn __repr__(&self) -> String {
        format!(
            "ValidationError(func={}, message={})",
            self.func, self.message
        )
    }

    fn __str__(&self) -> String {
        if self.message.is_empty() {
            format!("ValidationError(func={})", self.func)
        } else {
            format!(
                "ValidationError(func={}, message={})",
                self.func, self.message
            )
        }
    }
}

#[pymodule]
fn _rapidvalidators(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyValidationError>()?;

    m.add_function(wrap_pyfunction!(email::py_email, m)?)?;
    m.add_function(wrap_pyfunction!(url::py_url, m)?)?;
    m.add_function(wrap_pyfunction!(domain::py_domain, m)?)?;
    m.add_function(wrap_pyfunction!(hostname::py_hostname, m)?)?;
    m.add_function(wrap_pyfunction!(ip_address::py_ipv4, m)?)?;
    m.add_function(wrap_pyfunction!(ip_address::py_ipv6, m)?)?;
    m.add_function(wrap_pyfunction!(mac_address::py_mac_address, m)?)?;
    m.add_function(wrap_pyfunction!(uuid::py_uuid, m)?)?;
    m.add_function(wrap_pyfunction!(slug::py_slug, m)?)?;
    m.add_function(wrap_pyfunction!(length::py_length, m)?)?;
    m.add_function(wrap_pyfunction!(between::py_between, m)?)?;
    m.add_function(wrap_pyfunction!(encoding::py_base16, m)?)?;
    m.add_function(wrap_pyfunction!(encoding::py_base32, m)?)?;
    m.add_function(wrap_pyfunction!(encoding::py_base58, m)?)?;
    m.add_function(wrap_pyfunction!(encoding::py_base64, m)?)?;
    m.add_function(wrap_pyfunction!(hashes::py_md5, m)?)?;
    m.add_function(wrap_pyfunction!(hashes::py_sha1, m)?)?;
    m.add_function(wrap_pyfunction!(hashes::py_sha224, m)?)?;
    m.add_function(wrap_pyfunction!(hashes::py_sha256, m)?)?;
    m.add_function(wrap_pyfunction!(hashes::py_sha384, m)?)?;
    m.add_function(wrap_pyfunction!(hashes::py_sha512, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_card_number, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_visa, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_mastercard, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_amex, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_discover, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_diners, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_jcb, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_mir, m)?)?;
    m.add_function(wrap_pyfunction!(card::py_unionpay, m)?)?;
    m.add_function(wrap_pyfunction!(crypto_address::py_btc_address, m)?)?;
    m.add_function(wrap_pyfunction!(crypto_address::py_eth_address, m)?)?;
    m.add_function(wrap_pyfunction!(crypto_address::py_bsc_address, m)?)?;
    m.add_function(wrap_pyfunction!(crypto_address::py_trx_address, m)?)?;
    m.add_function(wrap_pyfunction!(finance::py_iban, m)?)?;
    m.add_function(wrap_pyfunction!(finance::py_cusip, m)?)?;
    m.add_function(wrap_pyfunction!(finance::py_isin, m)?)?;
    m.add_function(wrap_pyfunction!(finance::py_sedol, m)?)?;
    m.add_function(wrap_pyfunction!(country::py_country_code, m)?)?;
    m.add_function(wrap_pyfunction!(country::py_currency, m)?)?;
    m.add_function(wrap_pyfunction!(country::py_calling_code, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_es_cif, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_es_doi, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_es_nie, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_es_nif, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_fi_business_id, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_fi_ssn, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_fr_department, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_fr_ssn, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_ind_aadhar, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_ind_pan, m)?)?;
    m.add_function(wrap_pyfunction!(i18n::py_ru_inn, m)?)?;
    m.add_function(wrap_pyfunction!(cron::py_cron, m)?)?;

    Ok(())
}

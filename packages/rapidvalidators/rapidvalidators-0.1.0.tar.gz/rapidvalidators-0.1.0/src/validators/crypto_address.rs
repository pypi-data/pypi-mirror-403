//! Crypto address validators

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;
use sha2::{Digest, Sha256};

// Bech32 format for SegWit addresses
static BTC_BECH32: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^bc1[a-zA-HJ-NP-Z0-9]{25,89}$").unwrap());
static TRX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^T[a-km-zA-HJ-NP-Z1-9]{33}$").unwrap());

/// Validate base58check encoding (used by P2PKH and P2SH addresses)
/// The last 4 bytes are a checksum of the first N-4 bytes
fn validate_base58check(addr: &str) -> bool {
    // Decode base58
    let decoded = match bs58::decode(addr).into_vec() {
        Ok(v) => v,
        Err(_) => return false,
    };

    // Must have at least 5 bytes (1 version + some payload + 4 checksum)
    if decoded.len() < 5 {
        return false;
    }

    // Split into payload and checksum
    let (payload, checksum) = decoded.split_at(decoded.len() - 4);

    // Calculate expected checksum: SHA256(SHA256(payload))[0..4]
    let hash1 = Sha256::digest(payload);
    let hash2 = Sha256::digest(&hash1);

    // Compare first 4 bytes of double hash with provided checksum
    checksum == &hash2[0..4]
}

/// Validate BTC address - matches original validators library behavior
/// Uses actual base58check decoding for P2PKH/P2SH addresses
pub fn validate_btc_address(v: &str) -> bool {
    if v.is_empty() {
        return false;
    }

    // Bech32 (SegWit) addresses start with bc1
    if v.starts_with("bc1") {
        return BTC_BECH32.is_match(v);
    }

    // P2PKH (starts with 1) or P2SH (starts with 3)
    if v.starts_with('1') || v.starts_with('3') {
        return validate_base58check(v);
    }

    false
}

/// Optimized ETH address validator - no regex, direct byte checking
/// Format: 0x followed by exactly 40 hex characters
#[inline]
pub fn validate_eth_address(v: &str) -> bool {
    let bytes = v.as_bytes();
    // Must be exactly 42 characters: "0x" + 40 hex digits
    if bytes.len() != 42 {
        return false;
    }
    // Check "0x" prefix
    if bytes[0] != b'0' || bytes[1] != b'x' {
        return false;
    }
    // Check all remaining 40 chars are hex
    bytes[2..].iter().all(|&b| b.is_ascii_hexdigit())
}

pub fn validate_bsc_address(v: &str) -> bool {
    validate_eth_address(v)
}
pub fn validate_trx_address(v: &str) -> bool {
    !v.is_empty() && TRX.is_match(v)
}

fn crypto_result(py: Python<'_>, valid: bool, name: &str, value: &str) -> PyResult<PyObject> {
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
#[pyo3(name = "btc_address", signature = (value, /))]
pub fn py_btc_address(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    crypto_result(py, validate_btc_address(value), "btc_address", value)
}
#[pyfunction]
#[pyo3(name = "eth_address", signature = (value, /))]
pub fn py_eth_address(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    crypto_result(py, validate_eth_address(value), "eth_address", value)
}
#[pyfunction]
#[pyo3(name = "bsc_address", signature = (value, /))]
pub fn py_bsc_address(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    crypto_result(py, validate_bsc_address(value), "bsc_address", value)
}
#[pyfunction]
#[pyo3(name = "trx_address", signature = (value, /))]
pub fn py_trx_address(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    crypto_result(py, validate_trx_address(value), "trx_address", value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_crypto() {
        assert!(validate_btc_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"));
        assert!(validate_eth_address(
            "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
        ));
    }
}

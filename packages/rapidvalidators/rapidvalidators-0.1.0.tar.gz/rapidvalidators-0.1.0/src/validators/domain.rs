//! Domain validation module

use super::validation_result;
use idna::domain_to_ascii;
use once_cell::sync::Lazy;
use pyo3::prelude::*;
use regex::Regex;

// Pattern allows alphanumeric TLDs to support punycode like xn--p1ai (рф)
// TLD pattern allows hyphens for punycode: xn--[alphanumeric]+
static DOMAIN_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$").unwrap()
});

pub fn validate_domain(value: &str, consider_tld: bool, rfc_1034: bool, _rfc_2782: bool) -> bool {
    if value.is_empty() || value.chars().any(|c| c.is_whitespace()) {
        return false;
    }

    let mut domain = value.to_string();
    if domain.ends_with('.') {
        if !rfc_1034 {
            return false;
        }
        domain.pop();
    }

    // Convert IDN (internationalized domain names) to ASCII/punycode
    // This handles Unicode domains like münchen.de -> xn--mnchen-3ya.de
    let ascii_domain = if domain.chars().any(|c| !c.is_ascii()) {
        match domain_to_ascii(&domain) {
            Ok(ascii) => ascii,
            Err(_) => return false,
        }
    } else {
        domain.clone()
    };

    if ascii_domain.len() > 253 || !ascii_domain.contains('.') {
        return false;
    }

    let labels: Vec<&str> = ascii_domain.split('.').collect();
    for label in &labels {
        if label.is_empty() || label.len() > 63 || label.starts_with('-') || label.ends_with('-') {
            return false;
        }
    }

    if consider_tld {
        if let Some(tld) = labels.last() {
            if tld.len() < 2 || !tld.chars().all(|c| c.is_ascii_alphabetic()) {
                return false;
            }
        }
    }

    DOMAIN_PATTERN.is_match(&ascii_domain)
}

#[pyfunction]
#[pyo3(name = "domain", signature = (value, /, *, consider_tld=false, rfc_1034=false, rfc_2782=false))]
pub fn py_domain(
    py: Python<'_>,
    value: &str,
    consider_tld: bool,
    rfc_1034: bool,
    rfc_2782: bool,
) -> PyResult<PyObject> {
    validation_result(
        py,
        validate_domain(value, consider_tld, rfc_1034, rfc_2782),
        "domain",
        value,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_domain() {
        assert!(validate_domain("example.com", false, false, false));
        assert!(!validate_domain("localhost", false, false, false));
    }

    #[test]
    fn test_unicode_domains() {
        // IDN domains with Unicode characters
        assert!(validate_domain("münchen.de", false, false, false));
        assert!(validate_domain("日本.jp", false, false, false));
        // Cyrillic domain with Cyrillic TLD
        assert!(validate_domain("россия.рф", false, false, false));
        // Greek domain
        assert!(validate_domain("αβγ.ελ", false, false, false));
    }
}

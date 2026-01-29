//! Email validation module

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use regex::Regex;

use super::hostname::validate_hostname;
use super::ip_address::{validate_ipv4, validate_ipv6};
use super::validation_result;

static USERNAME_PATTERN: Lazy<Regex> =
    Lazy::new(|| Regex::new(r#"^[\w!#$%&'*+/=?^`{|}~-]+(\.[\w!#$%&'*+/=?^`{|}~-]+)*$"#).unwrap());

pub fn validate_email(
    value: &str,
    ipv6_address: bool,
    ipv4_address: bool,
    simple_host: bool,
    rfc_1034: bool,
    rfc_2782: bool,
) -> bool {
    if value.is_empty() || value.matches('@').count() != 1 {
        return false;
    }

    let parts: Vec<&str> = value.splitn(2, '@').collect();
    let username = parts[0];
    let domain = parts[1];

    if username.is_empty() || username.len() > 64 || domain.is_empty() || domain.len() > 253 {
        return false;
    }

    // Handle IP address domains
    if (ipv4_address || ipv6_address) && domain.starts_with('[') && domain.ends_with(']') {
        let ip_part = &domain[1..domain.len() - 1];
        if ipv6_address {
            let ip = if ip_part.to_lowercase().starts_with("ipv6:") {
                &ip_part[5..]
            } else {
                ip_part
            };
            if validate_ipv6(ip, false, false, true) {
                return USERNAME_PATTERN.is_match(username);
            }
        }
        if ipv4_address && validate_ipv4(ip_part, false, false, None, true) {
            return USERNAME_PATTERN.is_match(username);
        }
        return false;
    }

    if !USERNAME_PATTERN.is_match(username) {
        return false;
    }

    validate_hostname(
        domain,
        false,
        false,
        false,
        simple_host,
        false,
        None,
        rfc_1034,
        rfc_2782,
    )
}

#[pyfunction]
#[pyo3(name = "email", signature = (value, /, *, ipv6_address=false, ipv4_address=false, simple_host=false, rfc_1034=false, rfc_2782=false))]
pub fn py_email(
    py: Python<'_>,
    value: &str,
    ipv6_address: bool,
    ipv4_address: bool,
    simple_host: bool,
    rfc_1034: bool,
    rfc_2782: bool,
) -> PyResult<PyObject> {
    validation_result(
        py,
        validate_email(
            value,
            ipv6_address,
            ipv4_address,
            simple_host,
            rfc_1034,
            rfc_2782,
        ),
        "email",
        value,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_emails() {
        assert!(validate_email(
            "test@example.com",
            false,
            false,
            false,
            false,
            false
        ));
        assert!(validate_email(
            "user.name@domain.org",
            false,
            false,
            false,
            false,
            false
        ));
        assert!(!validate_email("", false, false, false, false, false));
        assert!(!validate_email(
            "notanemail",
            false,
            false,
            false,
            false,
            false
        ));
    }
}

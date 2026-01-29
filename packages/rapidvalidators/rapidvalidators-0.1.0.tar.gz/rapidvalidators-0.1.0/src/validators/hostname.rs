//! Hostname validation module

use super::ip_address::{validate_ipv4, validate_ipv6};
use super::validation_result;
use idna::domain_to_ascii;
use once_cell::sync::Lazy;
use pyo3::prelude::*;
use regex::Regex;

static HOSTNAME_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.?$").unwrap()
});

static SIMPLE_HOSTNAME_PATTERN: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$").unwrap());

#[allow(clippy::too_many_arguments)]
pub fn validate_hostname(
    value: &str,
    skip_ipv6: bool,
    skip_ipv4: bool,
    may_have_port: bool,
    maybe_simple: bool,
    consider_tld: bool,
    private: Option<bool>,
    rfc_1034: bool,
    _rfc_2782: bool,
) -> bool {
    if value.is_empty() || value.chars().any(|c| c.is_whitespace()) {
        return false;
    }

    let mut hostname = value.to_string();

    if may_have_port {
        if hostname.starts_with('[') {
            if let Some(bracket_end) = hostname.find(']') {
                let ipv6_part = &hostname[1..bracket_end];
                if !skip_ipv6 && validate_ipv6(ipv6_part, false, false, true) {
                    return true;
                }
            }
            return false;
        }
        if let Some(colon_pos) = hostname.rfind(':') {
            let potential_port = &hostname[colon_pos + 1..];
            if !potential_port.is_empty() && potential_port.chars().all(|c| c.is_ascii_digit()) {
                if potential_port.parse::<u16>().is_ok() {
                    hostname = hostname[..colon_pos].to_string();
                }
            }
        }
    }

    if !skip_ipv4 && validate_ipv4(&hostname, false, false, private, true) {
        return true;
    }
    if !skip_ipv6 && validate_ipv6(&hostname, false, false, true) {
        return true;
    }

    if hostname.ends_with('.') {
        if !rfc_1034 {
            return false;
        }
        hostname.pop();
    }

    // Convert IDN (internationalized domain names) to ASCII/punycode
    // This handles Unicode hostnames like münchen.de -> xn--mnchen-3ya.de
    let ascii_hostname = if hostname.chars().any(|c| !c.is_ascii()) {
        match domain_to_ascii(&hostname) {
            Ok(ascii) => ascii,
            Err(_) => return false,
        }
    } else {
        hostname.clone()
    };

    if ascii_hostname.len() > 253 {
        return false;
    }

    // Simple hostnames (like 'localhost') allowed when maybe_simple=true (default for hostname)
    if maybe_simple && SIMPLE_HOSTNAME_PATTERN.is_match(&ascii_hostname) {
        return true;
    }

    let labels: Vec<&str> = ascii_hostname.split('.').collect();

    // When maybe_simple=false, require at least 2 labels (domain + TLD)
    if !maybe_simple && labels.len() < 2 {
        return false;
    }

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

    HOSTNAME_PATTERN.is_match(&ascii_hostname)
}

#[pyfunction]
#[pyo3(name = "hostname", signature = (value, /, *, skip_ipv6_addr=false, skip_ipv4_addr=false, may_have_port=true, maybe_simple=true, consider_tld=false, private=None, rfc_1034=false, rfc_2782=false))]
#[allow(clippy::too_many_arguments)]
pub fn py_hostname(
    py: Python<'_>,
    value: &str,
    skip_ipv6_addr: bool,
    skip_ipv4_addr: bool,
    may_have_port: bool,
    maybe_simple: bool,
    consider_tld: bool,
    private: Option<bool>,
    rfc_1034: bool,
    rfc_2782: bool,
) -> PyResult<PyObject> {
    validation_result(
        py,
        validate_hostname(
            value,
            skip_ipv6_addr,
            skip_ipv4_addr,
            may_have_port,
            maybe_simple,
            consider_tld,
            private,
            rfc_1034,
            rfc_2782,
        ),
        "hostname",
        value,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_hostname() {
        assert!(validate_hostname(
            "example.com",
            false,
            false,
            true,
            true,
            false,
            None,
            false,
            false
        ));
        // localhost valid with maybe_simple=true (default)
        assert!(validate_hostname(
            "localhost",
            false,
            false,
            true,
            true,
            false,
            None,
            false,
            false
        ));
        // localhost invalid with maybe_simple=false
        assert!(!validate_hostname(
            "localhost",
            false,
            false,
            true,
            false,
            false,
            None,
            false,
            false
        ));
    }
}

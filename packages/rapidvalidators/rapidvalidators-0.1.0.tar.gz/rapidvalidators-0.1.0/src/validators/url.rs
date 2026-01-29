//! URL validation module

use super::hostname::validate_hostname;
use super::validation_result;
use once_cell::sync::Lazy;
use pyo3::prelude::*;
use regex::Regex;
use std::collections::HashSet;

static PATH_PATTERN: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^[/a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%\-]*$").unwrap());
static DEFAULT_SCHEMES: Lazy<HashSet<&'static str>> = Lazy::new(|| {
    [
        "http", "https", "ftp", "ftps", "git", "ssh", "file", "ws", "wss",
    ]
    .iter()
    .copied()
    .collect()
});

#[allow(clippy::too_many_arguments)]
pub fn validate_url(
    value: &str,
    skip_ipv6: bool,
    skip_ipv4: bool,
    may_have_port: bool,
    simple_host: bool,
    strict_query: bool,
    consider_tld: bool,
    private: Option<bool>,
    rfc_1034: bool,
    rfc_2782: bool,
) -> bool {
    if value.is_empty() || value.contains(' ') {
        return false;
    }

    let scheme_end = match value.find("://") {
        Some(pos) => pos,
        None => return false,
    };
    let scheme = value[..scheme_end].to_lowercase();
    if !DEFAULT_SCHEMES.contains(scheme.as_str()) {
        return false;
    }

    let after_scheme = &value[scheme_end + 3..];
    let (before_fragment, _fragment) = match after_scheme.find('#') {
        Some(pos) => (&after_scheme[..pos], Some(&after_scheme[pos + 1..])),
        None => (after_scheme, None),
    };

    let (before_query, _query) = match before_fragment.find('?') {
        Some(pos) => (&before_fragment[..pos], Some(&before_fragment[pos + 1..])),
        None => (before_fragment, None),
    };
    let _ = strict_query;

    let (netloc, path) = match before_query.find('/') {
        Some(pos) => (&before_query[..pos], Some(&before_query[pos..])),
        None => (before_query, None),
    };

    if let Some(p) = path {
        if !p.is_empty() && !PATH_PATTERN.is_match(p) {
            return false;
        }
    }

    let host_part = match netloc.find('@') {
        Some(pos) => {
            if netloc[..pos].is_empty() {
                return false;
            }
            &netloc[pos + 1..]
        }
        None => netloc,
    };

    if host_part.is_empty() {
        return false;
    }

    // For URLs, simple_host parameter controls whether simple hostnames (like 'localhost') are allowed
    // This maps to hostname's maybe_simple parameter
    validate_hostname(
        host_part,
        skip_ipv6,
        skip_ipv4,
        may_have_port,
        simple_host,
        consider_tld,
        private,
        rfc_1034,
        rfc_2782,
    )
}

#[pyfunction]
#[pyo3(name = "url", signature = (value, /, *, skip_ipv6_addr=false, skip_ipv4_addr=false, may_have_port=true, simple_host=false, strict_query=true, consider_tld=false, private=None, rfc_1034=false, rfc_2782=false))]
#[allow(clippy::too_many_arguments)]
pub fn py_url(
    py: Python<'_>,
    value: &str,
    skip_ipv6_addr: bool,
    skip_ipv4_addr: bool,
    may_have_port: bool,
    simple_host: bool,
    strict_query: bool,
    consider_tld: bool,
    private: Option<bool>,
    rfc_1034: bool,
    rfc_2782: bool,
) -> PyResult<PyObject> {
    validation_result(
        py,
        validate_url(
            value,
            skip_ipv6_addr,
            skip_ipv4_addr,
            may_have_port,
            simple_host,
            strict_query,
            consider_tld,
            private,
            rfc_1034,
            rfc_2782,
        ),
        "url",
        value,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_url() {
        assert!(validate_url(
            "http://example.com",
            false,
            false,
            true,
            false,
            true,
            false,
            None,
            false,
            false
        ));
        assert!(!validate_url(
            "not a url",
            false,
            false,
            true,
            false,
            true,
            false,
            None,
            false,
            false
        ));
    }
}

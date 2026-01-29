//! IP address validation module

use super::validation_result;
use pyo3::prelude::*;
use std::net::{Ipv4Addr, Ipv6Addr};
use std::str::FromStr;

pub fn validate_ipv4(
    value: &str,
    cidr: bool,
    strict: bool,
    private: Option<bool>,
    host_bit: bool,
) -> bool {
    if value.is_empty() {
        return false;
    }

    let slash_count = value.matches('/').count();
    if strict && slash_count != 1 {
        return false;
    }
    if slash_count > 1 {
        return false;
    }

    if slash_count == 1 {
        if !cidr {
            return false;
        }
        let parts: Vec<&str> = value.splitn(2, '/').collect();
        let ip = match Ipv4Addr::from_str(parts[0]) {
            Ok(ip) => ip,
            Err(_) => return false,
        };
        let prefix: u8 = match parts[1].parse() {
            Ok(p) if p <= 32 => p,
            _ => return false,
        };

        if !host_bit {
            let ip_int = u32::from(ip);
            let mask = if prefix == 0 {
                0
            } else {
                !0u32 << (32 - prefix)
            };
            if ip_int & !mask != 0 {
                return false;
            }
        }

        if let Some(want_private) = private {
            if (ip.is_private() || ip.is_loopback()) != want_private {
                return false;
            }
        }
        return true;
    }

    let ip = match Ipv4Addr::from_str(value) {
        Ok(ip) => ip,
        Err(_) => return false,
    };
    if let Some(want_private) = private {
        if (ip.is_private() || ip.is_loopback()) != want_private {
            return false;
        }
    }
    true
}

pub fn validate_ipv6(value: &str, cidr: bool, strict: bool, host_bit: bool) -> bool {
    if value.is_empty() {
        return false;
    }

    let slash_count = value.matches('/').count();
    if strict && slash_count != 1 {
        return false;
    }
    if slash_count > 1 {
        return false;
    }

    if slash_count == 1 {
        if !cidr {
            return false;
        }
        let parts: Vec<&str> = value.splitn(2, '/').collect();
        if Ipv6Addr::from_str(parts[0]).is_err() {
            return false;
        }
        let prefix: u8 = match parts[1].parse() {
            Ok(p) if p <= 128 => p,
            _ => return false,
        };
        let _ = (host_bit, prefix); // unused for now
        return true;
    }

    Ipv6Addr::from_str(value).is_ok()
}

#[pyfunction]
#[pyo3(name = "ipv4", signature = (value, /, *, cidr=true, strict=false, private=None, host_bit=true))]
pub fn py_ipv4(
    py: Python<'_>,
    value: &str,
    cidr: bool,
    strict: bool,
    private: Option<bool>,
    host_bit: bool,
) -> PyResult<PyObject> {
    validation_result(
        py,
        validate_ipv4(value, cidr, strict, private, host_bit),
        "ipv4",
        value,
    )
}

#[pyfunction]
#[pyo3(name = "ipv6", signature = (value, /, *, cidr=true, strict=false, host_bit=true))]
pub fn py_ipv6(
    py: Python<'_>,
    value: &str,
    cidr: bool,
    strict: bool,
    host_bit: bool,
) -> PyResult<PyObject> {
    validation_result(
        py,
        validate_ipv6(value, cidr, strict, host_bit),
        "ipv6",
        value,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_ipv4() {
        assert!(validate_ipv4("192.168.1.1", true, false, None, true));
        assert!(!validate_ipv4("256.1.1.1", true, false, None, true));
    }
    #[test]
    fn test_ipv6() {
        assert!(validate_ipv6("::1", true, false, true));
        assert!(validate_ipv6("2001:db8::1", true, false, true));
    }
}

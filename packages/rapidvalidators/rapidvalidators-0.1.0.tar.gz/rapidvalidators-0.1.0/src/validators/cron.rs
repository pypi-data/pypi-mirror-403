//! Cron validator

use pyo3::prelude::*;
use pyo3::types::PyDict;

pub fn validate_cron(v: &str) -> bool {
    let parts: Vec<&str> = v.split_whitespace().collect();
    if parts.len() != 5 {
        return false;
    }
    validate_field(parts[0], 0, 59)
        && validate_field(parts[1], 0, 23)
        && validate_field(parts[2], 1, 31)
        && validate_field(parts[3], 1, 12)
        && validate_field(parts[4], 0, 6)
}

fn validate_field(f: &str, min: u32, max: u32) -> bool {
    if f == "*" {
        return true;
    }
    for p in f.split(',') {
        let p = p.trim();
        if p.contains('/') {
            let sp: Vec<&str> = p.split('/').collect();
            if sp.len() != 2 {
                return false;
            }
            if sp[0] != "*" && !validate_range(sp[0], min, max) {
                return false;
            }
            if sp[1].parse::<u32>().is_err() {
                return false;
            }
        } else if p.contains('-') {
            if !validate_range(p, min, max) {
                return false;
            }
        } else if let Ok(n) = p.parse::<u32>() {
            if n < min || n > max {
                return false;
            }
        } else {
            return false;
        }
    }
    true
}

fn validate_range(r: &str, min: u32, max: u32) -> bool {
    let p: Vec<&str> = r.split('-').collect();
    if p.len() != 2 {
        return false;
    }
    let s: u32 = p[0].parse().unwrap_or(max + 1);
    let e: u32 = p[1].parse().unwrap_or(max + 1);
    s >= min && e <= max && s <= e
}

#[pyfunction]
#[pyo3(name = "cron", signature = (value, /))]
pub fn py_cron(py: Python<'_>, value: &str) -> PyResult<PyObject> {
    if validate_cron(value) {
        Ok(true.to_object(py))
    } else {
        let ve = py.get_type_bound::<crate::PyValidationError>();
        let args = PyDict::new_bound(py);
        args.set_item("value", value)?;
        Ok(ve.call1(("cron", args.to_object(py), ""))?.to_object(py))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_cron() {
        assert!(validate_cron("* * * * *"));
        assert!(!validate_cron("60 * * * *"));
    }
}

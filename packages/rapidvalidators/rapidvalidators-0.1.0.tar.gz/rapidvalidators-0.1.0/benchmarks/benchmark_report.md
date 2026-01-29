# RapidValidators Performance Benchmark Report

**Date:** 2026-01-25 00:50:31
**Iterations:** 10,000 per test
**Test values:** 10 per validator (5 valid + 5 invalid)

## Results

| Validator | Original (µs) | RapidValidators (µs) | Speedup |
|-----------|---------------|----------------------|---------|
| ipv4 | 45.65 | 0.97 | **47.0x** |
| ipv6 | 45.55 | 1.16 | **39.4x** |
| url | 75.13 | 2.09 | **35.9x** |
| email | 52.14 | 1.83 | **28.5x** |
| domain | 41.80 | 1.48 | **28.3x** |
| mac_address | 25.26 | 0.93 | **27.0x** |
| md5 | 23.81 | 1.05 | **22.7x** |
| slug | 23.62 | 1.04 | **22.6x** |
| uuid | 21.68 | 1.03 | **21.0x** |
| sha256 | 20.69 | 1.11 | **18.6x** |

## Summary

- **Average speedup:** 29.1x faster
- **Min speedup:** 18.6x
- **Max speedup:** 47.0x
- **Total validators tested:** 10

## Methodology

- Each validator was tested with 5 valid and 5 invalid inputs
- Each test was run for 10,000 iterations after a 100-iteration warmup
- Times are measured using `time.perf_counter_ns()` for nanosecond precision
- Statistics include mean time per batch of 10 validations

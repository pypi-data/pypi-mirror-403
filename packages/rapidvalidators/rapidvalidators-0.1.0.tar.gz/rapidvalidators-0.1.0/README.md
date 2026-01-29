# RapidValidators

[![CI](https://github.com/vivekkalyanarangan30/rapidvalidators/actions/workflows/ci.yml/badge.svg)](https://github.com/vivekkalyanarangan30/rapidvalidators/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

High-performance Python validators implemented in Rust. **Drop-in replacement** for the [`validators`](https://github.com/python-validators/validators) library with **29x average speedup**.

## ✨ Features

- 🚀 **29x faster** on average than the pure Python `validators` library
- 🔄 **100% API compatible** - just change your import
- 📦 **48+ validators** covering networks, finance, crypto, and more
- ✅ **370 tests** ensuring compatibility with the original library

## 📊 Performance

| Validator | Speedup | Validator | Speedup |
|-----------|---------|-----------|---------|
| ipv4 | **47.0x** | mac_address | **27.0x** |
| ipv6 | **39.4x** | md5 | **22.7x** |
| url | **35.9x** | slug | **22.6x** |
| email | **28.5x** | uuid | **21.0x** |
| domain | **28.3x** | sha256 | **18.6x** |

**Average: 29.1x faster** | Tested with 100,000 iterations per validator

## 📦 Installation

```bash
pip install rapidvalidators
```

## 🚀 Usage

```python
# Drop-in replacement - just change the import!
import rapidvalidators as validators

# Validate email
if validators.email("test@example.com"):
    print("Valid email!")

# Validate URL
if validators.url("https://example.com"):
    print("Valid URL!")

# ValidationError is falsy (just like the original)
result = validators.email("invalid")
if not result:
    print(f"Invalid: {result.func}")
```

## 📋 Available Validators

| Category | Validators |
|----------|------------|
| **Network** | `email`, `url`, `domain`, `hostname`, `ipv4`, `ipv6`, `mac_address` |
| **Data** | `uuid`, `slug`, `length`, `between` |
| **Encoding** | `base16`, `base32`, `base58`, `base64` |
| **Hashes** | `md5`, `sha1`, `sha224`, `sha256`, `sha384`, `sha512` |
| **Cards** | `card_number`, `visa`, `mastercard`, `amex`, `discover`, `diners`, `jcb`, `mir`, `unionpay` |
| **Crypto** | `btc_address`, `eth_address`, `bsc_address`, `trx_address` |
| **Finance** | `iban`, `cusip`, `isin`, `sedol` |
| **Country** | `country_code`, `currency`, `calling_code` |
| **International** | `es_cif`, `es_doi`, `es_nie`, `es_nif`, `fi_business_id`, `fi_ssn`, `fr_department`, `fr_ssn`, `ind_aadhar`, `ind_pan`, `ru_inn` |
| **Other** | `cron` |

## 🛠️ Development

```bash
# Clone the repository
git clone https://github.com/vivekkalyanarangan30/rapidvalidators.git
cd rapidvalidators

# Install development dependencies
pip install maturin pytest validators

# Build and install locally
maturin develop

# Run tests
cargo test          # Rust tests
pytest tests/ -v    # Python tests
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT

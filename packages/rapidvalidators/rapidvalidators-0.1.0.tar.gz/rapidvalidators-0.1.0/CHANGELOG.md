# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-25

### Added
- Initial release of RapidValidators
- **48+ validators** implemented in Rust with PyO3 bindings
- **29x average speedup** compared to pure Python `validators` library
- **100% API compatible** - drop-in replacement for `validators`

### Validators Included
- **Network**: email, url, domain, hostname, ipv4, ipv6, mac_address
- **Data**: uuid, slug, length, between
- **Encoding**: base16, base32, base58, base64
- **Hashes**: md5, sha1, sha224, sha256, sha384, sha512
- **Cards**: card_number, visa, mastercard, amex, discover, diners, jcb, mir, unionpay
- **Crypto**: btc_address (with base58check), eth_address, bsc_address, trx_address
- **Finance**: iban, cusip, isin, sedol
- **Country**: country_code, currency, calling_code
- **International IDs**: es_cif, es_doi, es_nie, es_nif, fi_business_id, fi_ssn, fr_department, fr_ssn, ind_aadhar, ind_pan, ru_inn
- **Other**: cron

### Performance Highlights
| Validator | Speedup |
|-----------|---------|
| ipv4 | 47.0x |
| ipv6 | 39.4x |
| url | 35.9x |
| email | 28.5x |
| domain | 28.3x |

[0.1.0]: https://github.com/vivekkalyanarangan30/rapidvalidators/releases/tag/v0.1.0

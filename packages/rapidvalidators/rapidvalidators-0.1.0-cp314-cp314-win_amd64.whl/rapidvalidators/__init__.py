"""
RapidValidators - High-performance validators implemented in Rust

Drop-in replacement for the `validators` library.
Usage: import rapidvalidators as validators
"""

import functools
import inspect

from rapidvalidators._rapidvalidators import (
    # Core class
    ValidationError,

    # Network validators
    email,
    url,
    domain,
    hostname,
    ipv4,
    ipv6,
    mac_address,

    # Data validators
    uuid,
    slug,
    length,
    between,

    # Encoding validators
    base16,
    base32,
    base58,
    base64,

    # Hash validators
    md5,
    sha1,
    sha224,
    sha256,
    sha384,
    sha512,

    # Card validators
    card_number,
    visa,
    mastercard,
    amex,
    discover,
    diners,
    jcb,
    mir,
    unionpay,

    # Crypto address validators
    btc_address,
    eth_address,
    bsc_address,
    trx_address,

    # Finance validators
    iban,
    cusip,
    isin,
    sedol,

    # Country validators
    country_code,
    currency,
    calling_code,

    # International ID validators
    es_cif,
    es_doi,
    es_nie,
    es_nif,
    fi_business_id,
    fi_ssn,
    fr_department,
    fr_ssn,
    ind_aadhar,
    ind_pan,
    ru_inn,

    # Cron validator
    cron,
)

def validator(func):
    """
    A decorator that makes given function a validator.

    Whenever the given `func` returns `False` this
    decorator returns `ValidationError` object.

    Examples:
        >>> @validator
        ... def is_even(value):
        ...     return value % 2 == 0
        >>> is_even(4)
        True
        >>> is_even(5)
        ValidationError(func=is_even, args={'value': 5})

    Args:
        func: Function which is to be decorated.

    Returns:
        A decorator which returns either `ValidationError` or `True`.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Build args dict for ValidationError
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        args_dict = dict(bound.arguments)

        result = func(*args, **kwargs)
        if result:
            return True
        else:
            return ValidationError(func.__name__, args_dict, "")

    return wrapper


__version__ = "0.1.0"
__all__ = [
    "ValidationError",
    "validator",
    "email", "url", "domain", "hostname", "ipv4", "ipv6", "mac_address",
    "uuid", "slug", "length", "between",
    "base16", "base32", "base58", "base64",
    "md5", "sha1", "sha224", "sha256", "sha384", "sha512",
    "card_number", "visa", "mastercard", "amex", "discover", "diners", "jcb", "mir", "unionpay",
    "btc_address", "eth_address", "bsc_address", "trx_address",
    "iban", "cusip", "isin", "sedol",
    "country_code", "currency", "calling_code",
    "es_cif", "es_doi", "es_nie", "es_nif",
    "fi_business_id", "fi_ssn", "fr_department", "fr_ssn",
    "ind_aadhar", "ind_pan", "ru_inn",
    "cron",
]

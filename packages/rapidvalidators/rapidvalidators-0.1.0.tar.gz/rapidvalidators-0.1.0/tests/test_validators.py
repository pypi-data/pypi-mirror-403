"""Tests for rapidvalidators - compatibility with validators library"""

import pytest
import rapidvalidators as validators


class TestEmail:
    def test_valid_emails(self):
        assert validators.email("test@example.com") == True
        assert validators.email("user.name@domain.org") == True
        assert validators.email("user+tag@example.com") == True

    def test_invalid_emails(self):
        assert not validators.email("")
        assert not validators.email("notanemail")
        assert not validators.email("@nodomain.com")


class TestUrl:
    def test_valid_urls(self):
        assert validators.url("http://example.com") == True
        assert validators.url("https://www.example.com/path") == True
        assert validators.url("ftp://files.example.com") == True

    def test_invalid_urls(self):
        assert not validators.url("")
        assert not validators.url("not a url")
        assert not validators.url("example.com")  # No scheme


class TestDomain:
    def test_valid_domains(self):
        assert validators.domain("example.com") == True
        assert validators.domain("sub.example.org") == True

    def test_invalid_domains(self):
        assert not validators.domain("localhost")  # No TLD
        assert not validators.domain("")


class TestIpAddress:
    def test_valid_ipv4(self):
        assert validators.ipv4("192.168.1.1") == True
        assert validators.ipv4("10.0.0.1") == True
        assert validators.ipv4("192.168.1.0/24") == True

    def test_invalid_ipv4(self):
        assert not validators.ipv4("256.1.1.1")
        assert not validators.ipv4("abc")

    def test_valid_ipv6(self):
        assert validators.ipv6("::1") == True
        assert validators.ipv6("2001:db8::1") == True

    def test_invalid_ipv6(self):
        assert not validators.ipv6("not-ipv6")


class TestUuid:
    def test_valid_uuid(self):
        assert validators.uuid("2bc1c94f-0deb-43e9-92a1-4775189ec9f8") == True

    def test_invalid_uuid(self):
        assert not validators.uuid("not-a-uuid")


class TestHashes:
    def test_md5(self):
        assert validators.md5("d41d8cd98f00b204e9800998ecf8427e") == True
        assert not validators.md5("invalid")

    def test_sha256(self):
        assert validators.sha256("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") == True


class TestCards:
    def test_visa(self):
        assert validators.visa("4532015112830366") == True

    def test_mastercard(self):
        assert validators.mastercard("5425233430109903") == True


class TestCrypto:
    def test_btc_address(self):
        assert validators.btc_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2") == True

    def test_eth_address(self):
        assert validators.eth_address("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed") == True


class TestFinance:
    def test_iban(self):
        assert validators.iban("GB82WEST12345698765432") == True

    def test_isin(self):
        assert validators.isin("US0378331005") == True


class TestValidationError:
    def test_validation_error_is_falsy(self):
        result = validators.email("invalid")
        assert not result
        assert bool(result) == False

    def test_validation_error_has_func(self):
        result = validators.email("invalid")
        assert result.func == "email"


class TestEncoding:
    def test_base16(self):
        assert validators.base16("deadbeef") == True
        assert validators.base16("abc") == True  # Odd length is valid per original library

    def test_base64(self):
        assert validators.base64("SGVsbG8=") == True


class TestCountry:
    def test_country_code(self):
        assert validators.country_code("US") == True
        assert validators.country_code("us") == True  # Case insensitive

    def test_currency(self):
        assert validators.currency("USD") == True


class TestOther:
    def test_slug(self):
        assert validators.slug("hello-world") == True
        assert not validators.slug("Hello-World")  # Uppercase

    def test_cron(self):
        assert validators.cron("* * * * *") == True
        assert not validators.cron("60 * * * *")  # Invalid minute

    def test_between(self):
        assert validators.between(5, min_val=1, max_val=10) == True
        assert not validators.between(0, min_val=1, max_val=10)

    def test_length(self):
        assert validators.length("hello", min_val=1, max_val=10) == True
        assert not validators.length("hello", min_val=10)

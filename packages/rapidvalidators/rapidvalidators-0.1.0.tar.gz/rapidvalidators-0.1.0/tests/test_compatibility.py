#!/usr/bin/env python3
"""
Compatibility tests - ensure rapidvalidators behaves identically to validators library.

These tests run the same inputs through both libraries and verify matching results.
"""

import pytest
import validators as original
import rapidvalidators as rapid


class TestEmailCompatibility:
    """Test email validator compatibility."""

    test_cases = [
        # Valid emails
        ("test@example.com", True),
        ("user.name@domain.org", True),
        ("user+tag@example.com", True),
        ("user@subdomain.example.com", True),
        ("a@b.co", True),
        ("test123@test-domain.com", True),
        ("_underscore@domain.com", True),
        ("hyphen-name@domain.com", True),
        # Invalid emails
        ("", False),
        ("notanemail", False),
        ("@nodomain.com", False),
        ("noat.com", False),
        ("two@@at.com", False),
        ("space in@email.com", False),
        (".startswithdot@domain.com", False),
        ("endswithdot.@domain.com", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_email_compatibility(self, value, expected_valid):
        orig_result = bool(original.email(value))
        rapid_result = bool(rapid.email(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestUrlCompatibility:
    """Test URL validator compatibility."""

    test_cases = [
        # Valid URLs
        ("http://example.com", True),
        ("https://www.example.com", True),
        ("https://example.com/path", True),
        ("https://example.com/path?query=value", True),
        ("https://example.com/path#fragment", True),
        ("https://example.com:8080", True),
        ("ftp://files.example.com", True),
        ("https://user:pass@example.com", True),
        # Invalid URLs
        ("", False),
        ("not a url", False),
        ("example.com", False),  # No scheme
        ("http://", False),
        ("://missing-scheme.com", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_url_compatibility(self, value, expected_valid):
        orig_result = bool(original.url(value))
        rapid_result = bool(rapid.url(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestDomainCompatibility:
    """Test domain validator compatibility."""

    test_cases = [
        # Valid domains
        ("example.com", True),
        ("subdomain.example.org", True),
        ("my-site.co.uk", True),
        ("example123.com", True),
        ("a.bc", True),
        # Invalid domains
        ("", False),
        ("localhost", False),  # No TLD
        ("-invalid.com", False),
        ("invalid-.com", False),
        (".com", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_domain_compatibility(self, value, expected_valid):
        orig_result = bool(original.domain(value))
        rapid_result = bool(rapid.domain(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestIpv4Compatibility:
    """Test IPv4 validator compatibility."""

    test_cases = [
        # Valid IPv4
        ("192.168.1.1", True),
        ("10.0.0.1", True),
        ("172.16.0.1", True),
        ("8.8.8.8", True),
        ("255.255.255.255", True),
        ("0.0.0.0", True),
        # Invalid IPv4
        ("", False),
        ("256.1.1.1", False),
        ("1.2.3", False),
        ("1.2.3.4.5", False),
        ("abc.def.ghi.jkl", False),
        ("192.168.1", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_ipv4_compatibility(self, value, expected_valid):
        orig_result = bool(original.ipv4(value))
        rapid_result = bool(rapid.ipv4(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestIpv6Compatibility:
    """Test IPv6 validator compatibility."""

    test_cases = [
        # Valid IPv6
        ("::1", True),
        ("2001:db8::1", True),
        ("fe80::1", True),
        ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", True),
        ("::", True),
        # Invalid IPv6
        ("", False),
        ("not-ipv6", False),
        (":::", False),
        ("12345::1", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_ipv6_compatibility(self, value, expected_valid):
        orig_result = bool(original.ipv6(value))
        rapid_result = bool(rapid.ipv6(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestUuidCompatibility:
    """Test UUID validator compatibility."""

    test_cases = [
        # Valid UUIDs
        ("2bc1c94f-0deb-43e9-92a1-4775189ec9f8", True),
        ("550e8400-e29b-41d4-a716-446655440000", True),
        ("6ba7b810-9dad-11d1-80b4-00c04fd430c8", True),
        ("A987FBC9-4BED-3078-CF07-9141BA07C9F3", True),  # Uppercase
        # Invalid UUIDs
        ("", False),
        ("not-a-uuid", False),
        ("2bc1c94f-0deb-43e9-92a1", False),  # Too short
        ("2bc1c94f0deb43e992a14775189ec9f8", True),  # No dashes - both libraries accept this
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_uuid_compatibility(self, value, expected_valid):
        orig_result = bool(original.uuid(value))
        rapid_result = bool(rapid.uuid(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestSlugCompatibility:
    """Test slug validator compatibility."""

    test_cases = [
        # Valid slugs
        ("hello-world", True),
        ("my-blog-post", True),
        ("test123", True),
        ("a", True),
        ("test-123-post", True),
        # Invalid slugs
        ("", False),
        ("Hello-World", False),  # Uppercase
        ("has spaces", False),
        ("-leading-dash", False),
        ("trailing-dash-", False),
        ("double--dash", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_slug_compatibility(self, value, expected_valid):
        orig_result = bool(original.slug(value))
        rapid_result = bool(rapid.slug(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestHashCompatibility:
    """Test hash validators compatibility."""

    md5_cases = [
        ("d41d8cd98f00b204e9800998ecf8427e", True),
        ("098f6bcd4621d373cade4e832627b4f6", True),
        ("", False),
        ("not-md5", False),
        ("d41d8cd98f00b204e9800998ecf8427", False),  # Too short
    ]

    sha1_cases = [
        ("da39a3ee5e6b4b0d3255bfef95601890afd80709", True),
        ("a94a8fe5ccb19ba61c4c0873d391e987982fbbd3", True),
        ("", False),
        ("not-sha1", False),
    ]

    sha256_cases = [
        ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", True),
        ("", False),
        ("not-sha256", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", md5_cases)
    def test_md5_compatibility(self, value, expected_valid):
        orig_result = bool(original.md5(value))
        rapid_result = bool(rapid.md5(value))
        assert orig_result == rapid_result, f"MD5 mismatch for '{value}'"

    @pytest.mark.parametrize("value,expected_valid", sha1_cases)
    def test_sha1_compatibility(self, value, expected_valid):
        orig_result = bool(original.sha1(value))
        rapid_result = bool(rapid.sha1(value))
        assert orig_result == rapid_result, f"SHA1 mismatch for '{value}'"

    @pytest.mark.parametrize("value,expected_valid", sha256_cases)
    def test_sha256_compatibility(self, value, expected_valid):
        orig_result = bool(original.sha256(value))
        rapid_result = bool(rapid.sha256(value))
        assert orig_result == rapid_result, f"SHA256 mismatch for '{value}'"


class TestMacAddressCompatibility:
    """Test MAC address validator compatibility."""

    test_cases = [
        # Valid MAC addresses
        ("00:11:22:33:44:55", True),
        ("AA:BB:CC:DD:EE:FF", True),
        ("aa:bb:cc:dd:ee:ff", True),
        ("00-11-22-33-44-55", True),
        # Invalid MAC addresses
        ("", False),
        ("00:11:22:33:44", False),  # Too short
        ("GG:HH:II:JJ:KK:LL", False),  # Invalid hex
        ("not-a-mac", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", test_cases)
    def test_mac_address_compatibility(self, value, expected_valid):
        orig_result = bool(original.mac_address(value))
        rapid_result = bool(rapid.mac_address(value))
        assert orig_result == rapid_result, f"Mismatch for '{value}': original={orig_result}, rapid={rapid_result}"


class TestCardCompatibility:
    """Test card validators compatibility."""

    visa_cases = [
        ("4532015112830366", True),
        ("4916338506082832", True),
        ("", False),
        ("1234567890123456", False),
    ]

    mastercard_cases = [
        ("5425233430109903", True),
        ("2223000048410010", True),
        ("", False),
        ("1234567890123456", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", visa_cases)
    def test_visa_compatibility(self, value, expected_valid):
        orig_result = bool(original.visa(value))
        rapid_result = bool(rapid.visa(value))
        assert orig_result == rapid_result, f"Visa mismatch for '{value}'"

    @pytest.mark.parametrize("value,expected_valid", mastercard_cases)
    def test_mastercard_compatibility(self, value, expected_valid):
        orig_result = bool(original.mastercard(value))
        rapid_result = bool(rapid.mastercard(value))
        assert orig_result == rapid_result, f"Mastercard mismatch for '{value}'"


class TestCryptoCompatibility:
    """Test crypto address validators compatibility."""

    btc_cases = [
        ("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", True),
        ("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", True),
        ("", False),
        ("invalid", False),
    ]

    eth_cases = [
        ("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", True),
        ("0x0000000000000000000000000000000000000000", True),
        ("", False),
        ("invalid", False),
        ("5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", False),  # No 0x prefix
    ]

    @pytest.mark.parametrize("value,expected_valid", btc_cases)
    def test_btc_address_compatibility(self, value, expected_valid):
        orig_result = bool(original.btc_address(value))
        rapid_result = bool(rapid.btc_address(value))
        assert orig_result == rapid_result, f"BTC mismatch for '{value}'"

    @pytest.mark.parametrize("value,expected_valid", eth_cases)
    def test_eth_address_compatibility(self, value, expected_valid):
        # Original library requires optional eth-hash package for eth_address validation
        # Skip if not installed
        try:
            orig_result = bool(original.eth_address(value))
        except Exception:
            pytest.skip("validators[crypto-eth-addresses] not installed")
        rapid_result = bool(rapid.eth_address(value))
        assert orig_result == rapid_result, f"ETH mismatch for '{value}'"


class TestFinanceCompatibility:
    """Test finance validators compatibility."""

    iban_cases = [
        ("GB82WEST12345698765432", True),
        ("DE89370400440532013000", True),
        ("", False),
        ("INVALID", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", iban_cases)
    def test_iban_compatibility(self, value, expected_valid):
        orig_result = bool(original.iban(value))
        rapid_result = bool(rapid.iban(value))
        assert orig_result == rapid_result, f"IBAN mismatch for '{value}'"


class TestValidationErrorCompatibility:
    """Test that ValidationError behaves correctly."""

    def test_validation_error_is_falsy(self):
        """ValidationError should be falsy like in original library."""
        orig_result = original.email("invalid")
        rapid_result = rapid.email("invalid")

        assert not orig_result
        assert not rapid_result
        assert bool(orig_result) == bool(rapid_result) == False

    def test_valid_result_is_truthy(self):
        """Valid results should be truthy."""
        orig_result = original.email("test@example.com")
        rapid_result = rapid.email("test@example.com")

        assert orig_result
        assert rapid_result
        assert bool(orig_result) == bool(rapid_result) == True

    def test_validation_error_has_func_attribute(self):
        """ValidationError should have func attribute."""
        result = rapid.email("invalid")
        assert hasattr(result, 'func')
        assert result.func == "email"


class TestEncodingCompatibility:
    """Test encoding validators compatibility."""

    base64_cases = [
        ("SGVsbG8gV29ybGQ=", True),
        ("YWJjZA==", True),
        ("", False),
    ]

    base16_cases = [
        ("deadbeef", True),
        ("DEADBEEF", True),
        ("0123456789abcdef", True),
        ("", False),
        ("xyz", False),
    ]

    @pytest.mark.parametrize("value,expected_valid", base64_cases)
    def test_base64_compatibility(self, value, expected_valid):
        orig_result = bool(original.base64(value))
        rapid_result = bool(rapid.base64(value))
        assert orig_result == rapid_result, f"Base64 mismatch for '{value}'"

    @pytest.mark.parametrize("value,expected_valid", base16_cases)
    def test_base16_compatibility(self, value, expected_valid):
        orig_result = bool(original.base16(value))
        rapid_result = bool(rapid.base16(value))
        assert orig_result == rapid_result, f"Base16 mismatch for '{value}'"

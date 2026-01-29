#!/usr/bin/env python3
"""
Edge case tests for rapidvalidators.

These tests cover boundary conditions, malformed inputs, and unusual but valid inputs
to ensure the library handles edge cases correctly and matches the original library.
"""

import pytest
import validators as original
import rapidvalidators as rapid


class TestEmailEdgeCases:
    """Edge cases for email validation."""

    edge_cases = [
        # Very long local part (up to 64 chars allowed)
        ("a" * 64 + "@example.com", "long_local"),
        # Very long domain
        ("test@" + "a" * 63 + ".com", "long_domain"),
        # Minimum valid email
        ("a@b.co", "minimal"),
        # Numbers in local part
        ("123@example.com", "numeric_local"),
        # Plus addressing
        ("user+tag+subtag@example.com", "plus_addressing"),
        # Dots in local part
        ("first.middle.last@example.com", "dots_local"),
        # Hyphen in domain
        ("test@my-domain.com", "hyphen_domain"),
        # Multiple subdomains
        ("test@a.b.c.d.example.com", "subdomains"),
        # Uppercase (should be valid)
        ("TEST@EXAMPLE.COM", "uppercase"),
        # Mixed case
        ("TeSt@ExAmPlE.cOm", "mixed_case"),
        # Numbers in domain
        ("test@123.com", "numeric_domain"),
        # IP-like domain (but valid domain)
        ("test@192.168.1.1.com", "ip_like_domain"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # No @
        ("testexample.com", "no_at"),
        # Multiple @
        ("test@@example.com", "double_at"),
        ("test@exam@ple.com", "at_in_domain"),
        # Leading dot
        (".test@example.com", "leading_dot"),
        # Trailing dot in local
        ("test.@example.com", "trailing_dot_local"),
        # Consecutive dots
        ("test..name@example.com", "consecutive_dots"),
        # Space
        ("test @example.com", "space_local"),
        ("test@ example.com", "space_domain"),
        # Missing parts
        ("@example.com", "no_local"),
        ("test@", "no_domain"),
        ("test@.com", "no_domain_name"),
        # Just @
        ("@", "just_at"),
        # Unicode (typically invalid in standard email)
        ("tëst@example.com", "unicode_local"),
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.email(value))
        rapid_result = bool(rapid.email(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.email(value))
        rapid_result = bool(rapid.email(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestUrlEdgeCases:
    """Edge cases for URL validation."""

    edge_cases = [
        # With port
        ("https://example.com:8080", "with_port"),
        ("https://example.com:443", "standard_port"),
        # With path
        ("https://example.com/path/to/resource", "with_path"),
        # With query
        ("https://example.com?key=value", "with_query"),
        ("https://example.com?a=1&b=2&c=3", "multi_query"),
        # With fragment
        ("https://example.com#section", "with_fragment"),
        # With everything
        ("https://user:pass@example.com:8080/path?query=1#frag", "full_url"),
        # IP address
        ("http://192.168.1.1", "ipv4"),
        ("http://192.168.1.1:8080/path", "ipv4_with_port"),
        # Different schemes
        ("ftp://files.example.com", "ftp"),
        ("ftps://secure.example.com", "ftps"),
        # Encoded characters
        ("https://example.com/path%20with%20spaces", "encoded_spaces"),
        ("https://example.com/path?q=hello%20world", "encoded_query"),
        # Long URL
        ("https://example.com/" + "a" * 100, "long_path"),
        # Subdomain
        ("https://www.subdomain.example.com", "subdomain"),
        # Trailing slash
        ("https://example.com/", "trailing_slash"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # No scheme
        ("example.com", "no_scheme"),
        ("www.example.com", "no_scheme_www"),
        # Invalid scheme
        ("htp://example.com", "typo_scheme"),
        ("://example.com", "empty_scheme"),
        # Spaces
        ("https://exam ple.com", "space_domain"),
        ("https:// example.com", "space_after_scheme"),
        # Just scheme
        ("https://", "just_scheme"),
        # Invalid characters
        ("https://example<>.com", "invalid_chars"),
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.url(value))
        rapid_result = bool(rapid.url(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.url(value))
        rapid_result = bool(rapid.url(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestIPv4EdgeCases:
    """Edge cases for IPv4 validation."""

    edge_cases = [
        # Boundaries
        ("0.0.0.0", "all_zeros"),
        ("255.255.255.255", "all_max"),
        ("0.0.0.1", "min_nonzero"),
        ("1.0.0.0", "first_octet_one"),
        # Common addresses
        ("127.0.0.1", "localhost"),
        ("192.168.0.1", "private_c"),
        ("10.0.0.1", "private_a"),
        ("172.16.0.1", "private_b"),
        # Broadcast
        ("255.255.255.0", "subnet_mask"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # Out of range
        ("256.1.1.1", "first_overflow"),
        ("1.256.1.1", "second_overflow"),
        ("1.1.256.1", "third_overflow"),
        ("1.1.1.256", "fourth_overflow"),
        # Wrong format
        ("1.2.3", "three_octets"),
        ("1.2.3.4.5", "five_octets"),
        ("1.2.3.", "trailing_dot"),
        (".1.2.3", "leading_dot"),
        ("1..2.3", "double_dot"),
        # Non-numeric
        ("a.b.c.d", "letters"),
        ("1.2.3.a", "letter_octet"),
        # Negative
        ("-1.2.3.4", "negative"),
        # Leading zeros (may or may not be valid depending on implementation)
        ("01.02.03.04", "leading_zeros"),
        # Spaces
        ("1.2.3.4 ", "trailing_space"),
        (" 1.2.3.4", "leading_space"),
        ("1. 2.3.4", "internal_space"),
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.ipv4(value))
        rapid_result = bool(rapid.ipv4(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.ipv4(value))
        rapid_result = bool(rapid.ipv4(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestIPv6EdgeCases:
    """Edge cases for IPv6 validation."""

    edge_cases = [
        # Loopback
        ("::1", "loopback"),
        # All zeros
        ("::", "all_zeros"),
        # Full form
        ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "full"),
        # Compressed
        ("2001:db8:85a3::8a2e:370:7334", "compressed"),
        # Link local
        ("fe80::1", "link_local"),
        # Max value
        ("ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "all_max"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # Too many colons
        (":::", "triple_colon"),
        ("2001:::1", "triple_middle"),
        # Too many groups
        ("1:2:3:4:5:6:7:8:9", "nine_groups"),
        # Invalid hex
        ("gggg::1", "invalid_hex"),
        # Group too long
        ("12345::1", "group_overflow"),
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.ipv6(value))
        rapid_result = bool(rapid.ipv6(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.ipv6(value))
        rapid_result = bool(rapid.ipv6(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestUUIDEdgeCases:
    """Edge cases for UUID validation."""

    edge_cases = [
        # Standard format
        ("550e8400-e29b-41d4-a716-446655440000", "standard"),
        # Uppercase
        ("550E8400-E29B-41D4-A716-446655440000", "uppercase"),
        # Mixed case
        ("550e8400-E29B-41d4-A716-446655440000", "mixed_case"),
        # Without dashes
        ("550e8400e29b41d4a716446655440000", "no_dashes"),
        # All zeros
        ("00000000-0000-0000-0000-000000000000", "nil_uuid"),
        # All f's
        ("ffffffff-ffff-ffff-ffff-ffffffffffff", "max_uuid"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # Too short
        ("550e8400-e29b-41d4-a716", "too_short"),
        # Too long
        ("550e8400-e29b-41d4-a716-446655440000-extra", "too_long"),
        # Invalid characters
        ("550g8400-e29b-41d4-a716-446655440000", "invalid_char"),
        # Note: Original library is permissive about dash positions and braces
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.uuid(value))
        rapid_result = bool(rapid.uuid(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.uuid(value))
        rapid_result = bool(rapid.uuid(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestIBANEdgeCases:
    """Edge cases for IBAN validation."""

    edge_cases = [
        # Various countries
        ("GB82WEST12345698765432", "uk"),
        ("DE89370400440532013000", "germany"),
        ("FR1420041010050500013M02606", "france"),
        ("ES9121000418450200051332", "spain"),
        ("IT60X0542811101000000123456", "italy"),
        # With spaces (should be cleaned)
        ("GB82 WEST 1234 5698 7654 32", "with_spaces"),
        # Lowercase (should be uppercased)
        ("gb82west12345698765432", "lowercase"),
        # Mixed case
        ("Gb82WeSt12345698765432", "mixed_case"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # Too short
        ("GB82", "too_short"),
        # Invalid checksum
        ("GB82WEST12345698765433", "bad_checksum"),
        # Invalid country code
        ("XX82WEST12345698765432", "invalid_country"),
        # Invalid characters
        ("GB82WEST!2345698765432", "special_char"),
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.iban(value))
        rapid_result = bool(rapid.iban(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.iban(value))
        rapid_result = bool(rapid.iban(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestSlugEdgeCases:
    """Edge cases for slug validation."""

    edge_cases = [
        # Simple
        ("hello", "single_word"),
        ("hello-world", "two_words"),
        # Numbers
        ("post-123", "with_numbers"),
        ("123-post", "number_first"),
        ("123", "only_numbers"),
        # Long slug
        ("this-is-a-very-long-slug-with-many-words", "long_slug"),
        # Single char
        ("a", "single_char"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # Uppercase
        ("Hello-World", "uppercase"),
        ("HELLO", "all_uppercase"),
        # Spaces
        ("hello world", "with_space"),
        # Underscores
        ("hello_world", "underscore"),
        # Leading/trailing dashes
        ("-hello", "leading_dash"),
        ("hello-", "trailing_dash"),
        # Double dashes
        ("hello--world", "double_dash"),
        # Special characters
        ("hello@world", "special_char"),
        ("hello.world", "dot"),
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.slug(value))
        rapid_result = bool(rapid.slug(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.slug(value))
        rapid_result = bool(rapid.slug(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestMacAddressEdgeCases:
    """Edge cases for MAC address validation."""

    edge_cases = [
        # Colon separated
        ("00:11:22:33:44:55", "colon_lower"),
        ("AA:BB:CC:DD:EE:FF", "colon_upper"),
        ("aa:bb:cc:dd:ee:ff", "colon_lower_hex"),
        # Hyphen separated
        ("00-11-22-33-44-55", "hyphen"),
        ("AA-BB-CC-DD-EE-FF", "hyphen_upper"),
        # Mixed case
        ("Aa:Bb:Cc:Dd:Ee:Ff", "mixed_case"),
        # Broadcast
        ("FF:FF:FF:FF:FF:FF", "broadcast"),
        # All zeros
        ("00:00:00:00:00:00", "all_zeros"),
    ]

    invalid_cases = [
        # Empty
        ("", "empty"),
        # Too short
        ("00:11:22:33:44", "too_short"),
        # Too long
        ("00:11:22:33:44:55:66", "too_long"),
        # Invalid hex
        ("GG:HH:II:JJ:KK:LL", "invalid_hex"),
        ("00:11:22:33:44:GG", "partial_invalid"),
        # Mixed separators
        ("00:11-22:33-44:55", "mixed_separators"),
        # No separators
        ("001122334455", "no_separators"),
        # Wrong separator
        ("00.11.22.33.44.55", "dot_separator"),
    ]

    @pytest.mark.parametrize("value,case_name", edge_cases)
    def test_valid_edge_cases(self, value, case_name):
        orig = bool(original.mac_address(value))
        rapid_result = bool(rapid.mac_address(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, case_name):
        orig = bool(original.mac_address(value))
        rapid_result = bool(rapid.mac_address(value))
        assert orig == rapid_result, f"Mismatch for {case_name}: {value!r}"


class TestHashEdgeCases:
    """Edge cases for hash validation."""

    md5_cases = [
        ("d41d8cd98f00b204e9800998ecf8427e", True, "valid_lowercase"),
        ("D41D8CD98F00B204E9800998ECF8427E", True, "valid_uppercase"),
        ("d41D8cd98F00b204E9800998ecF8427E", True, "valid_mixed"),
        ("", False, "empty"),
        ("d41d8cd98f00b204e9800998ecf8427", False, "too_short"),
        ("d41d8cd98f00b204e9800998ecf8427ee", False, "too_long"),
        ("g41d8cd98f00b204e9800998ecf8427e", False, "invalid_char"),
    ]

    sha256_cases = [
        ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", True, "valid"),
        ("E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855", True, "uppercase"),
        ("", False, "empty"),
        ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85", False, "too_short"),
    ]

    @pytest.mark.parametrize("value,expected_valid,case_name", md5_cases)
    def test_md5_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.md5(value))
        rapid_result = bool(rapid.md5(value))
        assert orig == rapid_result, f"MD5 mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,expected_valid,case_name", sha256_cases)
    def test_sha256_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.sha256(value))
        rapid_result = bool(rapid.sha256(value))
        assert orig == rapid_result, f"SHA256 mismatch for {case_name}: {value!r}"


class TestCardEdgeCases:
    """Edge cases for credit card validation."""

    visa_cases = [
        ("4532015112830366", True, "valid_16"),
        ("4111111111111111", True, "test_card"),
        ("4000000000000000", False, "invalid_luhn"),
        ("", False, "empty"),
        ("4532015112830", False, "too_short"),
        ("45320151128303661", False, "too_long"),
        ("5532015112830366", False, "wrong_prefix"),
    ]

    mastercard_cases = [
        ("5425233430109903", True, "valid_54"),
        ("5500000000000004", True, "test_card"),
        ("2223000048410010", True, "new_range"),
        ("5500000000000000", False, "invalid_luhn"),
        ("", False, "empty"),
        ("4425233430109903", False, "wrong_prefix"),
    ]

    @pytest.mark.parametrize("value,expected_valid,case_name", visa_cases)
    def test_visa_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.visa(value))
        rapid_result = bool(rapid.visa(value))
        assert orig == rapid_result, f"Visa mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,expected_valid,case_name", mastercard_cases)
    def test_mastercard_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.mastercard(value))
        rapid_result = bool(rapid.mastercard(value))
        assert orig == rapid_result, f"Mastercard mismatch for {case_name}: {value!r}"


class TestDomainEdgeCases:
    """Edge cases for domain validation."""

    edge_cases = [
        ("example.com", True, "simple"),
        ("sub.example.com", True, "subdomain"),
        ("a.b.c.d.example.com", True, "deep_subdomain"),
        ("example.co.uk", True, "country_tld"),
        ("123.com", True, "numeric_start"),
        ("a.bc", True, "short_tld"),
        ("xn--n3h.com", True, "punycode"),
    ]

    invalid_cases = [
        ("", False, "empty"),
        ("localhost", False, "no_tld"),
        ("-example.com", False, "leading_hyphen"),
        ("example-.com", False, "trailing_hyphen"),
        (".example.com", False, "leading_dot"),
        ("example..com", False, "double_dot"),
        ("example.com.", False, "trailing_dot"),
        ("exam ple.com", False, "space"),
        ("example", False, "no_dot"),
    ]

    @pytest.mark.parametrize("value,expected_valid,case_name", edge_cases)
    def test_valid_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.domain(value))
        rapid_result = bool(rapid.domain(value))
        assert orig == rapid_result, f"Domain mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,expected_valid,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.domain(value))
        rapid_result = bool(rapid.domain(value))
        assert orig == rapid_result, f"Domain mismatch for {case_name}: {value!r}"


class TestBtcAddressEdgeCases:
    """Edge cases for Bitcoin address validation."""

    edge_cases = [
        # P2PKH (starts with 1)
        ("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", True, "p2pkh_1"),
        ("1111111111111111111114oLvT2", True, "p2pkh_min"),
        # P2SH (starts with 3)
        ("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", True, "p2sh"),
        # Bech32 (starts with bc1)
        ("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", True, "bech32"),
    ]

    invalid_cases = [
        ("", False, "empty"),
        ("invalid", False, "invalid_string"),
        ("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN", False, "too_short"),
        ("0BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", False, "wrong_prefix"),
    ]

    @pytest.mark.parametrize("value,expected_valid,case_name", edge_cases)
    def test_valid_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.btc_address(value))
        rapid_result = bool(rapid.btc_address(value))
        assert orig == rapid_result, f"BTC mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,expected_valid,case_name", invalid_cases)
    def test_invalid_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.btc_address(value))
        rapid_result = bool(rapid.btc_address(value))
        assert orig == rapid_result, f"BTC mismatch for {case_name}: {value!r}"


class TestLengthAndBetweenEdgeCases:
    """Edge cases for length and between validators."""

    def test_length_no_constraints(self):
        """Length with no min/max should always pass."""
        orig = bool(original.length("anything"))
        rapid_result = bool(rapid.length("anything"))
        assert orig == rapid_result

    def test_length_empty_string(self):
        """Empty string length checks."""
        orig = bool(original.length("", min_val=0))
        rapid_result = bool(rapid.length("", min_val=0))
        assert orig == rapid_result

        orig = bool(original.length("", min_val=1))
        rapid_result = bool(rapid.length("", min_val=1))
        assert orig == rapid_result

    def test_length_exact(self):
        """Exact length match."""
        orig = bool(original.length("hello", min_val=5, max_val=5))
        rapid_result = bool(rapid.length("hello", min_val=5, max_val=5))
        assert orig == rapid_result

    def test_between_boundaries(self):
        """Between at exact boundaries."""
        # At min
        orig = bool(original.between(1, min_val=1, max_val=10))
        rapid_result = bool(rapid.between(1, min_val=1, max_val=10))
        assert orig == rapid_result

        # At max
        orig = bool(original.between(10, min_val=1, max_val=10))
        rapid_result = bool(rapid.between(10, min_val=1, max_val=10))
        assert orig == rapid_result

    def test_between_floats(self):
        """Between with float values."""
        orig = bool(original.between(5.5, min_val=1.0, max_val=10.0))
        rapid_result = bool(rapid.between(5.5, min_val=1.0, max_val=10.0))
        assert orig == rapid_result

    def test_between_no_constraints(self):
        """Between with no constraints."""
        orig = bool(original.between(999999))
        rapid_result = bool(rapid.between(999999))
        assert orig == rapid_result


class TestValidatorDecoratorEdgeCases:
    """Edge cases for the validator decorator."""

    def test_decorator_with_multiple_args(self):
        """Decorator with multiple arguments."""
        @rapid.validator
        def is_in_range(value, min_val, max_val):
            return min_val <= value <= max_val

        assert bool(is_in_range(5, 1, 10)) == True
        assert bool(is_in_range(15, 1, 10)) == False

    def test_decorator_with_kwargs(self):
        """Decorator with keyword arguments."""
        @rapid.validator
        def has_prefix(value, prefix="test"):
            return value.startswith(prefix)

        assert bool(has_prefix("test_value")) == True
        assert bool(has_prefix("other_value")) == False
        assert bool(has_prefix("hello", prefix="hel")) == True

    def test_decorator_preserves_function_name(self):
        """Decorator preserves function name."""
        @rapid.validator
        def my_custom_validator(value):
            return len(value) > 0

        assert my_custom_validator.__name__ == "my_custom_validator"

    def test_decorator_error_has_func_name(self):
        """ValidationError has correct function name."""
        @rapid.validator
        def always_fails(value):
            return False

        result = always_fails("test")
        assert result.func == "always_fails"


class TestEncodingEdgeCases:
    """Edge cases for encoding validators."""

    base64_cases = [
        ("SGVsbG8gV29ybGQ=", True, "valid_padded"),
        ("SGVsbG8=", True, "single_pad"),
        ("SGVsbG8gV29ybGQh", True, "no_pad_needed"),
        ("", False, "empty"),
    ]

    base16_cases = [
        ("deadbeef", True, "lowercase"),
        ("DEADBEEF", True, "uppercase"),
        ("DeAdBeEf", True, "mixed_case"),
        ("0123456789abcdef", True, "all_hex"),
        ("", False, "empty"),
        ("xyz", False, "invalid_chars"),
        ("abc", True, "odd_length"),  # Original library accepts odd-length hex
    ]

    @pytest.mark.parametrize("value,expected_valid,case_name", base64_cases)
    def test_base64_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.base64(value))
        rapid_result = bool(rapid.base64(value))
        assert orig == rapid_result, f"Base64 mismatch for {case_name}: {value!r}"

    @pytest.mark.parametrize("value,expected_valid,case_name", base16_cases)
    def test_base16_edge_cases(self, value, expected_valid, case_name):
        orig = bool(original.base16(value))
        rapid_result = bool(rapid.base16(value))
        assert orig == rapid_result, f"Base16 mismatch for {case_name}: {value!r}"

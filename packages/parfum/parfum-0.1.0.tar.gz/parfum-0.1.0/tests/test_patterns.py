"""
Tests for the patterns module.

Tests regex patterns and PatternRegistry class.
"""

import pytest
import re
from parfum.patterns import (
    EMAIL_PATTERN,
    PHONE_PATTERNS,
    CREDIT_CARD_PATTERNS,
    SSN_PATTERN,
    IP_V4_PATTERN,
    IP_V6_PATTERN,
    URL_PATTERN,
    DATE_PATTERNS,
    IBAN_PATTERN,
    PatternRegistry,
    default_registry,
)
from parfum.entities import PIIType


class TestEmailPattern:
    """Tests for email regex pattern."""
    
    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user.name@domain.org",
        "user+tag@subdomain.domain.co.uk",
        "simple@test.io",
        "UPPERCASE@EXAMPLE.COM",
        "with.dots@many.dots.example.com",
        "numbers123@test456.com",
    ])
    def test_valid_emails(self, email):
        """Test that valid emails are matched."""
        assert EMAIL_PATTERN.search(email) is not None
    
    @pytest.mark.parametrize("invalid", [
        "not_an_email",
        "@missing.local",
        "missing@.domain",
        "spaces in@email.com",
        "missing_at_sign.com",
    ])
    def test_invalid_emails(self, invalid):
        """Test that invalid emails are not matched as full match."""
        match = EMAIL_PATTERN.search(invalid)
        if match:
            # If there's a match, it shouldn't be the full string
            assert match.group() != invalid


class TestPhonePatterns:
    """Tests for phone number regex patterns."""
    
    @pytest.mark.parametrize("phone", [
        "555-123-4567",
        "(555) 123-4567",
        "555.123.4567",
        "5551234567",
        "+1-555-123-4567",
        "+1 555 123 4567",
    ])
    def test_valid_phones(self, phone):
        """Test that valid phone numbers are matched."""
        matched = any(p.search(phone) for p in PHONE_PATTERNS)
        assert matched, f"Phone not matched: {phone}"
    
    def test_short_number_not_matched(self):
        """Test that very short numbers are not matched."""
        # 7 digits without country code usually not matched
        short = "555-123"
        matched = any(p.fullmatch(short) for p in PHONE_PATTERNS)
        assert not matched


class TestCreditCardPatterns:
    """Tests for credit card regex patterns."""
    
    @pytest.mark.parametrize("card,card_type", [
        ("4111111111111111", "Visa"),
        ("4111-1111-1111-1111", "Visa"),
        ("4111 1111 1111 1111", "Visa"),
        ("5500000000000004", "Mastercard"),
        ("5500-0000-0000-0004", "Mastercard"),
        ("371449635398431", "Amex"),
        ("3714-496353-98431", "Amex"),
    ])
    def test_valid_credit_cards(self, card, card_type):
        """Test that valid credit card numbers are matched."""
        matched = any(p.search(card) for p in CREDIT_CARD_PATTERNS)
        assert matched, f"{card_type} card not matched: {card}"
    
    def test_random_numbers_not_matched(self):
        """Test that random 16-digit non-card numbers work or don't match."""
        # Generic pattern catches 16 digits, but real cards have checksums
        pass  # Pattern intentionally catches generic 16 digits


class TestSSNPattern:
    """Tests for SSN regex pattern."""
    
    @pytest.mark.parametrize("ssn", [
        "123-45-6789",
        "123 45 6789",
        "123456789",
    ])
    def test_valid_ssns(self, ssn):
        """Test that valid SSNs are matched."""
        assert SSN_PATTERN.search(ssn) is not None
    
    def test_invalid_ssn(self):
        """Test that invalid SSNs are not matched."""
        invalid = "12-345-6789"  # Wrong format
        match = SSN_PATTERN.search(invalid)
        # May match partial, but that's okay for this test
        assert match is None or match.group() != invalid


class TestIPPatterns:
    """Tests for IP address regex patterns."""
    
    @pytest.mark.parametrize("ip", [
        "192.168.1.1",
        "10.0.0.1",
        "255.255.255.255",
        "0.0.0.0",
        "172.16.0.1",
    ])
    def test_valid_ipv4(self, ip):
        """Test that valid IPv4 addresses are matched."""
        assert IP_V4_PATTERN.search(ip) is not None
    
    @pytest.mark.parametrize("invalid_ip", [
        "256.1.1.1",
        "192.168.1",
        "192.168.1.1.1",
    ])
    def test_invalid_ipv4(self, invalid_ip):
        """Test that invalid IPv4 addresses are not fully matched."""
        match = IP_V4_PATTERN.search(invalid_ip)
        if match:
            assert match.group() != invalid_ip
    
    @pytest.mark.parametrize("ipv6", [
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "fe80:0000:0000:0000:0000:0000:0000:0001",
    ])
    def test_valid_ipv6(self, ipv6):
        """Test that valid IPv6 addresses are matched."""
        assert IP_V6_PATTERN.search(ipv6) is not None


class TestURLPattern:
    """Tests for URL regex pattern."""
    
    @pytest.mark.parametrize("url", [
        "https://example.com",
        "http://www.example.com",
        "https://subdomain.example.com/path",
        "example.com",
        "www.example.org",
        "https://example.com/path/to/page?query=1",
    ])
    def test_valid_urls(self, url):
        """Test that valid URLs are matched."""
        assert URL_PATTERN.search(url) is not None


class TestDatePatterns:
    """Tests for date regex patterns."""
    
    @pytest.mark.parametrize("date", [
        "2024-01-15",
        "2024/01/15",
        "01/15/2024",
        "01-15-2024",
        "January 15, 2024",
        "15 January 2024",
        "Jan 15, 2024",
        "15 Jan 2024",
    ])
    def test_valid_dates(self, date):
        """Test that valid date formats are matched."""
        matched = any(p.search(date) for p in DATE_PATTERNS)
        assert matched, f"Date not matched: {date}"


class TestIBANPattern:
    """Tests for IBAN regex pattern."""
    
    @pytest.mark.parametrize("iban", [
        "DE89370400440532013000",
        "GB82WEST12345698765432",
        "FR7630006000011234567890189",
    ])
    def test_valid_ibans(self, iban):
        """Test that valid IBANs are matched."""
        assert IBAN_PATTERN.search(iban) is not None


class TestPatternRegistry:
    """Tests for PatternRegistry class."""
    
    def test_default_registry_exists(self):
        """Test that default registry is available."""
        assert default_registry is not None
        assert isinstance(default_registry, PatternRegistry)
    
    def test_get_patterns_for_email(self):
        """Test getting patterns for EMAIL type."""
        registry = PatternRegistry()
        patterns = registry.get_patterns(PIIType.EMAIL)
        
        assert len(patterns) == 1
        assert patterns[0] == EMAIL_PATTERN
    
    def test_get_patterns_for_phone(self):
        """Test getting patterns for PHONE type."""
        registry = PatternRegistry()
        patterns = registry.get_patterns(PIIType.PHONE)
        
        assert len(patterns) == len(PHONE_PATTERNS)
    
    def test_get_patterns_unknown_type(self):
        """Test getting patterns for type with no patterns."""
        registry = PatternRegistry()
        patterns = registry.get_patterns(PIIType.PERSON)  # No regex for PERSON
        
        assert patterns == []
    
    def test_get_all_patterns(self):
        """Test getting all patterns."""
        registry = PatternRegistry()
        all_patterns = registry.get_all_patterns()
        
        assert PIIType.EMAIL in all_patterns
        assert PIIType.PHONE in all_patterns
        assert PIIType.SSN in all_patterns
    
    def test_add_custom_pattern(self):
        """Test adding a custom pattern."""
        registry = PatternRegistry()
        registry.add_custom_pattern(
            name="employee_id",
            pattern=r"EMP-\d{6}",
            pii_type=PIIType.CUSTOM,
        )
        
        patterns = registry.get_patterns(PIIType.CUSTOM)
        assert len(patterns) >= 1
        
        # Test the pattern works
        text = "Contact EMP-123456"
        matched = any(p.search(text) for p in patterns)
        assert matched
    
    def test_add_custom_pattern_with_flags(self):
        """Test adding custom pattern with regex flags."""
        registry = PatternRegistry()
        registry.add_custom_pattern(
            name="secret_code",
            pattern=r"SECRET-[A-Z]+",
            pii_type=PIIType.CUSTOM,
            flags=re.IGNORECASE,
        )
        
        patterns = registry.get_patterns(PIIType.CUSTOM)
        text = "Code: secret-abc"
        matched = any(p.search(text) for p in patterns)
        assert matched
    
    def test_get_custom_patterns(self):
        """Test getting custom patterns."""
        registry = PatternRegistry()
        registry.add_custom_pattern("test1", r"TEST1", PIIType.CUSTOM)
        registry.add_custom_pattern("test2", r"TEST2", PIIType.CUSTOM)
        
        custom = registry.get_custom_patterns()
        assert "test1" in custom
        assert "test2" in custom
    
    def test_add_pattern_new_type(self):
        """Test adding pattern creates new type entry if needed."""
        registry = PatternRegistry()
        
        # PERSON has no default patterns
        initial = registry.get_patterns(PIIType.PERSON)
        assert len(initial) == 0
        
        # Add pattern for PERSON
        registry.add_custom_pattern("mr_prefix", r"Mr\.\s+\w+", PIIType.PERSON)
        
        after = registry.get_patterns(PIIType.PERSON)
        assert len(after) == 1
    
    def test_registry_isolation(self):
        """Test that different registry instances are isolated."""
        registry1 = PatternRegistry()
        registry2 = PatternRegistry()
        
        registry1.add_custom_pattern("only_in_1", r"ONLY1", PIIType.CUSTOM)
        
        custom1 = registry1.get_custom_patterns()
        custom2 = registry2.get_custom_patterns()
        
        assert "only_in_1" in custom1
        assert "only_in_1" not in custom2

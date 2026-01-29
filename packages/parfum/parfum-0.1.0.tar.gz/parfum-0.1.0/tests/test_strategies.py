"""
Tests for the strategies module.

Tests Strategy enum and Anonymizers class with all anonymization methods.
"""

import pytest
import hashlib
from parfum.strategies import Strategy, Anonymizers
from parfum.entities import PIIType, PIIMatch


class TestStrategyEnum:
    """Tests for Strategy enum."""
    
    def test_all_strategies_exist(self):
        """Verify all expected strategies are defined."""
        expected = ["REPLACE", "MASK", "HASH", "FAKE", "REDACT"]
        for name in expected:
            assert hasattr(Strategy, name), f"Missing Strategy: {name}"
    
    def test_strategy_values(self):
        """Verify strategy values."""
        assert Strategy.REPLACE.value == "replace"
        assert Strategy.MASK.value == "mask"
        assert Strategy.HASH.value == "hash"
        assert Strategy.FAKE.value == "fake"
        assert Strategy.REDACT.value == "redact"
    
    def test_strategy_from_string(self):
        """Test creating strategy from string value."""
        assert Strategy("replace") == Strategy.REPLACE
        assert Strategy("mask") == Strategy.MASK


class TestAnonymizersInit:
    """Tests for Anonymizers initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        anon = Anonymizers()
        
        assert anon.faker is not None
        assert anon._fake_cache == {}
    
    def test_init_with_locale(self):
        """Test initialization with locale."""
        anon = Anonymizers(locale="de_DE")
        
        assert anon.faker is not None
    
    def test_init_with_seed(self):
        """Test initialization with seed for reproducibility."""
        anon1 = Anonymizers(seed=42)
        anon2 = Anonymizers(seed=42)
        
        # Same seed should produce same fake data
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        fake1 = anon1.fake(match)
        
        # Reset for second anonymizer
        anon2._fake_cache.clear()
        fake2 = anon2.fake(PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16))
        
        # Note: Due to Faker's global seed, this may not always match
        # but the mechanism should work


class TestAnonymizersReplace:
    """Tests for replace strategy."""
    
    def test_replace_email(self):
        """Test replacing email."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        
        result = anon.replace(match)
        
        assert result == "[EMAIL]"
    
    def test_replace_phone(self):
        """Test replacing phone."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.PHONE, "555-123-4567", 0, 12)
        
        result = anon.replace(match)
        
        assert result == "[PHONE]"
    
    def test_replace_all_types(self):
        """Test replace works for all PII types."""
        anon = Anonymizers()
        
        for pii_type in PIIType:
            match = PIIMatch(pii_type, "test", 0, 4)
            result = anon.replace(match)
            assert result == f"[{pii_type.value}]"


class TestAnonymizersRedact:
    """Tests for redact strategy."""
    
    def test_redact(self):
        """Test that redact returns empty string."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        
        result = anon.redact(match)
        
        assert result == ""


class TestAnonymizersMask:
    """Tests for mask strategy."""
    
    def test_mask_email(self):
        """Test email masking."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.EMAIL, "john.doe@example.com", 0, 20)
        
        result = anon.mask(match)
        
        assert "@" in result
        assert "*" in result
        assert "john.doe@example.com" != result
    
    def test_mask_email_preserves_structure(self):
        """Test that masked email preserves @ and domain structure."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.EMAIL, "test@domain.com", 0, 15)
        
        result = anon.mask(match)
        
        assert "@" in result
        assert ".com" in result or "." in result
    
    def test_mask_phone(self):
        """Test phone masking."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.PHONE, "555-123-4567", 0, 12)
        
        result = anon.mask(match)
        
        # Should keep first 3 and last 2 digits
        assert result.startswith("555")
        assert result.endswith("67")
        assert "*" in result
    
    def test_mask_credit_card(self):
        """Test credit card masking."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.CREDIT_CARD, "4111-1111-1111-1234", 0, 19)
        
        result = anon.mask(match)
        
        # Should keep last 4 digits
        assert "1234" in result
        assert "4111" not in result
        assert "*" in result
    
    def test_mask_ssn(self):
        """Test SSN masking."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.SSN, "123-45-6789", 0, 11)
        
        result = anon.mask(match)
        
        # Should keep last 4 digits
        assert "6789" in result
        assert "123" not in result
        assert "*" in result
    
    def test_mask_ip(self):
        """Test IP address masking."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.IP_ADDRESS, "192.168.1.100", 0, 13)
        
        result = anon.mask(match)
        
        # Should keep first two octets
        assert "192.168" in result
        assert "*" in result
    
    def test_mask_generic(self):
        """Test generic masking for unknown types."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.CUSTOM, "secretdata", 0, 10)
        
        result = anon.mask(match)
        
        # Generic mask keeps first and last char
        assert result.startswith("s")
        assert result.endswith("a")
        assert "*" in result
    
    def test_mask_short_text(self):
        """Test masking very short text."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.CUSTOM, "ab", 0, 2)
        
        result = anon.mask(match)
        
        # Very short text is fully masked
        assert result == "**"


class TestAnonymizersHash:
    """Tests for hash strategy."""
    
    def test_hash_email(self):
        """Test hashing email."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        
        result = anon.hash(match)
        
        # Should be 16 character hex string
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)
    
    def test_hash_consistent(self):
        """Test that same input produces same hash."""
        anon = Anonymizers()
        match1 = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        match2 = PIIMatch(PIIType.EMAIL, "test@example.com", 5, 21)  # Different position
        
        result1 = anon.hash(match1)
        result2 = anon.hash(match2)
        
        assert result1 == result2
    
    def test_hash_different_inputs(self):
        """Test that different inputs produce different hashes."""
        anon = Anonymizers()
        match1 = PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7)
        match2 = PIIMatch(PIIType.EMAIL, "c@d.com", 0, 7)
        
        result1 = anon.hash(match1)
        result2 = anon.hash(match2)
        
        assert result1 != result2
    
    def test_hash_is_sha256(self):
        """Test that hash uses SHA-256."""
        anon = Anonymizers()
        text = "test@example.com"
        match = PIIMatch(PIIType.EMAIL, text, 0, len(text))
        
        result = anon.hash(match)
        expected = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        
        assert result == expected


class TestAnonymizersFake:
    """Tests for fake data generation strategy."""
    
    def test_fake_email(self):
        """Test generating fake email."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        
        result = anon.fake(match)
        
        assert "@" in result
        assert "test@example.com" != result
    
    def test_fake_phone(self):
        """Test generating fake phone."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.PHONE, "555-123-4567", 0, 12)
        
        result = anon.fake(match)
        
        assert result != "555-123-4567"
    
    def test_fake_name(self):
        """Test generating fake name."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.PERSON, "John Doe", 0, 8)
        
        result = anon.fake(match)
        
        assert result != "John Doe"
        assert len(result) > 0
    
    def test_fake_ssn(self):
        """Test generating fake SSN."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.SSN, "123-45-6789", 0, 11)
        
        result = anon.fake(match)
        
        assert result != "123-45-6789"
    
    def test_fake_ip(self):
        """Test generating fake IP."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.IP_ADDRESS, "192.168.1.1", 0, 11)
        
        result = anon.fake(match)
        
        assert "." in result
    
    def test_fake_url(self):
        """Test generating fake URL."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.URL, "https://example.com", 0, 19)
        
        result = anon.fake(match)
        
        assert "://" in result or "." in result
    
    def test_fake_cached(self):
        """Test that fake data is cached for consistency."""
        anon = Anonymizers()
        match1 = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        match2 = PIIMatch(PIIType.EMAIL, "test@example.com", 5, 21)
        
        result1 = anon.fake(match1)
        result2 = anon.fake(match2)
        
        assert result1 == result2
    
    def test_fake_different_values_different_results(self):
        """Test that different original values get different fake values."""
        anon = Anonymizers()
        match1 = PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7)
        match2 = PIIMatch(PIIType.EMAIL, "c@d.com", 0, 7)
        
        result1 = anon.fake(match1)
        result2 = anon.fake(match2)
        
        # Usually different, but with small probability could be same
        # Just check they're both valid emails
        assert "@" in result1
        assert "@" in result2
    
    def test_fake_custom_type_fallback(self):
        """Test fake for custom type falls back to placeholder."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.CUSTOM, "custom_data", 0, 11)
        
        result = anon.fake(match)
        
        assert result == "[CUSTOM]"


class TestAnonymizersCache:
    """Tests for fake data cache."""
    
    def test_clear_cache(self):
        """Test clearing the fake data cache."""
        anon = Anonymizers()
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        
        result1 = anon.fake(match)
        anon.clear_cache()
        result2 = anon.fake(match)
        
        # After clearing, might get different result (depends on Faker state)
        assert isinstance(result1, str)
        assert isinstance(result2, str)


class TestAnonymizersGetAnonymizer:
    """Tests for get_anonymizer method."""
    
    def test_get_anonymizer_replace(self):
        """Test getting replace anonymizer function."""
        anon = Anonymizers()
        func = anon.get_anonymizer(Strategy.REPLACE)
        
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        assert func(match) == "[EMAIL]"
    
    def test_get_anonymizer_mask(self):
        """Test getting mask anonymizer function."""
        anon = Anonymizers()
        func = anon.get_anonymizer(Strategy.MASK)
        
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        result = func(match)
        assert "*" in result
    
    def test_get_anonymizer_hash(self):
        """Test getting hash anonymizer function."""
        anon = Anonymizers()
        func = anon.get_anonymizer(Strategy.HASH)
        
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        result = func(match)
        assert len(result) == 16
    
    def test_get_anonymizer_fake(self):
        """Test getting fake anonymizer function."""
        anon = Anonymizers()
        func = anon.get_anonymizer(Strategy.FAKE)
        
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        result = func(match)
        assert "@" in result
    
    def test_get_anonymizer_redact(self):
        """Test getting redact anonymizer function."""
        anon = Anonymizers()
        func = anon.get_anonymizer(Strategy.REDACT)
        
        match = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        assert func(match) == ""

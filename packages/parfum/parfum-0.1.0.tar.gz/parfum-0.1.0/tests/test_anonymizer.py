"""
Tests for the Parfum anonymizer.
"""

import pytest
from parfum import Anonymizer, PIIType, Strategy, PIIMatch


class TestAnonymizer:
    """Tests for the main Anonymizer class."""
    
    def test_anonymize_email(self):
        """Test email detection and anonymization."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Contact me at john.doe@example.com")
        
        assert "[EMAIL]" in result.text
        assert "john.doe@example.com" not in result.text
        assert result.pii_found
        assert result.pii_count == 1
    
    def test_anonymize_phone(self):
        """Test phone number detection."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Call me at 555-123-4567")
        
        assert "[PHONE]" in result.text
        assert "555-123-4567" not in result.text
    
    def test_anonymize_multiple_pii(self):
        """Test multiple PII types in one text."""
        anon = Anonymizer(use_ner=False)
        text = "Email: test@email.com, Phone: 555-123-4567, SSN: 123-45-6789"
        result = anon.anonymize(text)
        
        assert "[EMAIL]" in result.text
        assert "[PHONE]" in result.text
        assert "[SSN]" in result.text
        assert result.pii_count == 3
    
    def test_mask_strategy(self):
        """Test mask anonymization strategy."""
        anon = Anonymizer(strategy="mask", use_ner=False)
        result = anon.anonymize("Email: john@example.com")
        
        # Should contain masked email, not placeholder
        assert "[EMAIL]" not in result.text
        assert "@" in result.text
        assert "*" in result.text
    
    def test_fake_strategy(self):
        """Test fake data generation strategy."""
        anon = Anonymizer(strategy="fake", use_ner=False, seed=42)
        result = anon.anonymize("Email: john@example.com")
        
        # Should contain a different email
        assert "[EMAIL]" not in result.text
        assert "@" in result.text
        assert "john@example.com" not in result.text
    
    def test_hash_strategy(self):
        """Test hash anonymization strategy."""
        anon = Anonymizer(strategy="hash", use_ner=False)
        result = anon.anonymize("Email: john@example.com")
        
        # Hash should be hex string
        assert "[EMAIL]" not in result.text
        assert "john@example.com" not in result.text
    
    def test_redact_strategy(self):
        """Test redact (removal) strategy."""
        anon = Anonymizer(strategy="redact", use_ner=False)
        result = anon.anonymize("Email: john@example.com today")
        
        assert "john@example.com" not in result.text
        assert "[EMAIL]" not in result.text
        assert "Email:" in result.text
        assert "today" in result.text
    
    def test_no_pii(self):
        """Test text with no PII."""
        anon = Anonymizer(use_ner=False)
        text = "Hello, this is a simple message."
        result = anon.anonymize(text)
        
        assert result.text == text
        assert not result.pii_found
        assert result.pii_count == 0
    
    def test_anonymize_chat(self):
        """Test chat conversation anonymization."""
        anon = Anonymizer(use_ner=False)
        chat = [
            {"role": "user", "content": "My email is test@example.com"},
            {"role": "assistant", "content": "I'll contact you at that email."}
        ]
        
        result = anon.anonymize_chat(chat)
        
        assert "[EMAIL]" in result[0]["content"]
        assert "test@example.com" not in result[0]["content"]
        assert result[1]["content"] == chat[1]["content"]  # No PII, unchanged
    
    def test_custom_pattern(self):
        """Test adding custom patterns."""
        anon = Anonymizer(use_ner=False)
        anon.add_pattern("employee_id", r"EMP-\d{6}", PIIType.CUSTOM)
        
        result = anon.anonymize("Contact EMP-123456 for help")
        
        assert "[CUSTOM]" in result.text
        assert "EMP-123456" not in result.text
    
    def test_detect_only(self):
        """Test detection without anonymization."""
        anon = Anonymizer(use_ner=False)
        matches = anon.detect("Email: test@example.com, Phone: 555-123-4567")
        
        assert len(matches) == 2
        assert any(m.pii_type == PIIType.EMAIL for m in matches)
        assert any(m.pii_type == PIIType.PHONE for m in matches)
    
    def test_per_type_strategy(self):
        """Test different strategies per PII type."""
        anon = Anonymizer(strategy="replace", use_ner=False)
        anon.set_strategy(Strategy.MASK, pii_type=PIIType.EMAIL)
        
        result = anon.anonymize("Email: john.doe@example.com, SSN: 123-45-6789")
        
        # Email should be masked (contains * and @)
        assert "[EMAIL]" not in result.text
        assert "@" in result.text
        assert "john.doe@example.com" not in result.text
        # SSN should be replaced
        assert "[SSN]" in result.text


class TestPIIPatterns:
    """Tests for specific PII pattern detection."""
    
    def test_credit_card_visa(self):
        """Test Visa card detection."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Card: 4111-1111-1111-1111")
        
        assert "[CREDIT_CARD]" in result.text
    
    def test_credit_card_mastercard(self):
        """Test Mastercard detection."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Card: 5500 0000 0000 0004")
        
        assert "[CREDIT_CARD]" in result.text
    
    def test_ip_v4(self):
        """Test IPv4 address detection."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Server: 192.168.1.100")
        
        assert "[IP_ADDRESS]" in result.text
    
    def test_url(self):
        """Test URL detection."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Visit https://example.com/path")
        
        assert "[URL]" in result.text
    
    def test_date_iso(self):
        """Test ISO date detection."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Date: 2024-01-15")
        
        assert "[DATE]" in result.text
    
    def test_date_us_format(self):
        """Test US date format detection."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Date: 01/15/2024")
        
        assert "[DATE]" in result.text


class TestAnonymizedResult:
    """Tests for AnonymizedResult dataclass."""
    
    def test_replacements_dict(self):
        """Test replacements dictionary."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("Email: test@example.com")
        
        assert "test@example.com" in result.replacements
        assert result.replacements["test@example.com"] == "[EMAIL]"
    
    def test_get_by_type(self):
        """Test filtering matches by type."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("test@email.com and 555-123-4567")
        
        emails = result.get_by_type(PIIType.EMAIL)
        phones = result.get_by_type(PIIType.PHONE)
        
        assert len(emails) == 1
        assert len(phones) == 1
        assert emails[0].pii_type == PIIType.EMAIL


class TestMaskStrategy:
    """Tests for masking strategy specifics."""
    
    def test_mask_email(self):
        """Test email masking format."""
        anon = Anonymizer(strategy="mask", use_ner=False)
        result = anon.anonymize("john.doe@example.com")
        
        # Should preserve @ and domain structure
        assert "@" in result.text
        assert "*" in result.text
    
    def test_mask_phone(self):
        """Test phone masking - keeps first 3 and last 2 digits."""
        anon = Anonymizer(strategy="mask", use_ner=False)
        result = anon.anonymize("555-123-4567")
        
        # Should start with 555 and end with 67
        assert "555" in result.text
        assert result.text.endswith("67")
    
    def test_mask_credit_card(self):
        """Test credit card masking - keeps last 4 digits."""
        anon = Anonymizer(strategy="mask", use_ner=False)
        result = anon.anonymize("4111-1111-1111-1234")
        
        assert "1234" in result.text
        assert "4111" not in result.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

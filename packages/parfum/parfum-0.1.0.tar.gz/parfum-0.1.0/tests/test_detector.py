"""
Tests for the detector module.

Tests PIIDetector class and all its methods.
"""

import pytest
from parfum.detector import PIIDetector
from parfum.entities import PIIType, PIIMatch
from parfum.patterns import PatternRegistry


class TestPIIDetectorInit:
    """Tests for PIIDetector initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        detector = PIIDetector(use_ner=False)
        
        assert detector.pattern_registry is not None
        assert detector.use_ner is False
    
    def test_init_with_custom_registry(self):
        """Test initialization with custom registry."""
        custom_registry = PatternRegistry()
        detector = PIIDetector(use_ner=False, pattern_registry=custom_registry)
        
        assert detector.pattern_registry is custom_registry
    
    def test_init_with_ner_disabled(self):
        """Test initialization with NER explicitly disabled."""
        detector = PIIDetector(use_ner=False)
        
        assert detector._nlp is None
        assert detector.use_ner is False


class TestPIIDetectorDetect:
    """Tests for PIIDetector.detect() method."""
    
    def test_detect_email(self):
        """Test detecting email addresses."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Contact: test@example.com")
        
        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EMAIL
        assert matches[0].text == "test@example.com"
    
    def test_detect_phone(self):
        """Test detecting phone numbers."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Call: 555-123-4567")
        
        assert len(matches) >= 1
        phone_matches = [m for m in matches if m.pii_type == PIIType.PHONE]
        assert len(phone_matches) >= 1
    
    def test_detect_ssn(self):
        """Test detecting SSNs."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("SSN: 123-45-6789")
        
        ssn_matches = [m for m in matches if m.pii_type == PIIType.SSN]
        assert len(ssn_matches) >= 1
    
    def test_detect_credit_card(self):
        """Test detecting credit card numbers."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Card: 4111-1111-1111-1111")
        
        cc_matches = [m for m in matches if m.pii_type == PIIType.CREDIT_CARD]
        assert len(cc_matches) >= 1
    
    def test_detect_ip_address(self):
        """Test detecting IP addresses."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Server: 192.168.1.100")
        
        ip_matches = [m for m in matches if m.pii_type == PIIType.IP_ADDRESS]
        assert len(ip_matches) == 1
    
    def test_detect_url(self):
        """Test detecting URLs."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Visit: https://example.com/page")
        
        url_matches = [m for m in matches if m.pii_type == PIIType.URL]
        assert len(url_matches) >= 1
    
    def test_detect_date(self):
        """Test detecting dates."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Born: 2024-01-15")
        
        date_matches = [m for m in matches if m.pii_type == PIIType.DATE]
        assert len(date_matches) >= 1
    
    def test_detect_multiple_types(self):
        """Test detecting multiple PII types in same text."""
        detector = PIIDetector(use_ner=False)
        text = "Email: a@b.com, Phone: 555-123-4567, SSN: 123-45-6789"
        matches = detector.detect(text)
        
        types_found = {m.pii_type for m in matches}
        assert PIIType.EMAIL in types_found
        assert PIIType.PHONE in types_found or PIIType.SSN in types_found
    
    def test_detect_empty_text(self):
        """Test detecting PII in empty text."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("")
        
        assert matches == []
    
    def test_detect_no_pii(self):
        """Test detecting PII in text without PII."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Hello, this is a simple message.")
        
        assert len(matches) == 0
    
    def test_detect_positions_correct(self):
        """Test that detected positions are correct."""
        detector = PIIDetector(use_ner=False)
        text = "Email: test@example.com here"
        matches = detector.detect(text)
        
        email_match = [m for m in matches if m.pii_type == PIIType.EMAIL][0]
        assert text[email_match.start:email_match.end] == email_match.text
    
    def test_detect_sorted_by_position(self):
        """Test that matches are sorted by position."""
        detector = PIIDetector(use_ner=False)
        text = "a@b.com and 555-123-4567 and 192.168.1.1"
        matches = detector.detect(text)
        
        positions = [m.start for m in matches]
        assert positions == sorted(positions)


class TestPIIDetectorPatterns:
    """Tests for PIIDetector pattern detection internals."""
    
    def test_detect_with_patterns_returns_list(self):
        """Test _detect_with_patterns method."""
        detector = PIIDetector(use_ner=False)
        matches = detector._detect_with_patterns("test@example.com")
        
        assert isinstance(matches, list)
        assert len(matches) >= 1
    
    def test_pattern_match_score(self):
        """Test that pattern matches have correct score."""
        detector = PIIDetector(use_ner=False)
        matches = detector._detect_with_patterns("test@example.com")
        
        for match in matches:
            assert match.score == 0.95  # Regex confidence score


class TestPIIDetectorOverlaps:
    """Tests for overlap resolution."""
    
    def test_resolve_overlaps_keeps_higher_score(self):
        """Test that higher-scored matches are kept."""
        detector = PIIDetector(use_ner=False)
        
        matches = [
            PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16, score=0.95),
            PIIMatch(PIIType.URL, "example.com", 5, 16, score=0.90),
        ]
        
        resolved = detector._resolve_overlaps(matches)
        
        # Should keep the email (higher score, earlier start)
        assert len(resolved) == 1
        assert resolved[0].pii_type == PIIType.EMAIL
    
    def test_resolve_overlaps_non_overlapping(self):
        """Test that non-overlapping matches are all kept."""
        detector = PIIDetector(use_ner=False)
        
        matches = [
            PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7, score=0.95),
            PIIMatch(PIIType.PHONE, "555-1234", 10, 18, score=0.95),
        ]
        
        resolved = detector._resolve_overlaps(matches)
        
        assert len(resolved) == 2
    
    def test_resolve_overlaps_empty(self):
        """Test resolve_overlaps with empty list."""
        detector = PIIDetector(use_ner=False)
        resolved = detector._resolve_overlaps([])
        
        assert resolved == []


class TestPIIDetectorAddPattern:
    """Tests for adding custom patterns."""
    
    def test_add_pattern(self):
        """Test adding a custom pattern."""
        detector = PIIDetector(use_ner=False)
        detector.add_pattern(
            name="employee_id",
            pattern=r"EMP-\d{6}",
            pii_type=PIIType.CUSTOM,
        )
        
        matches = detector.detect("Contact EMP-123456 for help")
        
        custom_matches = [m for m in matches if m.pii_type == PIIType.CUSTOM]
        assert len(custom_matches) == 1
        assert custom_matches[0].text == "EMP-123456"
    
    def test_add_pattern_with_flags(self):
        """Test adding pattern with regex flags."""
        import re
        detector = PIIDetector(use_ner=False)
        detector.add_pattern(
            name="secret",
            pattern=r"SECRET-[A-Z]+",
            pii_type=PIIType.CUSTOM,
            flags=re.IGNORECASE,
        )
        
        matches = detector.detect("Code: secret-abc")
        
        custom_matches = [m for m in matches if m.pii_type == PIIType.CUSTOM]
        assert len(custom_matches) == 1
    
    def test_add_pattern_specific_type(self):
        """Test adding pattern with specific type."""
        detector = PIIDetector(use_ner=False)
        detector.add_pattern(
            name="company_email",
            pattern=r"\w+@company\.com",
            pii_type=PIIType.EMAIL,
        )
        
        matches = detector.detect("Contact: user@company.com")
        
        email_matches = [m for m in matches if m.pii_type == PIIType.EMAIL]
        assert len(email_matches) >= 1


class TestPIIDetectorDetectTypes:
    """Tests for detect_types method."""
    
    def test_detect_types_single(self):
        """Test detecting only specific types."""
        detector = PIIDetector(use_ner=False)
        text = "Email: a@b.com, Phone: 555-123-4567"
        
        matches = detector.detect_types(text, [PIIType.EMAIL])
        
        assert all(m.pii_type == PIIType.EMAIL for m in matches)
    
    def test_detect_types_multiple(self):
        """Test detecting multiple specific types."""
        detector = PIIDetector(use_ner=False)
        text = "Email: a@b.com, Phone: 555-123-4567, IP: 192.168.1.1"
        
        matches = detector.detect_types(text, [PIIType.EMAIL, PIIType.IP_ADDRESS])
        
        types_found = {m.pii_type for m in matches}
        assert PIIType.EMAIL in types_found
        assert PIIType.IP_ADDRESS in types_found
        assert PIIType.PHONE not in types_found
    
    def test_detect_types_none_found(self):
        """Test when specified types are not in text."""
        detector = PIIDetector(use_ner=False)
        text = "Email: a@b.com"
        
        matches = detector.detect_types(text, [PIIType.PHONE])
        
        assert len(matches) == 0

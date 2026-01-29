"""
Tests for the entities module.

Tests PIIType enum, PIIMatch dataclass, and AnonymizedResult dataclass.
"""

import pytest
from parfum.entities import PIIType, PIIMatch, AnonymizedResult


class TestPIIType:
    """Tests for PIIType enum."""
    
    def test_all_pii_types_exist(self):
        """Verify all expected PII types are defined."""
        expected_types = [
            "PERSON", "EMAIL", "PHONE", "CREDIT_CARD", "SSN", "IBAN",
            "IP_ADDRESS", "URL", "ADDRESS", "LOCATION", "DATE", 
            "DATE_OF_BIRTH", "ORGANIZATION", "CUSTOM"
        ]
        for type_name in expected_types:
            assert hasattr(PIIType, type_name), f"Missing PIIType: {type_name}"
    
    def test_pii_type_values(self):
        """Verify PII type values match their names."""
        assert PIIType.EMAIL.value == "EMAIL"
        assert PIIType.PERSON.value == "PERSON"
        assert PIIType.PHONE.value == "PHONE"
    
    def test_pii_type_iteration(self):
        """Test that PIIType can be iterated."""
        types = list(PIIType)
        assert len(types) >= 14
    
    def test_pii_type_comparison(self):
        """Test PIIType enum comparison."""
        assert PIIType.EMAIL == PIIType.EMAIL
        assert PIIType.EMAIL != PIIType.PHONE


class TestPIIMatch:
    """Tests for PIIMatch dataclass."""
    
    def test_create_match(self):
        """Test creating a PIIMatch."""
        match = PIIMatch(
            pii_type=PIIType.EMAIL,
            text="test@example.com",
            start=0,
            end=16,
        )
        assert match.pii_type == PIIType.EMAIL
        assert match.text == "test@example.com"
        assert match.start == 0
        assert match.end == 16
        assert match.score == 1.0  # Default value
        assert match.pattern_name is None
    
    def test_match_with_custom_score(self):
        """Test PIIMatch with custom score."""
        match = PIIMatch(
            pii_type=PIIType.PHONE,
            text="555-1234",
            start=10,
            end=18,
            score=0.85,
        )
        assert match.score == 0.85
    
    def test_match_with_pattern_name(self):
        """Test PIIMatch with pattern name."""
        match = PIIMatch(
            pii_type=PIIType.CUSTOM,
            text="EMP-123456",
            start=0,
            end=10,
            pattern_name="employee_id",
        )
        assert match.pattern_name == "employee_id"
    
    def test_match_repr(self):
        """Test PIIMatch string representation."""
        match = PIIMatch(
            pii_type=PIIType.EMAIL,
            text="test@example.com",
            start=5,
            end=21,
        )
        repr_str = repr(match)
        assert "EMAIL" in repr_str
        assert "test@example.com" in repr_str
        assert "5:21" in repr_str
    
    def test_overlaps_no_overlap(self):
        """Test overlaps() with non-overlapping matches."""
        match1 = PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7)
        match2 = PIIMatch(PIIType.PHONE, "555-1234", 10, 18)
        
        assert not match1.overlaps(match2)
        assert not match2.overlaps(match1)
    
    def test_overlaps_with_overlap(self):
        """Test overlaps() with overlapping matches."""
        match1 = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)
        match2 = PIIMatch(PIIType.URL, "example.com", 5, 16)
        
        assert match1.overlaps(match2)
        assert match2.overlaps(match1)
    
    def test_overlaps_adjacent(self):
        """Test overlaps() with adjacent (non-overlapping) matches."""
        match1 = PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7)
        match2 = PIIMatch(PIIType.PHONE, "555", 7, 10)
        
        assert not match1.overlaps(match2)
        assert not match2.overlaps(match1)
    
    def test_overlaps_contained(self):
        """Test overlaps() where one match contains another."""
        match1 = PIIMatch(PIIType.EMAIL, "test@example.com", 0, 30)
        match2 = PIIMatch(PIIType.URL, "example.com", 10, 21)
        
        assert match1.overlaps(match2)
        assert match2.overlaps(match1)


class TestAnonymizedResult:
    """Tests for AnonymizedResult dataclass."""
    
    def test_create_result(self):
        """Test creating an AnonymizedResult."""
        matches = [
            PIIMatch(PIIType.EMAIL, "test@example.com", 7, 23)
        ]
        result = AnonymizedResult(
            text="Email: [EMAIL]",
            original_text="Email: test@example.com",
            matches=matches,
            replacements={"test@example.com": "[EMAIL]"},
        )
        
        assert result.text == "Email: [EMAIL]"
        assert result.original_text == "Email: test@example.com"
        assert len(result.matches) == 1
        assert "test@example.com" in result.replacements
    
    def test_pii_found_true(self):
        """Test pii_found property when PII exists."""
        result = AnonymizedResult(
            text="[EMAIL]",
            original_text="test@example.com",
            matches=[PIIMatch(PIIType.EMAIL, "test@example.com", 0, 16)],
            replacements={"test@example.com": "[EMAIL]"},
        )
        assert result.pii_found is True
    
    def test_pii_found_false(self):
        """Test pii_found property when no PII exists."""
        result = AnonymizedResult(
            text="Hello world",
            original_text="Hello world",
            matches=[],
            replacements={},
        )
        assert result.pii_found is False
    
    def test_pii_count(self):
        """Test pii_count property."""
        matches = [
            PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7),
            PIIMatch(PIIType.PHONE, "555-1234", 10, 18),
            PIIMatch(PIIType.SSN, "123-45-6789", 20, 31),
        ]
        result = AnonymizedResult(
            text="[EMAIL] [PHONE] [SSN]",
            original_text="a@b.com 555-1234 123-45-6789",
            matches=matches,
            replacements={},
        )
        assert result.pii_count == 3
    
    def test_get_by_type_single(self):
        """Test get_by_type with single match."""
        matches = [
            PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7),
            PIIMatch(PIIType.PHONE, "555-1234", 10, 18),
        ]
        result = AnonymizedResult(
            text="", original_text="", matches=matches, replacements={}
        )
        
        emails = result.get_by_type(PIIType.EMAIL)
        assert len(emails) == 1
        assert emails[0].pii_type == PIIType.EMAIL
    
    def test_get_by_type_multiple(self):
        """Test get_by_type with multiple matches of same type."""
        matches = [
            PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7),
            PIIMatch(PIIType.EMAIL, "c@d.com", 10, 17),
            PIIMatch(PIIType.PHONE, "555-1234", 20, 28),
        ]
        result = AnonymizedResult(
            text="", original_text="", matches=matches, replacements={}
        )
        
        emails = result.get_by_type(PIIType.EMAIL)
        assert len(emails) == 2
    
    def test_get_by_type_none(self):
        """Test get_by_type when no matches of type exist."""
        matches = [
            PIIMatch(PIIType.EMAIL, "a@b.com", 0, 7),
        ]
        result = AnonymizedResult(
            text="", original_text="", matches=matches, replacements={}
        )
        
        phones = result.get_by_type(PIIType.PHONE)
        assert len(phones) == 0

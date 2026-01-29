"""
Parfum - PII entity type definitions.

Defines the types of personally identifiable information (PII) 
that can be detected and anonymized.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class PIIType(Enum):
    """Enumeration of PII entity types."""
    
    # Identity
    PERSON = "PERSON"
    
    # Contact Information
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    
    # Financial
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    IBAN = "IBAN"
    
    # Technical
    IP_ADDRESS = "IP_ADDRESS"
    URL = "URL"
    
    # Location & Time
    ADDRESS = "ADDRESS"
    LOCATION = "LOCATION"
    DATE = "DATE"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    
    # Organization
    ORGANIZATION = "ORGANIZATION"
    
    # Custom user-defined patterns
    CUSTOM = "CUSTOM"


@dataclass
class PIIMatch:
    """Represents a detected PII entity in text."""
    
    pii_type: PIIType
    text: str
    start: int
    end: int
    score: float = 1.0
    pattern_name: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"PIIMatch({self.pii_type.value}: '{self.text}' [{self.start}:{self.end}])"
    
    def overlaps(self, other: "PIIMatch") -> bool:
        """Check if this match overlaps with another."""
        return not (self.end <= other.start or self.start >= other.end)


@dataclass
class AnonymizedResult:
    """Result of anonymization containing the cleaned text and metadata."""
    
    text: str
    original_text: str
    matches: list[PIIMatch]
    replacements: dict[str, str]
    
    @property
    def pii_found(self) -> bool:
        """Returns True if any PII was detected."""
        return len(self.matches) > 0
    
    @property
    def pii_count(self) -> int:
        """Returns the number of PII entities found."""
        return len(self.matches)
    
    def get_by_type(self, pii_type: PIIType) -> list[PIIMatch]:
        """Get all matches of a specific PII type."""
        return [m for m in self.matches if m.pii_type == pii_type]

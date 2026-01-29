"""
Parfum - Regex patterns for PII detection.

Contains compiled regex patterns for detecting various types of 
personally identifiable information in text.
"""

import re
from typing import Pattern
from .entities import PIIType


# Email pattern - RFC 5322 simplified
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

# Phone patterns - supports multiple international formats
PHONE_PATTERNS = [
    # US/Canada: (123) 456-7890, 123-456-7890, 123.456.7890
    re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    # International with country code: +91 12345 67890, +44 1234 567890
    re.compile(r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),
    # Generic: 10+ digit numbers that look like phones
    re.compile(r'\b\d{10,15}\b'),
]

# Credit card patterns
CREDIT_CARD_PATTERNS = [
    # Visa: 4xxx xxxx xxxx xxxx
    re.compile(r'\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    # Mastercard: 5xxx xxxx xxxx xxxx
    re.compile(r'\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    # American Express: 3xxx xxxxxx xxxxx
    re.compile(r'\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b'),
    # Generic 16 digit card number
    re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
]

# SSN pattern (US Social Security Number)
SSN_PATTERN = re.compile(
    r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
)

# IP Address patterns
IP_V4_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

IP_V6_PATTERN = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|'
    r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|'
    r'\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b',
    re.IGNORECASE
)

# URL pattern
URL_PATTERN = re.compile(
    r'\b(?:https?://)?(?:www\.)?'
    r'[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z]{2,})+(?:/[^\s]*)?\b',
    re.IGNORECASE
)

# Date patterns - various common formats
DATE_PATTERNS = [
    # ISO format: 2024-01-15
    re.compile(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'),
    # US format: 01/15/2024, 01-15-2024
    re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'),
    # Written: January 15, 2024 or 15 January 2024
    re.compile(
        r'\b(?:January|February|March|April|May|June|July|August|'
        r'September|October|November|December|'
        r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+'
        r'\d{1,2}(?:st|nd|rd|th)?,?\s*\d{2,4}\b',
        re.IGNORECASE
    ),
    re.compile(
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+'
        r'(?:January|February|March|April|May|June|July|August|'
        r'September|October|November|December|'
        r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?,?\s*\d{2,4}\b',
        re.IGNORECASE
    ),
]

# IBAN pattern (International Bank Account Number)
IBAN_PATTERN = re.compile(
    r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b',
    re.IGNORECASE
)


class PatternRegistry:
    """Registry of regex patterns mapped to PII types."""
    
    def __init__(self):
        self._patterns: dict[PIIType, list[Pattern]] = {
            PIIType.EMAIL: [EMAIL_PATTERN],
            PIIType.PHONE: PHONE_PATTERNS,
            PIIType.CREDIT_CARD: CREDIT_CARD_PATTERNS,
            PIIType.SSN: [SSN_PATTERN],
            PIIType.IP_ADDRESS: [IP_V4_PATTERN, IP_V6_PATTERN],
            PIIType.URL: [URL_PATTERN],
            PIIType.DATE: DATE_PATTERNS,
            PIIType.IBAN: [IBAN_PATTERN],
        }
        self._custom_patterns: dict[str, tuple[Pattern, PIIType]] = {}
    
    def get_patterns(self, pii_type: PIIType) -> list[Pattern]:
        """Get all patterns for a specific PII type."""
        return self._patterns.get(pii_type, [])
    
    def get_all_patterns(self) -> dict[PIIType, list[Pattern]]:
        """Get all registered patterns."""
        return self._patterns.copy()
    
    def add_custom_pattern(
        self, 
        name: str, 
        pattern: str, 
        pii_type: PIIType = PIIType.CUSTOM,
        flags: int = 0
    ) -> None:
        """Add a custom regex pattern."""
        compiled = re.compile(pattern, flags)
        self._custom_patterns[name] = (compiled, pii_type)
        
        # Also add to the main patterns dict
        if pii_type not in self._patterns:
            self._patterns[pii_type] = []
        self._patterns[pii_type].append(compiled)
    
    def get_custom_patterns(self) -> dict[str, tuple[Pattern, PIIType]]:
        """Get all custom patterns."""
        return self._custom_patterns.copy()


# Default pattern registry instance
default_registry = PatternRegistry()

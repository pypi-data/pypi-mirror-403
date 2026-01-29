"""
Parfum - PII Anonymization for LLM Training Data.

A Python library for anonymizing personally identifiable information (PII)
in private chat data before training language models.

Example:
    >>> from parfum import Anonymizer
    >>> anon = Anonymizer()
    >>> result = anon.anonymize("Contact me at john@example.com")
    >>> print(result.text)
    "Contact me at [EMAIL]"
"""

__version__ = "0.1.0"

from .entities import PIIType, PIIMatch, AnonymizedResult
from .strategies import Strategy
from .anonymizer import Anonymizer, anonymize
from .detector import PIIDetector
from .chat import (
    process_file,
    process_directory,
    process_json,
    process_jsonl,
    process_csv,
    process_text,
)

__all__ = [
    # Version
    "__version__",
    # Main classes
    "Anonymizer",
    "PIIDetector",
    # Enums
    "PIIType",
    "Strategy",
    # Data classes
    "PIIMatch",
    "AnonymizedResult",
    # Functions
    "anonymize",
    "process_file",
    "process_directory",
    "process_json",
    "process_jsonl",
    "process_csv",
    "process_text",
]

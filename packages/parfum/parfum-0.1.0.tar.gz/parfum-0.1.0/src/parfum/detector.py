"""
Parfum - PII Detection Engine.

Combines regex-based pattern matching with optional NER-based 
detection for comprehensive PII identification.
"""

from typing import Optional, Callable
import logging

from .entities import PIIType, PIIMatch
from .patterns import PatternRegistry, default_registry


logger = logging.getLogger(__name__)


class PIIDetector:
    """
    Detects personally identifiable information in text.
    
    Combines regex patterns for structured data (emails, phones, etc.)
    with optional NER for unstructured entities (names, locations).
    """
    
    def __init__(
        self,
        use_ner: bool = True,
        ner_model: str = "en_core_web_sm",
        pattern_registry: Optional[PatternRegistry] = None,
    ):
        """
        Initialize the PII detector.
        
        Args:
            use_ner: Whether to use NER for name/location detection
            ner_model: spaCy model name for NER
            pattern_registry: Custom pattern registry (uses default if None)
        """
        self.pattern_registry = pattern_registry or default_registry
        self.use_ner = use_ner
        self._nlp = None
        self._ner_model = ner_model
        
        if use_ner:
            self._load_ner_model()
    
    def _load_ner_model(self) -> None:
        """Load spaCy NER model if available."""
        try:
            import spacy
            try:
                self._nlp = spacy.load(self._ner_model)
                logger.info(f"Loaded spaCy model: {self._ner_model}")
            except OSError:
                logger.warning(
                    f"spaCy model '{self._ner_model}' not found. "
                    f"Run: python -m spacy download {self._ner_model}"
                )
                self._nlp = None
                self.use_ner = False
        except ImportError:
            logger.warning(
                "spaCy not installed. NER-based detection disabled. "
                "Install with: pip install parfum[ner]"
            )
            self._nlp = None
            self.use_ner = False
    
    def detect(self, text: str) -> list[PIIMatch]:
        """
        Detect all PII entities in text.
        
        Args:
            text: Input text to scan for PII
            
        Returns:
            List of PIIMatch objects for all detected entities
        """
        matches: list[PIIMatch] = []
        
        # Regex-based detection
        matches.extend(self._detect_with_patterns(text))
        
        # NER-based detection
        if self.use_ner and self._nlp:
            matches.extend(self._detect_with_ner(text))
        
        # Remove overlapping matches (keep higher score)
        matches = self._resolve_overlaps(matches)
        
        # Sort by position
        matches.sort(key=lambda m: m.start)
        
        return matches
    
    def _detect_with_patterns(self, text: str) -> list[PIIMatch]:
        """Detect PII using regex patterns."""
        matches = []
        
        for pii_type, patterns in self.pattern_registry.get_all_patterns().items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    matches.append(PIIMatch(
                        pii_type=pii_type,
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        score=0.95,  # High confidence for regex matches
                    ))
        
        return matches
    
    def _detect_with_ner(self, text: str) -> list[PIIMatch]:
        """Detect PII using spaCy NER."""
        matches = []
        
        if not self._nlp:
            return matches
        
        doc = self._nlp(text)
        
        # Map spaCy entity labels to PIIType
        label_mapping = {
            "PERSON": PIIType.PERSON,
            "ORG": PIIType.ORGANIZATION,
            "GPE": PIIType.LOCATION,  # Geo-political entity
            "LOC": PIIType.LOCATION,
            "FAC": PIIType.LOCATION,  # Facility
            "DATE": PIIType.DATE,
        }
        
        for ent in doc.ents:
            if ent.label_ in label_mapping:
                matches.append(PIIMatch(
                    pii_type=label_mapping[ent.label_],
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    score=0.85,  # Slightly lower for NER
                ))
        
        return matches
    
    def _resolve_overlaps(self, matches: list[PIIMatch]) -> list[PIIMatch]:
        """Remove overlapping matches, keeping higher-scored ones."""
        if not matches:
            return matches
        
        # Sort by start position, then by score (descending)
        sorted_matches = sorted(matches, key=lambda m: (m.start, -m.score))
        
        resolved = []
        for match in sorted_matches:
            # Check if this match overlaps with any already accepted match
            overlaps = False
            for accepted in resolved:
                if match.overlaps(accepted):
                    overlaps = True
                    break
            
            if not overlaps:
                resolved.append(match)
        
        return resolved
    
    def add_pattern(
        self,
        name: str,
        pattern: str,
        pii_type: PIIType = PIIType.CUSTOM,
        flags: int = 0,
    ) -> None:
        """
        Add a custom regex pattern for detection.
        
        Args:
            name: Unique name for the pattern
            pattern: Regex pattern string
            pii_type: PII type to assign to matches
            flags: Regex flags (e.g., re.IGNORECASE)
        """
        self.pattern_registry.add_custom_pattern(name, pattern, pii_type, flags)
    
    def detect_types(
        self, 
        text: str, 
        types: list[PIIType]
    ) -> list[PIIMatch]:
        """
        Detect only specific PII types.
        
        Args:
            text: Input text
            types: List of PII types to detect
            
        Returns:
            List of matches for specified types only
        """
        all_matches = self.detect(text)
        return [m for m in all_matches if m.pii_type in types]

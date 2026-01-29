"""
Parfum - Main Anonymizer Class.

The primary interface for anonymizing PII in text and chat data.
"""

from typing import Optional, Union, Callable
import logging

from .entities import PIIType, PIIMatch, AnonymizedResult
from .detector import PIIDetector
from .strategies import Strategy, Anonymizers
from .patterns import PatternRegistry


logger = logging.getLogger(__name__)


class Anonymizer:
    """
    Main class for anonymizing personally identifiable information.
    
    Example:
        >>> from parfum import Anonymizer
        >>> anon = Anonymizer()
        >>> result = anon.anonymize("Email me at john@example.com")
        >>> print(result.text)
        "Email me at [EMAIL]"
    """
    
    def __init__(
        self,
        strategy: Union[str, Strategy] = Strategy.REPLACE,
        use_ner: bool = True,
        ner_model: str = "en_core_web_sm",
        locale: str = "en_US",
        seed: Optional[int] = None,
        pattern_registry: Optional[PatternRegistry] = None,
    ):
        """
        Initialize the anonymizer.
        
        Args:
            strategy: Anonymization strategy (replace, mask, hash, fake, redact)
            use_ner: Whether to use NER for name/location detection
            ner_model: spaCy model name for NER
            locale: Locale for generating fake data
            seed: Random seed for reproducible fake data
            pattern_registry: Custom pattern registry
        """
        # Parse strategy
        if isinstance(strategy, str):
            strategy = Strategy(strategy.lower())
        self.strategy = strategy
        
        # Initialize components
        self.detector = PIIDetector(
            use_ner=use_ner,
            ner_model=ner_model,
            pattern_registry=pattern_registry,
        )
        self.anonymizers = Anonymizers(locale=locale, seed=seed)
        
        # Custom anonymizers per PII type
        self._type_strategies: dict[PIIType, Union[Strategy, Callable]] = {}
    
    def anonymize(self, text: str) -> AnonymizedResult:
        """
        Anonymize all PII in the given text.
        
        Args:
            text: Input text containing potential PII
            
        Returns:
            AnonymizedResult with cleaned text and metadata
        """
        # Detect all PII
        matches = self.detector.detect(text)
        
        if not matches:
            return AnonymizedResult(
                text=text,
                original_text=text,
                matches=[],
                replacements={},
            )
        
        # Apply anonymization (process from end to preserve positions)
        result_text = text
        replacements = {}
        
        for match in sorted(matches, key=lambda m: m.start, reverse=True):
            # Get strategy for this type
            type_strategy = self._type_strategies.get(match.pii_type, self.strategy)
            
            # Apply anonymization
            if callable(type_strategy):
                replacement = type_strategy(match)
            else:
                anonymizer_fn = self.anonymizers.get_anonymizer(type_strategy)
                replacement = anonymizer_fn(match)
            
            # Replace in text
            result_text = result_text[:match.start] + replacement + result_text[match.end:]
            replacements[match.text] = replacement
        
        return AnonymizedResult(
            text=result_text,
            original_text=text,
            matches=matches,
            replacements=replacements,
        )
    
    def anonymize_many(self, texts: list[str]) -> list[AnonymizedResult]:
        """
        Anonymize multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of AnonymizedResult objects
        """
        return [self.anonymize(text) for text in texts]
    
    def anonymize_chat(
        self,
        messages: list[dict],
        content_key: str = "content",
    ) -> list[dict]:
        """
        Anonymize a chat conversation while preserving structure.
        
        Args:
            messages: List of message dictionaries (e.g., [{"role": "user", "content": "..."}])
            content_key: Key containing the text content in each message
            
        Returns:
            New list of messages with anonymized content
        """
        result = []
        
        for message in messages:
            new_message = message.copy()
            if content_key in new_message:
                anonymized = self.anonymize(new_message[content_key])
                new_message[content_key] = anonymized.text
            result.append(new_message)
        
        return result
    
    def set_strategy(
        self,
        strategy: Union[str, Strategy],
        pii_type: Optional[PIIType] = None,
    ) -> None:
        """
        Set anonymization strategy globally or for a specific PII type.
        
        Args:
            strategy: The strategy to use
            pii_type: If specified, apply only to this PII type
        """
        if isinstance(strategy, str):
            strategy = Strategy(strategy.lower())
        
        if pii_type:
            self._type_strategies[pii_type] = strategy
        else:
            self.strategy = strategy
    
    def set_custom_anonymizer(
        self,
        pii_type: PIIType,
        anonymizer: Callable[[PIIMatch], str],
    ) -> None:
        """
        Set a custom anonymization function for a PII type.
        
        Args:
            pii_type: The PII type to customize
            anonymizer: Function that takes PIIMatch and returns replacement string
        """
        self._type_strategies[pii_type] = anonymizer
    
    def add_pattern(
        self,
        name: str,
        pattern: str,
        pii_type: PIIType = PIIType.CUSTOM,
        flags: int = 0,
    ) -> None:
        """
        Add a custom regex pattern for PII detection.
        
        Args:
            name: Unique name for the pattern
            pattern: Regex pattern string
            pii_type: PII type to assign to matches
            flags: Regex flags
        """
        self.detector.add_pattern(name, pattern, pii_type, flags)
    
    def detect(self, text: str) -> list[PIIMatch]:
        """
        Detect PII without anonymizing.
        
        Args:
            text: Input text
            
        Returns:
            List of detected PII matches
        """
        return self.detector.detect(text)
    
    def clear_cache(self) -> None:
        """Clear the fake data cache (for 'fake' strategy)."""
        self.anonymizers.clear_cache()


def anonymize(
    text: str,
    strategy: str = "replace",
    use_ner: bool = True,
) -> str:
    """
    Quick function to anonymize text with default settings.
    
    Args:
        text: Input text
        strategy: Anonymization strategy
        use_ner: Whether to use NER
        
    Returns:
        Anonymized text string
    """
    anonymizer = Anonymizer(strategy=strategy, use_ner=use_ner)
    return anonymizer.anonymize(text).text

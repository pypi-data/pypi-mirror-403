"""
Parfum - Anonymization Strategies.

Different methods for anonymizing detected PII entities.
"""

import hashlib
from enum import Enum
from typing import Callable, Optional
from faker import Faker

from .entities import PIIType, PIIMatch


class Strategy(Enum):
    """Available anonymization strategies."""
    
    REPLACE = "replace"    # Replace with [PII_TYPE] placeholder
    MASK = "mask"          # Partial masking: john@email.com -> j***@e***.com
    HASH = "hash"          # SHA-256 hash
    FAKE = "fake"          # Generate realistic fake data
    REDACT = "redact"      # Complete removal


class Anonymizers:
    """
    Collection of anonymization functions for different strategies.
    """
    
    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize anonymizers.
        
        Args:
            locale: Locale for Faker to generate locale-appropriate fake data
            seed: Random seed for reproducible fake data generation
        """
        self.faker = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
        
        # Cache for consistent fake replacements within a session
        self._fake_cache: dict[str, str] = {}
    
    def replace(self, match: PIIMatch) -> str:
        """Replace with placeholder like [EMAIL] or [PERSON]."""
        return f"[{match.pii_type.value}]"
    
    def redact(self, match: PIIMatch) -> str:
        """Completely remove the PII."""
        return ""
    
    def mask(self, match: PIIMatch) -> str:
        """Partially mask the PII value."""
        text = match.text
        pii_type = match.pii_type
        
        if pii_type == PIIType.EMAIL:
            return self._mask_email(text)
        elif pii_type == PIIType.PHONE:
            return self._mask_phone(text)
        elif pii_type == PIIType.CREDIT_CARD:
            return self._mask_credit_card(text)
        elif pii_type == PIIType.SSN:
            return self._mask_ssn(text)
        elif pii_type == PIIType.IP_ADDRESS:
            return self._mask_ip(text)
        else:
            # Generic masking: show first and last char
            return self._mask_generic(text)
    
    def hash(self, match: PIIMatch) -> str:
        """Hash the PII value using SHA-256."""
        hash_obj = hashlib.sha256(match.text.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # Truncate for readability
    
    def fake(self, match: PIIMatch) -> str:
        """Generate realistic fake data."""
        # Check cache for consistent replacement
        cache_key = f"{match.pii_type.value}:{match.text}"
        if cache_key in self._fake_cache:
            return self._fake_cache[cache_key]
        
        fake_value = self._generate_fake(match)
        self._fake_cache[cache_key] = fake_value
        return fake_value
    
    def _generate_fake(self, match: PIIMatch) -> str:
        """Generate type-appropriate fake data."""
        pii_type = match.pii_type
        
        generators = {
            PIIType.PERSON: self.faker.name,
            PIIType.EMAIL: self.faker.email,
            PIIType.PHONE: self.faker.phone_number,
            PIIType.CREDIT_CARD: lambda: self.faker.credit_card_number(card_type=None),
            PIIType.SSN: self.faker.ssn,
            PIIType.IP_ADDRESS: self.faker.ipv4,
            PIIType.URL: self.faker.url,
            PIIType.DATE: lambda: self.faker.date(),
            PIIType.DATE_OF_BIRTH: lambda: self.faker.date_of_birth().strftime("%Y-%m-%d"),
            PIIType.ADDRESS: self.faker.address,
            PIIType.LOCATION: self.faker.city,
            PIIType.ORGANIZATION: self.faker.company,
            PIIType.IBAN: self.faker.iban,
        }
        
        generator = generators.get(pii_type, lambda: f"[{pii_type.value}]")
        return generator()
    
    def _mask_email(self, email: str) -> str:
        """Mask email: john.doe@example.com -> j***.d**@e******.com"""
        if "@" not in email:
            return self._mask_generic(email)
        
        local, domain = email.rsplit("@", 1)
        masked_local = self._mask_part(local)
        
        if "." in domain:
            domain_name, tld = domain.rsplit(".", 1)
            masked_domain = self._mask_part(domain_name) + "." + tld
        else:
            masked_domain = self._mask_part(domain)
        
        return f"{masked_local}@{masked_domain}"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone: 555-123-4567 -> 555-***-**67"""
        # Keep first 3 and last 2 digits
        digits = [c for c in phone if c.isdigit()]
        if len(digits) < 6:
            return "*" * len(phone)
        
        result = []
        digit_count = 0
        for c in phone:
            if c.isdigit():
                if digit_count < 3 or digit_count >= len(digits) - 2:
                    result.append(c)
                else:
                    result.append("*")
                digit_count += 1
            else:
                result.append(c)
        
        return "".join(result)
    
    def _mask_credit_card(self, card: str) -> str:
        """Mask credit card: 4111-1111-1111-1111 -> ****-****-****-1111"""
        # Keep only last 4 digits
        digits = [c for c in card if c.isdigit()]
        result = []
        digit_count = 0
        
        for c in card:
            if c.isdigit():
                if digit_count >= len(digits) - 4:
                    result.append(c)
                else:
                    result.append("*")
                digit_count += 1
            else:
                result.append(c)
        
        return "".join(result)
    
    def _mask_ssn(self, ssn: str) -> str:
        """Mask SSN: 123-45-6789 -> ***-**-6789"""
        # Keep only last 4 digits
        digits = [c for c in ssn if c.isdigit()]
        result = []
        digit_count = 0
        
        for c in ssn:
            if c.isdigit():
                if digit_count >= len(digits) - 4:
                    result.append(c)
                else:
                    result.append("*")
                digit_count += 1
            else:
                result.append(c)
        
        return "".join(result)
    
    def _mask_ip(self, ip: str) -> str:
        """Mask IP: 192.168.1.100 -> 192.168.*.*"""
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        return self._mask_generic(ip)
    
    def _mask_part(self, text: str) -> str:
        """Mask a text part, keeping first character."""
        if len(text) <= 1:
            return text
        return text[0] + "*" * (len(text) - 1)
    
    def _mask_generic(self, text: str) -> str:
        """Generic masking: keep first and last character."""
        if len(text) <= 2:
            return "*" * len(text)
        return text[0] + "*" * (len(text) - 2) + text[-1]
    
    def clear_cache(self) -> None:
        """Clear the fake data cache."""
        self._fake_cache.clear()
    
    def get_anonymizer(self, strategy: Strategy) -> Callable[[PIIMatch], str]:
        """Get the anonymization function for a strategy."""
        strategy_map = {
            Strategy.REPLACE: self.replace,
            Strategy.MASK: self.mask,
            Strategy.HASH: self.hash,
            Strategy.FAKE: self.fake,
            Strategy.REDACT: self.redact,
        }
        return strategy_map[strategy]

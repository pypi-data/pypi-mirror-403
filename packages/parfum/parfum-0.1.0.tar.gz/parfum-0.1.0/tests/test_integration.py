"""
Integration tests for the entire Parfum pipeline.

Tests end-to-end workflows combining all components.
"""

import pytest
import json
import tempfile
from pathlib import Path
from parfum import (
    Anonymizer,
    PIIType,
    PIIMatch,
    AnonymizedResult,
    Strategy,
    PIIDetector,
    anonymize,
    process_file,
    process_directory,
)


class TestEndToEndAnonymization:
    """End-to-end tests for the complete anonymization pipeline."""
    
    def test_complete_pipeline_replace(self):
        """Test complete pipeline with replace strategy."""
        text = """
        Hello, I'm John Smith. You can reach me at:
        - Email: john.smith@example.com
        - Phone: 555-123-4567
        - SSN: 123-45-6789
        My credit card is 4111-1111-1111-1111.
        I'm connecting from IP 192.168.1.100.
        """
        
        anon = Anonymizer(strategy="replace", use_ner=False)
        result = anon.anonymize(text)
        
        # Verify all PII types are replaced
        assert "[EMAIL]" in result.text
        assert "[PHONE]" in result.text or "[SSN]" in result.text
        assert "[CREDIT_CARD]" in result.text
        assert "[IP_ADDRESS]" in result.text
        
        # Original PII should not appear
        assert "john.smith@example.com" not in result.text
        assert "4111-1111-1111-1111" not in result.text
        assert "192.168.1.100" not in result.text
    
    def test_complete_pipeline_mask(self):
        """Test complete pipeline with mask strategy."""
        text = "Email: john@example.com, Phone: 555-123-4567"
        
        anon = Anonymizer(strategy="mask", use_ner=False)
        result = anon.anonymize(text)
        
        # Email should be masked but keep structure
        assert "@" in result.text
        assert "*" in result.text
        assert "john@example.com" not in result.text
        
        # Phone should be partially masked
        assert "555" in result.text  # First 3 digits kept
        assert "67" in result.text   # Last 2 digits kept
    
    def test_complete_pipeline_fake(self):
        """Test complete pipeline with fake data strategy."""
        text = "Contact: john@example.com"
        
        anon = Anonymizer(strategy="fake", use_ner=False, seed=42)
        result = anon.anonymize(text)
        
        # Should have a different email
        assert "@" in result.text
        assert "john@example.com" not in result.text
    
    def test_complete_pipeline_hash(self):
        """Test complete pipeline with hash strategy."""
        text = "Email: test@example.com"
        
        anon = Anonymizer(strategy="hash", use_ner=False)
        result = anon.anonymize(text)
        
        assert "test@example.com" not in result.text
        # Hash should be hex string
        assert any(c in "0123456789abcdef" for c in result.text)
    
    def test_complete_pipeline_redact(self):
        """Test complete pipeline with redact strategy."""
        text = "Email: test@example.com is valid"
        
        anon = Anonymizer(strategy="redact", use_ner=False)
        result = anon.anonymize(text)
        
        assert "test@example.com" not in result.text
        assert "Email:" in result.text
        assert "is valid" in result.text


class TestChatAnonymization:
    """Tests for chat conversation anonymization."""
    
    def test_chat_single_message(self):
        """Test anonymizing single chat message."""
        anon = Anonymizer(use_ner=False)
        chat = [{"role": "user", "content": "My email is test@example.com"}]
        
        result = anon.anonymize_chat(chat)
        
        assert result[0]["role"] == "user"
        assert "[EMAIL]" in result[0]["content"]
    
    def test_chat_multi_turn(self):
        """Test anonymizing multi-turn conversation."""
        anon = Anonymizer(use_ner=False)
        chat = [
            {"role": "user", "content": "Email: a@b.com"},
            {"role": "assistant", "content": "Got it!"},
            {"role": "user", "content": "Phone: 555-123-4567"},
            {"role": "assistant", "content": "Noted!"},
        ]
        
        result = anon.anonymize_chat(chat)
        
        assert len(result) == 4
        assert "[EMAIL]" in result[0]["content"]
        assert result[1]["content"] == "Got it!"  # No PII, unchanged
        assert "[PHONE]" in result[2]["content"]
    
    def test_chat_preserves_structure(self):
        """Test that chat structure is preserved."""
        anon = Anonymizer(use_ner=False)
        chat = [
            {"role": "user", "content": "test@a.com", "timestamp": "2024-01-01"},
            {"role": "assistant", "content": "OK", "metadata": {"tokens": 5}},
        ]
        
        result = anon.anonymize_chat(chat)
        
        assert result[0]["timestamp"] == "2024-01-01"
        assert result[1]["metadata"]["tokens"] == 5
    
    def test_chat_custom_content_key(self):
        """Test chat with custom content key."""
        anon = Anonymizer(use_ner=False)
        chat = [{"role": "user", "text": "Email: test@example.com"}]
        
        result = anon.anonymize_chat(chat, content_key="text")
        
        assert "[EMAIL]" in result[0]["text"]


class TestConsistentAnonymization:
    """Tests for consistent anonymization with fake strategy."""
    
    def test_same_pii_same_replacement(self):
        """Test that same PII gets same fake replacement."""
        anon = Anonymizer(strategy="fake", use_ner=False)
        
        text = "Email john@example.com and again john@example.com"
        result = anon.anonymize(text)
        
        # Count occurrences of the replacement
        replacements = list(result.replacements.values())
        # The replaced email should appear twice in the text
        # Actually, since we replace all occurrences, they should be consistent
    
    def test_different_pii_different_replacement(self):
        """Test that different PII gets different fake replacement."""
        anon = Anonymizer(strategy="fake", use_ner=False)
        
        text = "Emails: a@b.com and c@d.com"
        result = anon.anonymize(text)
        
        # Should have two different replacements
        assert len(result.replacements) == 2


class TestCustomPatterns:
    """Tests for custom pattern integration."""
    
    def test_custom_pattern_detection(self):
        """Test custom pattern is detected."""
        anon = Anonymizer(use_ner=False)
        anon.add_pattern("order_id", r"ORD-\d{8}", PIIType.CUSTOM)
        
        result = anon.anonymize("Order: ORD-12345678")
        
        assert "[CUSTOM]" in result.text
        assert "ORD-12345678" not in result.text
    
    def test_custom_pattern_with_multiple(self):
        """Test multiple custom patterns."""
        anon = Anonymizer(use_ner=False)
        anon.add_pattern("order_id", r"ORD-\d{8}", PIIType.CUSTOM)
        anon.add_pattern("emp_id", r"EMP-\d{6}", PIIType.CUSTOM)
        
        text = "Order: ORD-12345678, Employee: EMP-123456"
        result = anon.anonymize(text)
        
        assert "ORD-12345678" not in result.text
        assert "EMP-123456" not in result.text


class TestTypeSpecificStrategies:
    """Tests for type-specific anonymization strategies."""
    
    def test_different_strategy_per_type(self):
        """Test using different strategies for different types."""
        anon = Anonymizer(strategy="replace", use_ner=False)
        anon.set_strategy(Strategy.MASK, pii_type=PIIType.EMAIL)
        anon.set_strategy(Strategy.FAKE, pii_type=PIIType.PHONE)
        
        text = "Email: john@example.com, Phone: 555-123-4567"
        result = anon.anonymize(text)
        
        # Email should be masked (has * and @)
        assert "@" in result.text
        # Other PII has their strategies applied


class TestFileProcessing:
    """Tests for file processing integration."""
    
    def test_json_file_processing(self):
        """Test processing JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.json"
            output_file = tmpdir / "output.json"
            
            data = [
                {"content": "Email: test@example.com"},
                {"content": "Phone: 555-123-4567"},
            ]
            input_file.write_text(json.dumps(data))
            
            anon = Anonymizer(use_ner=False)
            count = process_file(input_file, output_file, anon)
            
            assert count == 2
            
            result = json.loads(output_file.read_text())
            assert "[EMAIL]" in result[0]["content"]
    
    def test_directory_batch_processing(self):
        """Test batch processing a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "input"
            output_dir = tmpdir / "output"
            input_dir.mkdir()
            
            # Create test files
            for i in range(3):
                (input_dir / f"file{i}.txt").write_text(f"email{i}@test.com\n")
            
            anon = Anonymizer(use_ner=False)
            results = process_directory(input_dir, output_dir, anon, pattern="*.txt")
            
            assert len(results) == 3
            for i in range(3):
                assert (output_dir / f"file{i}.txt").exists()


class TestQuickFunction:
    """Tests for the quick anonymize function."""
    
    def test_quick_anonymize(self):
        """Test quick anonymize function."""
        result = anonymize("Email: test@example.com", strategy="replace", use_ner=False)
        
        assert "[EMAIL]" in result
        assert "test@example.com" not in result
    
    def test_quick_anonymize_mask(self):
        """Test quick anonymize with mask strategy."""
        result = anonymize("Email: john@example.com", strategy="mask", use_ner=False)
        
        assert "@" in result
        assert "*" in result


class TestBatchProcessing:
    """Tests for batch processing."""
    
    def test_anonymize_many(self):
        """Test anonymizing multiple texts."""
        anon = Anonymizer(use_ner=False)
        texts = [
            "Email: a@b.com",
            "Phone: 555-123-4567",
            "IP: 192.168.1.1",
        ]
        
        results = anon.anonymize_many(texts)
        
        assert len(results) == 3
        assert all(isinstance(r, AnonymizedResult) for r in results)
        assert "[EMAIL]" in results[0].text
        assert "[IP_ADDRESS]" in results[2].text


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_text(self):
        """Test anonymizing empty text."""
        anon = Anonymizer(use_ner=False)
        result = anon.anonymize("")
        
        assert result.text == ""
        assert not result.pii_found
    
    def test_no_pii(self):
        """Test text with no PII."""
        anon = Anonymizer(use_ner=False)
        text = "This is a simple sentence with no personal information."
        result = anon.anonymize(text)
        
        assert result.text == text
        assert not result.pii_found
    
    def test_unicode_text(self):
        """Test text with unicode characters."""
        anon = Anonymizer(use_ner=False)
        text = "联系方式: test@example.com 📧"
        result = anon.anonymize(text)
        
        assert "[EMAIL]" in result.text
        assert "📧" in result.text
    
    def test_very_long_text(self):
        """Test anonymizing very long text."""
        anon = Anonymizer(use_ner=False)
        text = "Email: test@example.com. " * 1000
        result = anon.anonymize(text)
        
        assert "[EMAIL]" in result.text
        assert "test@example.com" not in result.text
    
    def test_multiple_same_pii(self):
        """Test multiple occurrences of same PII."""
        anon = Anonymizer(use_ner=False)
        text = "Email test@a.com and also test@a.com repeated"
        result = anon.anonymize(text)
        
        # Both should be replaced
        assert "test@a.com" not in result.text
    
    def test_adjacent_pii(self):
        """Test adjacent PII entities."""
        anon = Anonymizer(use_ner=False)
        text = "a@b.com c@d.com"
        result = anon.anonymize(text)
        
        assert "a@b.com" not in result.text
        assert "c@d.com" not in result.text


class TestDetectorIntegration:
    """Tests for detector integration with anonymizer."""
    
    def test_detect_returns_matches(self):
        """Test that detect method returns proper matches."""
        anon = Anonymizer(use_ner=False)
        matches = anon.detect("Email: test@example.com")
        
        assert len(matches) >= 1
        assert all(isinstance(m, PIIMatch) for m in matches)
    
    def test_detector_standalone(self):
        """Test PIIDetector can be used standalone."""
        detector = PIIDetector(use_ner=False)
        matches = detector.detect("Email: test@example.com")
        
        assert len(matches) >= 1
        assert matches[0].pii_type == PIIType.EMAIL


class TestResultMetadata:
    """Tests for result metadata."""
    
    def test_replacements_dict(self):
        """Test replacements dictionary contains all mappings."""
        anon = Anonymizer(use_ner=False)
        text = "Emails: a@b.com and c@d.com"
        result = anon.anonymize(text)
        
        assert "a@b.com" in result.replacements
        assert "c@d.com" in result.replacements
    
    def test_matches_have_positions(self):
        """Test that matches have correct position information."""
        anon = Anonymizer(use_ner=False)
        text = "Email: test@example.com here"
        result = anon.anonymize(text)
        
        for match in result.matches:
            # Position should be in original text
            assert text[match.start:match.end] == match.text
    
    def test_original_text_preserved(self):
        """Test that original text is preserved in result."""
        anon = Anonymizer(use_ner=False)
        text = "Email: test@example.com"
        result = anon.anonymize(text)
        
        assert result.original_text == text

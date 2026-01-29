"""
Tests for the CLI module.

Tests command-line interface functions.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import patch
from parfum.cli import main, cmd_anonymize, cmd_detect, cmd_quick


class MockArgs:
    """Mock argument object for testing."""
    pass


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestMainFunction:
    """Tests for main CLI entry point."""
    
    def test_main_no_args(self):
        """Test main with no arguments shows help."""
        with patch.object(sys, 'argv', ['parfum']):
            result = main()
            assert result == 0
    
    def test_main_help(self):
        """Test main with --help."""
        with patch.object(sys, 'argv', ['parfum', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestCmdAnonymize:
    """Tests for anonymize command."""
    
    def test_anonymize_file(self, temp_dir):
        """Test anonymizing a single file."""
        input_file = temp_dir / "input.txt"
        output_file = temp_dir / "output.txt"
        
        input_file.write_text("Email: test@example.com\n")
        
        args = MockArgs()
        args.input = str(input_file)
        args.output = str(output_file)
        args.strategy = "replace"
        args.no_ner = True
        args.recursive = False
        args.pattern = "*"
        args.content_key = "content"
        args.locale = "en_US"
        args.seed = None
        args.verbose = False
        
        result = cmd_anonymize(args)
        
        assert result == 0
        assert output_file.exists()
        assert "[EMAIL]" in output_file.read_text()
    
    def test_anonymize_file_mask_strategy(self, temp_dir):
        """Test anonymizing with mask strategy."""
        input_file = temp_dir / "input.txt"
        output_file = temp_dir / "output.txt"
        
        input_file.write_text("Email: john@example.com\n")
        
        args = MockArgs()
        args.input = str(input_file)
        args.output = str(output_file)
        args.strategy = "mask"
        args.no_ner = True
        args.recursive = False
        args.pattern = "*"
        args.content_key = "content"
        args.locale = "en_US"
        args.seed = None
        args.verbose = False
        
        result = cmd_anonymize(args)
        
        assert result == 0
        content = output_file.read_text()
        assert "*" in content
        assert "@" in content
    
    def test_anonymize_directory(self, temp_dir):
        """Test anonymizing a directory."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        
        (input_dir / "file1.txt").write_text("a@b.com\n")
        (input_dir / "file2.txt").write_text("c@d.com\n")
        
        args = MockArgs()
        args.input = str(input_dir)
        args.output = str(output_dir)
        args.strategy = "replace"
        args.no_ner = True
        args.recursive = False
        args.pattern = "*.txt"
        args.content_key = "content"
        args.locale = "en_US"
        args.seed = None
        args.verbose = False
        
        result = cmd_anonymize(args)
        
        assert result == 0
        assert (output_dir / "file1.txt").exists()
        assert (output_dir / "file2.txt").exists()
    
    def test_anonymize_nonexistent_input(self, temp_dir):
        """Test anonymizing non-existent input."""
        args = MockArgs()
        args.input = str(temp_dir / "nonexistent.txt")
        args.output = str(temp_dir / "output.txt")
        args.strategy = "replace"
        args.no_ner = True
        args.verbose = False
        
        result = cmd_anonymize(args)
        
        assert result == 1  # Error


class TestCmdDetect:
    """Tests for detect command."""
    
    def test_detect_text_arg(self):
        """Test detecting PII from text argument."""
        args = MockArgs()
        args.text = "Email: test@example.com"
        args.file = None
        args.no_ner = True
        args.verbose = False
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cmd_detect(args)
            output = mock_stdout.getvalue()
        
        assert result == 0
        assert "EMAIL" in output
    
    def test_detect_from_file(self, temp_dir):
        """Test detecting PII from file."""
        input_file = temp_dir / "input.txt"
        input_file.write_text("Phone: 555-123-4567")
        
        args = MockArgs()
        args.text = None
        args.file = str(input_file)
        args.no_ner = True
        args.verbose = False
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cmd_detect(args)
            output = mock_stdout.getvalue()
        
        assert result == 0
        assert "PHONE" in output
    
    def test_detect_no_pii(self):
        """Test detecting when no PII present."""
        args = MockArgs()
        args.text = "Hello world"
        args.file = None
        args.no_ner = True
        args.verbose = False
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cmd_detect(args)
            output = mock_stdout.getvalue()
        
        assert result == 0
        assert "No PII detected" in output


class TestCmdQuick:
    """Tests for quick anonymize command."""
    
    def test_quick_replace(self):
        """Test quick anonymization with replace."""
        args = MockArgs()
        args.text = "Email: test@example.com"
        args.strategy = "replace"
        args.no_ner = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cmd_quick(args)
            output = mock_stdout.getvalue()
        
        assert result == 0
        assert "[EMAIL]" in output
    
    def test_quick_mask(self):
        """Test quick anonymization with mask."""
        args = MockArgs()
        args.text = "Email: john@example.com"
        args.strategy = "mask"
        args.no_ner = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cmd_quick(args)
            output = mock_stdout.getvalue()
        
        assert result == 0
        assert "*" in output
        assert "@" in output
    
    def test_quick_hash(self):
        """Test quick anonymization with hash."""
        args = MockArgs()
        args.text = "Email: test@example.com"
        args.strategy = "hash"
        args.no_ner = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cmd_quick(args)
            output = mock_stdout.getvalue()
        
        assert result == 0
        # Hash is 16 hex characters
        assert "test@example.com" not in output
    
    def test_quick_no_pii(self):
        """Test quick anonymization with no PII."""
        args = MockArgs()
        args.text = "Hello world"
        args.strategy = "replace"
        args.no_ner = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cmd_quick(args)
            output = mock_stdout.getvalue()
        
        assert result == 0
        assert "Hello world" in output

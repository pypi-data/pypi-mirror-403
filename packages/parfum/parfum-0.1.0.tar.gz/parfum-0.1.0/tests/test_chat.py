"""
Tests for the chat module.

Tests file processing functions for JSON, JSONL, CSV, and text files.
"""

import pytest
import json
import csv
import tempfile
from pathlib import Path
from parfum.chat import (
    process_json,
    process_jsonl,
    process_csv,
    process_text,
    process_file,
    process_directory,
)
from parfum.anonymizer import Anonymizer


@pytest.fixture
def anonymizer():
    """Create a test anonymizer."""
    return Anonymizer(strategy="replace", use_ner=False)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestProcessJsonl:
    """Tests for process_jsonl function."""
    
    def test_process_jsonl_single_line(self, anonymizer, temp_dir):
        """Test processing JSONL with single line."""
        input_file = temp_dir / "input.jsonl"
        output_file = temp_dir / "output.jsonl"
        
        input_file.write_text('{"content": "Email: test@example.com"}\n')
        
        count = process_jsonl(input_file, output_file, anonymizer)
        
        assert count == 1
        result = json.loads(output_file.read_text().strip())
        assert "[EMAIL]" in result["content"]
    
    def test_process_jsonl_multiple_lines(self, anonymizer, temp_dir):
        """Test processing JSONL with multiple lines."""
        input_file = temp_dir / "input.jsonl"
        output_file = temp_dir / "output.jsonl"
        
        lines = [
            '{"content": "Email: a@b.com"}\n',
            '{"content": "Phone: 555-123-4567"}\n',
            '{"content": "IP: 192.168.1.1"}\n',
        ]
        input_file.write_text("".join(lines))
        
        count = process_jsonl(input_file, output_file, anonymizer)
        
        assert count == 3
    
    def test_process_jsonl_with_messages(self, anonymizer, temp_dir):
        """Test processing JSONL with messages format."""
        input_file = temp_dir / "input.jsonl"
        output_file = temp_dir / "output.jsonl"
        
        data = {
            "messages": [
                {"role": "user", "content": "My email is test@example.com"},
                {"role": "assistant", "content": "Got it!"}
            ]
        }
        input_file.write_text(json.dumps(data) + "\n")
        
        count = process_jsonl(input_file, output_file, anonymizer)
        
        assert count == 1
        result = json.loads(output_file.read_text().strip())
        assert "[EMAIL]" in result["messages"][0]["content"]
    
    def test_process_jsonl_empty_lines(self, anonymizer, temp_dir):
        """Test processing JSONL with empty lines."""
        input_file = temp_dir / "input.jsonl"
        output_file = temp_dir / "output.jsonl"
        
        input_file.write_text('{"content": "test@a.com"}\n\n{"content": "b@c.com"}\n')
        
        count = process_jsonl(input_file, output_file, anonymizer)
        
        assert count == 2


class TestProcessJson:
    """Tests for process_json function."""
    
    def test_process_json_array(self, anonymizer, temp_dir):
        """Test processing JSON array."""
        input_file = temp_dir / "input.json"
        output_file = temp_dir / "output.json"
        
        data = [
            {"content": "Email: a@b.com"},
            {"content": "Phone: 555-123-4567"},
        ]
        input_file.write_text(json.dumps(data))
        
        count = process_json(input_file, output_file, anonymizer)
        
        assert count == 2
        result = json.loads(output_file.read_text())
        assert "[EMAIL]" in result[0]["content"]
    
    def test_process_json_conversation(self, anonymizer, temp_dir):
        """Test processing JSON with conversation format."""
        input_file = temp_dir / "input.json"
        output_file = temp_dir / "output.json"
        
        data = {
            "messages": [
                {"role": "user", "content": "test@example.com"},
            ]
        }
        input_file.write_text(json.dumps(data))
        
        count = process_json(input_file, output_file, anonymizer)
        
        assert count == 1
        result = json.loads(output_file.read_text())
        assert "[EMAIL]" in result["messages"][0]["content"]
    
    def test_process_json_custom_key(self, anonymizer, temp_dir):
        """Test processing JSON with custom content key."""
        input_file = temp_dir / "input.json"
        output_file = temp_dir / "output.json"
        
        data = [{"text": "Email: a@b.com"}]
        input_file.write_text(json.dumps(data))
        
        count = process_json(input_file, output_file, anonymizer, content_key="text")
        
        assert count == 1
        result = json.loads(output_file.read_text())
        assert "[EMAIL]" in result[0]["text"]


class TestProcessCsv:
    """Tests for process_csv function."""
    
    def test_process_csv_all_columns(self, anonymizer, temp_dir):
        """Test processing all CSV columns."""
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "email", "phone"])
            writer.writeheader()
            writer.writerow({"id": "1", "email": "a@b.com", "phone": "555-123-4567"})
        
        count = process_csv(input_file, output_file, anonymizer)
        
        assert count == 1
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert "[EMAIL]" in row["email"]
    
    def test_process_csv_specific_columns(self, anonymizer, temp_dir):
        """Test processing specific CSV columns."""
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "email", "phone"])
            writer.writeheader()
            writer.writerow({"id": "1", "email": "a@b.com", "phone": "555-123-4567"})
        
        count = process_csv(input_file, output_file, anonymizer, text_columns=["email"])
        
        assert count == 1
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert "[EMAIL]" in row["email"]
            # Phone not in text_columns, but may still be processed
    
    def test_process_csv_multiple_rows(self, anonymizer, temp_dir):
        """Test processing multiple CSV rows."""
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["email"])
            writer.writeheader()
            writer.writerow({"email": "a@b.com"})
            writer.writerow({"email": "c@d.com"})
            writer.writerow({"email": "e@f.com"})
        
        count = process_csv(input_file, output_file, anonymizer)
        
        assert count == 3


class TestProcessText:
    """Tests for process_text function."""
    
    def test_process_text_single_line(self, anonymizer, temp_dir):
        """Test processing single line text."""
        input_file = temp_dir / "input.txt"
        output_file = temp_dir / "output.txt"
        
        input_file.write_text("Email: test@example.com\n")
        
        count = process_text(input_file, output_file, anonymizer)
        
        assert count == 1
        assert "[EMAIL]" in output_file.read_text()
    
    def test_process_text_multiple_lines(self, anonymizer, temp_dir):
        """Test processing multiple lines."""
        input_file = temp_dir / "input.txt"
        output_file = temp_dir / "output.txt"
        
        input_file.write_text("Line 1: a@b.com\nLine 2: 555-123-4567\nLine 3: 192.168.1.1\n")
        
        count = process_text(input_file, output_file, anonymizer)
        
        assert count == 3


class TestProcessFile:
    """Tests for process_file function (auto-detect format)."""
    
    def test_process_file_json(self, anonymizer, temp_dir):
        """Test auto-detecting JSON file."""
        input_file = temp_dir / "data.json"
        output_file = temp_dir / "output.json"
        
        data = [{"content": "test@example.com"}]
        input_file.write_text(json.dumps(data))
        
        count = process_file(input_file, output_file, anonymizer)
        
        assert count == 1
    
    def test_process_file_jsonl(self, anonymizer, temp_dir):
        """Test auto-detecting JSONL file."""
        input_file = temp_dir / "data.jsonl"
        output_file = temp_dir / "output.jsonl"
        
        input_file.write_text('{"content": "test@example.com"}\n')
        
        count = process_file(input_file, output_file, anonymizer)
        
        assert count == 1
    
    def test_process_file_csv(self, anonymizer, temp_dir):
        """Test auto-detecting CSV file."""
        input_file = temp_dir / "data.csv"
        output_file = temp_dir / "output.csv"
        
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["email"])
            writer.writeheader()
            writer.writerow({"email": "test@example.com"})
        
        count = process_file(input_file, output_file, anonymizer)
        
        assert count == 1
    
    def test_process_file_txt(self, anonymizer, temp_dir):
        """Test auto-detecting text file."""
        input_file = temp_dir / "data.txt"
        output_file = temp_dir / "output.txt"
        
        input_file.write_text("test@example.com\n")
        
        count = process_file(input_file, output_file, anonymizer)
        
        assert count == 1


class TestProcessDirectory:
    """Tests for process_directory function."""
    
    def test_process_directory_single_file(self, anonymizer, temp_dir):
        """Test processing directory with single file."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        
        (input_dir / "data.txt").write_text("test@example.com\n")
        
        results = process_directory(input_dir, output_dir, anonymizer, pattern="*.txt")
        
        assert len(results) == 1
        assert (output_dir / "data.txt").exists()
    
    def test_process_directory_multiple_files(self, anonymizer, temp_dir):
        """Test processing directory with multiple files."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        
        (input_dir / "data1.txt").write_text("a@b.com\n")
        (input_dir / "data2.txt").write_text("c@d.com\n")
        
        results = process_directory(input_dir, output_dir, anonymizer, pattern="*.txt")
        
        assert len(results) == 2
    
    def test_process_directory_recursive(self, anonymizer, temp_dir):
        """Test recursive directory processing."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        subdir = input_dir / "subdir"
        input_dir.mkdir()
        subdir.mkdir()
        
        (input_dir / "data1.txt").write_text("a@b.com\n")
        (subdir / "data2.txt").write_text("c@d.com\n")
        
        results = process_directory(
            input_dir, output_dir, anonymizer, 
            pattern="*.txt", recursive=True
        )
        
        assert len(results) == 2
        assert (output_dir / "subdir" / "data2.txt").exists()
    
    def test_process_directory_pattern_filter(self, anonymizer, temp_dir):
        """Test directory processing with pattern filter."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        
        (input_dir / "data.txt").write_text("a@b.com\n")
        (input_dir / "data.json").write_text('{"content": "c@d.com"}')
        
        results = process_directory(input_dir, output_dir, anonymizer, pattern="*.txt")
        
        assert len(results) == 1
        assert (output_dir / "data.txt").exists()
        assert not (output_dir / "data.json").exists()

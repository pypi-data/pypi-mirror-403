"""
Parfum - Chat Data Processing.

Handles various chat data formats including JSON, CSV, and plain text.
"""

import json
import csv
from pathlib import Path
from typing import Union, Iterator, Optional
import logging

from .anonymizer import Anonymizer


logger = logging.getLogger(__name__)


def process_jsonl(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    anonymizer: Anonymizer,
    content_key: str = "content",
) -> int:
    """
    Process a JSONL file (one JSON object per line).
    
    Args:
        input_path: Path to input JSONL file
        output_path: Path to output file
        anonymizer: Anonymizer instance
        content_key: Key containing text content
        
    Returns:
        Number of lines processed
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    count = 0
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            line = line.strip()
            if not line:
                continue
            
            try:
                obj = json.loads(line)
                
                # Handle conversation format
                if "messages" in obj:
                    obj["messages"] = anonymizer.anonymize_chat(
                        obj["messages"], 
                        content_key=content_key
                    )
                elif content_key in obj:
                    result = anonymizer.anonymize(obj[content_key])
                    obj[content_key] = result.text
                
                outfile.write(json.dumps(obj) + "\n")
                count += 1
                
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON line: {e}")
                continue
    
    return count


def process_json(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    anonymizer: Anonymizer,
    content_key: str = "content",
) -> int:
    """
    Process a JSON file (array of objects or conversations).
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output file
        anonymizer: Anonymizer instance
        content_key: Key containing text content
        
    Returns:
        Number of items processed
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count = 0
    
    if isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                if "messages" in item:
                    data[i]["messages"] = anonymizer.anonymize_chat(
                        item["messages"],
                        content_key=content_key
                    )
                elif content_key in item:
                    result = anonymizer.anonymize(item[content_key])
                    data[i][content_key] = result.text
                count += 1
    elif isinstance(data, dict):
        if "messages" in data:
            data["messages"] = anonymizer.anonymize_chat(
                data["messages"],
                content_key=content_key
            )
            count = len(data["messages"])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return count


def process_csv(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    anonymizer: Anonymizer,
    text_columns: Optional[list[str]] = None,
) -> int:
    """
    Process a CSV file.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output file
        anonymizer: Anonymizer instance
        text_columns: Columns to anonymize (if None, anonymize all)
        
    Returns:
        Number of rows processed
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    count = 0
    
    with open(input_path, 'r', encoding='utf-8', newline='') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        
        columns_to_process = text_columns or fieldnames
        
        with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                for col in columns_to_process:
                    if col in row and row[col]:
                        result = anonymizer.anonymize(row[col])
                        row[col] = result.text
                
                writer.writerow(row)
                count += 1
    
    return count


def process_text(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    anonymizer: Anonymizer,
) -> int:
    """
    Process a plain text file line by line.
    
    Args:
        input_path: Path to input text file
        output_path: Path to output file
        anonymizer: Anonymizer instance
        
    Returns:
        Number of lines processed
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    count = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            result = anonymizer.anonymize(line)
            outfile.write(result.text)
            count += 1
    
    return count


def process_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    anonymizer: Anonymizer,
    content_key: str = "content",
    text_columns: Optional[list[str]] = None,
) -> int:
    """
    Process a file, automatically detecting format by extension.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
        anonymizer: Anonymizer instance
        content_key: Key for JSON content
        text_columns: Columns for CSV files
        
    Returns:
        Number of items processed
    """
    input_path = Path(input_path)
    suffix = input_path.suffix.lower()
    
    if suffix == '.jsonl':
        return process_jsonl(input_path, output_path, anonymizer, content_key)
    elif suffix == '.json':
        return process_json(input_path, output_path, anonymizer, content_key)
    elif suffix == '.csv':
        return process_csv(input_path, output_path, anonymizer, text_columns)
    else:
        # Treat as plain text
        return process_text(input_path, output_path, anonymizer)


def process_directory(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    anonymizer: Anonymizer,
    pattern: str = "*",
    recursive: bool = False,
    content_key: str = "content",
) -> dict[str, int]:
    """
    Process all matching files in a directory.
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        anonymizer: Anonymizer instance
        pattern: Glob pattern for files
        recursive: Whether to search recursively
        content_key: Key for JSON content
        
    Returns:
        Dictionary mapping file paths to items processed
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    glob_method = input_dir.rglob if recursive else input_dir.glob
    
    for input_file in glob_method(pattern):
        if input_file.is_file():
            # Preserve directory structure
            relative = input_file.relative_to(input_dir)
            output_file = output_dir / relative
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                count = process_file(
                    input_file, 
                    output_file, 
                    anonymizer,
                    content_key=content_key,
                )
                results[str(input_file)] = count
                logger.info(f"Processed {input_file}: {count} items")
            except Exception as e:
                logger.error(f"Error processing {input_file}: {e}")
                results[str(input_file)] = -1
    
    return results

"""
Parfum - Command Line Interface.

Provides CLI commands for anonymizing files and directories.
"""

import argparse
import sys
import logging
from pathlib import Path

from .anonymizer import Anonymizer
from .strategies import Strategy
from .chat import process_file, process_directory


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="parfum",
        description="Anonymize PII in text and chat data for LLM training",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Anonymize command
    anon_parser = subparsers.add_parser(
        "anonymize",
        help="Anonymize a file or directory",
    )
    anon_parser.add_argument(
        "input",
        help="Input file or directory path",
    )
    anon_parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output file or directory path",
    )
    anon_parser.add_argument(
        "-s", "--strategy",
        choices=["replace", "mask", "hash", "fake", "redact"],
        default="replace",
        help="Anonymization strategy (default: replace)",
    )
    anon_parser.add_argument(
        "--no-ner",
        action="store_true",
        help="Disable NER-based detection (names, locations)",
    )
    anon_parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process directories recursively",
    )
    anon_parser.add_argument(
        "-p", "--pattern",
        default="*",
        help="Glob pattern for files (default: *)",
    )
    anon_parser.add_argument(
        "--content-key",
        default="content",
        help="JSON key containing text content (default: content)",
    )
    anon_parser.add_argument(
        "--locale",
        default="en_US",
        help="Locale for fake data generation (default: en_US)",
    )
    anon_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible fake data",
    )
    anon_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    
    # Detect command
    detect_parser = subparsers.add_parser(
        "detect",
        help="Detect PII in text (without anonymizing)",
    )
    detect_parser.add_argument(
        "text",
        nargs="?",
        help="Text to scan (or use --file)",
    )
    detect_parser.add_argument(
        "-f", "--file",
        help="File to scan",
    )
    detect_parser.add_argument(
        "--no-ner",
        action="store_true",
        help="Disable NER-based detection",
    )
    detect_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    
    # Quick anonymize command
    quick_parser = subparsers.add_parser(
        "quick",
        help="Quick anonymize from command line",
    )
    quick_parser.add_argument(
        "text",
        help="Text to anonymize",
    )
    quick_parser.add_argument(
        "-s", "--strategy",
        choices=["replace", "mask", "hash", "fake", "redact"],
        default="replace",
        help="Anonymization strategy (default: replace)",
    )
    quick_parser.add_argument(
        "--no-ner",
        action="store_true",
        help="Disable NER-based detection",
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == "anonymize":
        return cmd_anonymize(args)
    elif args.command == "detect":
        return cmd_detect(args)
    elif args.command == "quick":
        return cmd_quick(args)
    
    return 0


def cmd_anonymize(args) -> int:
    """Handle anonymize command."""
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1
    
    # Create anonymizer
    anonymizer = Anonymizer(
        strategy=args.strategy,
        use_ner=not args.no_ner,
        locale=args.locale,
        seed=args.seed,
    )
    
    if input_path.is_file():
        # Process single file
        logger.info(f"Processing file: {input_path}")
        count = process_file(
            input_path,
            output_path,
            anonymizer,
            content_key=args.content_key,
        )
        logger.info(f"Processed {count} items -> {output_path}")
        
    elif input_path.is_dir():
        # Process directory
        logger.info(f"Processing directory: {input_path}")
        results = process_directory(
            input_path,
            output_path,
            anonymizer,
            pattern=args.pattern,
            recursive=args.recursive,
            content_key=args.content_key,
        )
        
        total = sum(v for v in results.values() if v > 0)
        files = len([v for v in results.values() if v > 0])
        logger.info(f"Processed {total} items in {files} files -> {output_path}")
    
    return 0


def cmd_detect(args) -> int:
    """Handle detect command."""
    setup_logging(args.verbose)
    
    # Get text to scan
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        # Read from stdin
        text = sys.stdin.read()
    
    anonymizer = Anonymizer(use_ner=not args.no_ner)
    matches = anonymizer.detect(text)
    
    if not matches:
        print("No PII detected.")
        return 0
    
    print(f"Found {len(matches)} PII entities:\n")
    for match in matches:
        print(f"  [{match.pii_type.value}] \"{match.text}\" (pos {match.start}-{match.end})")
    
    return 0


def cmd_quick(args) -> int:
    """Handle quick anonymize command."""
    anonymizer = Anonymizer(
        strategy=args.strategy,
        use_ner=not args.no_ner,
    )
    
    result = anonymizer.anonymize(args.text)
    print(result.text)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

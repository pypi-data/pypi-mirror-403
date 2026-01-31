#!/usr/bin/env python3
"""
JSON Validator CLI
A simple command-line tool to validate JSON files against schemas.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional


def load_json_file(filepath: str) -> Optional[Dict[Any, Any]]:
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filepath}': {e}", file=sys.stderr)
        return None


def validate_json_syntax(filepath: str) -> bool:
    """Validate JSON file syntax."""
    data = load_json_file(filepath)
    if data is None:
        return False
    print(f"✓ '{filepath}' is valid JSON")
    return True


def validate_json_schema(filepath: str, schema_path: str) -> bool:
    """Validate JSON file against a JSON schema."""
    try:
        from jsonschema import validate, ValidationError
    except ImportError:
        print("Error: jsonschema package is required for schema validation.", file=sys.stderr)
        print("Install it with: pip install jsonschema", file=sys.stderr)
        return False
    
    data = load_json_file(filepath)
    schema = load_json_file(schema_path)
    
    if data is None or schema is None:
        return False
    
    try:
        validate(instance=data, schema=schema)
        print(f"✓ '{filepath}' is valid according to schema '{schema_path}'")
        return True
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}", file=sys.stderr)
        return False


def pretty_print_json(filepath: str, indent: int = 2) -> bool:
    """Pretty print a JSON file."""
    data = load_json_file(filepath)
    if data is None:
        return False
    
    print(json.dumps(data, indent=indent, ensure_ascii=False))
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="JSON Validator CLI - Validate and format JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jsonvalidator validate data.json
  jsonvalidator validate data.json --schema schema.json
  jsonvalidator format data.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate JSON file')
    validate_parser.add_argument('file', help='JSON file to validate')
    validate_parser.add_argument('--schema', '-s', help='JSON schema file for validation')
    
    # Format command
    format_parser = subparsers.add_parser('format', help='Pretty print JSON file')
    format_parser.add_argument('file', help='JSON file to format')
    format_parser.add_argument('--indent', '-i', type=int, default=2, help='Indentation spaces (default: 2)')
    
    # Version command
    subparsers.add_parser('version', help='Show version')
    
    args = parser.parse_args()
    
    if args.command == 'validate':
        if args.schema:
            success = validate_json_schema(args.file, args.schema)
        else:
            success = validate_json_syntax(args.file)
        sys.exit(0 if success else 1)
    
    elif args.command == 'format':
        success = pretty_print_json(args.file, args.indent)
        sys.exit(0 if success else 1)
    
    elif args.command == 'version':
        from jsonvalidator import __version__
        print(f"jsonvalidator {__version__}")
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

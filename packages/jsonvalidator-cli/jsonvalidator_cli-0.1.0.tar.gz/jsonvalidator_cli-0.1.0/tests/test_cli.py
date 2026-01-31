"""Tests for JSON Validator CLI."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from jsonvalidator.cli import (
    load_json_file,
    validate_json_syntax,
    validate_json_schema,
    pretty_print_json,
)


@pytest.fixture
def valid_json_file():
    """Create a temporary valid JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"name": "test", "value": 42}, f)
        filepath = f.name
    yield filepath
    os.unlink(filepath)


@pytest.fixture
def invalid_json_file():
    """Create a temporary invalid JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write('{"name": "test", invalid}')
        filepath = f.name
    yield filepath
    os.unlink(filepath)


@pytest.fixture
def json_schema_file():
    """Create a temporary JSON schema file."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"}
        },
        "required": ["name"]
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(schema, f)
        filepath = f.name
    yield filepath
    os.unlink(filepath)


class TestLoadJsonFile:
    """Test load_json_file function."""
    
    def test_load_valid_json(self, valid_json_file):
        """Test loading a valid JSON file."""
        data = load_json_file(valid_json_file)
        assert data is not None
        assert data["name"] == "test"
        assert data["value"] == 42
    
    def test_load_invalid_json(self, invalid_json_file):
        """Test loading an invalid JSON file."""
        data = load_json_file(invalid_json_file)
        assert data is None
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        data = load_json_file("nonexistent_file.json")
        assert data is None


class TestValidateJsonSyntax:
    """Test validate_json_syntax function."""
    
    def test_validate_valid_json(self, valid_json_file):
        """Test validating a valid JSON file."""
        result = validate_json_syntax(valid_json_file)
        assert result is True
    
    def test_validate_invalid_json(self, invalid_json_file):
        """Test validating an invalid JSON file."""
        result = validate_json_syntax(invalid_json_file)
        assert result is False


class TestValidateJsonSchema:
    """Test validate_json_schema function."""
    
    def test_validate_with_schema_success(self, valid_json_file, json_schema_file):
        """Test validating a JSON file against a schema (should pass)."""
        result = validate_json_schema(valid_json_file, json_schema_file)
        assert result is True
    
    def test_validate_with_schema_failure(self, json_schema_file):
        """Test validating a JSON file that doesn't match schema."""
        # Create a file that violates the schema
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({"value": "not an integer"}, f)  # Missing required 'name' field
            filepath = f.name
        
        try:
            result = validate_json_schema(filepath, json_schema_file)
            assert result is False
        finally:
            os.unlink(filepath)


class TestPrettyPrintJson:
    """Test pretty_print_json function."""
    
    def test_pretty_print_valid_json(self, valid_json_file, capsys):
        """Test pretty printing a valid JSON file."""
        result = pretty_print_json(valid_json_file, indent=2)
        assert result is True
        
        captured = capsys.readouterr()
        # Check that output is formatted JSON
        assert '"name"' in captured.out
        assert '"test"' in captured.out
    
    def test_pretty_print_invalid_json(self, invalid_json_file):
        """Test pretty printing an invalid JSON file."""
        result = pretty_print_json(invalid_json_file)
        assert result is False


class TestCLIIntegration:
    """Integration tests for the CLI."""
    
    def test_version_display(self):
        """Test that version can be imported."""
        from jsonvalidator import __version__
        assert __version__ == "0.1.0"

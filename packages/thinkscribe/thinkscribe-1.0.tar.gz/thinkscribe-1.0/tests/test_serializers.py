"""Tests for data serialization utilities."""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thinkscribe.serializers import serialize_data


class TestSerializeData:
    """Test suite for serialize_data function."""

    def test_serialize_string_returns_as_is(self):
        """Test that string input returns unchanged."""
        input_str = "hello world"
        result = serialize_data(input_str)
        assert result == input_str
        assert isinstance(result, str)

    def test_serialize_empty_string(self):
        """Test that empty string is handled correctly."""
        result = serialize_data("")
        assert result == ""

    def test_serialize_multiline_string(self):
        """Test that multiline strings are preserved."""
        input_str = "line 1\nline 2\nline 3"
        result = serialize_data(input_str)
        assert result == input_str

    def test_serialize_simple_dict(self):
        """Test that dictionary converts to JSON."""
        data = {"key": "value", "number": 42}
        result = serialize_data(data)

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == data
        assert "key" in result
        assert "value" in result

    def test_serialize_nested_dict(self):
        """Test that nested dictionaries are handled correctly."""
        data = {
            "outer": {
                "inner": {
                    "deep": "value"
                }
            },
            "list": [1, 2, 3]
        }
        result = serialize_data(data)

        parsed = json.loads(result)
        assert parsed == data
        assert parsed["outer"]["inner"]["deep"] == "value"

    def test_serialize_simple_list(self):
        """Test that list converts to JSON."""
        data = [1, 2, 3, "four", 5.5]
        result = serialize_data(data)

        parsed = json.loads(result)
        assert parsed == data

    def test_serialize_empty_list(self):
        """Test that empty list is handled."""
        result = serialize_data([])
        parsed = json.loads(result)
        assert parsed == []

    def test_serialize_empty_dict(self):
        """Test that empty dict is handled."""
        result = serialize_data({})
        parsed = json.loads(result)
        assert parsed == {}

    def test_serialize_list_of_dicts(self):
        """Test that complex nested structures work."""
        data = [
            {"name": "Alice", "score": 85},
            {"name": "Bob", "score": 92},
            {"name": "Charlie", "score": 78}
        ]
        result = serialize_data(data)

        parsed = json.loads(result)
        assert parsed == data
        assert len(parsed) == 3

    def test_serialize_with_datetime_uses_fallback(self):
        """Test that non-JSON types use str() fallback."""
        now = datetime.now()
        data = {"timestamp": now, "value": 123}
        result = serialize_data(data)

        # Should not raise, uses default=str
        parsed = json.loads(result)
        assert parsed["value"] == 123
        assert isinstance(parsed["timestamp"], str)

    def test_serialize_integer(self):
        """Test that plain integer converts to string."""
        result = serialize_data(42)
        assert result == "42"

    def test_serialize_float(self):
        """Test that float converts to string."""
        result = serialize_data(3.14159)
        assert result == "3.14159"

    def test_serialize_boolean(self):
        """Test that boolean converts to string."""
        assert serialize_data(True) == "True"
        assert serialize_data(False) == "False"

    def test_serialize_none(self):
        """Test that None converts to string."""
        result = serialize_data(None)
        assert result == "None"

    def test_serialize_with_unicode(self):
        """Test that Unicode characters are preserved."""
        data = {"message": "Hello 世界 🌍"}
        result = serialize_data(data)

        parsed = json.loads(result)
        assert parsed["message"] == "Hello 世界 🌍"

    def test_serialize_numeric_dict_keys(self):
        """Test that numeric keys in dict are handled."""
        data = {1: "one", 2: "two", 3: "three"}
        result = serialize_data(data)

        # JSON converts numeric keys to strings
        parsed = json.loads(result)
        assert parsed["1"] == "one"

    def test_serialize_mixed_types_list(self):
        """Test list with mixed types."""
        data = [1, "string", 3.14, True, None, {"key": "value"}]
        result = serialize_data(data)

        parsed = json.loads(result)
        assert len(parsed) == 6
        assert parsed[0] == 1
        assert parsed[1] == "string"
        assert parsed[5] == {"key": "value"}

    def test_serialize_indentation(self):
        """Test that JSON output is indented for readability."""
        data = {"a": 1, "b": 2}
        result = serialize_data(data)

        # Should contain newlines (indented)
        assert "\n" in result
        assert "  " in result  # 2-space indent

    def test_serialize_custom_object_with_str(self):
        """Test that custom objects use str() representation."""
        class CustomObj:
            def __str__(self):
                return "CustomObject(42)"

        obj = CustomObj()
        result = serialize_data(obj)
        assert "CustomObject(42)" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_serialize_very_long_string(self):
        """Test that very long strings are handled."""
        long_string = "x" * 10000
        result = serialize_data(long_string)
        assert result == long_string
        assert len(result) == 10000

    def test_serialize_deeply_nested_structure(self):
        """Test deeply nested data structure."""
        data = {"level1": {"level2": {"level3": {"level4": "deep value"}}}}
        result = serialize_data(data)

        parsed = json.loads(result)
        assert parsed["level1"]["level2"]["level3"]["level4"] == "deep value"

    def test_serialize_special_json_characters(self):
        """Test that special JSON characters are escaped."""
        data = {"quote": 'He said "hello"', "backslash": "path\\to\\file"}
        result = serialize_data(data)

        parsed = json.loads(result)
        assert parsed["quote"] == 'He said "hello"'
        assert parsed["backslash"] == "path\\to\\file"

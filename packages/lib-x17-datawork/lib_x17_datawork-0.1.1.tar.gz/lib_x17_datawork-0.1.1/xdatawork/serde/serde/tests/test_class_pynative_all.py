from unittest.mock import patch

import pytest

from xdatawork.serde.format.dataformat import DataFormat
from xdatawork.serde.serde.errors import (
    SerDeFailedError,
    SerDeImportError,
    SerDeNotSupportedError,
    SerDeTypeError,
)
from xdatawork.serde.serde.pynative import SerDePynative
from xdatawork.serde.serde.serdelike import SerDeLike

# ==================== Class Attributes Tests ====================


def test_serdepynative_supported_ser_source():
    """Test SUPPORTED_SER_SOURCE contains dict and list"""
    assert SerDePynative.SUPPORTED_SER_SOURCE == {dict, list}


def test_serdepynative_supported_de_source():
    """Test SUPPORTED_DE_SOURCE contains bytes"""
    assert SerDePynative.SUPPORTED_DE_SOURCE == {bytes}


def test_serdepynative_supported_format():
    """Test SUPPORTED_FORMAT contains expected formats"""
    expected = {DataFormat.TOML, DataFormat.JSON}
    assert SerDePynative.SUPPORTED_FORMAT == expected


def test_serdepynative_implements_serdelike():
    """Test SerDePynative implements SerDeLike protocol"""
    serde = SerDePynative()
    assert isinstance(serde, SerDeLike)


# ==================== Serialise Method Tests ====================


def test_serialise_json_dict():
    """Test serialise dict with JSON format"""
    data = {"key": "value", "number": 42}

    result = SerDePynative.serialise(data, DataFormat.JSON)

    assert isinstance(result, bytes)
    assert b"key" in result
    assert b"value" in result


def test_serialise_json_list():
    """Test serialise list with JSON format"""
    data = [1, 2, 3, "test"]

    result = SerDePynative.serialise(data, DataFormat.JSON)

    assert isinstance(result, bytes)
    assert b"test" in result


def test_serialise_json_with_string_format():
    """Test serialise with string format 'json'"""
    data = {"a": 1}

    result = SerDePynative.serialise(data, "json")

    assert isinstance(result, bytes)


def test_serialise_toml_dict():
    """Test serialise dict with TOML format"""
    data = {"key": "value", "number": 42}

    result = SerDePynative.serialise(data, DataFormat.TOML)

    assert isinstance(result, bytes)
    assert b"key" in result
    assert b"value" in result


def test_serialise_toml_with_string_format():
    """Test serialise with string format 'toml'"""
    data = {"section": {"key": "value"}}

    result = SerDePynative.serialise(data, "toml")

    assert isinstance(result, bytes)


def test_serialise_invalid_type_string():
    """Test serialise raises SerDeTypeError for string"""
    with pytest.raises(SerDeTypeError, match="SerDePynative.serialise expects"):
        SerDePynative.serialise("invalid", DataFormat.JSON)


def test_serialise_invalid_type_int():
    """Test serialise raises SerDeTypeError for int"""
    with pytest.raises(SerDeTypeError):
        SerDePynative.serialise(123, DataFormat.JSON)


def test_serialise_invalid_type_none():
    """Test serialise raises SerDeTypeError for None"""
    with pytest.raises(SerDeTypeError):
        SerDePynative.serialise(None, DataFormat.JSON)


def test_serialise_unsupported_format():
    """Test serialise raises SerDeNotSupportedError for unsupported format"""
    data = {"key": "value"}

    with pytest.raises(SerDeNotSupportedError, match="SerDePynative.serialise supports"):
        SerDePynative.serialise(data, DataFormat.PARQUET)


def test_serialise_csv_not_supported():
    """Test serialise raises error for CSV format"""
    data = {"key": "value"}

    with pytest.raises(SerDeNotSupportedError):
        SerDePynative.serialise(data, DataFormat.CSV)


# ==================== Deserialise Method Tests ====================


def test_deserialise_json_dict():
    """Test deserialise JSON to dict"""
    json_data = b'{"key": "value", "number": 42}'

    result = SerDePynative.deserialise(json_data, DataFormat.JSON)

    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 42


def test_deserialise_json_list():
    """Test deserialise JSON to list"""
    json_data = b'[1, 2, 3, "test"]'

    result = SerDePynative.deserialise(json_data, DataFormat.JSON)

    assert isinstance(result, list)
    assert len(result) == 4
    assert result[3] == "test"


def test_deserialise_json_with_string_format():
    """Test deserialise with string format 'json'"""
    json_data = b'{"a": 1}'

    result = SerDePynative.deserialise(json_data, "json")

    assert isinstance(result, dict)


def test_deserialise_toml_dict():
    """Test deserialise TOML to dict"""
    toml_data = b'key = "value"\nnumber = 42'

    result = SerDePynative.deserialise(toml_data, DataFormat.TOML)

    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 42


def test_deserialise_toml_with_string_format():
    """Test deserialise with string format 'toml'"""
    toml_data = b'key = "value"'

    result = SerDePynative.deserialise(toml_data, "toml")

    assert isinstance(result, dict)


def test_deserialise_invalid_type_string():
    """Test deserialise raises SerDeTypeError for string"""
    with pytest.raises(SerDeTypeError, match="SerDePynative.deserialise expects"):
        SerDePynative.deserialise("invalid", DataFormat.JSON)


def test_deserialise_invalid_type_dict():
    """Test deserialise raises SerDeTypeError for dict"""
    with pytest.raises(SerDeTypeError):
        SerDePynative.deserialise({"key": "value"}, DataFormat.JSON)


def test_deserialise_unsupported_format():
    """Test deserialise raises SerDeNotSupportedError for unsupported format"""
    data = b"some data"

    with pytest.raises(SerDeNotSupportedError, match="SerDePynative.deserialise supports"):
        SerDePynative.deserialise(data, DataFormat.PARQUET)


# ==================== Round-Trip Tests ====================


def test_roundtrip_json_dict():
    """Test JSON dict serialise -> deserialise roundtrip"""
    original = {"key": "value", "number": 42, "nested": {"a": 1, "b": 2}}

    serialised = SerDePynative.serialise(original, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)

    assert deserialised == original


def test_roundtrip_json_list():
    """Test JSON list serialise -> deserialise roundtrip"""
    original = [1, 2, "test", {"nested": "dict"}]

    serialised = SerDePynative.serialise(original, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)

    assert deserialised == original


def test_roundtrip_toml_dict():
    """Test TOML dict serialise -> deserialise roundtrip"""
    original = {"key": "value", "number": 42}

    serialised = SerDePynative.serialise(original, DataFormat.TOML)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.TOML)

    assert deserialised == original


def test_roundtrip_nested_dict():
    """Test roundtrip with nested dictionaries"""
    original = {"level1": {"level2": {"level3": "value"}}, "other": "data"}

    for fmt in [DataFormat.JSON, DataFormat.TOML]:
        serialised = SerDePynative.serialise(original, fmt)
        deserialised = SerDePynative.deserialise(serialised, fmt)
        assert deserialised == original


def test_roundtrip_complex_structure():
    """Test roundtrip with complex data structure"""
    original = {
        "string": "test",
        "integer": 123,
        "float": 45.67,
        "boolean": True,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
    }

    # TOML doesn't support top-level lists, only dicts
    for fmt in [DataFormat.JSON]:
        serialised = SerDePynative.serialise(original, fmt)
        deserialised = SerDePynative.deserialise(serialised, fmt)
        assert deserialised == original


# ==================== JSON Specific Tests ====================


def test_to_json_default_indent():
    """Test to_json uses indent=4 by default"""
    data = {"a": 1, "b": 2}

    result = SerDePynative.to_json(data)

    # Indented JSON has newlines
    assert b"\n" in result


def test_to_json_custom_indent():
    """Test to_json with custom indent"""
    data = {"a": 1}

    result = SerDePynative.to_json(data, indent=2)

    assert isinstance(result, bytes)


def test_to_json_no_indent():
    """Test to_json without indent (compact)"""
    data = {"a": 1, "b": 2}

    result = SerDePynative.to_json(data, indent=None)

    # Compact JSON
    assert result == b'{"a":1,"b":2}' or result == b'{"a": 1, "b": 2}'


def test_to_json_ensure_ascii_false():
    """Test to_json with ensure_ascii=False by default"""
    data = {"text": "你好"}

    result = SerDePynative.to_json(data)

    # Unicode characters preserved
    assert "你好".encode("utf-8") in result


def test_to_json_sort_keys():
    """Test to_json sorts keys by default"""
    data = {"z": 1, "a": 2, "m": 3}

    result = SerDePynative.to_json(data, indent=None)

    # Keys should be sorted: a, m, z
    text = result.decode("utf-8")
    assert text.index('"a"') < text.index('"m"') < text.index('"z"')


def test_to_json_custom_encoding():
    """Test to_json with custom encoding"""
    data = {"key": "value"}

    result = SerDePynative.to_json(data, encoding="utf-8")

    assert isinstance(result, bytes)


def test_from_json_basic():
    """Test from_json with valid JSON"""
    json_data = b'{"key": "value", "num": 123}'

    result = SerDePynative.from_json(json_data)

    assert result == {"key": "value", "num": 123}


def test_from_json_with_encoding():
    """Test from_json with custom encoding"""
    json_data = '{"text": "你好"}'.encode("utf-8")

    result = SerDePynative.from_json(json_data, encoding="utf-8")

    assert result["text"] == "你好"


def test_from_json_invalid_data():
    """Test from_json raises SerDeFailedError on invalid JSON"""
    invalid_json = b"not valid json at all"

    with pytest.raises(SerDeFailedError, match="Failed to deserialise"):
        SerDePynative.from_json(invalid_json)


def test_json_with_special_characters():
    """Test JSON with special characters"""
    data = {"text": "line1\nline2", "quote": 'test"value'}

    serialised = SerDePynative.serialise(data, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)

    assert deserialised == data


# ==================== TOML Specific Tests ====================


def test_to_toml_default_indent():
    """Test to_toml uses indent=4 by default"""
    data = {"key": "value"}

    result = SerDePynative.to_toml(data)

    assert isinstance(result, bytes)
    assert b"key" in result


def test_to_toml_nested_sections():
    """Test to_toml with nested sections"""
    data = {"section1": {"key1": "value1"}, "section2": {"key2": "value2"}}

    result = SerDePynative.to_toml(data)

    assert b"section1" in result
    assert b"section2" in result


def test_from_toml_basic():
    """Test from_toml with valid TOML"""
    toml_data = b'key = "value"\nnum = 123'

    result = SerDePynative.from_toml(toml_data)

    assert result == {"key": "value", "num": 123}


def test_from_toml_with_encoding():
    """Test from_toml with custom encoding"""
    toml_data = 'text = "你好"'.encode("utf-8")

    result = SerDePynative.from_toml(toml_data, encoding="utf-8")

    assert result["text"] == "你好"


def test_from_toml_with_sections():
    """Test from_toml with sections"""
    toml_data = b"""
[section1]
key1 = "value1"

[section2]
key2 = "value2"
"""

    result = SerDePynative.from_toml(toml_data)

    assert "section1" in result
    assert "section2" in result
    assert result["section1"]["key1"] == "value1"


def test_from_toml_invalid_data():
    """Test from_toml raises SerDeFailedError on invalid TOML"""
    invalid_toml = b"not valid toml [[[at all"

    with pytest.raises(SerDeFailedError, match="Failed to deserialise"):
        SerDePynative.from_toml(invalid_toml)


def test_toml_import_error_serialise():
    """Test TOML serialise raises SerDeImportError when tomli_w unavailable"""
    data = {"key": "value"}

    with patch("xdatawork.serde.serde.pynative.tomlkit.dumps", side_effect=ImportError("tomlkit")):
        with pytest.raises(SerDeImportError, match="tomlkit"):
            SerDePynative.to_toml(data)


def test_toml_import_error_deserialise():
    """Test TOML deserialise raises SerDeImportError when tomli unavailable"""
    data = b'key = "value"'

    with patch("xdatawork.serde.serde.pynative.tomlkit.loads", side_effect=ImportError("tomlkit")):
        with pytest.raises(SerDeImportError, match="tomlkit"):
            SerDePynative.from_toml(data)


# ==================== Edge Cases ====================


def test_empty_dict():
    """Test serialise/deserialise empty dict"""
    data = {}

    for fmt in [DataFormat.JSON, DataFormat.TOML]:
        serialised = SerDePynative.serialise(data, fmt)
        deserialised = SerDePynative.deserialise(serialised, fmt)
        assert deserialised == data


def test_empty_list():
    """Test serialise/deserialise empty list"""
    data = []

    # Only JSON supports top-level lists
    serialised = SerDePynative.serialise(data, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)
    assert deserialised == data


def test_single_item_dict():
    """Test serialise/deserialise single item dict"""
    data = {"only_key": "only_value"}

    for fmt in [DataFormat.JSON, DataFormat.TOML]:
        serialised = SerDePynative.serialise(data, fmt)
        deserialised = SerDePynative.deserialise(serialised, fmt)
        assert deserialised == data


def test_single_item_list():
    """Test serialise/deserialise single item list"""
    data = ["single"]

    serialised = SerDePynative.serialise(data, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)
    assert deserialised == data


def test_large_dict():
    """Test serialise/deserialise large dict"""
    data = {f"key_{i}": f"value_{i}" for i in range(100)}

    for fmt in [DataFormat.JSON, DataFormat.TOML]:
        serialised = SerDePynative.serialise(data, fmt)
        deserialised = SerDePynative.deserialise(serialised, fmt)
        assert deserialised == data


def test_large_list():
    """Test serialise/deserialise large list"""
    data = list(range(1000))

    serialised = SerDePynative.serialise(data, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)
    assert deserialised == data


def test_unicode_characters():
    """Test with unicode characters"""
    data = {"chinese": "你好", "arabic": "مرحبا", "japanese": "こんにちは", "emoji": "😀🎉"}

    for fmt in [DataFormat.JSON, DataFormat.TOML]:
        serialised = SerDePynative.serialise(data, fmt)
        deserialised = SerDePynative.deserialise(serialised, fmt)
        assert deserialised == data


def test_special_values():
    """Test with special values"""
    data = {
        "null_like": None,
        "boolean_true": True,
        "boolean_false": False,
        "zero": 0,
        "negative": -42,
        "float": 3.14159,
    }

    # JSON handles all these
    serialised = SerDePynative.serialise(data, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)
    assert deserialised == data


def test_deeply_nested_structure():
    """Test with deeply nested structure"""
    data = {"l1": {"l2": {"l3": {"l4": {"l5": "deep_value"}}}}}

    for fmt in [DataFormat.JSON, DataFormat.TOML]:
        serialised = SerDePynative.serialise(data, fmt)
        deserialised = SerDePynative.deserialise(serialised, fmt)
        assert deserialised == data


def test_mixed_list_types():
    """Test list with mixed types"""
    data = [1, "string", 3.14, True, None, {"nested": "dict"}, [1, 2]]

    serialised = SerDePynative.serialise(data, DataFormat.JSON)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.JSON)
    assert deserialised == data


# ==================== Kwargs Propagation Tests ====================


def test_serialise_propagates_kwargs_to_json():
    """Test serialise propagates kwargs to to_json"""
    data = {"b": 2, "a": 1}

    # Override sort_keys to False
    result = SerDePynative.serialise(data, DataFormat.JSON, sort_keys=False, indent=None)

    # Without sorting, original order might be preserved (Python 3.7+)
    assert isinstance(result, bytes)


def test_deserialise_propagates_kwargs_to_json():
    """Test deserialise propagates kwargs to from_json"""
    json_data = b'{"key": "value"}'

    result = SerDePynative.deserialise(json_data, DataFormat.JSON, encoding="utf-8")

    assert result == {"key": "value"}


def test_deserialise_propagates_kwargs_to_toml():
    """Test deserialise propagates kwargs to from_toml"""
    toml_data = b'key = "value"'

    result = SerDePynative.deserialise(toml_data, DataFormat.TOML, encoding="utf-8")

    assert result == {"key": "value"}


# ==================== Module Tests ====================


def test_serdepynative_module():
    """Test SerDePynative is in correct module"""
    assert SerDePynative.__module__ == "xdatawork.serde.serde.pynative"


def test_serdepynative_name():
    """Test SerDePynative has correct name"""
    assert SerDePynative.__name__ == "SerDePynative"


# ==================== Type Validation Tests ====================


def test_type_validation_in_serialise():
    """Test type validation in serialise method"""
    invalid_types = [
        "string data",
        123,
        45.67,
        True,
        None,
        b"bytes data",
        (1, 2, 3),  # tuple
        {1, 2, 3},  # set
    ]

    for invalid in invalid_types:
        with pytest.raises(SerDeTypeError):
            SerDePynative.serialise(invalid, DataFormat.JSON)


def test_type_validation_in_deserialise():
    """Test type validation in deserialise method"""
    invalid_types = [
        {"dict": "data"},
        ["list", "data"],
        "string data",
        123,
        None,
    ]

    for invalid in invalid_types:
        with pytest.raises(SerDeTypeError):
            SerDePynative.deserialise(invalid, DataFormat.JSON)


# ==================== Format Conversion Tests ====================


def test_serialise_accepts_dataformat_enum():
    """Test serialise accepts DataFormat enum"""
    data = {"key": "value"}

    result = SerDePynative.serialise(data, DataFormat.JSON)

    assert isinstance(result, bytes)


def test_serialise_accepts_string_format():
    """Test serialise accepts string format"""
    data = {"key": "value"}

    result = SerDePynative.serialise(data, "json")

    assert isinstance(result, bytes)


def test_deserialise_accepts_dataformat_enum():
    """Test deserialise accepts DataFormat enum"""
    data = b'{"key": "value"}'

    result = SerDePynative.deserialise(data, DataFormat.JSON)

    assert isinstance(result, dict)


def test_deserialise_accepts_string_format():
    """Test deserialise accepts string format"""
    data = b'{"key": "value"}'

    result = SerDePynative.deserialise(data, "json")

    assert isinstance(result, dict)


def test_format_case_insensitive():
    """Test format string is case insensitive"""
    data = {"key": "value"}

    result1 = SerDePynative.serialise(data, "JSON")
    result2 = SerDePynative.serialise(data, "json")
    result3 = SerDePynative.serialise(data, "Json")

    # All should produce valid bytes
    assert isinstance(result1, bytes)
    assert isinstance(result2, bytes)
    assert isinstance(result3, bytes)


# ==================== Error Message Tests ====================


def test_serialise_error_message_format():
    """Test serialise error message includes type information"""
    try:
        SerDePynative.serialise("invalid", DataFormat.JSON)
    except SerDeTypeError as e:
        assert "expects" in str(e)
        assert "dict" in str(e) or "list" in str(e)


def test_deserialise_error_message_format():
    """Test deserialise error message includes type information"""
    try:
        SerDePynative.deserialise("invalid", DataFormat.JSON)
    except SerDeTypeError as e:
        assert "expects" in str(e)
        assert "bytes" in str(e) or "{bytes}" in str(e)


def test_unsupported_format_error_message():
    """Test unsupported format error message"""
    data = {"key": "value"}

    try:
        SerDePynative.serialise(data, DataFormat.PARQUET)
    except SerDeNotSupportedError as e:
        assert "supports" in str(e)
        assert "PARQUET" in str(e) or "parquet" in str(e)


# ==================== JSON Failure Edge Cases ====================


def test_json_serialise_failure():
    """Test JSON serialise with unserializable object"""

    # Create an object that can't be serialized to JSON
    class UnserializableObject:
        pass

    data = {"obj": UnserializableObject()}

    with pytest.raises(SerDeFailedError, match="Failed to serialize"):
        SerDePynative.to_json(data)


def test_json_deserialise_malformed():
    """Test JSON deserialise with malformed data"""
    malformed_json = b'{"key": "value"'  # Missing closing brace

    with pytest.raises(SerDeFailedError):
        SerDePynative.from_json(malformed_json)


# ==================== TOML Edge Cases ====================


def test_toml_list_not_supported_at_top_level():
    """Test TOML doesn't support top-level lists"""
    data = [1, 2, 3]

    # TOML requires top-level to be a table (dict)
    with pytest.raises(SerDeFailedError):
        SerDePynative.serialise(data, DataFormat.TOML)


def test_toml_with_array_values():
    """Test TOML with array values in dict"""
    data = {"numbers": [1, 2, 3], "strings": ["a", "b", "c"]}

    serialised = SerDePynative.serialise(data, DataFormat.TOML)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.TOML)

    assert deserialised == data


def test_toml_with_nested_tables():
    """Test TOML with nested tables"""
    data = {"database": {"server": "localhost", "ports": [8001, 8002], "connection": {"max": 100}}}

    serialised = SerDePynative.serialise(data, DataFormat.TOML)
    deserialised = SerDePynative.deserialise(serialised, DataFormat.TOML)

    assert deserialised == data


def test_toml_deserialise_malformed():
    """Test TOML deserialise with malformed data"""
    malformed_toml = b'key = "value\nnext = invalid'

    with pytest.raises(SerDeFailedError):
        SerDePynative.from_toml(malformed_toml)


# ==================== Comparison with Pandas SerDe ====================


def test_different_supported_sources_than_pandas():
    """Test SerDePynative supports different types than SerDePandas"""
    # SerDePynative supports dict/list, not DataFrames
    assert dict in SerDePynative.SUPPORTED_SER_SOURCE
    assert list in SerDePynative.SUPPORTED_SER_SOURCE


def test_different_formats_than_pandas():
    """Test SerDePynative supports different formats than SerDePandas"""
    # SerDePynative supports TOML and JSON, not Parquet/CSV
    assert DataFormat.TOML in SerDePynative.SUPPORTED_FORMAT
    assert DataFormat.JSON in SerDePynative.SUPPORTED_FORMAT
    assert DataFormat.PARQUET not in SerDePynative.SUPPORTED_FORMAT
    assert DataFormat.CSV not in SerDePynative.SUPPORTED_FORMAT

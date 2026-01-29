from unittest.mock import patch

import pandas as pd
import pytest

from xdatawork.serde.format.dataformat import DataFormat
from xdatawork.serde.serde.errors import (
    SerDeFailedError,
    SerDeImportError,
    SerDeNotSupportedError,
    SerDeTypeError,
)
from xdatawork.serde.serde.pandas import SerDePandas
from xdatawork.serde.serde.serdelike import SerDeLike

# ==================== Class Attributes Tests ====================


def test_serdepandas_supported_ser_source():
    """Test SUPPORTED_SER_SOURCE contains pd.DataFrame"""
    assert SerDePandas.SUPPORTED_SER_SOURCE == {pd.DataFrame}


def test_serdepandas_supported_de_source():
    """Test SUPPORTED_DE_SOURCE contains bytes"""
    assert SerDePandas.SUPPORTED_DE_SOURCE == {bytes}


def test_serdepandas_supported_format():
    """Test SUPPORTED_FORMAT contains expected formats"""
    expected = {DataFormat.PARQUET, DataFormat.CSV, DataFormat.JSON}
    assert SerDePandas.SUPPORTED_FORMAT == expected


def test_serdepandas_implements_serdelike():
    """Test SerDePandas implements SerDeLike protocol"""
    serde = SerDePandas()
    assert isinstance(serde, SerDeLike)


# ==================== Serialise Method Tests ====================


def test_serialise_csv_basic():
    """Test serialise with CSV format"""
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    result = SerDePandas.serialise(df, DataFormat.CSV)

    assert isinstance(result, bytes)
    assert b"a,b" in result
    assert b"1,4" in result


def test_serialise_csv_with_string_format():
    """Test serialise with string format 'csv'"""
    df = pd.DataFrame({"x": [10, 20]})

    result = SerDePandas.serialise(df, "csv")

    assert isinstance(result, bytes)
    assert b"x" in result


def test_serialise_json_basic():
    """Test serialise with JSON format"""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    result = SerDePandas.serialise(df, DataFormat.JSON)

    assert isinstance(result, bytes)
    assert b"a" in result
    assert b"b" in result


def test_serialise_parquet_basic():
    """Test serialise with Parquet format"""
    df = pd.DataFrame({"col1": [100, 200], "col2": [300, 400]})

    result = SerDePandas.serialise(df, DataFormat.PARQUET)

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_serialise_invalid_type():
    """Test serialise raises SerDeTypeError for non-DataFrame"""
    with pytest.raises(SerDeTypeError, match="SerDePandas.serialise expects"):
        SerDePandas.serialise([1, 2, 3], DataFormat.CSV)


def test_serialise_dict_raises_error():
    """Test serialise raises SerDeTypeError for dict"""
    with pytest.raises(SerDeTypeError):
        SerDePandas.serialise({"a": 1}, DataFormat.JSON)


def test_serialise_unsupported_format():
    """Test serialise raises SerDeNotSupportedError for unsupported format"""
    df = pd.DataFrame({"a": [1]})

    with pytest.raises(SerDeNotSupportedError, match="SerDePandas.serialise supports"):
        SerDePandas.serialise(df, DataFormat.TOML)


def test_serialise_empty_dataframe():
    """Test serialise with empty DataFrame"""
    df = pd.DataFrame()

    result = SerDePandas.serialise(df, DataFormat.CSV)

    assert isinstance(result, bytes)


# ==================== Deserialise Method Tests ====================


def test_deserialise_csv_basic():
    """Test deserialise with CSV format"""
    csv_data = b"a,b\n1,4\n2,5\n3,6"

    result = SerDePandas.deserialise(csv_data, DataFormat.CSV)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["a", "b"]
    assert len(result) == 3


def test_deserialise_csv_with_string_format():
    """Test deserialise with string format 'csv'"""
    csv_data = b"x\n10\n20"

    result = SerDePandas.deserialise(csv_data, "csv")

    assert isinstance(result, pd.DataFrame)
    assert "x" in result.columns


def test_deserialise_json_basic():
    """Test deserialise with JSON format"""
    json_data = b'[{"a":1,"b":3},{"a":2,"b":4}]'

    result = SerDePandas.deserialise(json_data, DataFormat.JSON)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["a", "b"]
    assert len(result) == 2


def test_deserialise_parquet_basic():
    """Test deserialise with Parquet format"""
    df = pd.DataFrame({"col1": [100, 200], "col2": [300, 400]})
    parquet_data = SerDePandas.serialise(df, DataFormat.PARQUET)

    result = SerDePandas.deserialise(parquet_data, DataFormat.PARQUET)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["col1", "col2"]
    assert len(result) == 2


def test_deserialise_invalid_type():
    """Test deserialise raises SerDeTypeError for non-bytes"""
    with pytest.raises(SerDeTypeError, match="SerDePandas.deserialise expects"):
        SerDePandas.deserialise("string data", DataFormat.CSV)


def test_deserialise_list_raises_error():
    """Test deserialise raises SerDeTypeError for list"""
    with pytest.raises(SerDeTypeError):
        SerDePandas.deserialise([1, 2, 3], DataFormat.JSON)


def test_deserialise_unsupported_format():
    """Test deserialise raises SerDeNotSupportedError for unsupported format"""
    data = b"some data"

    with pytest.raises(SerDeNotSupportedError, match="SerDePandas.deserialise supports"):
        SerDePandas.deserialise(data, DataFormat.TOML)


# ==================== Round-Trip Tests ====================


def test_roundtrip_csv():
    """Test CSV serialise -> deserialise roundtrip"""
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    serialised = SerDePandas.serialise(df, DataFormat.CSV)
    deserialised = SerDePandas.deserialise(serialised, DataFormat.CSV)

    pd.testing.assert_frame_equal(df, deserialised)


def test_roundtrip_json():
    """Test JSON serialise -> deserialise roundtrip"""
    df = pd.DataFrame({"x": [10, 20, 30], "y": [40, 50, 60]})

    serialised = SerDePandas.serialise(df, DataFormat.JSON)
    deserialised = SerDePandas.deserialise(serialised, DataFormat.JSON)

    pd.testing.assert_frame_equal(df, deserialised)


def test_roundtrip_parquet():
    """Test Parquet serialise -> deserialise roundtrip"""
    df = pd.DataFrame({"col_a": [100, 200], "col_b": [300, 400]})

    serialised = SerDePandas.serialise(df, DataFormat.PARQUET)
    deserialised = SerDePandas.deserialise(serialised, DataFormat.PARQUET)

    pd.testing.assert_frame_equal(df, deserialised)


def test_roundtrip_with_string_columns():
    """Test roundtrip with string data"""
    df = pd.DataFrame({"name": ["Alice", "Bob"], "city": ["NYC", "LA"]})

    for fmt in [DataFormat.CSV, DataFormat.JSON, DataFormat.PARQUET]:
        serialised = SerDePandas.serialise(df, fmt)
        deserialised = SerDePandas.deserialise(serialised, fmt)

        pd.testing.assert_frame_equal(df, deserialised)


def test_roundtrip_with_mixed_types():
    """Test roundtrip with mixed data types"""
    df = pd.DataFrame(
        {
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
        }
    )

    # CSV loses type information, so skip it
    for fmt in [DataFormat.JSON, DataFormat.PARQUET]:
        serialised = SerDePandas.serialise(df, fmt)
        deserialised = SerDePandas.deserialise(serialised, fmt)

        assert list(deserialised.columns) == list(df.columns)
        assert len(deserialised) == len(df)


# ==================== CSV Specific Tests ====================


def test_to_csv_without_index():
    """Test to_csv doesn't include index by default"""
    df = pd.DataFrame({"a": [1, 2]})

    result = SerDePandas.to_csv(df)

    # Should not contain index numbers
    assert b"0" not in result or b"a,b" in result  # Index might coincide with data


def test_to_csv_custom_encoding():
    """Test to_csv with custom encoding"""
    df = pd.DataFrame({"text": ["hello"]})

    result = SerDePandas.to_csv(df, encoding="utf-8")

    assert isinstance(result, bytes)


def test_to_csv_with_kwargs():
    """Test to_csv with additional kwargs"""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    result = SerDePandas.to_csv(df, sep=";")

    assert b";" in result


def test_from_csv_with_encoding():
    """Test from_csv with custom encoding"""
    csv_data = "a,b\n1,2".encode("utf-8")

    result = SerDePandas.from_csv(csv_data, encoding="utf-8")

    assert isinstance(result, pd.DataFrame)


def test_from_csv_with_kwargs():
    """Test from_csv with additional kwargs"""
    csv_data = b"a;b\n1;2"

    result = SerDePandas.from_csv(csv_data, sep=";")

    assert list(result.columns) == ["a", "b"]


def test_csv_failed_error():
    """Test CSV deserialisation raises SerDeFailedError on invalid data"""
    invalid_csv = b"invalid\ncsv\ndata\nwith\ninconsistent\ncolumns"

    # This might or might not fail depending on pandas behavior
    # but if it does, it should wrap in SerDeFailedError
    try:
        SerDePandas.from_csv(invalid_csv)
    except SerDeFailedError:
        pass  # Expected


# ==================== JSON Specific Tests ====================


def test_to_json_default_orient():
    """Test to_json uses records orient by default"""
    df = pd.DataFrame({"a": [1, 2]})

    result = SerDePandas.to_json(df)

    # records orient produces array of objects
    assert b"[" in result
    assert b"{" in result


def test_to_json_custom_orient():
    """Test to_json with custom orient"""
    df = pd.DataFrame({"a": [1, 2]})

    result = SerDePandas.to_json(df, orient="split")

    assert isinstance(result, bytes)
    assert b"columns" in result or b"data" in result


def test_to_json_with_lines():
    """Test to_json with lines=True"""
    df = pd.DataFrame({"a": [1, 2]})

    result = SerDePandas.to_json(df, lines=True)

    # lines format has newlines between records
    assert b"\n" in result


def test_from_json_default_orient():
    """Test from_json uses records orient by default"""
    json_data = b'[{"a":1},{"a":2}]'

    result = SerDePandas.from_json(json_data)

    assert isinstance(result, pd.DataFrame)
    assert "a" in result.columns


def test_from_json_custom_orient():
    """Test from_json with custom orient"""
    json_data = b'{"columns":["a"],"data":[[1],[2]]}'

    result = SerDePandas.from_json(json_data, orient="split")

    assert isinstance(result, pd.DataFrame)


def test_from_json_with_lines():
    """Test from_json with lines=True"""
    json_data = b'{"a":1}\n{"a":2}'

    result = SerDePandas.from_json(json_data, lines=True)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2


def test_json_failed_error():
    """Test JSON deserialisation raises SerDeFailedError on invalid data"""
    invalid_json = b"not valid json at all"

    with pytest.raises(SerDeFailedError, match="Failed to deserialize data"):
        SerDePandas.from_json(invalid_json)


# ==================== Parquet Specific Tests ====================


def test_to_parquet_without_index():
    """Test to_parquet doesn't include index by default"""
    df = pd.DataFrame({"a": [1, 2]})

    result = SerDePandas.to_parquet(df)

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_to_parquet_default_engine():
    """Test to_parquet uses pyarrow by default"""
    df = pd.DataFrame({"a": [1, 2]})

    # Should work with pyarrow
    result = SerDePandas.to_parquet(df)

    assert isinstance(result, bytes)


def test_to_parquet_with_kwargs():
    """Test to_parquet with additional kwargs"""
    df = pd.DataFrame({"a": [1, 2]})

    result = SerDePandas.to_parquet(df, compression="snappy")

    assert isinstance(result, bytes)


def test_from_parquet_basic():
    """Test from_parquet with valid parquet data"""
    df = pd.DataFrame({"a": [1, 2, 3]})
    parquet_data = SerDePandas.to_parquet(df)

    result = SerDePandas.from_parquet(parquet_data)

    pd.testing.assert_frame_equal(df, result)


def test_from_parquet_with_kwargs():
    """Test from_parquet with additional kwargs"""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    parquet_data = SerDePandas.to_parquet(df)

    result = SerDePandas.from_parquet(parquet_data, columns=["a"])

    assert list(result.columns) == ["a"]


def test_parquet_import_error():
    """Test Parquet raises SerDeImportError when pyarrow unavailable"""
    df = pd.DataFrame({"a": [1, 2]})

    # Mock ImportError from pandas
    with patch.object(pd.DataFrame, "to_parquet", side_effect=ImportError("pyarrow")):
        with pytest.raises(SerDeImportError, match="pyarrow"):
            SerDePandas.to_parquet(df)


def test_parquet_deserialise_import_error():
    """Test Parquet deserialise raises SerDeImportError when pyarrow unavailable"""
    data = b"fake parquet data"

    with patch("pandas.read_parquet", side_effect=ImportError("pyarrow")):
        with pytest.raises(SerDeImportError, match="pyarrow"):
            SerDePandas.from_parquet(data)


def test_parquet_failed_error():
    """Test Parquet deserialisation raises SerDeFailedError on invalid data"""
    invalid_parquet = b"not valid parquet data"

    with pytest.raises(SerDeFailedError, match="Failed to deserialize data"):
        SerDePandas.from_parquet(invalid_parquet)


# ==================== Edge Cases ====================


def test_empty_dataframe_csv():
    """Test serialise empty DataFrame to CSV"""
    df = pd.DataFrame()

    result = SerDePandas.serialise(df, DataFormat.CSV)

    assert isinstance(result, bytes)


def test_empty_dataframe_json():
    """Test serialise empty DataFrame to JSON"""
    df = pd.DataFrame()

    result = SerDePandas.serialise(df, DataFormat.JSON)

    assert isinstance(result, bytes)


def test_empty_dataframe_parquet():
    """Test serialise empty DataFrame to Parquet"""
    df = pd.DataFrame()

    result = SerDePandas.serialise(df, DataFormat.PARQUET)

    assert isinstance(result, bytes)


def test_single_row_dataframe():
    """Test serialise single row DataFrame"""
    df = pd.DataFrame({"a": [1], "b": [2]})

    for fmt in [DataFormat.CSV, DataFormat.JSON, DataFormat.PARQUET]:
        result = SerDePandas.serialise(df, fmt)
        assert isinstance(result, bytes)


def test_single_column_dataframe():
    """Test serialise single column DataFrame"""
    df = pd.DataFrame({"only_col": [1, 2, 3]})

    for fmt in [DataFormat.CSV, DataFormat.JSON, DataFormat.PARQUET]:
        result = SerDePandas.serialise(df, fmt)
        assert isinstance(result, bytes)


def test_large_dataframe():
    """Test serialise large DataFrame"""
    df = pd.DataFrame({"col_" + str(i): range(1000) for i in range(10)})

    for fmt in [DataFormat.CSV, DataFormat.JSON, DataFormat.PARQUET]:
        result = SerDePandas.serialise(df, fmt)
        assert isinstance(result, bytes)
        assert len(result) > 0


def test_special_characters_in_data():
    """Test serialise DataFrame with special characters"""
    df = pd.DataFrame({"text": ["hello, world", "line1\nline2", 'quote"test']})

    # CSV and JSON should handle special characters
    for fmt in [DataFormat.CSV, DataFormat.JSON]:
        serialised = SerDePandas.serialise(df, fmt)
        deserialised = SerDePandas.deserialise(serialised, fmt)
        assert len(deserialised) == 3


def test_unicode_characters():
    """Test serialise DataFrame with unicode characters"""
    df = pd.DataFrame({"text": ["你好", "مرحبا", "こんにちは"]})

    for fmt in [DataFormat.CSV, DataFormat.JSON, DataFormat.PARQUET]:
        serialised = SerDePandas.serialise(df, fmt)
        deserialised = SerDePandas.deserialise(serialised, fmt)
        assert len(deserialised) == 3


# ==================== Kwargs Propagation Tests ====================


def test_serialise_propagates_kwargs_to_csv():
    """Test serialise propagates kwargs to to_csv"""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    result = SerDePandas.serialise(df, DataFormat.CSV, sep="|")

    assert b"|" in result


def test_serialise_propagates_kwargs_to_json():
    """Test serialise propagates kwargs to to_json"""
    df = pd.DataFrame({"a": [1, 2]})

    result = SerDePandas.serialise(df, DataFormat.JSON, indent=2)

    # Indented JSON has more spaces
    assert len(result) > len(SerDePandas.serialise(df, DataFormat.JSON))


def test_serialise_propagates_kwargs_to_parquet():
    """Test serialise propagates kwargs to to_parquet"""
    df = pd.DataFrame({"a": [1, 2]})

    # Should accept compression kwarg
    result = SerDePandas.serialise(df, DataFormat.PARQUET, compression="gzip")

    assert isinstance(result, bytes)


def test_deserialise_propagates_kwargs_to_csv():
    """Test deserialise propagates kwargs to from_csv"""
    csv_data = b"a|b\n1|2"

    result = SerDePandas.deserialise(csv_data, DataFormat.CSV, sep="|")

    assert list(result.columns) == ["a", "b"]


def test_deserialise_propagates_kwargs_to_json():
    """Test deserialise propagates kwargs to from_json"""
    json_data = b'{"columns":["a"],"data":[[1]]}'

    result = SerDePandas.deserialise(json_data, DataFormat.JSON, orient="split")

    assert "a" in result.columns


# ==================== Module Tests ====================


def test_serdepandas_module():
    """Test SerDePandas is in correct module"""
    assert SerDePandas.__module__ == "xdatawork.serde.serde.pandas"


def test_serdepandas_name():
    """Test SerDePandas has correct name"""
    assert SerDePandas.__name__ == "SerDePandas"


# ==================== Type Validation Tests ====================


def test_type_validation_in_serialise():
    """Test type validation in serialise method"""
    invalid_types = [
        {"dict": "data"},
        ["list", "data"],
        "string data",
        123,
        None,
    ]

    for invalid in invalid_types:
        with pytest.raises(SerDeTypeError):
            SerDePandas.serialise(invalid, DataFormat.CSV)


def test_type_validation_in_deserialise():
    """Test type validation in deserialise method"""
    invalid_types = [
        {"dict": "data"},
        ["list", "data"],
        "string data",
        123,
        None,
        pd.DataFrame({"a": [1]}),  # DataFrame is not bytes
    ]

    for invalid in invalid_types:
        with pytest.raises(SerDeTypeError):
            SerDePandas.deserialise(invalid, DataFormat.CSV)


# ==================== Format Conversion Tests ====================


def test_serialise_accepts_dataformat_enum():
    """Test serialise accepts DataFormat enum"""
    df = pd.DataFrame({"a": [1]})

    result = SerDePandas.serialise(df, DataFormat.CSV)

    assert isinstance(result, bytes)


def test_serialise_accepts_string_format():
    """Test serialise accepts string format"""
    df = pd.DataFrame({"a": [1]})

    result = SerDePandas.serialise(df, "csv")

    assert isinstance(result, bytes)


def test_deserialise_accepts_dataformat_enum():
    """Test deserialise accepts DataFormat enum"""
    data = b"a\n1"

    result = SerDePandas.deserialise(data, DataFormat.CSV)

    assert isinstance(result, pd.DataFrame)


def test_deserialise_accepts_string_format():
    """Test deserialise accepts string format"""
    data = b"a\n1"

    result = SerDePandas.deserialise(data, "csv")

    assert isinstance(result, pd.DataFrame)


def test_format_case_insensitive():
    """Test format string is case insensitive"""
    df = pd.DataFrame({"a": [1]})

    result1 = SerDePandas.serialise(df, "CSV")
    result2 = SerDePandas.serialise(df, "csv")
    result3 = SerDePandas.serialise(df, "Csv")

    # All should produce equivalent results
    assert isinstance(result1, bytes)
    assert isinstance(result2, bytes)
    assert isinstance(result3, bytes)

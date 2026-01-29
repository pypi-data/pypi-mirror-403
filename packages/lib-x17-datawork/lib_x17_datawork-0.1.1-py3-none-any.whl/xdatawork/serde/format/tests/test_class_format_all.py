import pytest

from xdatawork.serde.format.dataformat import DataFormat


def test_dataformat_is_enum():
    """Test DataFormat is an Enum"""
    from enum import Enum

    assert issubclass(DataFormat, Enum)


def test_dataformat_is_str_enum():
    """Test DataFormat inherits from str"""
    assert issubclass(DataFormat, str)


def test_dataformat_has_parquet():
    """Test DataFormat has PARQUET attribute"""
    assert hasattr(DataFormat, "PARQUET")
    assert DataFormat.PARQUET == "parquet"


def test_dataformat_has_csv():
    """Test DataFormat has CSV attribute"""
    assert hasattr(DataFormat, "CSV")
    assert DataFormat.CSV == "csv"


def test_dataformat_has_json():
    """Test DataFormat has JSON attribute"""
    assert hasattr(DataFormat, "JSON")
    assert DataFormat.JSON == "json"


def test_dataformat_values_are_lowercase():
    """Test all DataFormat values are lowercase"""
    for fmt in DataFormat:
        assert fmt.value == fmt.value.lower()


# ==================== from_str() Method Tests ====================


def test_from_str_parquet_lowercase():
    """Test from_str with lowercase 'parquet'"""
    fmt = DataFormat.from_str("parquet")

    assert fmt == DataFormat.PARQUET
    assert isinstance(fmt, DataFormat)


def test_from_str_parquet_uppercase():
    """Test from_str with uppercase 'PARQUET'"""
    fmt = DataFormat.from_str("PARQUET")

    assert fmt == DataFormat.PARQUET


def test_from_str_parquet_mixed_case():
    """Test from_str with mixed case 'PaRqUeT'"""
    fmt = DataFormat.from_str("PaRqUeT")

    assert fmt == DataFormat.PARQUET


def test_from_str_csv_lowercase():
    """Test from_str with lowercase 'csv'"""
    fmt = DataFormat.from_str("csv")

    assert fmt == DataFormat.CSV


def test_from_str_csv_uppercase():
    """Test from_str with uppercase 'CSV'"""
    fmt = DataFormat.from_str("CSV")

    assert fmt == DataFormat.CSV


def test_from_str_csv_mixed_case():
    """Test from_str with mixed case 'CsV'"""
    fmt = DataFormat.from_str("CsV")

    assert fmt == DataFormat.CSV


def test_from_str_json_lowercase():
    """Test from_str with lowercase 'json'"""
    fmt = DataFormat.from_str("json")

    assert fmt == DataFormat.JSON


def test_from_str_json_uppercase():
    """Test from_str with uppercase 'JSON'"""
    fmt = DataFormat.from_str("JSON")

    assert fmt == DataFormat.JSON


def test_from_str_json_mixed_case():
    """Test from_str with mixed case 'JsOn'"""
    fmt = DataFormat.from_str("JsOn")

    assert fmt == DataFormat.JSON


def test_from_str_invalid_format_raises_error():
    """Test from_str raises ValueError for invalid format"""
    with pytest.raises(ValueError, match="Unknown DataFormat: xml"):
        DataFormat.from_str("xml")


def test_from_str_empty_string_raises_error():
    """Test from_str raises ValueError for empty string"""
    with pytest.raises(ValueError, match="Unknown DataFormat"):
        DataFormat.from_str("")


def test_from_str_with_whitespace():
    """Test from_str does not strip whitespace (should fail)"""
    with pytest.raises(ValueError):
        DataFormat.from_str(" parquet ")


def test_from_str_numeric_string():
    """Test from_str with numeric string raises error"""
    with pytest.raises(ValueError):
        DataFormat.from_str("123")


# ==================== from_any() Method Tests ====================


def test_from_any_with_enum():
    """Test from_any with DataFormat enum instance"""
    fmt = DataFormat.from_any(DataFormat.PARQUET)

    assert fmt == DataFormat.PARQUET
    assert isinstance(fmt, DataFormat)


def test_from_any_with_string_lowercase():
    """Test from_any with lowercase string"""
    fmt = DataFormat.from_any("csv")

    assert fmt == DataFormat.CSV


def test_from_any_with_string_uppercase():
    """Test from_any with uppercase string"""
    fmt = DataFormat.from_any("JSON")

    assert fmt == DataFormat.JSON


def test_from_any_with_string_mixed_case():
    """Test from_any with mixed case string"""
    fmt = DataFormat.from_any("PaRqUeT")

    assert fmt == DataFormat.PARQUET


def test_from_any_returns_same_instance():
    """Test from_any returns same instance for enum input"""
    original = DataFormat.CSV
    result = DataFormat.from_any(original)

    assert result is original


def test_from_any_with_invalid_string():
    """Test from_any raises ValueError for invalid string"""
    with pytest.raises(ValueError, match="Unknown DataFormat"):
        DataFormat.from_any("invalid")


def test_from_any_all_formats():
    """Test from_any with all valid format strings"""
    test_cases = [
        ("parquet", DataFormat.PARQUET),
        ("PARQUET", DataFormat.PARQUET),
        ("csv", DataFormat.CSV),
        ("CSV", DataFormat.CSV),
        ("json", DataFormat.JSON),
        ("JSON", DataFormat.JSON),
    ]

    for input_str, expected in test_cases:
        result = DataFormat.from_any(input_str)
        assert result == expected


def test_from_any_with_enum_instances():
    """Test from_any with all enum instances"""
    for fmt in DataFormat:
        result = DataFormat.from_any(fmt)
        assert result == fmt
        assert result is fmt


# ==================== list_all() Method Tests ====================


def test_list_all_returns_list():
    """Test list_all returns a list"""
    result = DataFormat.list_all()

    assert isinstance(result, list)


def test_list_all_returns_all_formats():
    result = DataFormat.list_all()
    assert DataFormat.PARQUET in result
    assert DataFormat.CSV in result
    assert DataFormat.JSON in result
    assert DataFormat.TOML in result


def test_list_all_contains_dataformat_instances():
    """Test list_all contains only DataFormat instances"""
    result = DataFormat.list_all()

    for item in result:
        assert isinstance(item, DataFormat)


def test_list_all_is_complete():
    """Test list_all matches manual iteration"""
    list_result = DataFormat.list_all()
    manual_list = [fmt for fmt in DataFormat]

    assert list_result == manual_list


# ==================== __str__() Method Tests ====================


def test_str_parquet():
    """Test __str__ for PARQUET format"""
    result = str(DataFormat.PARQUET)

    assert result == "parquet"
    assert isinstance(result, str)


def test_str_csv():
    """Test __str__ for CSV format"""
    result = str(DataFormat.CSV)

    assert result == "csv"


def test_str_json():
    """Test __str__ for JSON format"""
    result = str(DataFormat.JSON)

    assert result == "json"


def test_str_all_formats():
    """Test __str__ for all formats returns value"""
    for fmt in DataFormat:
        result = str(fmt)
        assert result == fmt.value


def test_str_in_f_string():
    """Test DataFormat works in f-strings"""
    fmt = DataFormat.PARQUET
    result = f"Format is {fmt}"

    assert result == "Format is parquet"


def test_str_in_format():
    """Test DataFormat works with .format()"""
    fmt = DataFormat.CSV
    result = "Format is {}".format(fmt)

    assert result == "Format is csv"


# ==================== __repr__() Method Tests ====================


def test_repr_parquet():
    """Test __repr__ for PARQUET format"""
    result = repr(DataFormat.PARQUET)

    assert result == "DataFormat.PARQUET"


def test_repr_csv():
    """Test __repr__ for CSV format"""
    result = repr(DataFormat.CSV)

    assert result == "DataFormat.CSV"


def test_repr_json():
    """Test __repr__ for JSON format"""
    result = repr(DataFormat.JSON)

    assert result == "DataFormat.JSON"


def test_repr_all_formats():
    """Test __repr__ for all formats"""
    test_cases = [
        (DataFormat.PARQUET, "DataFormat.PARQUET"),
        (DataFormat.CSV, "DataFormat.CSV"),
        (DataFormat.JSON, "DataFormat.JSON"),
    ]

    for fmt, expected in test_cases:
        assert repr(fmt) == expected


def test_repr_contains_class_name():
    """Test __repr__ contains class name"""
    for fmt in DataFormat:
        result = repr(fmt)
        assert "DataFormat" in result


def test_repr_contains_member_name():
    """Test __repr__ contains member name"""
    assert "PARQUET" in repr(DataFormat.PARQUET)
    assert "CSV" in repr(DataFormat.CSV)
    assert "JSON" in repr(DataFormat.JSON)


# ==================== String Comparison Tests ====================


def test_equals_string_lowercase():
    """Test DataFormat equals lowercase string"""
    assert DataFormat.PARQUET == "parquet"
    assert DataFormat.CSV == "csv"
    assert DataFormat.JSON == "json"


def test_not_equals_uppercase_string():
    """Test DataFormat does not equal uppercase string directly"""
    # Since DataFormat inherits from str, it compares values directly
    assert DataFormat.PARQUET != "PARQUET"
    assert DataFormat.CSV != "CSV"
    assert DataFormat.JSON != "JSON"


def test_equals_another_enum_instance():
    """Test DataFormat equals another instance of same value"""
    fmt1 = DataFormat.PARQUET
    fmt2 = DataFormat.PARQUET

    assert fmt1 == fmt2
    assert fmt1 is fmt2  # Same instance


def test_not_equals_different_format():
    """Test DataFormat not equals different format"""
    assert DataFormat.PARQUET != DataFormat.CSV
    assert DataFormat.CSV != DataFormat.JSON
    assert DataFormat.JSON != DataFormat.PARQUET


def test_in_operator_with_list():
    """Test DataFormat with 'in' operator"""
    formats = [DataFormat.PARQUET, DataFormat.CSV]

    assert DataFormat.PARQUET in formats
    assert DataFormat.JSON not in formats


def test_in_operator_with_strings():
    """Test DataFormat value in string list"""
    strings = ["parquet", "csv"]

    assert DataFormat.PARQUET in strings
    assert DataFormat.JSON not in strings


# ==================== Enum Iteration Tests ====================


def test_iterate_all_formats():
    """Test iterating over DataFormat"""
    formats = []
    for fmt in DataFormat:
        formats.append(fmt)

    assert DataFormat.PARQUET in formats
    assert DataFormat.CSV in formats
    assert DataFormat.JSON in formats
    assert DataFormat.TOML in formats


def test_enum_members_are_unique():
    """Test all DataFormat members are unique"""
    members = list(DataFormat)
    values = [fmt.value for fmt in members]

    assert len(values) == len(set(values))


# ==================== Type Checking Tests ====================


def test_isinstance_dataformat():
    """Test isinstance check for DataFormat"""
    fmt = DataFormat.PARQUET

    assert isinstance(fmt, DataFormat)


def test_isinstance_str():
    """Test DataFormat instance is also a str"""
    fmt = DataFormat.CSV

    assert isinstance(fmt, str)


def test_isinstance_enum():
    """Test DataFormat instance is also an Enum"""
    from enum import Enum

    fmt = DataFormat.JSON

    assert isinstance(fmt, Enum)


def test_type_of_format():
    """Test type() returns DataFormat"""
    fmt = DataFormat.PARQUET

    assert type(fmt) is DataFormat


# ==================== Value Access Tests ====================


def test_access_value_attribute():
    """Test accessing .value attribute"""
    assert DataFormat.PARQUET.value == "parquet"
    assert DataFormat.CSV.value == "csv"
    assert DataFormat.JSON.value == "json"


def test_access_name_attribute():
    """Test accessing .name attribute"""
    assert DataFormat.PARQUET.name == "PARQUET"
    assert DataFormat.CSV.name == "CSV"
    assert DataFormat.JSON.name == "JSON"


def test_name_attribute_is_uppercase():
    """Test .name attribute is uppercase"""
    for fmt in DataFormat:
        assert fmt.name == fmt.name.upper()


def test_value_and_str_are_same():
    """Test .value and str() return same result"""
    for fmt in DataFormat:
        assert fmt.value == str(fmt)


# ==================== Dictionary and Set Operations ====================


def test_dataformat_as_dict_key():
    """Test using DataFormat as dictionary key"""
    mapping = {
        DataFormat.PARQUET: "parquet_handler",
        DataFormat.CSV: "csv_handler",
        DataFormat.JSON: "json_handler",
    }

    assert mapping[DataFormat.PARQUET] == "parquet_handler"
    assert mapping[DataFormat.CSV] == "csv_handler"
    assert mapping[DataFormat.JSON] == "json_handler"


def test_dataformat_in_set():
    """Test DataFormat in set operations"""
    formats_set = {DataFormat.PARQUET, DataFormat.CSV, DataFormat.CSV}

    assert len(formats_set) == 2  # Duplicate removed
    assert DataFormat.PARQUET in formats_set
    assert DataFormat.CSV in formats_set
    assert DataFormat.JSON not in formats_set


def test_dataformat_hashable():
    """Test DataFormat is hashable"""
    # Should not raise
    hash(DataFormat.PARQUET)
    hash(DataFormat.CSV)
    hash(DataFormat.JSON)


# ==================== Edge Cases and Error Handling ====================


def test_from_str_case_variations():
    """Test from_str with various case combinations"""
    variations = [
        "parquet",
        "PARQUET",
        "Parquet",
        "pArQuEt",
        "ParQueT",
    ]

    for variant in variations:
        result = DataFormat.from_str(variant)
        assert result == DataFormat.PARQUET


def test_from_str_special_characters_raises_error():
    """Test from_str with special characters raises error"""
    invalid_inputs = ["parquet!", "csv#", "json@", "par-quet", "c_sv"]

    for invalid in invalid_inputs:
        with pytest.raises(ValueError):
            DataFormat.from_str(invalid)


def test_from_any_type_error_for_invalid_type():
    """Test from_any behavior with invalid type (should raise ValueError in from_str)"""
    # from_any expects DataFormat or str, passing int will fail when calling from_str
    with pytest.raises(AttributeError):  # int doesn't have .lower()
        DataFormat.from_any(123)


def test_comparison_with_none():
    """Test DataFormat comparison with None"""
    assert DataFormat.PARQUET is not None


def test_boolean_context():
    """Test DataFormat in boolean context"""
    # All enum members are truthy
    assert bool(DataFormat.PARQUET)
    assert bool(DataFormat.CSV)
    assert bool(DataFormat.JSON)


# ==================== Integration Tests ====================


def test_roundtrip_str_to_enum_to_str():
    """Test round trip conversion string -> enum -> string"""
    original = "parquet"
    fmt = DataFormat.from_str(original)
    result = str(fmt)

    assert result == original


def test_from_any_roundtrip():
    """Test from_any roundtrip with string and enum"""
    # String -> Enum -> Same Enum
    fmt1 = DataFormat.from_any("csv")
    fmt2 = DataFormat.from_any(fmt1)

    assert fmt1 == fmt2
    assert fmt1 is fmt2


def test_all_formats_work_with_all_methods():
    """Test all formats work with all methods"""
    for fmt in DataFormat:
        # from_any
        assert DataFormat.from_any(fmt) == fmt

        # from_str
        assert DataFormat.from_str(fmt.value) == fmt

        # __str__
        assert str(fmt) == fmt.value

        # __repr__
        assert "DataFormat" in repr(fmt)


def test_format_usage_in_conditional():
    """Test using DataFormat in conditional statements"""

    def process_format(fmt: DataFormat) -> str:
        if fmt == DataFormat.PARQUET:
            return "parquet_processor"
        elif fmt == DataFormat.CSV:
            return "csv_processor"
        elif fmt == DataFormat.JSON:
            return "json_processor"
        else:
            return "unknown"

    assert process_format(DataFormat.PARQUET) == "parquet_processor"
    assert process_format(DataFormat.CSV) == "csv_processor"
    assert process_format(DataFormat.JSON) == "json_processor"


def test_format_matching_with_string():
    """Test format matching with string values"""

    def get_extension(fmt: DataFormat) -> str:
        extensions = {
            "parquet": ".parquet",
            "csv": ".csv",
            "json": ".json",
        }
        return extensions.get(str(fmt), ".unknown")

    assert get_extension(DataFormat.PARQUET) == ".parquet"
    assert get_extension(DataFormat.CSV) == ".csv"
    assert get_extension(DataFormat.JSON) == ".json"


# ==================== String Method Tests ====================


def test_format_upper():
    """Test calling .upper() on DataFormat (as it inherits from str)"""
    result = DataFormat.PARQUET.upper()

    assert result == "PARQUET"
    assert isinstance(result, str)


def test_format_lower():
    """Test calling .lower() on DataFormat"""
    result = DataFormat.CSV.lower()

    assert result == "csv"


def test_format_startswith():
    """Test calling .startswith() on DataFormat"""
    assert DataFormat.PARQUET.startswith("par")
    assert DataFormat.CSV.startswith("c")
    assert DataFormat.JSON.startswith("js")


def test_format_endswith():
    """Test calling .endswith() on DataFormat"""
    assert DataFormat.PARQUET.endswith("quet")
    assert DataFormat.CSV.endswith("sv")
    assert DataFormat.JSON.endswith("son")


def test_format_in_string():
    """Test DataFormat in string operations"""
    text = "The format is parquet"

    assert DataFormat.PARQUET in text
    assert str(DataFormat.PARQUET) in text

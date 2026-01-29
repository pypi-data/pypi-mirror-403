import pytest

from xdatawork.interface.base.partitionkind import PartitionKind


def test_partitionkind_is_enum():
    """Test PartitionKind is an Enum"""
    from enum import Enum

    assert issubclass(PartitionKind, Enum)


def test_partitionkind_is_str_enum():
    """Test PartitionKind inherits from str"""
    assert issubclass(PartitionKind, str)


def test_partitionkind_has_non_partitioned():
    """Test PartitionKind has NON_PARTITIONED attribute"""
    assert hasattr(PartitionKind, "NON_PARTITIONED")
    assert PartitionKind.NON_PARTITIONED == "NON_PARTITIONED"


def test_partitionkind_has_date_partitioned():
    """Test PartitionKind has DATE_PARTITIONED attribute"""
    assert hasattr(PartitionKind, "DATE_PARTITIONED")
    assert PartitionKind.DATE_PARTITIONED == "DATE_PARTITIONED"


def test_partitionkind_has_datetime_partitioned():
    """Test PartitionKind has DATETIME_PARTITIONED attribute"""
    assert hasattr(PartitionKind, "DATETIME_PARTITIONED")
    assert PartitionKind.DATETIME_PARTITIONED == "DATETIME_PARTITIONED"


def test_partitionkind_has_year_month_partitioned():
    """Test PartitionKind has YEAR_MONTH_PARTITIONED attribute"""
    assert hasattr(PartitionKind, "YEAR_MONTH_PARTITIONED")
    assert PartitionKind.YEAR_MONTH_PARTITIONED == "YEAR_MONTH_PARTITIONED"


def test_partitionkind_has_hive_partitioned():
    """Test PartitionKind has HIVE_PARTITIONED attribute"""
    assert hasattr(PartitionKind, "HIVE_PARTITIONED")
    assert PartitionKind.HIVE_PARTITIONED == "HIVE_PARTITIONED"


def test_partitionkind_has_snapshot_partitioned():
    """Test PartitionKind has SNAPSHOT_PARTITIONED attribute"""
    assert hasattr(PartitionKind, "SNAPSHOT_PARTITIONED")
    assert PartitionKind.SNAPSHOT_PARTITIONED == "SNAPSHOT_PARTITIONED"


def test_partitionkind_has_custom_partitioned():
    """Test PartitionKind has CUSTOM_PARTITIONED attribute"""
    assert hasattr(PartitionKind, "CUSTOM_PARTITIONED")
    assert PartitionKind.CUSTOM_PARTITIONED == "CUSTOM_PARTITIONED"


def test_partitionkind_has_seven_members():
    """Test PartitionKind has exactly 7 members"""
    kinds = list(PartitionKind)
    assert len(kinds) == 7


def test_partitionkind_values_are_uppercase():
    """Test all PartitionKind values are uppercase"""
    for kind in PartitionKind:
        assert kind.value == kind.value.upper()


# ==================== from_str() Method Tests ====================


def test_from_str_non_partitioned_exact_case():
    """Test from_str with exact case 'NON_PARTITIONED'"""
    kind = PartitionKind.from_str("NON_PARTITIONED")

    assert kind == PartitionKind.NON_PARTITIONED
    assert isinstance(kind, PartitionKind)


def test_from_str_non_partitioned_lowercase():
    """Test from_str with lowercase 'non_partitioned'"""
    kind = PartitionKind.from_str("non_partitioned")

    assert kind == PartitionKind.NON_PARTITIONED


def test_from_str_non_partitioned_mixed_case():
    """Test from_str with mixed case 'Non_Partitioned'"""
    kind = PartitionKind.from_str("Non_Partitioned")

    assert kind == PartitionKind.NON_PARTITIONED


def test_from_str_date_partitioned():
    """Test from_str with 'date_partitioned'"""
    kind = PartitionKind.from_str("date_partitioned")

    assert kind == PartitionKind.DATE_PARTITIONED


def test_from_str_datetime_partitioned():
    """Test from_str with 'DATETIME_PARTITIONED'"""
    kind = PartitionKind.from_str("DATETIME_PARTITIONED")

    assert kind == PartitionKind.DATETIME_PARTITIONED


def test_from_str_year_month_partitioned():
    """Test from_str with 'year_month_partitioned'"""
    kind = PartitionKind.from_str("year_month_partitioned")

    assert kind == PartitionKind.YEAR_MONTH_PARTITIONED


def test_from_str_hive_partitioned():
    """Test from_str with 'hive_partitioned'"""
    kind = PartitionKind.from_str("hive_partitioned")

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_str_snapshot_partitioned():
    """Test from_str with 'snapshot_partitioned'"""
    kind = PartitionKind.from_str("snapshot_partitioned")

    assert kind == PartitionKind.SNAPSHOT_PARTITIONED


def test_from_str_custom_partitioned():
    """Test from_str with 'custom_partitioned'"""
    kind = PartitionKind.from_str("custom_partitioned")

    assert kind == PartitionKind.CUSTOM_PARTITIONED


def test_from_str_invalid_value():
    """Test from_str with invalid value raises ValueError"""
    with pytest.raises(ValueError, match="Unknown PartitionKind"):
        PartitionKind.from_str("invalid_partition_kind")


def test_from_str_empty_string():
    """Test from_str with empty string raises ValueError"""
    with pytest.raises(ValueError, match="Unknown PartitionKind"):
        PartitionKind.from_str("")


def test_from_str_is_case_insensitive():
    """Test from_str is case insensitive for all values"""
    for kind in PartitionKind:
        # Test lowercase
        result_lower = PartitionKind.from_str(kind.value.lower())
        assert result_lower == kind

        # Test uppercase
        result_upper = PartitionKind.from_str(kind.value.upper())
        assert result_upper == kind

        # Test mixed case
        result_title = PartitionKind.from_str(kind.value.title())
        assert result_title == kind


# ==================== from_any() Method Tests ====================


def test_from_any_with_partitionkind_enum():
    """Test from_any with PartitionKind enum value"""
    kind = PartitionKind.from_any(PartitionKind.DATE_PARTITIONED)

    assert kind == PartitionKind.DATE_PARTITIONED
    assert isinstance(kind, PartitionKind)


def test_from_any_with_string():
    """Test from_any with string value"""
    kind = PartitionKind.from_any("hive_partitioned")

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_any_with_uppercase_string():
    """Test from_any with uppercase string"""
    kind = PartitionKind.from_any("SNAPSHOT_PARTITIONED")

    assert kind == PartitionKind.SNAPSHOT_PARTITIONED


def test_from_any_with_all_enum_values():
    """Test from_any with all enum values returns same"""
    for kind in PartitionKind:
        result = PartitionKind.from_any(kind)
        assert result == kind
        assert result is kind


def test_from_any_with_all_string_values():
    """Test from_any with all string values"""
    for kind in PartitionKind:
        result = PartitionKind.from_any(kind.value)
        assert result == kind


def test_from_any_with_invalid_string():
    """Test from_any with invalid string raises ValueError"""
    with pytest.raises(ValueError, match="Unknown PartitionKind"):
        PartitionKind.from_any("invalid_kind")


# ==================== from_partition_fields() Method Tests ====================


def test_from_partition_fields_empty_list():
    """Test from_partition_fields with empty list returns NON_PARTITIONED"""
    kind = PartitionKind.from_partition_fields([])

    assert kind == PartitionKind.NON_PARTITIONED


def test_from_partition_fields_single_date():
    """Test from_partition_fields with ['date'] returns DATE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["date"])

    assert kind == PartitionKind.DATE_PARTITIONED


def test_from_partition_fields_single_date_uppercase():
    """Test from_partition_fields with ['DATE'] returns DATE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["DATE"])

    assert kind == PartitionKind.DATE_PARTITIONED


def test_from_partition_fields_single_date_mixed_case():
    """Test from_partition_fields with ['Date'] returns DATE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["Date"])

    assert kind == PartitionKind.DATE_PARTITIONED


def test_from_partition_fields_single_datetime():
    """Test from_partition_fields with ['datetime'] returns DATETIME_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["datetime"])

    assert kind == PartitionKind.DATETIME_PARTITIONED


def test_from_partition_fields_single_datetime_uppercase():
    """Test from_partition_fields with ['DATETIME'] returns DATETIME_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["DATETIME"])

    assert kind == PartitionKind.DATETIME_PARTITIONED


def test_from_partition_fields_single_snapshotdate():
    """Test from_partition_fields with ['snapshotdate'] returns SNAPSHOT_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["snapshotdate"])

    assert kind == PartitionKind.SNAPSHOT_PARTITIONED


def test_from_partition_fields_single_snapshotdate_uppercase():
    """Test from_partition_fields with ['SNAPSHOTDATE'] returns SNAPSHOT_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["SNAPSHOTDATE"])

    assert kind == PartitionKind.SNAPSHOT_PARTITIONED


def test_from_partition_fields_year_month():
    """Test from_partition_fields with ['year', 'month'] returns YEAR_MONTH_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["year", "month"])

    assert kind == PartitionKind.YEAR_MONTH_PARTITIONED


def test_from_partition_fields_year_month_uppercase():
    """Test from_partition_fields with ['YEAR', 'MONTH'] returns YEAR_MONTH_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["YEAR", "MONTH"])

    assert kind == PartitionKind.YEAR_MONTH_PARTITIONED


def test_from_partition_fields_month_year_order():
    """Test from_partition_fields with ['month', 'year'] returns YEAR_MONTH_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["month", "year"])

    assert kind == PartitionKind.YEAR_MONTH_PARTITIONED


def test_from_partition_fields_year_month_day():
    """Test from_partition_fields with ['year', 'month', 'day'] returns HIVE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["year", "month", "day"])

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_partition_fields_year_only():
    """Test from_partition_fields with ['year'] returns HIVE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["year"])

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_partition_fields_month_only():
    """Test from_partition_fields with ['month'] returns HIVE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["month"])

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_partition_fields_day_only():
    """Test from_partition_fields with ['day'] returns HIVE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["day"])

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_partition_fields_hour_only():
    """Test from_partition_fields with ['hour'] returns HIVE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["hour"])

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_partition_fields_year_month_day_hour():
    """Test from_partition_fields with ['year', 'month', 'day', 'hour'] returns HIVE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["year", "month", "day", "hour"])

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_partition_fields_custom_single_field():
    """Test from_partition_fields with custom single field returns CUSTOM_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["region"])

    assert kind == PartitionKind.CUSTOM_PARTITIONED


def test_from_partition_fields_custom_multiple_fields():
    """Test from_partition_fields with custom multiple fields returns CUSTOM_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["region", "country"])

    assert kind == PartitionKind.CUSTOM_PARTITIONED


def test_from_partition_fields_mixed_hive_and_custom():
    """Test from_partition_fields with year and custom field returns HIVE_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["year", "region"])

    assert kind == PartitionKind.HIVE_PARTITIONED


def test_from_partition_fields_three_custom_fields():
    """Test from_partition_fields with three custom fields returns CUSTOM_PARTITIONED"""
    kind = PartitionKind.from_partition_fields(["category", "product", "version"])

    assert kind == PartitionKind.CUSTOM_PARTITIONED


def test_from_partition_fields_hive_fields_mixed_case():
    """Test from_partition_fields with mixed case hive fields"""
    kind = PartitionKind.from_partition_fields(["Year", "Month", "Day"])

    assert kind == PartitionKind.HIVE_PARTITIONED


# ==================== list_all() Method Tests ====================


def test_list_all_returns_list():
    """Test list_all returns a list"""
    kinds = PartitionKind.list_all()

    assert isinstance(kinds, list)


def test_list_all_returns_all_kinds():
    """Test list_all returns all partition kinds"""
    kinds = PartitionKind.list_all()

    assert len(kinds) == 7
    assert PartitionKind.NON_PARTITIONED in kinds
    assert PartitionKind.DATE_PARTITIONED in kinds
    assert PartitionKind.DATETIME_PARTITIONED in kinds
    assert PartitionKind.YEAR_MONTH_PARTITIONED in kinds
    assert PartitionKind.HIVE_PARTITIONED in kinds
    assert PartitionKind.SNAPSHOT_PARTITIONED in kinds
    assert PartitionKind.CUSTOM_PARTITIONED in kinds


def test_list_all_returns_partitionkind_instances():
    """Test list_all returns PartitionKind instances"""
    kinds = PartitionKind.list_all()

    for kind in kinds:
        assert isinstance(kind, PartitionKind)


def test_list_all_same_as_iteration():
    """Test list_all returns same elements as iteration"""
    kinds_list = PartitionKind.list_all()
    kinds_iter = list(PartitionKind)

    assert kinds_list == kinds_iter


# ==================== __str__() Method Tests ====================


def test_str_non_partitioned():
    """Test __str__ for NON_PARTITIONED"""
    kind = PartitionKind.NON_PARTITIONED
    result = str(kind)

    assert result == "NON_PARTITIONED"


def test_str_date_partitioned():
    """Test __str__ for DATE_PARTITIONED"""
    kind = PartitionKind.DATE_PARTITIONED
    result = str(kind)

    assert result == "DATE_PARTITIONED"


def test_str_all_kinds():
    """Test __str__ for all partition kinds returns value"""
    for kind in PartitionKind:
        result = str(kind)
        assert result == kind.value


# ==================== __repr__() Method Tests ====================


def test_repr_non_partitioned():
    """Test __repr__ for NON_PARTITIONED"""
    kind = PartitionKind.NON_PARTITIONED
    result = repr(kind)

    assert result == "PartitionKind.NON_PARTITIONED"


def test_repr_date_partitioned():
    """Test __repr__ for DATE_PARTITIONED"""
    kind = PartitionKind.DATE_PARTITIONED
    result = repr(kind)

    assert result == "PartitionKind.DATE_PARTITIONED"


def test_repr_all_kinds():
    """Test __repr__ for all partition kinds"""
    for kind in PartitionKind:
        result = repr(kind)
        assert result == f"PartitionKind.{kind.name}"


def test_repr_format():
    """Test __repr__ follows expected format"""
    for kind in PartitionKind:
        result = repr(kind)
        assert result.startswith("PartitionKind.")
        assert kind.name in result


# ==================== Edge Cases and Integration Tests ====================


def test_partitionkind_enum_comparison():
    """Test PartitionKind enum comparison"""
    kind1 = PartitionKind.DATE_PARTITIONED
    kind2 = PartitionKind.DATE_PARTITIONED
    kind3 = PartitionKind.HIVE_PARTITIONED

    assert kind1 == kind2
    assert kind1 is kind2
    assert kind1 != kind3


def test_partitionkind_string_comparison():
    """Test PartitionKind can be compared with string"""
    kind = PartitionKind.DATE_PARTITIONED

    assert kind == "DATE_PARTITIONED"
    assert kind != "HIVE_PARTITIONED"


def test_partitionkind_in_set():
    """Test PartitionKind can be used in sets"""
    kinds = {PartitionKind.DATE_PARTITIONED, PartitionKind.HIVE_PARTITIONED}

    assert PartitionKind.DATE_PARTITIONED in kinds
    assert PartitionKind.CUSTOM_PARTITIONED not in kinds


def test_partitionkind_as_dict_key():
    """Test PartitionKind can be used as dictionary key"""
    mapping = {
        PartitionKind.DATE_PARTITIONED: "date",
        PartitionKind.HIVE_PARTITIONED: "hive",
    }

    assert mapping[PartitionKind.DATE_PARTITIONED] == "date"
    assert mapping[PartitionKind.HIVE_PARTITIONED] == "hive"


def test_partitionkind_from_str_roundtrip():
    """Test from_str and value roundtrip"""
    for kind in PartitionKind:
        result = PartitionKind.from_str(kind.value)
        assert result == kind


def test_partitionkind_from_any_roundtrip_with_enum():
    """Test from_any roundtrip with enum"""
    for kind in PartitionKind:
        result = PartitionKind.from_any(kind)
        assert result == kind
        assert result is kind


def test_partitionkind_from_any_roundtrip_with_string():
    """Test from_any roundtrip with string"""
    for kind in PartitionKind:
        result = PartitionKind.from_any(kind.value)
        assert result == kind


def test_from_partition_fields_inference_comprehensive():
    """Test comprehensive partition field inference"""
    test_cases = [
        ([], PartitionKind.NON_PARTITIONED),
        (["date"], PartitionKind.DATE_PARTITIONED),
        (["datetime"], PartitionKind.DATETIME_PARTITIONED),
        (["snapshotdate"], PartitionKind.SNAPSHOT_PARTITIONED),
        (["year", "month"], PartitionKind.YEAR_MONTH_PARTITIONED),
        (["month", "year"], PartitionKind.YEAR_MONTH_PARTITIONED),
        (["year"], PartitionKind.HIVE_PARTITIONED),
        (["month"], PartitionKind.HIVE_PARTITIONED),
        (["day"], PartitionKind.HIVE_PARTITIONED),
        (["hour"], PartitionKind.HIVE_PARTITIONED),
        (["year", "month", "day"], PartitionKind.HIVE_PARTITIONED),
        (["year", "month", "day", "hour"], PartitionKind.HIVE_PARTITIONED),
        (["region"], PartitionKind.CUSTOM_PARTITIONED),
        (["category", "product"], PartitionKind.CUSTOM_PARTITIONED),
        (["year", "region"], PartitionKind.HIVE_PARTITIONED),
    ]

    for fields, expected in test_cases:
        result = PartitionKind.from_partition_fields(fields)
        assert result == expected, f"Failed for {fields}: got {result}, expected {expected}"

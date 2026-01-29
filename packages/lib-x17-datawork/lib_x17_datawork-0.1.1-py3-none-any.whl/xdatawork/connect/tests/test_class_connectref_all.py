import tempfile

import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef

# ==================== Initialization Tests ====================


def test_connectref_init_with_location_only():
    """Test ConnectRef initialization with location only"""
    ref = ConnectRef(location="s3://bucket/key")

    assert ref.location == "s3://bucket/key"
    assert ref.kind is None


def test_connectref_init_with_location_and_kind():
    """Test ConnectRef initialization with location and kind"""
    ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)

    assert ref.location == "s3://bucket/key"
    assert ref.kind == ConnectKind.S3


def test_connectref_init_with_string_kind():
    """Test ConnectRef initialization with string kind"""
    ref = ConnectRef(location="/path/to/file", kind="macos")

    assert ref.location == "/path/to/file"
    assert ref.kind == "macos"


def test_connectref_init_with_empty_location():
    """Test ConnectRef with empty location"""
    ref = ConnectRef(location="", kind=ConnectKind.S3)

    assert ref.location == ""
    assert ref.kind == ConnectKind.S3


# ==================== from_dict() Method Tests ====================


def test_from_dict_with_location_only():
    """Test from_dict with location only"""
    data = {"location": "s3://bucket/path"}
    ref = ConnectRef.from_dict(data)

    assert ref.location == "s3://bucket/path"
    assert ref.kind is None


def test_from_dict_with_location_and_kind():
    """Test from_dict with location and kind"""
    data = {"location": "s3://bucket/path", "kind": "s3"}
    ref = ConnectRef.from_dict(data)

    assert ref.location == "s3://bucket/path"
    assert ref.kind == ConnectKind.S3


def test_from_dict_with_kind_enum():
    """Test from_dict with ConnectKind enum"""
    data = {"location": "/path", "kind": ConnectKind.MACOS}
    ref = ConnectRef.from_dict(data)

    assert ref.location == "/path"
    assert ref.kind == ConnectKind.MACOS


def test_from_dict_missing_location():
    """Test from_dict raises KeyError when location is missing"""
    data = {"kind": "s3"}

    with pytest.raises(KeyError, match="'location' is required"):
        ConnectRef.from_dict(data)


def test_from_dict_with_none_kind():
    """Test from_dict with None kind"""
    data = {"location": "s3://bucket/key", "kind": None}
    ref = ConnectRef.from_dict(data)

    assert ref.location == "s3://bucket/key"
    assert ref.kind is None


def test_from_dict_with_invalid_kind():
    """Test from_dict with invalid kind raises error"""
    data = {"location": "s3://bucket/key", "kind": "invalid"}

    with pytest.raises(ValueError, match="Unknown ConnectKind"):
        ConnectRef.from_dict(data)


def test_from_dict_with_extra_fields():
    """Test from_dict ignores extra fields"""
    data = {"location": "s3://bucket", "kind": "s3", "extra": "ignored"}
    ref = ConnectRef.from_dict(data)

    assert ref.location == "s3://bucket"
    assert ref.kind == ConnectKind.S3


# ==================== to_dict() Method Tests ====================


def test_to_dict_with_location_only():
    """Test to_dict with location only"""
    ref = ConnectRef(location="s3://bucket/key", kind=None)
    result = ref.to_dict()

    assert result["location"] == "s3://bucket/key"
    assert result["kind"] is None
    assert result["partitions"] == {}
    assert result["is_partitioned"] is False


def test_to_dict_with_location_and_kind():
    """Test to_dict with location and kind"""
    ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    result = ref.to_dict()

    assert result["location"] == "s3://bucket/key"
    assert result["kind"] == "s3"
    assert result["partitions"] == {}
    assert result["is_partitioned"] is False


def test_to_dict_returns_dict():
    """Test to_dict returns a dictionary"""
    ref = ConnectRef(location="/path", kind=ConnectKind.MACOS)
    result = ref.to_dict()

    assert isinstance(result, dict)


def test_to_dict_roundtrip():
    """Test from_dict and to_dict roundtrip"""
    original = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    data = original.to_dict()
    restored = ConnectRef.from_dict(data)

    assert restored.location == original.location
    assert restored.kind == original.kind


# ==================== describe() Method Tests ====================


def test_describe_with_location_only():
    """Test describe with location only"""
    ref = ConnectRef(location="s3://bucket/key", kind=None)
    result = ref.describe()

    assert result["location"] == "s3://bucket/key"
    assert result["is_partitioned"] == "False"
    assert "kind" not in result  # kind is None so not included


def test_describe_with_location_and_kind():
    """Test describe with location and kind"""
    ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    result = ref.describe()

    assert result["location"] == "s3://bucket/key"
    assert result["kind"] == "s3"
    assert result["is_partitioned"] == "False"


def test_describe_returns_dict():
    """Test describe returns a dictionary"""
    ref = ConnectRef(location="/path", kind=ConnectKind.MACOS)
    result = ref.describe()

    assert isinstance(result, dict)


# ==================== to() Method Tests ====================


def test_to_with_relative_path():
    """Test to() method with relative path"""
    with tempfile.TemporaryDirectory():
        ref = ConnectRef(location="s3://bucket/base", kind=ConnectKind.S3)
        result = ref.to("subdir/file.txt")

        assert result.location == "s3://bucket/base/subdir/file.txt"
        assert result.kind == ConnectKind.S3


def test_to_removes_trailing_slash():
    """Test to() removes trailing slash from base"""
    ref = ConnectRef(location="s3://bucket/base/", kind=ConnectKind.S3)
    result = ref.to("file.txt")

    assert result.location == "s3://bucket/base/file.txt"


def test_to_removes_leading_slash():
    """Test to() removes leading slash from relative path"""
    ref = ConnectRef(location="s3://bucket/base", kind=ConnectKind.S3)
    result = ref.to("/subdir/file.txt")

    assert result.location == "s3://bucket/base/subdir/file.txt"


def test_to_with_both_slashes():
    """Test to() handles both trailing and leading slashes"""
    ref = ConnectRef(location="s3://bucket/base/", kind=ConnectKind.S3)
    result = ref.to("/file.txt")

    assert result.location == "s3://bucket/base/file.txt"


def test_to_preserves_kind():
    """Test to() preserves kind"""
    ref = ConnectRef(location="/path", kind=ConnectKind.MACOS)
    result = ref.to("subdir")

    assert result.kind == ConnectKind.MACOS


def test_to_returns_new_instance():
    """Test to() returns a new ConnectRef instance"""
    ref = ConnectRef(location="s3://bucket", kind=ConnectKind.S3)
    result = ref.to("file.txt")

    assert result is not ref
    assert isinstance(result, ConnectRef)


def test_to_with_empty_relative():
    """Test to() with empty string"""
    ref = ConnectRef(location="s3://bucket/base", kind=ConnectKind.S3)
    result = ref.to("")

    assert result.location == "s3://bucket/base/"


def test_to_chaining():
    """Test chaining to() calls"""
    ref = ConnectRef(location="s3://bucket", kind=ConnectKind.S3)
    result = ref.to("dir1").to("dir2").to("file.txt")

    assert result.location == "s3://bucket/dir1/dir2/file.txt"


# ==================== Equality Tests ====================


def test_equality_same_values():
    """Test equality with same values"""
    ref1 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)

    assert ref1 == ref2


def test_equality_different_location():
    """Test inequality with different location"""
    ref1 = ConnectRef(location="s3://bucket/key1", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="s3://bucket/key2", kind=ConnectKind.S3)

    assert ref1 != ref2


def test_equality_different_kind():
    """Test inequality with different kind"""
    ref1 = ConnectRef(location="/path", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="/path", kind=ConnectKind.MACOS)

    assert ref1 != ref2


def test_equality_with_none_kind():
    """Test equality when kind is None"""
    ref1 = ConnectRef(location="s3://bucket/key", kind=None)
    ref2 = ConnectRef(location="s3://bucket/key", kind=None)

    assert ref1 == ref2


def test_equality_one_none_kind():
    """Test inequality when one kind is None"""
    ref1 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="s3://bucket/key", kind=None)

    assert ref1 != ref2


def test_equality_with_different_type():
    """Test inequality with different type returns NotImplemented"""
    ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)

    assert ref != "s3://bucket/key"
    assert ref != {"location": "s3://bucket/key"}


# ==================== Hash Tests ====================


def test_hash_same_values():
    """Test hash is same for equal objects"""
    ref1 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)

    assert hash(ref1) == hash(ref2)


def test_hash_different_location():
    """Test hash differs for different location"""
    ref1 = ConnectRef(location="s3://bucket/key1", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="s3://bucket/key2", kind=ConnectKind.S3)

    assert hash(ref1) != hash(ref2)


def test_hash_in_set():
    """Test ConnectRef can be used in set"""
    ref1 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    ref3 = ConnectRef(location="s3://bucket/other", kind=ConnectKind.S3)

    ref_set = {ref1, ref2, ref3}

    assert len(ref_set) == 2
    assert ref1 in ref_set


def test_hash_as_dict_key():
    """Test ConnectRef can be used as dict key"""
    ref1 = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    ref2 = ConnectRef(location="/path", kind=ConnectKind.MACOS)

    ref_dict = {ref1: "value1", ref2: "value2"}

    assert ref_dict[ref1] == "value1"
    assert ref_dict[ref2] == "value2"


# ==================== String Representation Tests ====================


def test_str_representation():
    """Test __str__ returns location"""
    ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)

    assert str(ref) == "s3://bucket/key"


def test_str_without_kind():
    """Test __str__ works without kind"""
    ref = ConnectRef(location="/path/to/file", kind=None)

    assert str(ref) == "/path/to/file"


def test_repr_representation():
    """Test __repr__ representation"""
    ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    result = repr(ref)

    assert "ConnectRef" in result
    assert "s3://bucket/key" in result
    assert "s3" in result or "S3" in result


def test_repr_without_kind():
    """Test __repr__ without kind"""
    ref = ConnectRef(location="/path", kind=None)
    result = repr(ref)

    assert "ConnectRef" in result
    assert "/path" in result


# ==================== Edge Cases ====================


def test_connectref_with_special_characters():
    """Test ConnectRef with special characters in location"""
    ref = ConnectRef(location="s3://bucket/path with spaces/file.txt", kind=ConnectKind.S3)

    assert ref.location == "s3://bucket/path with spaces/file.txt"


def test_connectref_with_unicode():
    """Test ConnectRef with unicode characters"""
    ref = ConnectRef(location="s3://bucket/文件.txt", kind=ConnectKind.S3)

    assert ref.location == "s3://bucket/文件.txt"


def test_connectref_with_query_params():
    """Test ConnectRef with query parameters"""
    ref = ConnectRef(location="s3://bucket/key?version=1", kind=ConnectKind.S3)

    assert ref.location == "s3://bucket/key?version=1"


def test_connectref_immutability():
    """Test ConnectRef attributes are not accidentally immutable"""
    ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)

    ref.location = "new_location"
    assert ref.location == "new_location"


def test_connectref_with_very_long_location():
    """Test ConnectRef with very long location"""
    long_location = "s3://bucket/" + "a" * 1000
    ref = ConnectRef(location=long_location, kind=ConnectKind.S3)

    assert ref.location == long_location
    assert len(ref.location) > 1000


# ==================== Integration Tests ====================


def test_full_workflow():
    """Test full workflow of creating, modifying, and serializing"""
    ref = ConnectRef(location="s3://bucket", kind=ConnectKind.S3)

    ref = ref.to("data").to("file.parquet")
    data = ref.to_dict()
    restored = ConnectRef.from_dict(data)

    assert restored.location == "s3://bucket/data/file.parquet"
    assert restored.kind == ConnectKind.S3


def test_multiple_kinds():
    """Test creating refs with different kinds"""
    s3_ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)
    macos_ref = ConnectRef(location="/Users/user/file", kind=ConnectKind.MACOS)
    any_ref = ConnectRef(location="path/to/file", kind=ConnectKind.ANY)

    assert s3_ref.kind == ConnectKind.S3
    assert macos_ref.kind == ConnectKind.MACOS
    assert any_ref.kind == ConnectKind.ANY


# ==================== Partition Field Parsing Tests ====================


def test_partition_fields_none():
    """Test partition_fields=None results in empty partitions"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=None,
    )

    assert ref.partitions == {}
    assert ref.is_partitioned is False


def test_partition_fields_list():
    """Test partition_fields as list extracts specified partitions"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.partitions == {"year": "2024", "month": "01"}
    assert ref.is_partitioned is True


def test_partition_fields_string_comma_separated():
    """Test partition_fields as comma-separated string"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/month=01/day=15/file.parquet",
        kind=ConnectKind.S3,
        partition_fields="year,month,day",
    )

    assert ref.partitions == {"year": "2024", "month": "01", "day": "15"}
    assert ref.is_partitioned is True


def test_partition_fields_single_string():
    """Test partition_fields as single string"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields="year",
    )

    assert ref.partitions == {"year": "2024"}
    assert ref.is_partitioned is True


def test_partition_fields_with_spaces():
    """Test partition_fields handles spaces in comma-separated string"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields="year, month",
    )

    assert ref.partitions == {"year": "2024", "month": "01"}


def test_partition_fields_empty_list():
    """Test partition_fields as empty list"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=[],
    )

    assert ref.partitions == {}
    assert ref.is_partitioned is False


def test_partition_fields_empty_string():
    """Test partition_fields as empty string"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields="",
    )

    assert ref.partitions == {}
    assert ref.is_partitioned is False


# ==================== Partition Extraction Tests ====================


def test_partition_extraction_basic():
    """Test basic partition extraction from location"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.partitions["year"] == "2024"
    assert ref.partitions["month"] == "01"


def test_partition_extraction_multiple_levels():
    """Test partition extraction with multiple nesting levels"""
    ref = ConnectRef(
        location="s3://bucket/data/year=2024/month=01/day=15/hour=10/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month", "day", "hour"],
    )

    assert ref.partitions == {
        "year": "2024",
        "month": "01",
        "day": "15",
        "hour": "10",
    }


def test_partition_extraction_only_specified_fields():
    """Test only specified partition fields are extracted"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/day=15/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert "year" in ref.partitions
    assert "month" in ref.partitions
    assert "day" not in ref.partitions


def test_partition_extraction_with_quotes():
    """Test partition extraction handles quoted values"""
    ref = ConnectRef(
        location="s3://bucket/year='2024'/month=\"01\"/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.partitions["year"] == "2024"
    assert ref.partitions["month"] == "01"


def test_partition_extraction_no_matching_partitions():
    """Test partition extraction when no partitions match"""
    ref = ConnectRef(
        location="s3://bucket/data/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert "year" in ref.partitions
    assert "month" in ref.partitions
    assert ref.partitions["year"] is None
    assert ref.partitions["month"] is None
    assert ref.is_partitioned is False  # No partitions exist
    assert ref.n_exist_partitions == 0
    assert ref.n_design_partitions == 2


def test_partition_extraction_partial_match():
    """Test partition extraction with partial match"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.partitions == {"year": "2024", "month": None}
    assert ref.is_partitioned is True


def test_partition_extraction_duplicate_keys():
    """Test partition extraction with duplicate keys (last one wins)"""
    ref = ConnectRef(
        location="s3://bucket/year=2023/data/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year"],
    )

    assert ref.partitions["year"] == "2024"


def test_partition_extraction_special_values():
    """Test partition extraction with special character values"""
    ref = ConnectRef(
        location="s3://bucket/region=us-east-1/env=dev_test/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["region", "env"],
    )
    assert ref.partitions["region"] == "us-east-1"
    assert ref.partitions["env"] == "dev_test"


# ==================== Dynamic Partition Attributes Tests ====================


def test_partition_access_via_get_partition():
    """Test partition access via get_partition method"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.get_partition("year") == "2024"
    assert ref.get_partition("month") == "01"
    assert ref.partitions["year"] == "2024"
    assert ref.partitions["month"] == "01"
    assert ref.n_exist_partitions == 2
    assert ref.full_partitioned is True


def test_partitions_empty_without_partition_fields():
    """Test partitions dict is empty when partition_fields is None"""
    ref = ConnectRef(
        location="s3://bucket/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=None,
    )

    assert ref.partitions == {}
    assert ref.n_exist_partitions == 0
    assert ref.n_design_partitions == 0
    assert ref.is_partitioned is False


def test_partitions_partial_match():
    """Test partitions dict includes None for unmatched fields"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.partitions["year"] == "2024"
    assert ref.partitions["month"] is None
    assert ref.n_exist_partitions == 1
    assert ref.n_design_partitions == 2
    assert ref.is_partitioned is True
    assert ref.full_partitioned is False


def test_partitions_multiple_fields():
    """Test multiple partition fields extraction"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/day=15/hour=10/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month", "day", "hour"],
    )

    assert ref.get_partition("year") == "2024"
    assert ref.get_partition("month") == "01"
    assert ref.get_partition("day") == "15"
    assert ref.get_partition("hour") == "10"
    assert ref.n_exist_partitions == 4
    assert ref.n_design_partitions == 4
    assert ref.full_partitioned is True


# ==================== is_partitioned Flag Tests ====================


def test_is_partitioned_true():
    """Test is_partitioned is True when partitions exist"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year"],
    )

    assert ref.is_partitioned is True


def test_is_partitioned_false_no_fields():
    """Test is_partitioned is False when partition_fields is None"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=None,
    )

    assert ref.is_partitioned is False


def test_is_partitioned_false_no_matches():
    """Test is_partitioned is False when no partitions match"""
    ref = ConnectRef(
        location="s3://bucket/data/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.is_partitioned is False  # No existing partitions
    assert ref.n_exist_partitions == 0
    assert ref.n_design_partitions == 2


def test_is_partitioned_with_multiple_partitions():
    """Test is_partitioned with multiple partitions"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/day=15/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month", "day"],
    )

    assert ref.is_partitioned is True


# ==================== list_partition_fields() Method Tests ====================


def test_list_partition_fields_with_partitions():
    """Test list_partition_fields returns list of partition keys"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    fields = ref.list_partition_fields()
    assert isinstance(fields, list)
    assert set(fields) == {"year", "month"}


def test_list_partition_fields_empty():
    """Test list_partition_fields returns empty list when no partitions"""
    ref = ConnectRef(
        location="s3://bucket/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=None,
    )

    fields = ref.list_partition_fields()
    assert fields == []


def test_list_partition_fields_single():
    """Test list_partition_fields with single partition"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year"],
    )

    fields = ref.list_partition_fields()
    assert fields == ["year"]


def test_list_partition_fields_order():
    """Test list_partition_fields maintains order"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/day=15/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month", "day"],
    )

    fields = ref.list_partition_fields()
    assert len(fields) == 3
    assert "year" in fields
    assert "month" in fields
    assert "day" in fields


# ==================== get_partition() Method Tests ====================


def test_get_partition_existing_field():
    """Test get_partition returns value for existing field"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.get_partition("year") == "2024"
    assert ref.get_partition("month") == "01"


def test_get_partition_missing_field_returns_none():
    """Test get_partition returns None for missing field"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year"],
    )

    assert ref.get_partition("month") is None


def test_get_partition_with_default():
    """Test get_partition returns default for missing field"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year"],
    )

    assert ref.get_partition("month", default="01") == "01"


def test_get_partition_default_not_used_when_exists():
    """Test get_partition doesn't use default when field exists"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=02/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    assert ref.get_partition("month", default="01") == "02"


def test_get_partition_no_partitions():
    """Test get_partition when no partitions"""
    ref = ConnectRef(
        location="s3://bucket/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=None,
    )

    assert ref.get_partition("year") is None
    assert ref.get_partition("year", default="2024") == "2024"


# ==================== Partition Integration Tests ====================


def test_partition_with_to_method():
    """Test partitions work with to() method"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    new_ref = ref.to("day=15/file.parquet")

    # Original ref still has partitions
    assert ref.partitions == {"year": "2024", "month": "01"}

    # New ref preserves partition_fields and extracts new partitions
    assert new_ref.partitions == {"year": "2024", "month": "01"}
    assert new_ref.location == "s3://bucket/year=2024/month=01/day=15/file.parquet"


def test_partition_equality():
    """Test equality considers partitions"""
    ref1 = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year"],
    )
    ref2 = ConnectRef(
        location="s3://bucket/year=2024/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=None,
    )

    # They are NOT equal because partitions differ
    assert ref1 != ref2
    assert ref1.partitions == {"year": "2024"}
    assert ref2.partitions == {}


def test_partition_repr():
    """Test __repr__ includes partitions"""
    ref = ConnectRef(
        location="s3://bucket/year=2024/month=01/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month"],
    )

    result = repr(ref)
    assert "partitions" in result
    assert "year" in result or "2024" in result


def test_partition_macos_path():
    """Test partitions work with MacOS paths"""
    ref = ConnectRef(
        location="/Users/data/year=2024/month=01/file.parquet",
        kind=ConnectKind.MACOS,
        partition_fields=["year", "month"],
    )

    assert ref.partitions == {"year": "2024", "month": "01"}
    assert ref.is_partitioned is True


def test_partition_complex_location():
    """Test partitions with complex location patterns"""
    ref = ConnectRef(
        location="s3://bucket/data/raw/year=2024/month=01/day=15/region=us-east-1/file.parquet",
        kind=ConnectKind.S3,
        partition_fields=["year", "month", "day", "region"],
    )

    assert ref.get_partition("year") == "2024"
    assert ref.get_partition("month") == "01"
    assert ref.get_partition("day") == "15"
    assert ref.get_partition("region") == "us-east-1"
    assert len(ref.list_partition_fields()) == 4
    assert ref.full_partitioned is True
    assert ref.n_exist_partitions == 4

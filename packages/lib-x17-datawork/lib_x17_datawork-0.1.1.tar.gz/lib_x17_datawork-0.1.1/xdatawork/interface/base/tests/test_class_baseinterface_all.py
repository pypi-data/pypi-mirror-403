import pytest

from xdatawork.artifact.artifact import Artifact
from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.interface import BaseInterface
from xdatawork.interface.base.partitionkind import PartitionKind

# ==================== Mock Connect Implementation ====================


class MockConnect:
    """Mock implementation of ConnectLike for testing"""

    def __init__(self, kind: ConnectKind = ConnectKind.S3):
        self.kind = kind
        self._storage: dict[str, bytes] = {}

    def get_object(self, location: str, **kwargs) -> bytes:
        return self._storage.get(location, b"mock data")

    def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
        self._storage[location] = data
        return ConnectRef(location=location, kind=self.kind)

    def list_objects(
        self,
        location: str | ConnectRefLike,
        level: int | None = None,
        pattern: str | None = None,
        **kwargs,
    ) -> list[ConnectRef]:
        """Mock list_objects that returns predictable refs"""
        base_loc = location if isinstance(location, str) else location.location
        return [
            ConnectRef(location=f"{base_loc}/file1.txt", kind=self.kind),
            ConnectRef(location=f"{base_loc}/file2.txt", kind=self.kind),
        ]


# ==================== Initialization Tests ====================


def test_baseinterface_init_with_minimal_args():
    """Test BaseInterface initialization with minimal required arguments"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)

    assert interface.ref == ref
    assert interface.connect == connect
    assert interface.parent is None
    assert interface.partition_fields == []
    assert interface.partition_kind == PartitionKind.NON_PARTITIONED


def test_baseinterface_init_with_dict_ref():
    """Test BaseInterface initialization with dict ref"""
    connect = MockConnect()
    ref_dict = {"location": "s3://bucket/data"}

    interface = BaseInterface(ref=ref_dict, connect=connect)

    assert interface.ref.location == "s3://bucket/data"
    assert interface.connect == connect


def test_baseinterface_init_with_partition_fields_list():
    """Test BaseInterface initialization with partition_fields as list"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month"])

    assert interface.partition_fields == ["year", "month"]
    assert interface.partition_kind == PartitionKind.YEAR_MONTH_PARTITIONED


def test_baseinterface_init_with_partition_fields_string():
    """Test BaseInterface initialization with partition_fields as string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields="year,month,day")

    assert interface.partition_fields == ["year", "month", "day"]
    assert interface.partition_kind == PartitionKind.HIVE_PARTITIONED


def test_baseinterface_init_with_partition_fields_string_with_spaces():
    """Test BaseInterface initialization with partition_fields string with spaces"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields="year, month, day")

    assert interface.partition_fields == ["year", "month", "day"]
    assert interface.partition_kind == PartitionKind.HIVE_PARTITIONED


def test_baseinterface_init_with_single_partition_field_string():
    """Test BaseInterface initialization with single partition field string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields="date")

    assert interface.partition_fields == ["date"]
    assert interface.partition_kind == PartitionKind.DATE_PARTITIONED


def test_baseinterface_init_with_parent():
    """Test BaseInterface initialization with parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, parent=parent)

    assert child.parent == parent
    assert child.connect == connect  # Inherited from parent


def test_baseinterface_init_child_inherits_connect_from_parent():
    """Test child interface inherits connect from parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, parent=parent)

    assert child.connect is parent.connect


def test_baseinterface_init_child_can_override_connect():
    """Test child interface can override parent's connect"""
    parent_connect = MockConnect(ConnectKind.S3)
    child_connect = MockConnect(ConnectKind.MACOS)

    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=parent_connect)

    child_ref = ConnectRef(location="/local/child")
    child = BaseInterface(ref=child_ref, connect=child_connect, parent=parent)

    assert child.connect is child_connect
    assert child.connect is not parent.connect


# ==================== _resolve_parent() Tests ====================


def test_resolve_parent_with_none():
    """Test _resolve_parent with None returns None"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, parent=None)

    assert interface.parent is None


def test_resolve_parent_with_valid_parent():
    """Test _resolve_parent with valid parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, parent=parent, connect=connect)

    assert child.parent is parent


def test_resolve_parent_with_invalid_type():
    """Test _resolve_parent with invalid type raises TypeError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(TypeError, match="Invalid parent.*must be BaseInterface"):
        BaseInterface(ref=ref, connect=connect, parent="invalid")


def test_resolve_parent_with_dict():
    """Test _resolve_parent with dict raises TypeError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(TypeError, match="Invalid parent.*must be BaseInterface"):
        BaseInterface(ref=ref, connect=connect, parent={"location": "s3://bucket/parent"})


# ==================== _resolve_ref() Tests ====================


def test_resolve_ref_with_connectref():
    """Test _resolve_ref with ConnectRef instance"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = BaseInterface(ref=ref, connect=connect)

    assert interface.ref is ref


def test_resolve_ref_with_dict():
    """Test _resolve_ref with dictionary"""
    connect = MockConnect()
    ref_dict = {"location": "s3://bucket/data", "kind": "s3"}

    interface = BaseInterface(ref=ref_dict, connect=connect)

    assert interface.ref.location == "s3://bucket/data"
    assert interface.ref.kind == ConnectKind.S3


def test_resolve_ref_with_none():
    """Test _resolve_ref with None raises ValueError"""
    connect = MockConnect()

    with pytest.raises(ValueError, match="ref cannot be None"):
        BaseInterface(ref=None, connect=connect)


def test_resolve_ref_with_invalid_type():
    """Test _resolve_ref with invalid type raises TypeError"""
    connect = MockConnect()

    with pytest.raises(TypeError, match="Invalid ref.*expected ConnectRefLike or dict"):
        BaseInterface(ref="s3://bucket/data", connect=connect)


def test_resolve_ref_with_integer():
    """Test _resolve_ref with integer raises TypeError"""
    connect = MockConnect()

    with pytest.raises(TypeError, match="Invalid ref.*expected ConnectRefLike or dict"):
        BaseInterface(ref=123, connect=connect)


# ==================== _resolve_connect() Tests ====================


def test_resolve_connect_with_valid_connect():
    """Test _resolve_connect with valid ConnectLike"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)

    assert interface.connect is connect


def test_resolve_connect_with_none_and_no_parent():
    """Test _resolve_connect with None and no parent raises ValueError"""
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(ValueError, match="connect cannot be None if parent is None"):
        BaseInterface(ref=ref, connect=None, parent=None)


def test_resolve_connect_with_none_and_parent():
    """Test _resolve_connect with None but parent exists uses parent's connect"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, connect=None, parent=parent)

    assert child.connect is parent.connect


def test_resolve_connect_with_invalid_type():
    """Test _resolve_connect with invalid type raises TypeError"""
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(TypeError, match="Invalid connect.*expected ConnectLike"):
        BaseInterface(ref=ref, connect="invalid")


def test_resolve_connect_with_dict():
    """Test _resolve_connect with dict raises TypeError"""
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(TypeError, match="Invalid connect.*expected ConnectLike"):
        BaseInterface(ref=ref, connect={"kind": "s3"})


# ==================== _resolve_partition_fields() Tests ====================


def test_resolve_partition_fields_with_none():
    """Test _resolve_partition_fields with None returns empty list"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=None)

    assert interface.partition_fields == []


def test_resolve_partition_fields_with_empty_list():
    """Test _resolve_partition_fields with empty list"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=[])

    assert interface.partition_fields == []


def test_resolve_partition_fields_with_list():
    """Test _resolve_partition_fields with list"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month"])

    assert interface.partition_fields == ["year", "month"]


def test_resolve_partition_fields_with_string():
    """Test _resolve_partition_fields with comma-separated string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields="year,month,day")

    assert interface.partition_fields == ["year", "month", "day"]


def test_resolve_partition_fields_with_string_with_spaces():
    """Test _resolve_partition_fields with string with spaces"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields="  year  ,  month  ,  day  ")

    assert interface.partition_fields == ["year", "month", "day"]


def test_resolve_partition_fields_with_empty_string():
    """Test _resolve_partition_fields with empty string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields="")

    assert interface.partition_fields == []


def test_resolve_partition_fields_with_string_only_commas():
    """Test _resolve_partition_fields with string containing only commas"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=",,,")

    assert interface.partition_fields == []


def test_resolve_partition_fields_with_list_of_ints():
    """Test _resolve_partition_fields with list of integers converts to strings"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=[1, 2, 3])

    assert interface.partition_fields == ["1", "2", "3"]


def test_resolve_partition_fields_with_invalid_type():
    """Test _resolve_partition_fields with invalid type raises TypeError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(TypeError, match="Partition fields expects list\\[str\\] or str"):
        BaseInterface(ref=ref, connect=connect, partition_fields=123)


def test_resolve_partition_fields_with_dict():
    """Test _resolve_partition_fields with dict raises TypeError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(TypeError, match="Partition fields expects list\\[str\\] or str"):
        BaseInterface(ref=ref, connect=connect, partition_fields={"field": "year"})


# ==================== _resolve_partition_kind() Tests ====================


def test_resolve_partition_kind_with_no_fields():
    """Test _resolve_partition_kind with no partition fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)

    assert interface.partition_kind == PartitionKind.NON_PARTITIONED


def test_resolve_partition_kind_with_date_field():
    """Test _resolve_partition_kind with date field"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["date"])

    assert interface.partition_kind == PartitionKind.DATE_PARTITIONED


def test_resolve_partition_kind_with_year_month_fields():
    """Test _resolve_partition_kind with year and month fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month"])

    assert interface.partition_kind == PartitionKind.YEAR_MONTH_PARTITIONED


def test_resolve_partition_kind_with_hive_fields():
    """Test _resolve_partition_kind with hive fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month", "day"])

    assert interface.partition_kind == PartitionKind.HIVE_PARTITIONED


def test_resolve_partition_kind_with_custom_fields():
    """Test _resolve_partition_kind with custom fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["region", "country"])

    assert interface.partition_kind == PartitionKind.CUSTOM_PARTITIONED


# ==================== list_refs() Method Tests ====================


def test_list_refs_with_no_args():
    """Test list_refs with no arguments"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    refs = interface.list_refs()

    assert isinstance(refs, list)
    assert len(refs) == 2
    assert all(isinstance(r, ConnectRef) for r in refs)


def test_list_refs_with_level():
    """Test list_refs with level parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    refs = interface.list_refs(level=1)

    assert isinstance(refs, list)
    assert len(refs) == 2


def test_list_refs_with_pattern():
    """Test list_refs with pattern parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    refs = interface.list_refs(pattern="*.txt")

    assert isinstance(refs, list)
    assert len(refs) == 2


def test_list_refs_with_level_and_pattern():
    """Test list_refs with both level and pattern"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    refs = interface.list_refs(level=1, pattern="*.txt")

    assert isinstance(refs, list)


def test_list_refs_returns_connectref_list():
    """Test list_refs returns list of ConnectRef"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    refs = interface.list_refs()

    for ref_item in refs:
        assert isinstance(ref_item, ConnectRef)


# ==================== list_artifacts() Method Tests ====================


def test_list_artifacts_with_no_args():
    """Test list_artifacts with no arguments"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    artifacts = interface.list_artifacts()

    assert isinstance(artifacts, list)
    assert len(artifacts) == 2
    assert all(isinstance(a, Artifact) for a in artifacts)


def test_list_artifacts_with_level():
    """Test list_artifacts with level parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    artifacts = interface.list_artifacts(level=1)

    assert isinstance(artifacts, list)
    assert len(artifacts) == 2


def test_list_artifacts_with_pattern():
    """Test list_artifacts with pattern parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    artifacts = interface.list_artifacts(pattern="*.txt")

    assert isinstance(artifacts, list)


def test_list_artifacts_with_level_and_pattern():
    """Test list_artifacts with both level and pattern"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    artifacts = interface.list_artifacts(level=1, pattern="*.txt")

    assert isinstance(artifacts, list)


def test_list_artifacts_returns_artifact_list():
    """Test list_artifacts returns list of Artifact"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    artifacts = interface.list_artifacts()

    for artifact in artifacts:
        assert isinstance(artifact, Artifact)


def test_list_artifacts_wraps_connectrefs():
    """Test list_artifacts wraps ConnectRefs with Artifacts"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    refs = interface.list_refs()
    artifacts = interface.list_artifacts()

    assert len(artifacts) == len(refs)
    for artifact, ref_item in zip(artifacts, refs):
        assert artifact.ref.location == ref_item.location


# ==================== describe() Method Tests ====================


def test_describe_with_minimal_interface():
    """Test describe with minimal interface"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = BaseInterface(ref=ref, connect=connect)
    description = interface.describe()

    assert isinstance(description, dict)
    assert "ref" in description
    assert "partition_kind" in description
    assert "connect" in description
    assert description["partition_kind"] == "NON_PARTITIONED"
    assert description["connect"] == "s3"


def test_describe_with_partition_fields():
    """Test describe with partition fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month"])
    description = interface.describe()

    assert "partition_fields" in description
    assert description["partition_fields"] == ["year", "month"]
    assert description["partition_kind"] == "YEAR_MONTH_PARTITIONED"


def test_describe_with_parent():
    """Test describe with parent interface"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, parent=parent)

    description = child.describe()

    assert "parent" in description
    assert isinstance(description["parent"], dict)
    assert "ref" in description["parent"]


def test_describe_without_parent():
    """Test describe without parent"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    description = interface.describe()

    assert "parent" not in description


def test_describe_ref_structure():
    """Test describe includes ref structure"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = BaseInterface(ref=ref, connect=connect)
    description = interface.describe()

    assert "ref" in description
    assert isinstance(description["ref"], dict)
    assert "location" in description["ref"]
    assert description["ref"]["location"] == "s3://bucket/data"


# ==================== to_dict() Method Tests ====================


def test_to_dict_with_minimal_interface():
    """Test to_dict with minimal interface"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = BaseInterface(ref=ref, connect=connect)
    result = interface.to_dict()

    assert isinstance(result, dict)
    assert "ref" in result
    assert "partition_fields" in result
    assert "partition_kind" in result
    assert "parent" in result
    assert "connect" in result
    assert result["partition_fields"] == []
    assert result["partition_kind"] == "NON_PARTITIONED"
    assert result["parent"] is None
    assert result["connect"] == "s3"


def test_to_dict_with_partition_fields():
    """Test to_dict with partition fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month"])
    result = interface.to_dict()

    assert result["partition_fields"] == ["year", "month"]
    assert result["partition_kind"] == "YEAR_MONTH_PARTITIONED"


def test_to_dict_with_parent():
    """Test to_dict with parent interface"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, parent=parent)

    result = child.to_dict()

    assert result["parent"] is not None
    assert isinstance(result["parent"], dict)
    assert "ref" in result["parent"]


def test_to_dict_without_parent():
    """Test to_dict without parent returns None"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["parent"] is None


def test_to_dict_ref_structure():
    """Test to_dict includes ref dictionary"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = BaseInterface(ref=ref, connect=connect)
    result = interface.to_dict()

    assert "ref" in result
    assert isinstance(result["ref"], dict)
    assert "location" in result["ref"]
    assert result["ref"]["location"] == "s3://bucket/data"


def test_to_dict_includes_all_required_keys():
    """Test to_dict includes all required keys"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    result = interface.to_dict()

    required_keys = ["ref", "partition_fields", "partition_kind", "parent", "connect"]
    for key in required_keys:
        assert key in result


# ==================== Integration Tests ====================


def test_parent_child_connect_inheritance():
    """Test parent-child connect inheritance"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, parent=parent)

    assert child.connect is parent.connect


def test_grandparent_parent_child_hierarchy():
    """Test three-level hierarchy"""
    connect = MockConnect()

    grandparent_ref = ConnectRef(location="s3://bucket/grandparent")
    grandparent = BaseInterface(ref=grandparent_ref, connect=connect)

    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = BaseInterface(ref=parent_ref, parent=grandparent)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(ref=child_ref, parent=parent)

    assert child.connect is grandparent.connect
    assert parent.connect is grandparent.connect


def test_partition_kind_inference_comprehensive():
    """Test partition kind inference with various field combinations"""
    connect = MockConnect()

    test_cases = [
        ([], PartitionKind.NON_PARTITIONED),
        (["date"], PartitionKind.DATE_PARTITIONED),
        (["datetime"], PartitionKind.DATETIME_PARTITIONED),
        (["snapshotdate"], PartitionKind.SNAPSHOT_PARTITIONED),
        (["year", "month"], PartitionKind.YEAR_MONTH_PARTITIONED),
        (["year", "month", "day"], PartitionKind.HIVE_PARTITIONED),
        (["region", "country"], PartitionKind.CUSTOM_PARTITIONED),
    ]

    for fields, expected_kind in test_cases:
        ref = ConnectRef(location="s3://bucket/data")
        interface = BaseInterface(ref=ref, connect=connect, partition_fields=fields)
        assert interface.partition_kind == expected_kind


def test_interface_with_different_connect_kinds():
    """Test interface with different connect kinds"""
    s3_connect = MockConnect(ConnectKind.S3)
    macos_connect = MockConnect(ConnectKind.MACOS)

    s3_ref = ConnectRef(location="s3://bucket/data")
    s3_interface = BaseInterface(ref=s3_ref, connect=s3_connect)

    macos_ref = ConnectRef(location="/local/data")
    macos_interface = BaseInterface(ref=macos_ref, connect=macos_connect)

    assert s3_interface.connect.kind == ConnectKind.S3
    assert macos_interface.connect.kind == ConnectKind.MACOS


def test_describe_and_to_dict_structure_difference():
    """Test describe and to_dict return different structures"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month"])

    description = interface.describe()
    dict_repr = interface.to_dict()

    # Both should have partition_kind
    assert "partition_kind" in description
    assert "partition_kind" in dict_repr

    # describe includes partition_fields only if not empty
    assert "partition_fields" in description
    assert "partition_fields" in dict_repr

    # to_dict always includes parent key
    assert "parent" in dict_repr


def test_list_artifacts_maintains_connect():
    """Test list_artifacts maintains connect in artifacts"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)
    artifacts = interface.list_artifacts()

    for artifact in artifacts:
        assert artifact.connect is connect


def test_empty_partition_fields_string_variations():
    """Test various empty partition field string variations"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    test_cases = ["", "   ", ",", " , , ", "  ,  ,  "]

    for fields_str in test_cases:
        interface = BaseInterface(ref=ref, connect=connect, partition_fields=fields_str)
        assert interface.partition_fields == []
        assert interface.partition_kind == PartitionKind.NON_PARTITIONED


def test_interface_is_not_none():
    """Test interface object is not None after creation"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect)

    assert interface is not None
    assert isinstance(interface, BaseInterface)


def test_interface_attributes_accessible():
    """Test all interface attributes are accessible"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = BaseInterface(ref=ref, connect=connect, partition_fields=["year", "month"])

    assert hasattr(interface, "ref")
    assert hasattr(interface, "connect")
    assert hasattr(interface, "parent")
    assert hasattr(interface, "partition_fields")
    assert hasattr(interface, "partition_kind")
    assert hasattr(interface, "list_refs")
    assert hasattr(interface, "list_artifacts")
    assert hasattr(interface, "describe")
    assert hasattr(interface, "to_dict")

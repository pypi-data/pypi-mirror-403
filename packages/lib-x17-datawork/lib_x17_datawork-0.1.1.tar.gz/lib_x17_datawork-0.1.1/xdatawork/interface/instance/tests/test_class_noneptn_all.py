import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.partitionkind import PartitionKind
from xdatawork.interface.instance.noneptn import NonePTN

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
            ConnectRef(location=f"{base_loc}/file2.parquet", kind=self.kind),
        ]


# ==================== Initialization Tests ====================


def test_noneptn_init_with_minimal_args():
    """Test NonePTN initialization with minimal required arguments"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert interface.ref == ref
    assert interface.connect == connect
    assert interface.parent is None
    assert interface.partition_fields == []
    assert interface.partition_kind == PartitionKind.NON_PARTITIONED


def test_noneptn_init_with_dict_ref():
    """Test NonePTN initialization with dict ref"""
    connect = MockConnect()
    ref_dict = {"location": "s3://bucket/data"}

    interface = NonePTN(ref=ref_dict, connect=connect)

    assert interface.ref.location == "s3://bucket/data"
    assert interface.connect == connect


def test_noneptn_init_with_parent():
    """Test NonePTN initialization with parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = NonePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = NonePTN(ref=child_ref, parent=parent)

    assert child.parent == parent
    assert child.connect == connect  # Inherited from parent


def test_noneptn_init_without_connect_without_parent_raises():
    """Test NonePTN initialization without connect and without parent raises error"""
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(ValueError, match="connect cannot be None if parent is None"):
        NonePTN(ref=ref, connect=None, parent=None)


def test_noneptn_init_sets_partition_fields_to_none():
    """Test NonePTN sets partition_fields to None (empty list)"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert interface.partition_fields == []


def test_noneptn_init_sets_partition_kind_to_non_partitioned():
    """Test NonePTN sets partition_kind to NON_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert interface.partition_kind == PartitionKind.NON_PARTITIONED


def test_noneptn_has_date_format_constant():
    """Test NonePTN has DATE_FORMAT constant"""
    assert hasattr(NonePTN, "DATE_FORMAT")
    assert NonePTN.DATE_FORMAT == "%Y-%m-%d"


# ==================== Inheritance Tests ====================


def test_noneptn_inherits_from_baseinterface():
    """Test NonePTN inherits from BaseInterface"""
    from xdatawork.interface.base.interface import BaseInterface

    assert issubclass(NonePTN, BaseInterface)


def test_noneptn_has_list_refs_method():
    """Test NonePTN has inherited list_refs method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert hasattr(interface, "list_refs")
    refs = interface.list_refs()
    assert isinstance(refs, list)


def test_noneptn_has_list_artifacts_method():
    """Test NonePTN has inherited list_artifacts method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert hasattr(interface, "list_artifacts")
    artifacts = interface.list_artifacts()
    assert isinstance(artifacts, list)


def test_noneptn_has_describe_method():
    """Test NonePTN has inherited describe method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)

    assert hasattr(interface, "describe")
    description = interface.describe()
    assert isinstance(description, dict)
    assert "partition_kind" in description
    assert description["partition_kind"] == "NON_PARTITIONED"


def test_noneptn_has_to_dict_method():
    """Test NonePTN has inherited to_dict method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)

    assert hasattr(interface, "to_dict")
    result = interface.to_dict()
    assert isinstance(result, dict)
    assert "partition_kind" in result
    assert result["partition_kind"] == "NON_PARTITIONED"


# ==================== list_refs() Tests ====================


def test_noneptn_list_refs_returns_list():
    """Test NonePTN list_refs returns list"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)
    refs = interface.list_refs()

    assert isinstance(refs, list)
    assert len(refs) == 2


def test_noneptn_list_refs_with_level():
    """Test NonePTN list_refs with level parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)
    refs = interface.list_refs(level=1)

    assert isinstance(refs, list)


def test_noneptn_list_refs_with_pattern():
    """Test NonePTN list_refs with pattern parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)
    refs = interface.list_refs(pattern="*.txt")

    assert isinstance(refs, list)


# ==================== list_artifacts() Tests ====================


def test_noneptn_list_artifacts_returns_list():
    """Test NonePTN list_artifacts returns list"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)
    artifacts = interface.list_artifacts()

    assert isinstance(artifacts, list)
    assert len(artifacts) == 2


def test_noneptn_list_artifacts_with_level():
    """Test NonePTN list_artifacts with level parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)
    artifacts = interface.list_artifacts(level=1)

    assert isinstance(artifacts, list)


def test_noneptn_list_artifacts_with_pattern():
    """Test NonePTN list_artifacts with pattern parameter"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)
    artifacts = interface.list_artifacts(pattern="*.parquet")

    assert isinstance(artifacts, list)


# ==================== describe() Tests ====================


def test_noneptn_describe_shows_non_partitioned():
    """Test NonePTN describe shows NON_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)
    description = interface.describe()

    assert description["partition_kind"] == "NON_PARTITIONED"


def test_noneptn_describe_includes_ref():
    """Test NonePTN describe includes ref"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)
    description = interface.describe()

    assert "ref" in description
    assert description["ref"]["location"] == "s3://bucket/data"


def test_noneptn_describe_includes_connect():
    """Test NonePTN describe includes connect"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)
    description = interface.describe()

    assert "connect" in description
    assert description["connect"] == "s3"


def test_noneptn_describe_with_parent():
    """Test NonePTN describe with parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = NonePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = NonePTN(ref=child_ref, parent=parent)

    description = child.describe()

    assert "parent" in description
    assert isinstance(description["parent"], dict)


# ==================== to_dict() Tests ====================


def test_noneptn_to_dict_shows_empty_partition_fields():
    """Test NonePTN to_dict shows empty partition_fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["partition_fields"] == []


def test_noneptn_to_dict_shows_non_partitioned():
    """Test NonePTN to_dict shows NON_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["partition_kind"] == "NON_PARTITIONED"


def test_noneptn_to_dict_includes_all_required_keys():
    """Test NonePTN to_dict includes all required keys"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = NonePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    required_keys = [
        "ref",
        "partition_fields",
        "partition_kind",
        "parent",
        "connect",
    ]
    for key in required_keys:
        assert key in result


def test_noneptn_to_dict_parent_is_none():
    """Test NonePTN to_dict parent is None when no parent"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["parent"] is None


def test_noneptn_to_dict_parent_is_dict_when_has_parent():
    """Test NonePTN to_dict parent is dict when has parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = NonePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = NonePTN(ref=child_ref, parent=parent)

    result = child.to_dict()

    assert result["parent"] is not None
    assert isinstance(result["parent"], dict)


# ==================== Integration Tests ====================


def test_noneptn_with_s3_connect():
    """Test NonePTN with S3 connect"""
    connect = MockConnect(ConnectKind.S3)
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert interface.connect.kind == ConnectKind.S3


def test_noneptn_with_macos_connect():
    """Test NonePTN with MacOS connect"""
    connect = MockConnect(ConnectKind.MACOS)
    ref = ConnectRef(location="/local/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert interface.connect.kind == ConnectKind.MACOS


def test_noneptn_parent_child_hierarchy():
    """Test NonePTN parent-child hierarchy"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = NonePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/parent/child")
    child = NonePTN(ref=child_ref, parent=parent)

    assert child.parent is parent
    assert child.connect is parent.connect


def test_noneptn_grandparent_parent_child_hierarchy():
    """Test NonePTN three-level hierarchy"""
    connect = MockConnect()

    grandparent_ref = ConnectRef(location="s3://bucket/grandparent")
    grandparent = NonePTN(ref=grandparent_ref, connect=connect)

    parent_ref = ConnectRef(location="s3://bucket/grandparent/parent")
    parent = NonePTN(ref=parent_ref, parent=grandparent)

    child_ref = ConnectRef(location="s3://bucket/grandparent/parent/child")
    child = NonePTN(ref=child_ref, parent=parent)

    assert child.parent is parent
    assert parent.parent is grandparent
    assert child.connect is grandparent.connect


def test_noneptn_instance_is_not_none():
    """Test NonePTN instance is not None"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert interface is not None
    assert isinstance(interface, NonePTN)


def test_noneptn_attributes_accessible():
    """Test NonePTN all attributes are accessible"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = NonePTN(ref=ref, connect=connect)

    assert hasattr(interface, "ref")
    assert hasattr(interface, "connect")
    assert hasattr(interface, "parent")
    assert hasattr(interface, "partition_fields")
    assert hasattr(interface, "partition_kind")
    assert hasattr(interface, "DATE_FORMAT")


def test_noneptn_date_format_is_correct():
    """Test NonePTN DATE_FORMAT is correct"""
    assert NonePTN.DATE_FORMAT == "%Y-%m-%d"


def test_noneptn_can_be_used_as_parent():
    """Test NonePTN can be used as parent for other interfaces"""
    from xdatawork.interface.base.interface import BaseInterface

    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = NonePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = BaseInterface(
        ref=child_ref,
        parent=parent,
        partition_fields=["date"],
    )

    assert child.parent is parent
    assert child.connect is parent.connect

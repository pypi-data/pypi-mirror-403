from datetime import date

import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.partitionkind import PartitionKind
from xdatawork.interface.instance.noneptn import NonePTN
from xdatawork.interface.instance.snapshotdateptn import SnapshotdatePTN

# ==================== Mock Connect Implementation ====================


class MockConnect:
    """Mock implementation of ConnectLike for testing"""

    def __init__(self, kind: ConnectKind = ConnectKind.S3):
        self.kind = kind
        self._storage: dict[str, bytes] = {}
        self._mock_refs: list[ConnectRef] = []

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
        """Mock list_objects that returns mock refs if set, otherwise default"""
        if self._mock_refs:
            return self._mock_refs
        base_loc = location if isinstance(location, str) else location.location
        # ConnectRef extracts partitions from location automatically when partition_fields is specified
        return [
            ConnectRef(
                location=f"{base_loc}/snapshotdate=2024-01-15/file1.txt",
                kind=self.kind,
                partition_fields=["snapshotdate"],
            ),
            ConnectRef(
                location=f"{base_loc}/snapshotdate=2024-01-20/file2.parquet",
                kind=self.kind,
                partition_fields=["snapshotdate"],
            ),
        ]

    def set_mock_refs(self, refs: list[ConnectRef]):
        """Helper to set specific mock refs for testing"""
        self._mock_refs = refs


# ==================== Initialization Tests ====================


def test_snapshotdateptn_init_with_minimal_args():
    """Test SnapshotdatePTN initialization with minimal required arguments"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert interface.ref == ref
    assert interface.connect == connect
    assert interface.parent is None
    assert interface.partition_fields == ["snapshotdate"]
    assert interface.partition_kind == PartitionKind.SNAPSHOT_PARTITIONED


def test_snapshotdateptn_init_with_dict_ref():
    """Test SnapshotdatePTN initialization with dict ref"""
    connect = MockConnect()
    ref_dict = {"location": "s3://bucket/data"}

    interface = SnapshotdatePTN(ref=ref_dict, connect=connect)

    assert interface.ref.location == "s3://bucket/data"
    assert interface.connect == connect


def test_snapshotdateptn_init_with_parent():
    """Test SnapshotdatePTN initialization with parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = SnapshotdatePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = SnapshotdatePTN(ref=child_ref, parent=parent)

    assert child.parent == parent
    assert child.connect == connect  # Inherited from parent


def test_snapshotdateptn_init_without_connect_without_parent_raises():
    """Test SnapshotdatePTN initialization without connect and without parent raises error"""
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(ValueError, match="connect cannot be None if parent is None"):
        SnapshotdatePTN(ref=ref, connect=None, parent=None)


def test_snapshotdateptn_init_sets_partition_fields_to_snapshotdate():
    """Test SnapshotdatePTN sets partition_fields to ['snapshotdate']"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert interface.partition_fields == ["snapshotdate"]


def test_snapshotdateptn_init_sets_partition_kind_to_snapshot_partitioned():
    """Test SnapshotdatePTN sets partition_kind to SNAPSHOT_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert interface.partition_kind == PartitionKind.SNAPSHOT_PARTITIONED


def test_snapshotdateptn_has_date_format_constant():
    """Test SnapshotdatePTN has DATE_FORMAT constant"""
    assert hasattr(SnapshotdatePTN, "DATE_FORMAT")
    assert SnapshotdatePTN.DATE_FORMAT == "%Y-%m-%d"


# ==================== Inheritance Tests ====================


def test_snapshotdateptn_inherits_from_baseinterface():
    """Test SnapshotdatePTN inherits from BaseInterface"""
    from xdatawork.interface.base.interface import BaseInterface

    assert issubclass(SnapshotdatePTN, BaseInterface)


def test_snapshotdateptn_has_list_refs_method():
    """Test SnapshotdatePTN has inherited list_refs method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert hasattr(interface, "list_refs")
    refs = interface.list_refs()
    assert isinstance(refs, list)


def test_snapshotdateptn_has_list_artifacts_method():
    """Test SnapshotdatePTN has inherited list_artifacts method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert hasattr(interface, "list_artifacts")
    artifacts = interface.list_artifacts()
    assert isinstance(artifacts, list)


# ==================== resolve_date() Method Tests ====================


def test_resolve_date_with_date_object():
    """Test resolve_date with date object"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    result = interface.resolve_date(date(2024, 1, 15))

    assert result == date(2024, 1, 15)


def test_resolve_date_with_valid_string():
    """Test resolve_date with valid date string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("2024-01-15")

    assert result is not None
    assert isinstance(result, date)


def test_resolve_date_with_invalid_string():
    """Test resolve_date with invalid date string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("invalid-date")

    assert result is None


def test_resolve_date_with_wrong_format():
    """Test resolve_date with flexible date format (datetime.strptime is lenient)"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("2024-1-5")  # datetime.strptime accepts this

    # datetime.strptime is lenient and accepts flexible formats
    assert result is not None
    assert isinstance(result, date)


def test_resolve_date_with_none():
    """Test resolve_date with None"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    result = interface.resolve_date(None)

    assert result is None


def test_resolve_date_with_string_with_spaces():
    """Test resolve_date with string with leading/trailing spaces"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("  2024-01-15  ")

    assert result is not None
    assert isinstance(result, date)


def test_resolve_date_with_empty_string():
    """Test resolve_date with empty string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("")

    assert result is None


# ==================== list_snapshotdate_refs() Method Tests ====================


def test_list_snapshotdate_refs_with_no_filters():
    """Test list_snapshotdate_refs with no filters returns all refs"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs()

    assert isinstance(refs, list)
    assert len(refs) == 2


def test_list_snapshotdate_refs_with_min_filter():
    """Test list_snapshotdate_refs with min filter"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/snapshotdate=2024-01-10/file.txt",
                partition_fields=["snapshotdate"],
            ),
            ConnectRef(
                location="s3://bucket/data/snapshotdate=2024-01-15/file.txt",
                partition_fields=["snapshotdate"],
            ),
            ConnectRef(
                location="s3://bucket/data/snapshotdate=2024-01-20/file.txt",
                partition_fields=["snapshotdate"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs(min="2024-01-15")

    assert len(refs) == 2
    dates = [r.get_partition("snapshotdate") for r in refs]
    assert "2024-01-15" in dates
    assert "2024-01-20" in dates
    assert "2024-01-10" not in dates


def test_list_snapshotdate_refs_with_max_filter():
    """Test list_snapshotdate_refs with max filter"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/snapshotdate=2024-01-10/file.txt",
                partition_fields=["snapshotdate"],
            ),
            ConnectRef(
                location="s3://bucket/data/snapshotdate=2024-01-15/file.txt",
                partition_fields=["snapshotdate"],
            ),
            ConnectRef(
                location="s3://bucket/data/snapshotdate=2024-01-20/file.txt",
                partition_fields=["snapshotdate"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs(max="2024-01-15")

    assert len(refs) == 2
    dates = [r.get_partition("snapshotdate") for r in refs]
    assert "2024-01-10" in dates
    assert "2024-01-15" in dates
    assert "2024-01-20" not in dates


def test_list_snapshotdate_refs_with_min_and_max_filter():
    """Test list_snapshotdate_refs with both min and max filters"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-10/file.txt", partition_fields=["snapshotdate"]),
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-15/file.txt", partition_fields=["snapshotdate"]),
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-20/file.txt", partition_fields=["snapshotdate"]),
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-25/file.txt", partition_fields=["snapshotdate"]),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs(min="2024-01-15", max="2024-01-20")

    assert len(refs) == 2
    dates = [r.get_partition("snapshotdate") for r in refs]
    assert "2024-01-15" in dates
    assert "2024-01-20" in dates
    assert "2024-01-10" not in dates
    assert "2024-01-25" not in dates


def test_list_snapshotdate_refs_skips_invalid_dates():
    """Test list_snapshotdate_refs skips refs with invalid date formats"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-15/file.txt", partition_fields=["snapshotdate"]),
            ConnectRef(location="s3://bucket/data/snapshotdate=invalid/file.txt", partition_fields=["snapshotdate"]),
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-20/file.txt", partition_fields=["snapshotdate"]),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs()

    assert len(refs) == 2
    dates = [r.get_partition("snapshotdate") for r in refs]
    assert "invalid" not in dates


def test_list_snapshotdate_refs_skips_refs_without_snapshotdate_partition():
    """Test list_snapshotdate_refs skips refs without snapshotdate partition"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-15/file.txt", partition_fields=["snapshotdate"]),
            ConnectRef(location="s3://bucket/data/other/file.txt", partition_fields=[]),
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-20/file.txt", partition_fields=["snapshotdate"]),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs()

    assert len(refs) == 2


def test_list_snapshotdate_refs_with_invalid_min():
    """Test list_snapshotdate_refs with invalid min date"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs(min="invalid-date")

    # Should return all refs since min is invalid (treated as None)
    assert isinstance(refs, list)


def test_list_snapshotdate_refs_with_invalid_max():
    """Test list_snapshotdate_refs with invalid max date"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    refs = interface.list_snapshotdate_refs(max="invalid-date")

    # Should return all refs since max is invalid (treated as None)
    assert isinstance(refs, list)


# ==================== get_subinterface() Method Tests ====================


def test_get_subinterface_with_valid_snapshotdate_string():
    """Test get_subinterface with valid snapshotdate string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(snapshotdate="2024-01-15")

    assert isinstance(subinterface, NonePTN)
    assert "snapshotdate=2024-01-15" in subinterface.ref.location
    assert subinterface.connect is connect
    assert subinterface.parent is interface


def test_get_subinterface_with_date_object():
    """Test get_subinterface with date object"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(snapshotdate=date(2024, 1, 15))

    assert isinstance(subinterface, NonePTN)
    assert "snapshotdate=2024-01-15" in subinterface.ref.location


def test_get_subinterface_with_invalid_snapshotdate_raises():
    """Test get_subinterface with invalid snapshotdate raises ValueError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    with pytest.raises(ValueError, match="Invalid snapshotdate"):
        interface.get_subinterface(snapshotdate="invalid-date")


def test_get_subinterface_with_none_raises():
    """Test get_subinterface with None raises ValueError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    with pytest.raises(ValueError, match="Invalid snapshotdate"):
        interface.get_subinterface(snapshotdate=None)


def test_get_subinterface_returns_noneptn():
    """Test get_subinterface returns NonePTN instance"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(snapshotdate="2024-01-15")

    assert isinstance(subinterface, NonePTN)
    assert subinterface.partition_kind == PartitionKind.NON_PARTITIONED


def test_get_subinterface_inherits_connect():
    """Test get_subinterface subinterface inherits connect"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(snapshotdate="2024-01-15")

    assert subinterface.connect is interface.connect


def test_get_subinterface_sets_parent():
    """Test get_subinterface sets parent correctly"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(snapshotdate="2024-01-15")

    assert subinterface.parent is interface


# ==================== describe() Tests ====================


def test_snapshotdateptn_describe_shows_snapshot_partitioned():
    """Test SnapshotdatePTN describe shows SNAPSHOT_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = SnapshotdatePTN(ref=ref, connect=connect)
    description = interface.describe()

    assert description["partition_kind"] == "SNAPSHOT_PARTITIONED"


def test_snapshotdateptn_describe_includes_partition_fields():
    """Test SnapshotdatePTN describe includes partition_fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = SnapshotdatePTN(ref=ref, connect=connect)
    description = interface.describe()

    assert "partition_fields" in description
    assert description["partition_fields"] == ["snapshotdate"]


# ==================== to_dict() Tests ====================


def test_snapshotdateptn_to_dict_shows_snapshotdate_partition_fields():
    """Test SnapshotdatePTN to_dict shows snapshotdate partition_fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = SnapshotdatePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["partition_fields"] == ["snapshotdate"]


def test_snapshotdateptn_to_dict_shows_snapshot_partitioned():
    """Test SnapshotdatePTN to_dict shows SNAPSHOT_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = SnapshotdatePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["partition_kind"] == "SNAPSHOT_PARTITIONED"


# ==================== Integration Tests ====================


def test_snapshotdateptn_with_s3_connect():
    """Test SnapshotdatePTN with S3 connect"""
    connect = MockConnect(ConnectKind.S3)
    ref = ConnectRef(location="s3://bucket/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert interface.connect.kind == ConnectKind.S3


def test_snapshotdateptn_with_macos_connect():
    """Test SnapshotdatePTN with MacOS connect"""
    connect = MockConnect(ConnectKind.MACOS)
    ref = ConnectRef(location="/local/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert interface.connect.kind == ConnectKind.MACOS


def test_snapshotdateptn_parent_child_hierarchy():
    """Test SnapshotdatePTN parent-child hierarchy"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = SnapshotdatePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/parent/child")
    child = SnapshotdatePTN(ref=child_ref, parent=parent)

    assert child.parent is parent
    assert child.connect is parent.connect


def test_snapshotdateptn_complete_workflow():
    """Test SnapshotdatePTN complete workflow from listing to subinterface"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-15/file.txt", partition_fields=["snapshotdate"]),
            ConnectRef(location="s3://bucket/data/snapshotdate=2024-01-20/file.txt", partition_fields=["snapshotdate"]),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = SnapshotdatePTN(ref=ref, connect=connect)

    # List all snapshotdate refs
    all_refs = interface.list_snapshotdate_refs()
    assert len(all_refs) == 2

    # Filter by date range
    filtered_refs = interface.list_snapshotdate_refs(min="2024-01-15", max="2024-01-20")
    assert len(filtered_refs) == 2

    # Get subinterface for specific snapshotdate
    subinterface = interface.get_subinterface(snapshotdate="2024-01-15")
    assert isinstance(subinterface, NonePTN)


def test_snapshotdateptn_attributes_accessible():
    """Test SnapshotdatePTN all attributes are accessible"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = SnapshotdatePTN(ref=ref, connect=connect)

    assert hasattr(interface, "ref")
    assert hasattr(interface, "connect")
    assert hasattr(interface, "parent")
    assert hasattr(interface, "partition_fields")
    assert hasattr(interface, "partition_kind")
    assert hasattr(interface, "DATE_FORMAT")
    assert hasattr(interface, "resolve_date")
    assert hasattr(interface, "list_snapshotdate_refs")
    assert hasattr(interface, "get_subinterface")


def test_snapshotdateptn_date_format_is_correct():
    """Test SnapshotdatePTN DATE_FORMAT is correct"""
    assert SnapshotdatePTN.DATE_FORMAT == "%Y-%m-%d"

from datetime import date

import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.partitionkind import PartitionKind
from xdatawork.interface.instance.dateptn import DatePTN
from xdatawork.interface.instance.noneptn import NonePTN

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
                location=f"{base_loc}/date=2024-01-15/file1.txt",
                kind=self.kind,
                partition_fields=["date"],
            ),
            ConnectRef(
                location=f"{base_loc}/date=2024-01-20/file2.parquet",
                kind=self.kind,
                partition_fields=["date"],
            ),
        ]

    def set_mock_refs(self, refs: list[ConnectRef]):
        """Helper to set specific mock refs for testing"""
        self._mock_refs = refs


# ==================== Initialization Tests ====================


def test_dateptn_init_with_minimal_args():
    """Test DatePTN initialization with minimal required arguments"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = DatePTN(ref=ref, connect=connect)

    assert interface.ref == ref
    assert interface.connect == connect
    assert interface.parent is None
    assert interface.partition_fields == ["date"]
    assert interface.partition_kind == PartitionKind.DATE_PARTITIONED


def test_dateptn_init_with_dict_ref():
    """Test DatePTN initialization with dict ref"""
    connect = MockConnect()
    ref_dict = {"location": "s3://bucket/data"}

    interface = DatePTN(ref=ref_dict, connect=connect)

    assert interface.ref.location == "s3://bucket/data"
    assert interface.connect == connect


def test_dateptn_init_with_parent():
    """Test DatePTN initialization with parent"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = DatePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/child")
    child = DatePTN(ref=child_ref, parent=parent)

    assert child.parent == parent
    assert child.connect == connect  # Inherited from parent


def test_dateptn_init_without_connect_without_parent_raises():
    """Test DatePTN initialization without connect and without parent raises error"""
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(ValueError, match="connect cannot be None if parent is None"):
        DatePTN(ref=ref, connect=None, parent=None)


def test_dateptn_init_sets_partition_fields_to_date():
    """Test DatePTN sets partition_fields to ['date']"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = DatePTN(ref=ref, connect=connect)

    assert interface.partition_fields == ["date"]


def test_dateptn_init_sets_partition_kind_to_date_partitioned():
    """Test DatePTN sets partition_kind to DATE_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = DatePTN(ref=ref, connect=connect)

    assert interface.partition_kind == PartitionKind.DATE_PARTITIONED


def test_dateptn_has_date_format_constant():
    """Test DatePTN has DATE_FORMAT constant"""
    assert hasattr(DatePTN, "DATE_FORMAT")
    assert DatePTN.DATE_FORMAT == "%Y-%m-%d"


# ==================== Inheritance Tests ====================


def test_dateptn_inherits_from_baseinterface():
    """Test DatePTN inherits from BaseInterface"""
    from xdatawork.interface.base.interface import BaseInterface

    assert issubclass(DatePTN, BaseInterface)


def test_dateptn_has_list_refs_method():
    """Test DatePTN has inherited list_refs method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = DatePTN(ref=ref, connect=connect)

    assert hasattr(interface, "list_refs")
    refs = interface.list_refs()
    assert isinstance(refs, list)


def test_dateptn_has_list_artifacts_method():
    """Test DatePTN has inherited list_artifacts method"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = DatePTN(ref=ref, connect=connect)

    assert hasattr(interface, "list_artifacts")
    artifacts = interface.list_artifacts()
    assert isinstance(artifacts, list)


# ==================== resolve_date() Method Tests ====================


def test_resolve_date_with_date_object():
    """Test resolve_date with date object"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    result = interface.resolve_date(date(2024, 1, 15))

    assert result == date(2024, 1, 15)


def test_resolve_date_with_valid_string():
    """Test resolve_date with valid date string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)
    result = interface.resolve_date("2024-01-15")
    assert result is not None
    assert isinstance(result, date)


def test_resolve_date_with_invalid_string():
    """Test resolve_date with invalid date string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("invalid-date")

    assert result is None


def test_resolve_date_with_wrong_format():
    """Test resolve_date with flexible date format (datetime.strptime is lenient)"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)
    result = interface.resolve_date("2024-1-5")  # datetime.strptime accepts this

    # datetime.strptime is lenient and accepts flexible formats
    assert result is not None
    assert isinstance(result, date)


def test_resolve_date_with_none():
    """Test resolve_date with None"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    result = interface.resolve_date(None)

    assert result is None


def test_resolve_date_with_string_with_spaces():
    """Test resolve_date with string with leading/trailing spaces"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("  2024-01-15  ")

    assert result is not None
    assert isinstance(result, date)


def test_resolve_date_with_empty_string():
    """Test resolve_date with empty string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    result = interface.resolve_date("")

    assert result is None


# ==================== list_date_refs() Method Tests ====================


def test_list_date_refs_with_no_filters():
    """Test list_date_refs with no filters returns all refs"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs()

    assert isinstance(refs, list)
    assert len(refs) == 2


def test_list_date_refs_with_min_filter():
    """Test list_date_refs with min filter"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/date=2024-01-10/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-15/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-20/file.txt",
                partition_fields=["date"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs(min="2024-01-15")

    assert len(refs) == 2
    dates = [r.get_partition("date") for r in refs]
    assert "2024-01-15" in dates
    assert "2024-01-20" in dates
    assert "2024-01-10" not in dates


def test_list_date_refs_with_max_filter():
    """Test list_date_refs with max filter"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/date=2024-01-10/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-15/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-20/file.txt",
                partition_fields=["date"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs(max="2024-01-15")

    assert len(refs) == 2
    dates = [r.get_partition("date") for r in refs]
    assert "2024-01-10" in dates
    assert "2024-01-15" in dates
    assert "2024-01-20" not in dates


def test_list_date_refs_with_min_and_max_filter():
    """Test list_date_refs with both min and max filters"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/date=2024-01-10/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-15/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-20/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-25/file.txt",
                partition_fields=["date"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs(min="2024-01-15", max="2024-01-20")

    assert len(refs) == 2
    dates = [r.get_partition("date") for r in refs]
    assert "2024-01-15" in dates
    assert "2024-01-20" in dates
    assert "2024-01-10" not in dates
    assert "2024-01-25" not in dates


def test_list_date_refs_with_date_objects():
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/date=2024-01-10/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-15/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-20/file.txt",
                partition_fields=["date"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs(min=date(2024, 1, 15), max=date(2024, 1, 20))

    assert len(refs) == 2


def test_list_date_refs_skips_invalid_dates():
    """Test list_date_refs skips refs with invalid date formats"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/date=2024-01-15/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=invalid/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-20/file.txt",
                partition_fields=["date"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs()

    assert len(refs) == 2
    dates = [r.get_partition("date") for r in refs]
    assert "invalid" not in dates


def test_list_date_refs_skips_refs_without_date_partition():
    """Test list_date_refs skips refs without date partition"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/date=2024-01-15/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(location="s3://bucket/data/other/file.txt", partition_fields=[]),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-20/file.txt",
                partition_fields=["date"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs()

    assert len(refs) == 2


def test_list_date_refs_with_invalid_min():
    """Test list_date_refs with invalid min date"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs(min="invalid-date")

    # Should return all refs since min is invalid (treated as None)
    assert isinstance(refs, list)


def test_list_date_refs_with_invalid_max():
    """Test list_date_refs with invalid max date"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    refs = interface.list_date_refs(max="invalid-date")

    # Should return all refs since max is invalid (treated as None)
    assert isinstance(refs, list)


# ==================== get_subinterface() Method Tests ====================


def test_get_subinterface_with_valid_date_string():
    """Test get_subinterface with valid date string"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(date="2024-01-15")

    assert isinstance(subinterface, NonePTN)
    assert "date=2024-01-15" in subinterface.ref.location
    assert subinterface.connect is connect
    assert subinterface.parent is interface


def test_get_subinterface_with_date_object():
    """Test get_subinterface with date object"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(date=date(2024, 1, 15))

    assert isinstance(subinterface, NonePTN)
    assert "date=2024-01-15" in subinterface.ref.location


def test_get_subinterface_with_invalid_date_raises():
    """Test get_subinterface with invalid date raises ValueError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    with pytest.raises(ValueError, match="Invalid date"):
        interface.get_subinterface(date="invalid-date")


def test_get_subinterface_with_none_raises():
    """Test get_subinterface with None raises ValueError"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    with pytest.raises(ValueError, match="Invalid date"):
        interface.get_subinterface(date=None)


def test_get_subinterface_returns_noneptn():
    """Test get_subinterface returns NonePTN instance"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(date="2024-01-15")

    assert isinstance(subinterface, NonePTN)
    assert subinterface.partition_kind == PartitionKind.NON_PARTITIONED


def test_get_subinterface_inherits_connect():
    """Test get_subinterface subinterface inherits connect"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(date="2024-01-15")

    assert subinterface.connect is interface.connect


def test_get_subinterface_sets_parent():
    """Test get_subinterface sets parent correctly"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    subinterface = interface.get_subinterface(date="2024-01-15")

    assert subinterface.parent is interface


# ==================== describe() Tests ====================


def test_dateptn_describe_shows_date_partitioned():
    """Test DatePTN describe shows DATE_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = DatePTN(ref=ref, connect=connect)
    description = interface.describe()

    assert description["partition_kind"] == "DATE_PARTITIONED"


def test_dateptn_describe_includes_partition_fields():
    """Test DatePTN describe includes partition_fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = DatePTN(ref=ref, connect=connect)
    description = interface.describe()

    assert "partition_fields" in description
    assert description["partition_fields"] == ["date"]


# ==================== to_dict() Tests ====================


def test_dateptn_to_dict_shows_date_partition_fields():
    """Test DatePTN to_dict shows date partition_fields"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = DatePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["partition_fields"] == ["date"]


def test_dateptn_to_dict_shows_date_partitioned():
    """Test DatePTN to_dict shows DATE_PARTITIONED"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data", kind=ConnectKind.S3)

    interface = DatePTN(ref=ref, connect=connect)
    result = interface.to_dict()

    assert result["partition_kind"] == "DATE_PARTITIONED"


# ==================== Integration Tests ====================


def test_dateptn_with_s3_connect():
    """Test DatePTN with S3 connect"""
    connect = MockConnect(ConnectKind.S3)
    ref = ConnectRef(location="s3://bucket/data")

    interface = DatePTN(ref=ref, connect=connect)

    assert interface.connect.kind == ConnectKind.S3


def test_dateptn_with_macos_connect():
    """Test DatePTN with MacOS connect"""
    connect = MockConnect(ConnectKind.MACOS)
    ref = ConnectRef(location="/local/data")
    interface = DatePTN(ref=ref, connect=connect)

    assert interface.connect.kind == ConnectKind.MACOS


def test_dateptn_parent_child_hierarchy():
    """Test DatePTN parent-child hierarchy"""
    connect = MockConnect()
    parent_ref = ConnectRef(location="s3://bucket/parent")
    parent = DatePTN(ref=parent_ref, connect=connect)

    child_ref = ConnectRef(location="s3://bucket/parent/child")
    child = DatePTN(ref=child_ref, parent=parent)

    assert child.parent is parent
    assert child.connect is parent.connect


def test_dateptn_complete_workflow():
    """Test DatePTN complete workflow from listing to subinterface"""
    connect = MockConnect()
    connect.set_mock_refs(
        [
            ConnectRef(
                location="s3://bucket/data/date=2024-01-15/file.txt",
                partition_fields=["date"],
            ),
            ConnectRef(
                location="s3://bucket/data/date=2024-01-20/file.txt",
                partition_fields=["date"],
            ),
        ]
    )
    ref = ConnectRef(location="s3://bucket/data")
    interface = DatePTN(ref=ref, connect=connect)

    # List all date refs
    all_refs = interface.list_date_refs()
    assert len(all_refs) == 2

    # Filter by date range
    filtered_refs = interface.list_date_refs(min="2024-01-15", max="2024-01-20")
    assert len(filtered_refs) == 2

    # Get subinterface for specific date
    subinterface = interface.get_subinterface(date="2024-01-15")
    assert isinstance(subinterface, NonePTN)


def test_dateptn_attributes_accessible():
    """Test DatePTN all attributes are accessible"""
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    interface = DatePTN(ref=ref, connect=connect)

    assert hasattr(interface, "ref")
    assert hasattr(interface, "connect")
    assert hasattr(interface, "parent")
    assert hasattr(interface, "partition_fields")
    assert hasattr(interface, "partition_kind")
    assert hasattr(interface, "DATE_FORMAT")
    assert hasattr(interface, "resolve_date")
    assert hasattr(interface, "list_date_refs")
    assert hasattr(interface, "get_subinterface")


def test_dateptn_date_format_is_correct():
    """Test DatePTN DATE_FORMAT is correct"""
    assert DatePTN.DATE_FORMAT == "%Y-%m-%d"

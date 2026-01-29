import tempfile
from pathlib import Path

import pytest

from xdatawork.artifact.artifact import Artifact
from xdatawork.artifact.errors import ArtifactReadError, ArtifactWriteError
from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.connect.macos import MacOSConnect
from xdatawork.serde.format.dataformat import DataFormat

# ==================== Test Helpers ====================


class MockConnect:
    """Mock ConnectLike implementation for testing"""

    def __init__(self, kind=ConnectKind.MACOS):
        self.kind = kind
        self._get_result = None
        self._put_result = None
        self._get_error = None
        self._put_error = None

    def get_object(self, location: str, **kwargs):
        if self._get_error:
            raise self._get_error
        return self._get_result

    def put_object(self, data: bytes, location: str, **kwargs):
        if self._put_error:
            raise self._put_error
        return self._put_result or ConnectRef(location=location, kind=self.kind)

    def list_objects(
        self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
    ):
        return []


class MockSerDe:
    """Mock SerDeLike implementation for testing"""

    SUPPORTED_SER_SOURCE = {dict, list, bytes}
    SUPPORTED_DE_SOURCE = {bytes}
    SUPPORTED_FORMAT = {DataFormat.JSON}

    def __init__(self):
        self.serialise_called = False
        self.deserialise_called = False
        self.serialise_args = []
        self.deserialise_args = []
        self._serialise_result = b"{}"
        self._deserialise_result = {}

    def serialise(self, data, format=None, **kwargs):
        self.serialise_called = True
        self.serialise_args.append((data, format, kwargs))
        return self._serialise_result

    def deserialise(self, data, format=None, **kwargs):
        self.deserialise_called = True
        self.deserialise_args.append((data, format, kwargs))
        return self._deserialise_result


# ==================== Initialization Tests ====================


def test_artifact_initialization_with_connectref():
    """Test Artifact initialization with ConnectRef"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)

    artifact = Artifact(ref=ref, connect=connect)

    assert artifact.ref == ref
    assert artifact.connect == connect
    assert artifact.data is None


def test_artifact_initialization_with_dict_ref():
    """Test Artifact initialization with dict ref"""
    connect = MacOSConnect()
    ref_dict = {"location": "/tmp/test.json", "kind": "macos"}

    artifact = Artifact(ref=ref_dict, connect=connect)

    assert isinstance(artifact.ref, ConnectRef)
    assert artifact.ref.location == "/tmp/test.json"
    assert artifact.connect == connect


def test_artifact_initialization_with_data():
    """Test Artifact initialization with data"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = {"key": "value"}

    artifact = Artifact(ref=ref, connect=connect, data=data)

    assert artifact.data == data


def test_artifact_initialization_invalid_ref_type():
    """Test Artifact raises TypeError for invalid ref type"""
    connect = MacOSConnect()

    with pytest.raises(TypeError, match="Invalid ref"):
        Artifact(ref="invalid_string", connect=connect)


def test_artifact_initialization_invalid_connect_type():
    """Test Artifact raises TypeError for invalid connect type"""
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)

    with pytest.raises(TypeError, match="Invalid connect"):
        Artifact(ref=ref, connect="not_a_connect")


# ==================== String Representation Tests ====================


def test_artifact_str_representation():
    """Test Artifact __str__ returns ref location"""
    connect = MacOSConnect()
    ref = ConnectRef(location="s3://bucket/key.json", kind=ConnectKind.S3)
    artifact = Artifact(ref=ref, connect=connect)

    result = str(artifact)

    assert "s3://bucket/key.json" in result


def test_artifact_repr_representation():
    """Test Artifact __repr__ returns class name and ref"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=connect)

    result = repr(artifact)

    assert "Artifact" in result
    assert "ref=" in result


# ==================== get_data() Method Tests ====================


def test_get_data_returns_none_when_no_data():
    """Test get_data returns None when no data is set"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=connect)

    result = artifact.get_data()

    assert result is None


def test_get_data_returns_data_when_set():
    """Test get_data returns data when data is set"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = {"key": "value", "count": 42}
    artifact = Artifact(ref=ref, connect=connect, data=data)

    result = artifact.get_data()

    assert result == data


def test_get_data_returns_bytes():
    """Test get_data returns bytes data"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.bin", kind=ConnectKind.MACOS)
    data = b"binary data"
    artifact = Artifact(ref=ref, connect=connect, data=data)

    result = artifact.get_data()

    assert result == data
    assert isinstance(result, bytes)


# ==================== read() Method Tests ====================


def test_read_without_serde():
    """Test read without serializer returns raw bytes"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_bytes(b"test content")

        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)
        artifact = Artifact(ref=ref, connect=connect)

        result = artifact.read()

        assert artifact.data == b"test content"
        assert result is artifact


def test_read_with_serde():
    """Test read with serializer deserializes data"""
    mock_connect = MockConnect()
    mock_connect._get_result = b'{"key": "value"}'

    mock_serde = MockSerDe()
    mock_serde._deserialise_result = {"key": "value"}

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=mock_connect)

    result = artifact.read(serde=mock_serde, format=DataFormat.JSON)

    assert artifact.data == {"key": "value"}
    assert result is artifact
    assert mock_serde.deserialise_called


def test_read_with_serde_and_kwargs():
    """Test read passes kwargs to serde"""
    mock_connect = MockConnect()
    mock_connect._get_result = b'{"key": "value"}'

    mock_serde = MockSerDe()
    mock_serde._deserialise_result = {"key": "value"}

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=mock_connect)

    artifact.read(serde=mock_serde, format=DataFormat.JSON, encoding="utf-8")

    assert mock_serde.deserialise_called
    assert len(mock_serde.deserialise_args) == 1
    data, format, kwargs = mock_serde.deserialise_args[0]
    assert format == DataFormat.JSON
    assert kwargs["encoding"] == "utf-8"


def test_read_raises_error_on_connect_failure():
    """Test read raises ArtifactReadError when connect fails"""
    mock_connect = MockConnect()
    mock_connect._get_error = Exception("Connection failed")

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=mock_connect)

    with pytest.raises(ArtifactReadError, match="Failed to read artifact"):
        artifact.read()


def test_read_with_format_string():
    """Test read with format as string"""
    mock_connect = MockConnect()
    mock_connect._get_result = b'{"key": "value"}'

    mock_serde = MockSerDe()
    mock_serde._deserialise_result = {"key": "value"}

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=mock_connect)

    artifact.read(serde=mock_serde, format="json")

    assert artifact.data == {"key": "value"}


# ==================== write() Method Tests ====================


def test_write_without_serde():
    """Test write without serializer writes raw bytes"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)
        data = b"test content"
        artifact = Artifact(ref=ref, connect=connect, data=data)

        result = artifact.write()

        assert file_path.read_bytes() == b"test content"
        assert result is artifact


def test_write_with_serde():
    """Test write with serializer serializes data"""
    mock_connect = MockConnect()

    mock_serde = MockSerDe()
    mock_serde._serialise_result = b'{"key": "value"}'

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = {"key": "value"}
    artifact = Artifact(ref=ref, connect=mock_connect, data=data)

    result = artifact.write(serde=mock_serde, format=DataFormat.JSON)

    assert result is artifact
    assert mock_serde.serialise_called


def test_write_with_serde_and_kwargs():
    """Test write passes kwargs to serde"""
    mock_connect = MockConnect()

    mock_serde = MockSerDe()
    mock_serde._serialise_result = b'{"key": "value"}'

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = {"key": "value"}
    artifact = Artifact(ref=ref, connect=mock_connect, data=data)

    artifact.write(serde=mock_serde, format=DataFormat.JSON, indent=2)

    assert mock_serde.serialise_called
    assert len(mock_serde.serialise_args) == 1
    data, format, kwargs = mock_serde.serialise_args[0]
    assert format == DataFormat.JSON
    assert kwargs["indent"] == 2


def test_write_raises_error_on_connect_failure():
    """Test write raises ArtifactWriteError when connect fails"""
    mock_connect = MockConnect()
    mock_connect._put_error = Exception("Connection failed")

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = b"test data"
    artifact = Artifact(ref=ref, connect=mock_connect, data=data)

    with pytest.raises(ArtifactWriteError, match="Failed to write artifact"):
        artifact.write()


def test_write_updates_ref():
    """Test write updates artifact ref from connect response"""
    mock_connect = MockConnect()
    new_ref = ConnectRef(location="/tmp/new_location.json", kind=ConnectKind.MACOS)
    mock_connect._put_result = new_ref

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=mock_connect, data=b"test")

    artifact.write()

    assert artifact.ref == new_ref


def test_write_with_format_string():
    """Test write with format as string"""
    mock_connect = MockConnect()

    mock_serde = MockSerDe()
    mock_serde._serialise_result = b'{"key": "value"}'

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = {"key": "value"}
    artifact = Artifact(ref=ref, connect=mock_connect, data=data)

    artifact.write(serde=mock_serde, format="json")

    assert mock_serde.serialise_called


# ==================== describe() Method Tests ====================


def test_describe_returns_dict():
    """Test describe returns dictionary with artifact info"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = {"key": "value"}
    artifact = Artifact(ref=ref, connect=connect, data=data)

    result = artifact.describe()

    assert isinstance(result, dict)
    assert "ref" in result
    assert "connect" in result
    assert "data" in result


def test_describe_contains_ref_info():
    """Test describe contains ref location and kind"""
    connect = MacOSConnect()
    ref = ConnectRef(location="s3://bucket/key.json", kind=ConnectKind.S3)
    artifact = Artifact(ref=ref, connect=connect)

    result = artifact.describe()

    assert result["ref"]["location"] == "s3://bucket/key.json"
    assert result["ref"]["kind"] == "s3"


def test_describe_contains_connect_info():
    """Test describe contains connect kind"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=connect)

    result = artifact.describe()

    assert result["connect"]["kind"] == "macos"


def test_describe_contains_data_type():
    """Test describe contains data type information"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = {"key": "value"}
    artifact = Artifact(ref=ref, connect=connect, data=data)

    result = artifact.describe()

    assert result["data"]["type"] == "dict"


def test_describe_with_none_data():
    """Test describe with None data"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=connect)

    result = artifact.describe()

    assert result["data"]["type"] == "NoneType"


def test_describe_with_bytes_data():
    """Test describe with bytes data"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.bin", kind=ConnectKind.MACOS)
    data = b"binary content"
    artifact = Artifact(ref=ref, connect=connect, data=data)

    result = artifact.describe()

    assert result["data"]["type"] == "bytes"


def test_describe_with_list_data():
    """Test describe with list data"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    data = [1, 2, 3, 4]
    artifact = Artifact(ref=ref, connect=connect, data=data)

    result = artifact.describe()

    assert result["data"]["type"] == "list"


# ==================== to_dict() Method Tests ====================


def test_to_dict_returns_dict():
    """Test to_dict returns dictionary"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=connect)

    result = artifact.to_dict()

    assert isinstance(result, dict)
    assert "ref" in result
    assert "connect" in result
    assert "data" in result


def test_to_dict_structure():
    """Test to_dict has correct structure"""
    connect = MacOSConnect()
    ref = ConnectRef(location="s3://bucket/data.json", kind=ConnectKind.S3)
    data = {"test": "data"}
    artifact = Artifact(ref=ref, connect=connect, data=data)

    result = artifact.to_dict()

    assert result["ref"]["location"] == "s3://bucket/data.json"
    assert result["ref"]["kind"] == "s3"
    assert result["connect"]["kind"] == "macos"
    assert result["data"]["type"] == "dict"


def test_to_dict_with_various_data_types():
    """Test to_dict with various data types"""
    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)

    # Test with string
    artifact = Artifact(ref=ref, connect=connect, data="string data")
    result = artifact.to_dict()
    assert result["data"]["type"] == "str"

    # Test with int
    artifact = Artifact(ref=ref, connect=connect, data=42)
    result = artifact.to_dict()
    assert result["data"]["type"] == "int"

    # Test with float
    artifact = Artifact(ref=ref, connect=connect, data=3.14)
    result = artifact.to_dict()
    assert result["data"]["type"] == "float"


# ==================== Integration Tests ====================


def test_full_write_read_cycle_without_serde():
    """Test complete write and read cycle without serializer"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.bin"
        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)

        # Write
        data = b"test binary content"
        artifact1 = Artifact(ref=ref, connect=connect, data=data)
        artifact1.write()

        # Read
        artifact2 = Artifact(ref=ref, connect=connect)
        artifact2.read()

        assert artifact2.data == data


def test_full_write_read_cycle_with_serde():
    """Test complete write and read cycle with serializer"""
    mock_connect = MockConnect()
    mock_connect._put_result = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    mock_connect._get_result = b'{"key": "value"}'

    mock_serde = MockSerDe()
    mock_serde._serialise_result = b'{"key": "value"}'
    mock_serde._deserialise_result = {"key": "value"}

    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)

    # Write
    data = {"key": "value"}
    artifact1 = Artifact(ref=ref, connect=mock_connect, data=data)
    artifact1.write(serde=mock_serde, format=DataFormat.JSON)

    # Read
    artifact2 = Artifact(ref=ref, connect=mock_connect)
    artifact2.read(serde=mock_serde, format=DataFormat.JSON)

    assert artifact2.data == data


def test_artifact_with_multiple_operations():
    """Test artifact with multiple read/write operations"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)

        # First write
        artifact = Artifact(ref=ref, connect=connect, data=b"first content")
        artifact.write()

        # Read
        artifact.read()
        assert artifact.data == b"first content"

        # Second write
        artifact.data = b"second content"
        artifact.write()

        # Read again
        artifact.read()
        assert artifact.data == b"second content"


def test_artifact_with_different_data_sizes():
    """Test artifact with different data sizes"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Small data
        file_path = Path(tmpdir) / "small.bin"
        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)
        small_data = b"x"
        artifact = Artifact(ref=ref, connect=connect, data=small_data)
        artifact.write()
        artifact.read()
        assert artifact.data == small_data

        # Large data
        file_path = Path(tmpdir) / "large.bin"
        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)
        large_data = b"x" * 1024 * 1024  # 1MB
        artifact = Artifact(ref=ref, connect=connect, data=large_data)
        artifact.write()
        artifact.read()
        assert artifact.data == large_data


def test_artifact_idempotent_operations():
    """Test artifact read/write operations are idempotent"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)
        data = b"test content"

        artifact = Artifact(ref=ref, connect=connect, data=data)

        # Multiple writes
        artifact.write()
        artifact.write()

        # Multiple reads
        artifact.read()
        artifact.read()

        assert artifact.data == data


# ==================== Edge Cases ====================


def test_artifact_with_empty_data():
    """Test artifact with empty data"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "empty.txt"
        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)

        artifact = Artifact(ref=ref, connect=connect, data=b"")
        artifact.write()
        artifact.read()

        assert artifact.data == b""


def test_artifact_with_unicode_data():
    """Test artifact with unicode data"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "unicode.txt"
        ref = ConnectRef(location=str(file_path), kind=ConnectKind.MACOS)
        unicode_data = "Hello 世界 🌍".encode("utf-8")

        artifact = Artifact(ref=ref, connect=connect, data=unicode_data)
        artifact.write()
        artifact.read()

        assert artifact.data == unicode_data


def test_artifact_describe_is_serializable():
    """Test describe output is JSON-serializable"""
    import json

    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=connect, data={"key": "value"})

    result = artifact.describe()

    # Should not raise exception
    json_str = json.dumps(result)
    assert isinstance(json_str, str)


def test_artifact_to_dict_is_serializable():
    """Test to_dict output is JSON-serializable"""
    import json

    connect = MacOSConnect()
    ref = ConnectRef(location="/tmp/test.json", kind=ConnectKind.MACOS)
    artifact = Artifact(ref=ref, connect=connect, data={"key": "value"})

    result = artifact.to_dict()

    # Should not raise exception
    json_str = json.dumps(result)
    assert isinstance(json_str, str)

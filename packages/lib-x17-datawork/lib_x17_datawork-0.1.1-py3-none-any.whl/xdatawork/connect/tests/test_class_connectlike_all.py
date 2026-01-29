import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike

# ==================== Implementation Tests ====================


class MinimalConnect:
    """Minimal implementation of ConnectLike"""

    def __init__(self):
        self.kind = ConnectKind.ANY

    def get_object(self, location: str, **kwargs) -> bytes:
        return b"test data"

    def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
        return ConnectRef(location=location)

    def list_objects(
        self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
    ) -> list[ConnectRefLike]:
        return []


class IncompleteConnect:
    """Incomplete implementation missing put_object"""

    def get_object(self, location: str, **kwargs) -> bytes:
        return b"data"


def test_minimal_implementation_is_connectlike():
    """Test minimal implementation is recognized as ConnectLike"""
    connect = MinimalConnect()

    assert isinstance(connect, ConnectLike)


def test_incomplete_implementation_is_not_connectlike():
    """Test incomplete implementation is not recognized as ConnectLike"""
    connect = IncompleteConnect()

    assert not isinstance(connect, ConnectLike)


def test_get_object_signature():
    """Test get_object has correct signature"""
    connect = MinimalConnect()

    result = connect.get_object("s3://bucket/key")

    assert isinstance(result, bytes)
    assert result == b"test data"


def test_get_object_with_kwargs():
    """Test get_object accepts kwargs"""

    class ConnectWithKwargs:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return kwargs.get("default", b"data")

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    connect = ConnectWithKwargs()

    result = connect.get_object("location", default=b"custom")

    assert result == b"custom"
    assert isinstance(connect, ConnectLike)


def test_put_object_signature():
    """Test put_object has correct signature"""
    connect = MinimalConnect()

    result = connect.put_object(b"data", "s3://bucket/key")

    assert isinstance(result, ConnectRef)
    assert result.location == "s3://bucket/key"


def test_put_object_with_kwargs():
    """Test put_object accepts kwargs"""

    class ConnectWithKwargs:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            kind = kwargs.get("kind")
            return ConnectRef(location=location, kind=kind)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    connect = ConnectWithKwargs()

    result = connect.put_object(b"data", "s3://bucket/key", kind=ConnectKind.S3)

    assert result.location == "s3://bucket/key"
    assert result.kind == ConnectKind.S3
    assert isinstance(connect, ConnectLike)


# ==================== Method Validation Tests ====================


def test_missing_get_object():
    """Test missing get_object is not ConnectLike"""

    class NoGetObject:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

    obj = NoGetObject()

    assert not isinstance(obj, ConnectLike)


def test_missing_put_object():
    """Test missing put_object is not ConnectLike"""

    class NoPutObject:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"data"

    obj = NoPutObject()

    assert not isinstance(obj, ConnectLike)


def test_wrong_get_object_signature():
    """Test wrong signature still recognized (duck typing)"""

    class WrongSignature:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self) -> bytes:  # Missing location parameter
            return b"data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    obj = WrongSignature()

    assert isinstance(obj, ConnectLike)


# ==================== Inheritance Tests ====================


def test_subclass_implementation():
    """Test subclass implementation of ConnectLike"""

    class S3Connect:
        def __init__(self):
            self.kind = ConnectKind.S3

        def get_object(self, location: str, **kwargs) -> bytes:
            return f"S3 data from {location}".encode()

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location, kind=ConnectKind.S3)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    connect = S3Connect()

    assert isinstance(connect, ConnectLike)
    assert connect.get_object("s3://bucket/key") == b"S3 data from s3://bucket/key"


def test_multiple_implementations():
    """Test multiple independent implementations"""

    class LocalConnect:
        def __init__(self):
            self.kind = ConnectKind.MACOS

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"local data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location, kind=ConnectKind.MACOS)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    class S3Connect:
        def __init__(self):
            self.kind = ConnectKind.S3

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"s3 data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location, kind=ConnectKind.S3)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    local = LocalConnect()
    s3 = S3Connect()

    assert isinstance(local, ConnectLike)
    assert isinstance(s3, ConnectLike)


# ==================== Return Type Tests ====================


def test_get_object_returns_bytes():
    """Test get_object must return bytes"""

    class ValidConnect:
        def get_object(self, location: str, **kwargs) -> bytes:
            return b"valid bytes"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

    connect = ValidConnect()

    result = connect.get_object("location")

    assert isinstance(result, bytes)


def test_put_object_returns_connectref():
    """Test put_object returns ConnectRef (or ConnectRefLike)"""

    class ValidConnect:
        def get_object(self, location: str, **kwargs) -> bytes:
            return b"data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location, kind=ConnectKind.S3)

    connect = ValidConnect()

    result = connect.put_object(b"data", "s3://bucket/key")

    assert isinstance(result, ConnectRef)


# ==================== Complex Implementation Tests ====================


def test_stateful_implementation():
    """Test stateful implementation of ConnectLike"""

    class StatefulConnect:
        def __init__(self):
            self.storage = {}
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return self.storage.get(location, b"not found")

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            self.storage[location] = data
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    connect = StatefulConnect()

    assert isinstance(connect, ConnectLike)

    connect.put_object(b"test data", "key1")
    assert connect.get_object("key1") == b"test data"


def test_implementation_with_error_handling():
    """Test implementation with error handling"""

    class SafeConnect:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            if not location:
                raise ValueError("Location cannot be empty")
            return b"data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            if not data:
                raise ValueError("Data cannot be empty")
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    connect = SafeConnect()

    assert isinstance(connect, ConnectLike)

    with pytest.raises(ValueError, match="Location cannot be empty"):
        connect.get_object("")

    with pytest.raises(ValueError, match="Data cannot be empty"):
        connect.put_object(b"", "location")


def test_implementation_with_additional_methods():
    """Test implementation with additional methods beyond protocol"""

    class ExtendedConnect:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

        def delete_object(self, location: str) -> bool:
            return True

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    connect = ExtendedConnect()

    assert isinstance(connect, ConnectLike)
    assert connect.delete_object("key")
    assert connect.list_objects("prefix") == []


# ==================== Type Checking Tests ====================


def test_protocol_with_type_hints():
    """Test protocol works with proper type hints"""

    class TypedConnect:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs: object) -> bytes:
            return b"typed data"

        def put_object(self, data: bytes, location: str, **kwargs: object) -> ConnectRef:
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    connect = TypedConnect()

    assert isinstance(connect, ConnectLike)


# ==================== Edge Cases ====================


def test_callable_instead_of_method():
    """Test using callable attributes instead of methods"""

    class CallableConnect:
        def __init__(self):
            self.kind = ConnectKind.ANY
            self.get_object = lambda location, **kwargs: b"data"
            self.put_object = lambda data, location, **kwargs: ConnectRef(location=location)
            self.list_objects = lambda location, level=None, pattern=None, **kwargs: []

    connect = CallableConnect()

    assert isinstance(connect, ConnectLike)


def test_property_methods():
    """Test implementation with property decorators"""

    class PropertyConnect:
        def __init__(self):
            self.kind = ConnectKind.ANY
            self._data = {}

        def get_object(self, location: str, **kwargs) -> bytes:
            return self._data.get(location, b"default")

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            self._data[location] = data
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

        @property
        def count(self) -> int:
            return len(self._data)

    connect = PropertyConnect()

    assert isinstance(connect, ConnectLike)
    assert connect.count == 0


def test_implementation_with_base_class():
    """Test implementation with explicit base class"""

    class BaseConnect:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"base data"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    class DerivedConnect(BaseConnect):
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            data = super().get_object(location, **kwargs)
            return data + b" extended"

    connect = DerivedConnect()

    assert isinstance(connect, ConnectLike)
    assert connect.get_object("key") == b"base data extended"


# ==================== Integration Tests ====================


def test_full_workflow_with_protocol():
    """Test full workflow using ConnectLike protocol"""

    class MockConnect:
        def __init__(self):
            self.kind = ConnectKind.ANY
            self.storage = {}

        def get_object(self, location: str, **kwargs) -> bytes:
            return self.storage.get(location, b"")

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            self.storage[location] = data
            kind = kwargs.get("kind", ConnectKind.ANY)
            return ConnectRef(location=location, kind=kind)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    def process_data(connect: ConnectLike, location: str, data: bytes):
        """Function accepting ConnectLike protocol"""
        ref = connect.put_object(data, location)
        retrieved = connect.get_object(ref.location)
        return retrieved

    connect = MockConnect()
    result = process_data(connect, "test/key", b"test data")

    assert result == b"test data"
    assert isinstance(connect, ConnectLike)


def test_protocol_in_list():
    """Test ConnectLike implementations in a list"""

    class Connect1:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"connect1"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

    class Connect2:
        def __init__(self):
            self.kind = ConnectKind.ANY

        def get_object(self, location: str, **kwargs) -> bytes:
            return b"connect2"

        def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
            return ConnectRef(location=location)

        def list_objects(
            self, location: str | ConnectRefLike, level: int | None = None, pattern: str | None = None, **kwargs
        ) -> list[ConnectRefLike]:
            return []

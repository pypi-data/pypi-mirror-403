import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectreflike import ConnectRefLike

# ==================== Implementation Tests ====================


class MinimalRef:
    """Minimal implementation of ConnectRefLike"""

    def __init__(self, location: str, kind=None):
        self.location = location
        self.kind = kind

    def to(self, rel: str) -> "MinimalRef":
        return MinimalRef(location=f"{self.location}/{rel}", kind=self.kind)


class IncompleteRef:
    """Incomplete implementation missing to() method"""

    def __init__(self, location: str):
        self.location = location
        self.kind = None


def test_minimal_implementation_is_connectreflike():
    """Test minimal implementation is recognized as ConnectRefLike"""
    ref = MinimalRef(location="s3://bucket/key")

    assert isinstance(ref, ConnectRefLike)


def test_incomplete_implementation_is_not_connectreflike():
    """Test incomplete implementation is not recognized as ConnectRefLike"""
    ref = IncompleteRef(location="s3://bucket/key")

    assert not isinstance(ref, ConnectRefLike)


def test_location_attribute():
    """Test location attribute exists and is string"""
    ref = MinimalRef(location="s3://bucket/key")

    assert hasattr(ref, "location")
    assert isinstance(ref.location, str)
    assert ref.location == "s3://bucket/key"


def test_kind_attribute():
    """Test kind attribute exists"""
    ref = MinimalRef(location="s3://bucket/key", kind=ConnectKind.S3)

    assert hasattr(ref, "kind")
    assert ref.kind == ConnectKind.S3


def test_kind_attribute_optional():
    """Test kind attribute can be None"""
    ref = MinimalRef(location="s3://bucket/key", kind=None)

    assert hasattr(ref, "kind")
    assert ref.kind is None


def test_to_method_signature():
    """Test to() method has correct signature"""
    ref = MinimalRef(location="s3://bucket")

    result = ref.to("subdir/file.txt")

    assert isinstance(result, ConnectRefLike)
    assert result.location == "s3://bucket/subdir/file.txt"


def test_to_method_returns_connectreflike():
    """Test to() method returns ConnectRefLike instance"""
    ref = MinimalRef(location="/path")

    result = ref.to("file.txt")

    assert isinstance(result, ConnectRefLike)


# ==================== Method Validation Tests ====================


def test_missing_location():
    """Test missing location attribute is not ConnectRefLike"""

    class NoLocation:
        def __init__(self):
            self.kind = None

        def to(self, rel: str) -> "NoLocation":
            return NoLocation()

    obj = NoLocation()

    assert not isinstance(obj, ConnectRefLike)


def test_missing_kind():
    """Test missing kind attribute is not ConnectRefLike"""

    class NoKind:
        def __init__(self, location: str):
            self.location = location

        def to(self, rel: str) -> "NoKind":
            return NoKind(location=f"{self.location}/{rel}")

    obj = NoKind(location="path")

    assert not isinstance(obj, ConnectRefLike)


def test_missing_to_method():
    """Test missing to() method is not ConnectRefLike"""

    class NoToMethod:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

    obj = NoToMethod(location="path")

    assert not isinstance(obj, ConnectRefLike)


# ==================== Inheritance Tests ====================


def test_subclass_implementation():
    """Test subclass implementation of ConnectRefLike"""

    class S3Ref:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.S3

        def to(self, rel: str) -> "S3Ref":
            base = self.location.rstrip("/")
            rel = rel.lstrip("/")
            return S3Ref(location=f"{base}/{rel}")

    ref = S3Ref(location="s3://bucket")

    assert isinstance(ref, ConnectRefLike)
    assert ref.kind == ConnectKind.S3


def test_multiple_implementations():
    """Test multiple independent implementations"""

    class LocalRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.MACOS

        def to(self, rel: str) -> "LocalRef":
            return LocalRef(location=f"{self.location}/{rel}")

    class S3Ref:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.S3

        def to(self, rel: str) -> "S3Ref":
            return S3Ref(location=f"{self.location}/{rel}")

    local = LocalRef(location="/Users/user")
    s3 = S3Ref(location="s3://bucket")

    assert isinstance(local, ConnectRefLike)
    assert isinstance(s3, ConnectRefLike)


# ==================== Return Type Tests ====================


def test_to_returns_same_type():
    """Test to() can return same type"""

    class TypedRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "TypedRef":
            return TypedRef(location=f"{self.location}/{rel}")

    ref = TypedRef(location="base")
    result = ref.to("path")

    assert isinstance(result, TypedRef)
    assert isinstance(result, ConnectRefLike)


def test_to_returns_different_type():
    """Test to() can return different ConnectRefLike type"""

    class RefA:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "RefB":
            return RefB(location=f"{self.location}/{rel}")

    class RefB:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "RefA":
            return RefA(location=f"{self.location}/{rel}")

    ref_a = RefA(location="base")
    ref_b = ref_a.to("sub")

    assert isinstance(ref_a, ConnectRefLike)
    assert isinstance(ref_b, ConnectRefLike)
    assert type(ref_b) is RefB


# ==================== Complex Implementation Tests ====================


def test_implementation_with_validation():
    """Test implementation with validation logic"""

    class ValidatedRef:
        def __init__(self, location: str):
            if not location:
                raise ValueError("Location cannot be empty")
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "ValidatedRef":
            if not rel:
                raise ValueError("Relative path cannot be empty")
            return ValidatedRef(location=f"{self.location}/{rel}")

    ref = ValidatedRef(location="base")

    assert isinstance(ref, ConnectRefLike)

    with pytest.raises(ValueError, match="Location cannot be empty"):
        ValidatedRef(location="")

    with pytest.raises(ValueError, match="Relative path cannot be empty"):
        ref.to("")


def test_implementation_with_additional_methods():
    """Test implementation with additional methods beyond protocol"""

    class ExtendedRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.S3

        def to(self, rel: str) -> "ExtendedRef":
            return ExtendedRef(location=f"{self.location}/{rel}")

        def parent(self) -> "ExtendedRef":
            parts = self.location.rsplit("/", 1)
            return ExtendedRef(location=parts[0])

        def name(self) -> str:
            return self.location.split("/")[-1]

    ref = ExtendedRef(location="s3://bucket/dir/file.txt")

    assert isinstance(ref, ConnectRefLike)
    assert ref.name() == "file.txt"
    assert ref.parent().location == "s3://bucket/dir"


def test_implementation_with_immutability():
    """Test implementation with immutable location"""

    class ImmutableRef:
        def __init__(self, location: str):
            self._location = location
            self.kind = None

        @property
        def location(self) -> str:
            return self._location

        def to(self, rel: str) -> "ImmutableRef":
            return ImmutableRef(location=f"{self._location}/{rel}")

    ref = ImmutableRef(location="base")

    assert isinstance(ref, ConnectRefLike)
    assert ref.location == "base"


# ==================== Chaining Tests ====================


def test_to_chaining():
    """Test chaining multiple to() calls"""

    class ChainableRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "ChainableRef":
            return ChainableRef(location=f"{self.location}/{rel}")

    ref = ChainableRef(location="base")
    result = ref.to("dir1").to("dir2").to("file.txt")

    assert isinstance(result, ConnectRefLike)
    assert result.location == "base/dir1/dir2/file.txt"


def test_to_preserves_kind():
    """Test to() preserves kind attribute"""

    class KindPreservingRef:
        def __init__(self, location: str, kind=None):
            self.location = location
            self.kind = kind

        def to(self, rel: str) -> "KindPreservingRef":
            return KindPreservingRef(location=f"{self.location}/{rel}", kind=self.kind)

    ref = KindPreservingRef(location="s3://bucket", kind=ConnectKind.S3)
    result = ref.to("file.txt")

    assert result.kind == ConnectKind.S3


# ==================== Type Checking Tests ====================


def test_protocol_with_type_hints():
    """Test protocol works with proper type hints"""

    class TypedRef:
        location: str
        kind: ConnectKind | None

        def __init__(self, location: str, kind: ConnectKind | None = None):
            self.location = location
            self.kind = kind

        def to(self, rel: str) -> "TypedRef":
            return TypedRef(location=f"{self.location}/{rel}", kind=self.kind)

    ref = TypedRef(location="path", kind=ConnectKind.MACOS)

    assert isinstance(ref, ConnectRefLike)


# ==================== Edge Cases ====================


def test_location_with_special_characters():
    """Test location with special characters"""

    class SpecialRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "SpecialRef":
            return SpecialRef(location=f"{self.location}/{rel}")

    ref = SpecialRef(location="s3://bucket/path with spaces")

    assert isinstance(ref, ConnectRefLike)
    assert ref.location == "s3://bucket/path with spaces"


def test_empty_location():
    """Test with empty location string"""

    class EmptyRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "EmptyRef":
            return EmptyRef(location=rel)

    ref = EmptyRef(location="")

    assert isinstance(ref, ConnectRefLike)
    assert ref.location == ""


def test_none_kind():
    """Test with None kind"""

    class NoneKindRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = None

        def to(self, rel: str) -> "NoneKindRef":
            return NoneKindRef(location=f"{self.location}/{rel}")

    ref = NoneKindRef(location="path")

    assert isinstance(ref, ConnectRefLike)
    assert ref.kind is None


# ==================== Integration Tests ====================


def test_full_workflow_with_protocol():
    """Test full workflow using ConnectRefLike protocol"""

    class WorkflowRef:
        def __init__(self, location: str, kind=None):
            self.location = location
            self.kind = kind

        def to(self, rel: str) -> "WorkflowRef":
            base = self.location.rstrip("/")
            rel = rel.lstrip("/")
            return WorkflowRef(location=f"{base}/{rel}", kind=self.kind)

    def build_path(ref: ConnectRefLike, *parts: str) -> ConnectRefLike:
        """Function accepting ConnectRefLike protocol"""
        result = ref
        for part in parts:
            result = result.to(part)
        return result

    ref = WorkflowRef(location="s3://bucket", kind=ConnectKind.S3)
    result = build_path(ref, "data", "year=2024", "file.parquet")

    assert isinstance(result, ConnectRefLike)
    assert result.location == "s3://bucket/data/year=2024/file.parquet"


def test_protocol_in_container():
    """Test ConnectRefLike implementations in containers"""

    class Ref1:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.S3

        def to(self, rel: str) -> "Ref1":
            return Ref1(location=f"{self.location}/{rel}")

    class Ref2:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.MACOS

        def to(self, rel: str) -> "Ref2":
            return Ref2(location=f"{self.location}/{rel}")

    refs = [
        Ref1(location="s3://bucket"),
        Ref2(location="/Users/user"),
    ]

    for ref in refs:
        assert isinstance(ref, ConnectRefLike)
        assert hasattr(ref, "location")
        assert hasattr(ref, "kind")


def test_mixed_protocol_usage():
    """Test mixing different ConnectRefLike implementations"""

    class S3Ref:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.S3

        def to(self, rel: str) -> "S3Ref":
            return S3Ref(location=f"{self.location}/{rel}")

    class LocalRef:
        def __init__(self, location: str):
            self.location = location
            self.kind = ConnectKind.MACOS

        def to(self, rel: str) -> "LocalRef":
            return LocalRef(location=f"{self.location}/{rel}")

    def process_refs(refs: list[ConnectRefLike]) -> list[str]:
        return [ref.to("data").location for ref in refs]

    s3 = S3Ref(location="s3://bucket")
    local = LocalRef(location="/path")

    results = process_refs([s3, local])

    assert results == ["s3://bucket/data", "/path/data"]

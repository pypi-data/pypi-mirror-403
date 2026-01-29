from xdatawork.serde.format.dataformat import DataFormat
from xdatawork.serde.serde.serdelike import SerDeLike

# ==================== Implementation Tests ====================


class MinimalSerDe:
    """Minimal implementation of SerDeLike"""

    SUPPORTED_SER_SOURCE = {dict}
    SUPPORTED_DE_SOURCE = {bytes}
    SUPPORTED_FORMAT = {DataFormat.JSON}

    @staticmethod
    def serialise(data, format, **kwargs):
        return b'{"test": "data"}'

    @staticmethod
    def deserialise(data, format, **kwargs):
        return {"test": "data"}


class IncompleteSerDe:
    """Incomplete implementation missing deserialise"""

    SUPPORTED_SER_SOURCE = {dict}
    SUPPORTED_DE_SOURCE = {bytes}
    SUPPORTED_FORMAT = {DataFormat.JSON}

    @staticmethod
    def serialise(data, format, **kwargs):
        return b"data"


class MissingAttributes:
    """Implementation missing required class attributes"""

    @staticmethod
    def serialise(data, format, **kwargs):
        return b"data"

    @staticmethod
    def deserialise(data, format, **kwargs):
        return {}


def test_minimal_implementation_is_serdelike():
    """Test minimal implementation is recognized as SerDeLike"""
    serde = MinimalSerDe()

    assert isinstance(serde, SerDeLike)


def test_incomplete_implementation_is_not_serdelike():
    """Test incomplete implementation is not recognized as SerDeLike"""
    serde = IncompleteSerDe()

    assert not isinstance(serde, SerDeLike)


def test_missing_attributes_is_not_serdelike():
    """Test implementation without attributes is not SerDeLike"""
    serde = MissingAttributes()

    assert not isinstance(serde, SerDeLike)


def test_serialise_signature():
    """Test serialise has correct signature"""
    serde = MinimalSerDe()

    result = serde.serialise({"key": "value"}, DataFormat.JSON)

    assert isinstance(result, bytes)


def test_serialise_with_string_format():
    """Test serialise accepts string format"""
    serde = MinimalSerDe()

    result = serde.serialise({"key": "value"}, "json")

    assert isinstance(result, bytes)


def test_serialise_with_kwargs():
    """Test serialise accepts kwargs"""

    class SerDeWithKwargs:
        SUPPORTED_SER_SOURCE = {dict}
        SUPPORTED_DE_SOURCE = {bytes}
        SUPPORTED_FORMAT = {DataFormat.JSON}

        @staticmethod
        def serialise(data, format, **kwargs):
            if kwargs.get("custom"):
                return b"custom"
            return b"default"

        @staticmethod
        def deserialise(data, format, **kwargs):
            return {}

    serde = SerDeWithKwargs()

    result = serde.serialise({}, DataFormat.JSON, custom=True)

    assert result == b"custom"
    assert isinstance(serde, SerDeLike)


def test_deserialise_signature():
    """Test deserialise has correct signature"""
    serde = MinimalSerDe()

    result = serde.deserialise(b'{"key": "value"}', DataFormat.JSON)

    assert isinstance(result, dict)


def test_deserialise_with_string_format():
    """Test deserialise accepts string format"""
    serde = MinimalSerDe()

    result = serde.deserialise(b"data", "json")

    assert isinstance(result, dict)


def test_deserialise_with_kwargs():
    """Test deserialise accepts kwargs"""

    class SerDeWithKwargs:
        SUPPORTED_SER_SOURCE = {dict}
        SUPPORTED_DE_SOURCE = {bytes}
        SUPPORTED_FORMAT = {DataFormat.JSON}

        @staticmethod
        def serialise(data, format, **kwargs):
            return b"data"

        @staticmethod
        def deserialise(data, format, **kwargs):
            return kwargs.get("default", {})

    serde = SerDeWithKwargs()

    result = serde.deserialise(b"data", DataFormat.JSON, default={"custom": "value"})

    assert result == {"custom": "value"}
    assert isinstance(serde, SerDeLike)


# ==================== Attribute Tests ====================


def test_supported_ser_source_attribute_exists():
    """Test SUPPORTED_SER_SOURCE attribute exists"""
    serde = MinimalSerDe()

    assert hasattr(serde, "SUPPORTED_SER_SOURCE")


def test_supported_ser_source_is_set():
    """Test SUPPORTED_SER_SOURCE is a set"""
    serde = MinimalSerDe()

    assert isinstance(serde.SUPPORTED_SER_SOURCE, set)


def test_supported_de_source_attribute_exists():
    """Test SUPPORTED_DE_SOURCE attribute exists"""
    serde = MinimalSerDe()

    assert hasattr(serde, "SUPPORTED_DE_SOURCE")


def test_supported_de_source_is_set():
    """Test SUPPORTED_DE_SOURCE is a set"""
    serde = MinimalSerDe()

    assert isinstance(serde.SUPPORTED_DE_SOURCE, set)


def test_supported_format_attribute_exists():
    """Test SUPPORTED_FORMAT attribute exists"""
    serde = MinimalSerDe()

    assert hasattr(serde, "SUPPORTED_FORMAT")


def test_supported_format_is_set():
    """Test SUPPORTED_FORMAT is a set"""
    serde = MinimalSerDe()

    assert isinstance(serde.SUPPORTED_FORMAT, set)


def test_supported_format_contains_dataformat():
    """Test SUPPORTED_FORMAT contains DataFormat instances"""
    serde = MinimalSerDe()

    for fmt in serde.SUPPORTED_FORMAT:
        assert isinstance(fmt, DataFormat)


# ==================== Method Validation Tests ====================


def test_serialise_is_static():
    """Test serialise is a static method"""
    assert isinstance(MinimalSerDe.__dict__["serialise"], staticmethod)


def test_deserialise_is_static():
    """Test deserialise is a static method"""
    assert isinstance(MinimalSerDe.__dict__["deserialise"], staticmethod)


def test_serialise_can_be_called_on_class():
    """Test serialise can be called on class directly"""
    result = MinimalSerDe.serialise({}, DataFormat.JSON)

    assert isinstance(result, bytes)


def test_deserialise_can_be_called_on_class():
    """Test deserialise can be called on class directly"""
    result = MinimalSerDe.deserialise(b"data", DataFormat.JSON)

    assert isinstance(result, dict)


# ==================== Protocol Tests ====================


def test_serdelike_is_protocol():
    """Test SerDeLike is a Protocol"""

    # runtime_checkable makes it a Protocol
    assert isinstance(SerDeLike, type)


def test_serdelike_is_runtime_checkable():
    """Test SerDeLike is runtime_checkable"""

    # If it's runtime_checkable, isinstance checks work
    assert isinstance(MinimalSerDe(), SerDeLike)


def test_protocol_checks_methods():
    """Test protocol validates required methods"""

    class OnlySerialise:
        SUPPORTED_SER_SOURCE = {dict}
        SUPPORTED_DE_SOURCE = {bytes}
        SUPPORTED_FORMAT = {DataFormat.JSON}

        @staticmethod
        def serialise(data, format, **kwargs):
            return b"data"

    serde = OnlySerialise()

    # Missing deserialise method
    assert not isinstance(serde, SerDeLike)


def test_protocol_checks_attributes():
    """Test protocol validates required attributes"""

    class NoAttributes:
        @staticmethod
        def serialise(data, format, **kwargs):
            return b"data"

        @staticmethod
        def deserialise(data, format, **kwargs):
            return {}

    serde = NoAttributes()

    # Missing class attributes
    assert not isinstance(serde, SerDeLike)


# ==================== Multiple Format Support Tests ====================


def test_multiple_formats_supported():
    """Test SerDeLike can support multiple formats"""

    class MultiFormatSerDe:
        SUPPORTED_SER_SOURCE = {dict, list}
        SUPPORTED_DE_SOURCE = {bytes, str}
        SUPPORTED_FORMAT = {DataFormat.JSON, DataFormat.CSV, DataFormat.PARQUET}

        @staticmethod
        def serialise(data, format, **kwargs):
            return b"data"

        @staticmethod
        def deserialise(data, format, **kwargs):
            return {}

    serde = MultiFormatSerDe()

    assert isinstance(serde, SerDeLike)
    assert len(serde.SUPPORTED_FORMAT) == 3
    assert DataFormat.JSON in serde.SUPPORTED_FORMAT
    assert DataFormat.CSV in serde.SUPPORTED_FORMAT
    assert DataFormat.PARQUET in serde.SUPPORTED_FORMAT


def test_multiple_source_types():
    """Test SerDeLike can support multiple source types"""

    class MultiSourceSerDe:
        SUPPORTED_SER_SOURCE = {dict, list, tuple}
        SUPPORTED_DE_SOURCE = {bytes, str, bytearray}
        SUPPORTED_FORMAT = {DataFormat.JSON}

        @staticmethod
        def serialise(data, format, **kwargs):
            return b"data"

        @staticmethod
        def deserialise(data, format, **kwargs):
            return {}

    serde = MultiSourceSerDe()

    assert isinstance(serde, SerDeLike)
    assert len(serde.SUPPORTED_SER_SOURCE) == 3
    assert len(serde.SUPPORTED_DE_SOURCE) == 3


# ==================== Module Tests ====================


def test_serdelike_module():
    """Test SerDeLike is in correct module"""
    assert SerDeLike.__module__ == "xdatawork.serde.serde.serdelike"


def test_serdelike_name():
    """Test SerDeLike has correct name"""
    assert SerDeLike.__name__ == "SerDeLike"


# ==================== Edge Cases ====================


def test_empty_supported_sets():
    """Test SerDeLike with empty supported sets"""

    class EmptySetsSerDe:
        SUPPORTED_SER_SOURCE = set()
        SUPPORTED_DE_SOURCE = set()
        SUPPORTED_FORMAT = set()

        @staticmethod
        def serialise(data, format, **kwargs):
            return b"data"

        @staticmethod
        def deserialise(data, format, **kwargs):
            return {}

    serde = EmptySetsSerDe()

    # Still valid protocol implementation
    assert isinstance(serde, SerDeLike)


def test_attributes_as_class_variables():
    """Test attributes work as class variables"""

    class ClassVarSerDe:
        SUPPORTED_SER_SOURCE = {dict}
        SUPPORTED_DE_SOURCE = {bytes}
        SUPPORTED_FORMAT = {DataFormat.JSON}

        @staticmethod
        def serialise(data, format, **kwargs):
            return b"data"

        @staticmethod
        def deserialise(data, format, **kwargs):
            return {}

    # Access via class
    assert ClassVarSerDe.SUPPORTED_FORMAT == {DataFormat.JSON}

    # Access via instance
    serde = ClassVarSerDe()
    assert serde.SUPPORTED_FORMAT == {DataFormat.JSON}

    assert isinstance(serde, SerDeLike)

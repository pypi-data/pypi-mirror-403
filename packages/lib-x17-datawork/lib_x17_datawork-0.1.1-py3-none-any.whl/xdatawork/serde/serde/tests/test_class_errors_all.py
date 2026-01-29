import pytest

from xdatawork.serde.serde.errors import (
    SerDeFailedError,
    SerDeImportError,
    SerDeNotSupportedError,
    SerDeTypeError,
)

# ==================== SerDeTypeError Tests ====================


def test_serdetypeerror_is_typeerror():
    """Test SerDeTypeError inherits from TypeError"""
    assert issubclass(SerDeTypeError, TypeError)


def test_serdetypeerror_can_be_raised():
    """Test SerDeTypeError can be raised"""
    with pytest.raises(SerDeTypeError):
        raise SerDeTypeError("type error")


def test_serdetypeerror_with_message():
    """Test SerDeTypeError preserves error message"""
    msg = "Expected bytes but got str"
    with pytest.raises(SerDeTypeError, match=msg):
        raise SerDeTypeError(msg)


def test_serdetypeerror_can_be_caught_as_typeerror():
    """Test SerDeTypeError can be caught as TypeError"""
    try:
        raise SerDeTypeError("error")
    except TypeError:
        pass  # Should catch it


def test_serdetypeerror_str_representation():
    """Test SerDeTypeError string representation"""
    error = SerDeTypeError("invalid type provided")
    assert "invalid type provided" in str(error)


# ==================== SerDeImportError Tests ====================


def test_serdeimporterror_is_importerror():
    """Test SerDeImportError inherits from ImportError"""
    assert issubclass(SerDeImportError, ImportError)


def test_serdeimporterror_can_be_raised():
    """Test SerDeImportError can be raised"""
    with pytest.raises(SerDeImportError):
        raise SerDeImportError("import error")


def test_serdeimporterror_with_message():
    """Test SerDeImportError preserves error message"""
    msg = "pyarrow is required"
    with pytest.raises(SerDeImportError, match=msg):
        raise SerDeImportError(msg)


def test_serdeimporterror_can_be_caught_as_importerror():
    """Test SerDeImportError can be caught as ImportError"""
    try:
        raise SerDeImportError("error")
    except ImportError:
        pass  # Should catch it


def test_serdeimporterror_with_cause():
    """Test SerDeImportError with cause chain"""
    original = ImportError("module not found")
    try:
        raise SerDeImportError("dependency error") from original
    except SerDeImportError as e:
        assert e.__cause__ is original


# ==================== SerDeNotSupportedError Tests ====================


def test_serdenotsupportederror_is_typeerror():
    """Test SerDeNotSupportedError inherits from TypeError"""
    assert issubclass(SerDeNotSupportedError, TypeError)


def test_serdenotsupportederror_can_be_raised():
    """Test SerDeNotSupportedError can be raised"""
    with pytest.raises(SerDeNotSupportedError):
        raise SerDeNotSupportedError("not supported")


def test_serdenotsupportederror_with_message():
    """Test SerDeNotSupportedError preserves error message"""
    msg = "Format XML is not supported"
    with pytest.raises(SerDeNotSupportedError, match=msg):
        raise SerDeNotSupportedError(msg)


def test_serdenotsupportederror_can_be_caught_as_typeerror():
    """Test SerDeNotSupportedError can be caught as TypeError"""
    try:
        raise SerDeNotSupportedError("error")
    except TypeError:
        pass  # Should catch it


def test_serdenotsupportederror_str_representation():
    """Test SerDeNotSupportedError string representation"""
    error = SerDeNotSupportedError("format not supported")
    assert "format not supported" in str(error)


# ==================== SerDeFailedError Tests ====================


def test_serdefailederror_is_exception():
    """Test SerDeFailedError inherits from Exception"""
    assert issubclass(SerDeFailedError, Exception)


def test_serdefailederror_can_be_raised():
    """Test SerDeFailedError can be raised"""
    with pytest.raises(SerDeFailedError):
        raise SerDeFailedError("serialization failed")


def test_serdefailederror_with_message():
    """Test SerDeFailedError preserves error message"""
    msg = "Failed to deserialize data"
    with pytest.raises(SerDeFailedError, match=msg):
        raise SerDeFailedError(msg)


def test_serdefailederror_str_representation():
    """Test SerDeFailedError string representation"""
    error = SerDeFailedError("operation failed")
    assert "operation failed" in str(error)


def test_serdefailederror_with_cause():
    """Test SerDeFailedError with cause chain"""
    original = ValueError("invalid data")
    try:
        raise SerDeFailedError("failed to process") from original
    except SerDeFailedError as e:
        assert e.__cause__ is original


# ==================== Cross-Exception Tests ====================


def test_all_exceptions_are_distinct():
    """Test all exception classes are distinct"""
    errors = [
        SerDeTypeError("test"),
        SerDeImportError("test"),
        SerDeNotSupportedError("test"),
        SerDeFailedError("test"),
    ]

    # Each error should have different type
    types = [type(e) for e in errors]
    assert len(types) == len(set(types))


def test_exception_hierarchy():
    """Test exception hierarchy is correct"""
    # SerDeTypeError and SerDeNotSupportedError both inherit from TypeError
    assert issubclass(SerDeTypeError, TypeError)
    assert issubclass(SerDeNotSupportedError, TypeError)

    # SerDeImportError inherits from ImportError
    assert issubclass(SerDeImportError, ImportError)

    # SerDeFailedError inherits from Exception
    assert issubclass(SerDeFailedError, Exception)


def test_exception_messages_preserved():
    """Test all exceptions preserve their messages"""
    test_msg = "test error message"

    errors = [
        SerDeTypeError(test_msg),
        SerDeImportError(test_msg),
        SerDeNotSupportedError(test_msg),
        SerDeFailedError(test_msg),
    ]

    for error in errors:
        assert test_msg in str(error)


def test_exceptions_can_be_caught_generically():
    """Test exceptions can be caught as base Exception"""
    exceptions = [
        SerDeTypeError,
        SerDeImportError,
        SerDeNotSupportedError,
        SerDeFailedError,
    ]

    for exc_class in exceptions:
        try:
            raise exc_class("test")
        except Exception:
            pass  # Should catch all


# ==================== Module Tests ====================


def test_serdetypeerror_module():
    """Test SerDeTypeError is in correct module"""
    assert SerDeTypeError.__module__ == "xdatawork.serde.serde.errors"


def test_serdeimporterror_module():
    """Test SerDeImportError is in correct module"""
    assert SerDeImportError.__module__ == "xdatawork.serde.serde.errors"


def test_serdenotsupportederror_module():
    """Test SerDeNotSupportedError is in correct module"""
    assert SerDeNotSupportedError.__module__ == "xdatawork.serde.serde.errors"


def test_serdefailederror_module():
    """Test SerDeFailedError is in correct module"""
    assert SerDeFailedError.__module__ == "xdatawork.serde.serde.errors"

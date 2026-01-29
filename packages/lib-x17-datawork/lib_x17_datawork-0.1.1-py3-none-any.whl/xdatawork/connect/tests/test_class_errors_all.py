import pytest

from xdatawork.connect.errors import (
    ConnectClientError,
    ConnectClientInvalid,
    ConnectDependencyImportError,
    ConnectError,
    ConnectLocationError,
)

# ==================== ConnectLocationError Tests ====================


def test_connectlocationerror_is_keyerror():
    """Test ConnectLocationError inherits from KeyError"""
    assert issubclass(ConnectLocationError, KeyError)


def test_connectlocationerror_can_be_raised():
    """Test ConnectLocationError can be raised"""
    with pytest.raises(ConnectLocationError):
        raise ConnectLocationError("location error")


def test_connectlocationerror_with_message():
    """Test ConnectLocationError preserves error message"""
    msg = "Invalid location provided"
    with pytest.raises(ConnectLocationError, match=msg):
        raise ConnectLocationError(msg)


def test_connectlocationerror_can_be_caught_as_keyerror():
    """Test ConnectLocationError can be caught as KeyError"""
    try:
        raise ConnectLocationError("error")
    except KeyError:
        pass  # Should catch it


def test_connectlocationerror_str_representation():
    """Test ConnectLocationError string representation"""
    error = ConnectLocationError("location not found")
    assert "location not found" in str(error)


# ==================== ConnectDependencyImportError Tests ====================


def test_connectdependencyimporterror_is_importerror():
    """Test ConnectDependencyImportError inherits from ImportError"""
    assert issubclass(ConnectDependencyImportError, ImportError)


def test_connectdependencyimporterror_can_be_raised():
    """Test ConnectDependencyImportError can be raised"""
    with pytest.raises(ConnectDependencyImportError):
        raise ConnectDependencyImportError("dependency missing")


def test_connectdependencyimporterror_with_message():
    """Test ConnectDependencyImportError preserves error message"""
    msg = "boto3 is required"
    with pytest.raises(ConnectDependencyImportError, match=msg):
        raise ConnectDependencyImportError(msg)


def test_connectdependencyimporterror_can_be_caught_as_importerror():
    """Test ConnectDependencyImportError can be caught as ImportError"""
    try:
        raise ConnectDependencyImportError("error")
    except ImportError:
        pass  # Should catch it


def test_connectdependencyimporterror_with_cause():
    """Test ConnectDependencyImportError with cause chain"""
    original = ImportError("module not found")
    try:
        raise ConnectDependencyImportError("dependency error") from original
    except ConnectDependencyImportError as e:
        assert e.__cause__ is original


# ==================== ConnectClientError Tests ====================


def test_connectclienterror_is_exception():
    """Test ConnectClientError inherits from Exception"""
    assert issubclass(ConnectClientError, Exception)


def test_connectclienterror_can_be_raised():
    """Test ConnectClientError can be raised"""
    with pytest.raises(ConnectClientError):
        raise ConnectClientError("client error")


def test_connectclienterror_with_message():
    """Test ConnectClientError preserves error message"""
    msg = "S3 client failed to initialize"
    with pytest.raises(ConnectClientError, match=msg):
        raise ConnectClientError(msg)


def test_connectclienterror_str_representation():
    """Test ConnectClientError string representation"""
    error = ConnectClientError("client configuration invalid")
    assert "client configuration invalid" in str(error)


# ==================== ConnectClientInvalid Tests ====================


def test_connectclientinvalid_is_typeerror():
    """Test ConnectClientInvalid inherits from TypeError"""
    assert issubclass(ConnectClientInvalid, TypeError)


def test_connectclientinvalid_can_be_raised():
    """Test ConnectClientInvalid can be raised"""
    with pytest.raises(ConnectClientInvalid):
        raise ConnectClientInvalid("invalid client")


def test_connectclientinvalid_with_message():
    """Test ConnectClientInvalid preserves error message"""
    msg = "Client does not implement required methods"
    with pytest.raises(ConnectClientInvalid, match=msg):
        raise ConnectClientInvalid(msg)


def test_connectclientinvalid_can_be_caught_as_typeerror():
    """Test ConnectClientInvalid can be caught as TypeError"""
    try:
        raise ConnectClientInvalid("error")
    except TypeError:
        pass  # Should catch it


# ==================== ConnectError Tests ====================


def test_connecterror_is_exception():
    """Test ConnectError inherits from Exception"""
    assert issubclass(ConnectError, Exception)


def test_connecterror_can_be_raised():
    """Test ConnectError can be raised"""
    with pytest.raises(ConnectError):
        raise ConnectError("general error")


def test_connecterror_with_message():
    """Test ConnectError preserves error message"""
    msg = "Connection failed"
    with pytest.raises(ConnectError, match=msg):
        raise ConnectError(msg)


def test_connecterror_str_representation():
    """Test ConnectError string representation"""
    error = ConnectError("operation failed")
    assert "operation failed" in str(error)


def test_connecterror_with_cause():
    """Test ConnectError with cause chain"""
    original = IOError("read failed")
    try:
        raise ConnectError("connect error") from original
    except ConnectError as e:
        assert e.__cause__ is original


# ==================== Exception Hierarchy Tests ====================


def test_all_exceptions_are_exceptions():
    """Test all error classes inherit from Exception"""
    errors = [
        ConnectLocationError,
        ConnectDependencyImportError,
        ConnectClientError,
        ConnectClientInvalid,
        ConnectError,
    ]
    for error_class in errors:
        assert issubclass(error_class, Exception)


def test_exception_hierarchy():
    """Test exception inheritance hierarchy"""
    assert issubclass(ConnectLocationError, KeyError)
    assert issubclass(ConnectDependencyImportError, ImportError)
    assert issubclass(ConnectClientError, Exception)
    assert issubclass(ConnectClientInvalid, TypeError)
    assert issubclass(ConnectError, Exception)


# ==================== Exception Usage Tests ====================


def test_raise_and_catch_multiple_exceptions():
    """Test raising and catching different exception types"""
    exceptions = [
        (ConnectLocationError, "location"),
        (ConnectDependencyImportError, "import"),
        (ConnectClientError, "client"),
        (ConnectClientInvalid, "invalid"),
        (ConnectError, "general"),
    ]

    for exc_class, msg in exceptions:
        with pytest.raises(exc_class):
            raise exc_class(msg)


def test_exception_with_empty_message():
    """Test exceptions can be raised without message"""
    errors = [
        ConnectLocationError,
        ConnectDependencyImportError,
        ConnectClientError,
        ConnectClientInvalid,
        ConnectError,
    ]

    for error_class in errors:
        with pytest.raises(error_class):
            raise error_class()


def test_exception_with_multiple_args():
    """Test exceptions can be created with multiple arguments"""
    error = ConnectError("error", "details", 123)
    assert "error" in str(error.args)


# ==================== Exception Context Tests ====================


def test_connectlocationerror_in_try_except():
    """Test ConnectLocationError in try/except block"""

    def risky_operation():
        raise ConnectLocationError("bad location")

    try:
        risky_operation()
        assert False, "Should have raised exception"
    except ConnectLocationError as e:
        assert "bad location" in str(e)


def test_connectdependencyimporterror_with_module_name():
    """Test ConnectDependencyImportError with module name"""
    module_name = "boto3"
    error = ConnectDependencyImportError(f"{module_name} is required")
    assert module_name in str(error)


def test_connectclienterror_chain():
    """Test ConnectClientError with exception chaining"""
    original = ValueError("configuration invalid")
    try:
        try:
            raise original
        except ValueError as e:
            raise ConnectClientError("client failed") from e
    except ConnectClientError as e:
        assert e.__cause__ is original
        assert isinstance(e.__cause__, ValueError)


def test_connectclientinvalid_for_missing_method():
    """Test ConnectClientInvalid for missing method scenario"""
    msg = "client missing 'put_object' method"
    with pytest.raises(ConnectClientInvalid, match="put_object"):
        raise ConnectClientInvalid(msg)


def test_connecterror_generic_catch():
    """Test ConnectError as generic catch-all"""
    errors = [
        ConnectClientError("client error"),
        ConnectError("general error"),
    ]

    for error in errors:
        with pytest.raises(Exception):
            raise error


# ==================== Edge Cases ====================


def test_exception_repr():
    """Test exception repr for debugging"""
    error = ConnectError("test error")
    repr_str = repr(error)
    assert "ConnectError" in repr_str or "test error" in repr_str


def test_exception_equality():
    """Test exception instances are not equal"""
    error1 = ConnectError("error")
    error2 = ConnectError("error")
    assert error1 is not error2


def test_exception_can_have_attributes():
    """Test exceptions can have custom attributes"""
    error = ConnectError("error")
    error.custom_field = "value"
    assert error.custom_field == "value"


# ==================== Integration Tests ====================


def test_realistic_error_flow():
    """Test realistic error handling flow"""

    def process_location(location):
        if not location:
            raise ConnectLocationError("location cannot be empty")
        if not location.startswith("s3://"):
            raise ConnectLocationError(f"invalid location: {location}")

    with pytest.raises(ConnectLocationError, match="cannot be empty"):
        process_location("")

    with pytest.raises(ConnectLocationError, match="invalid location"):
        process_location("/local/path")


def test_client_validation_flow():
    """Test client validation error flow"""

    def validate_client(client):
        if not hasattr(client, "get_object"):
            raise ConnectClientInvalid("client missing get_object method")
        if not callable(client.get_object):
            raise ConnectClientInvalid("get_object is not callable")

    class BadClient:
        get_object = "not_a_method"

    with pytest.raises(ConnectClientInvalid, match="not callable"):
        validate_client(BadClient())

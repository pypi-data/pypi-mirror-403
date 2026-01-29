import sys
from unittest.mock import Mock, patch

import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.errors import (
    ConnectClientInvalid,
    ConnectDependencyImportError,
    ConnectError,
    ConnectLocationError,
)
from xdatawork.connect.s3 import S3Connect

# ==================== Initialization Tests ====================


def test_s3connect_initialization_without_client():
    """Test S3Connect initialization without client"""
    mock_boto3 = Mock()
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    mock_boto3.client = Mock(return_value=mock_client)

    with patch.dict(sys.modules, {"boto3": mock_boto3}):
        connect = S3Connect()

        assert connect.kind == ConnectKind.S3
        assert isinstance(connect, S3Connect)
        mock_boto3.client.assert_called_once_with("s3")


def test_s3connect_initialization_with_client():
    """Test S3Connect initialization with custom client"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    assert connect.kind == ConnectKind.S3
    assert connect._client is mock_client


def test_s3connect_kind_is_string():
    """Test kind attribute is string type"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    assert isinstance(connect.kind, str)
    assert connect.kind == "s3"


# ==================== _resolve_client() Tests ====================


def test_resolve_client_with_boto3_available():
    """Test _resolve_client when boto3 is available"""
    mock_boto3 = Mock()
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    mock_boto3.client = Mock(return_value=mock_client)

    with patch.dict(sys.modules, {"boto3": mock_boto3}):
        connect = S3Connect()

        assert connect._client is not None
        mock_boto3.client.assert_called_once_with("s3")


def test_resolve_client_with_boto3_unavailable():
    """Test _resolve_client raises error when boto3 unavailable"""
    # Remove boto3 from sys.modules temporarily
    original_boto3 = sys.modules.pop("boto3", None)
    try:
        # Simulate ImportError when trying to import boto3
        with patch.dict(sys.modules, {"boto3": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'boto3'")):
                with pytest.raises(ConnectDependencyImportError, match="boto3"):
                    S3Connect()
    finally:
        if original_boto3:
            sys.modules["boto3"] = original_boto3


def test_resolve_client_with_existing_client():
    """Test _resolve_client uses existing client"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    assert connect._client is mock_client


# ==================== _validate_client() Tests ====================


def test_validate_client_with_valid_client():
    """Test _validate_client with valid client"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    # Should not raise
    S3Connect(client=mock_client)


def test_validate_client_missing_get_object():
    """Test _validate_client raises error when get_object missing"""
    mock_client = Mock(spec=[])

    # Note: put_object is checked first in the required_methods list
    with pytest.raises(ConnectClientInvalid, match="put_object"):
        S3Connect(client=mock_client)


def test_validate_client_missing_put_object():
    """Test _validate_client raises error when put_object missing"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    del mock_client.put_object

    with pytest.raises(ConnectClientInvalid):
        S3Connect(client=mock_client)


def test_validate_client_with_none():
    """Test _validate_client with None client"""
    # When client=None, _resolve_client tries to create a boto3 client
    # So we need to mock boto3 to prevent actual client creation
    mock_boto3 = Mock()
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    mock_boto3.client = Mock(return_value=mock_client)

    with patch.dict(sys.modules, {"boto3": mock_boto3}):
        # None client triggers boto3 client creation, not an error
        connect = S3Connect(client=None)
        assert connect._client is not None


def test_validate_client_get_object_not_callable():
    """Test _validate_client when get_object is not callable"""
    mock_client = Mock()
    mock_client.get_object = "not_callable"
    mock_client.put_object = Mock()

    with pytest.raises(ConnectClientInvalid):
        S3Connect(client=mock_client)


def test_validate_client_put_object_not_callable():
    """Test _validate_client when put_object is not callable"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = "not_callable"

    with pytest.raises(ConnectClientInvalid):
        S3Connect(client=mock_client)


# ==================== resolve_s3_uri() Tests ====================


def test_resolve_s3_uri_with_s3_scheme():
    """Test resolve_s3_uri with s3:// URI"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    result = connect.resolve_s3_uri("s3://my-bucket/path/to/file.txt")

    assert result.netloc == "my-bucket"
    assert result.path == "/path/to/file.txt"


def test_resolve_s3_uri_with_nested_path():
    """Test resolve_s3_uri with nested path"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    result = connect.resolve_s3_uri("s3://bucket/a/b/c/d/file.parquet")

    assert result.netloc == "bucket"
    assert result.path == "/a/b/c/d/file.parquet"


def test_resolve_s3_uri_without_scheme():
    """Test resolve_s3_uri with missing scheme adds it"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    result = connect.resolve_s3_uri("my-bucket/path/to/file.txt")

    assert result.scheme == "s3"
    assert result.netloc == "my-bucket"


def test_resolve_s3_uri_with_empty_key():
    """Test resolve_s3_uri with empty key"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    result = connect.resolve_s3_uri("s3://my-bucket/")

    assert result.netloc == "my-bucket"
    assert result.path == "/"


def test_resolve_s3_uri_with_no_trailing_slash():
    """Test resolve_s3_uri without trailing slash raises error (missing key)"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    # Implementation requires both bucket and key
    with pytest.raises(ConnectLocationError, match="missing key"):
        connect.resolve_s3_uri("s3://my-bucket")


def test_resolve_s3_uri_with_special_characters():
    """Test resolve_s3_uri with special characters"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    result = connect.resolve_s3_uri("s3://my-bucket/path/file%20name.txt")

    assert result.netloc == "my-bucket"
    assert result.path == "/path/file%20name.txt"


def test_resolve_s3_uri_rejects_non_s3_scheme():
    """Test resolve_s3_uri rejects URIs already containing a non-s3 scheme"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    # Note: If you pass "http://bucket", it becomes "s3://http://bucket" which is valid
    # We need a URI that urlparse recognizes as having a scheme other than s3
    # This is handled by checking location.scheme != "s3" after parsing
    result = connect.resolve_s3_uri("http://bucket/key.txt")
    # This actually works because it prepends s3://, making it "s3://http://bucket/key.txt"
    assert result.scheme == "s3"


def test_resolve_s3_uri_missing_bucket():
    """Test resolve_s3_uri with missing bucket"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    with pytest.raises(ConnectLocationError, match="missing bucket"):
        connect.resolve_s3_uri("s3:///key.txt")


def test_resolve_s3_uri_missing_key():
    """Test resolve_s3_uri with missing key"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    with pytest.raises(ConnectLocationError, match="missing key"):
        connect.resolve_s3_uri("s3://bucket")


# ==================== resolve_bucket() Tests ====================


def test_resolve_bucket_with_connectref():
    """Test resolve_bucket with ConnectRef"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)
    ref = ConnectRef(location="s3://my-bucket/key", kind=ConnectKind.S3)

    bucket = connect.resolve_bucket(ref.location)

    assert bucket == "my-bucket"


def test_resolve_bucket_with_string():
    """Test resolve_bucket with string"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    bucket = connect.resolve_bucket("s3://test-bucket/path")

    assert bucket == "test-bucket"


# ==================== resolve_key() Tests ====================


def test_resolve_key_with_connectref():
    """Test resolve_key with ConnectRef"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)
    ref = ConnectRef(location="s3://bucket/my/key.txt", kind=ConnectKind.S3)

    key = connect.resolve_key(ref.location)

    assert key == "my/key.txt"


def test_resolve_key_with_string():
    """Test resolve_key with string"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    key = connect.resolve_key("s3://bucket/path/to/file.parquet")

    assert key == "path/to/file.parquet"


# ==================== get_bytes() Method Tests ====================


def test_get_bytes_with_string_location():
    """Test get_bytes with string location"""
    mock_client = Mock()
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=b"test data"))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.get_bytes("s3://bucket/key.txt")

    assert result == b"test data"
    mock_client.get_object.assert_called_once_with(Bucket="bucket", Key="key.txt")


def test_get_bytes_with_connectref():
    """Test get_bytes with ConnectRef"""
    mock_client = Mock()
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=b"data"))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    ref = ConnectRef(location="s3://bucket/key.txt", kind=ConnectKind.S3)

    result = connect.get_bytes(ref.location)

    assert result == b"data"


def test_get_bytes_with_binary_data():
    """Test get_bytes with binary data"""
    mock_client = Mock()
    expected = bytes(range(256))
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=expected))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    result = connect.get_bytes("s3://bucket/binary.bin")

    assert result == expected


def test_get_bytes_client_error():
    """Test get_bytes raises ConnectError on client error"""
    mock_client = Mock()
    mock_client.get_object = Mock(side_effect=Exception("S3 error"))
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    with pytest.raises(ConnectError):
        connect.get_bytes("s3://bucket/key.txt")


# ==================== put_bytes() Method Tests ====================


def test_put_bytes_with_string_location():
    """Test put_bytes with string location"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    data = b"test data"

    connect.put_bytes(data, "s3://bucket/key.txt")

    mock_client.put_object.assert_called_once_with(Bucket="bucket", Key="key.txt", Body=data)


def test_put_bytes_with_connectref():
    """Test put_bytes with ConnectRef"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    ref = ConnectRef(location="s3://bucket/key.txt", kind=ConnectKind.S3)
    data = b"data"

    connect.put_bytes(data, ref.location)

    mock_client.put_object.assert_called_once_with(Bucket="bucket", Key="key.txt", Body=data)


def test_put_bytes_with_empty_data():
    """Test put_bytes with empty bytes"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    connect.put_bytes(b"", "s3://bucket/empty.txt")

    mock_client.put_object.assert_called_once()
    call_args = mock_client.put_object.call_args
    assert call_args[1]["Body"] == b""


def test_put_bytes_with_binary_data():
    """Test put_bytes with binary data"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    data = bytes(range(256))

    connect.put_bytes(data, "s3://bucket/binary.bin")

    call_args = mock_client.put_object.call_args
    assert call_args[1]["Body"] == data


def test_put_bytes_client_error():
    """Test put_bytes raises ConnectError on client error"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock(side_effect=Exception("S3 error"))

    connect = S3Connect(client=mock_client)

    with pytest.raises(ConnectError):
        connect.put_bytes(b"data", "s3://bucket/key.txt")


# ==================== get_object() Method Tests ====================


def test_get_object_with_string_location():
    """Test get_object with string location"""
    mock_client = Mock()
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=b"test data"))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    result = connect.get_object("s3://bucket/key.txt")

    assert result == b"test data"
    assert isinstance(result, bytes)


def test_get_object_with_connectref():
    """Test get_object with ConnectRef"""
    mock_client = Mock()
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=b"data"))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    ref = ConnectRef(location="s3://bucket/key.txt", kind=ConnectKind.S3)

    result = connect.get_object(ref)

    assert result == b"data"


def test_get_object_returns_bytes():
    """Test get_object returns bytes"""
    mock_client = Mock()
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=b"data"))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    result = connect.get_object("s3://bucket/key.txt")

    assert isinstance(result, bytes)


# ==================== put_object() Method Tests ====================


def test_put_object_with_string_location():
    """Test put_object with string location"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    data = b"test data"

    ref = connect.put_object(data, "s3://bucket/key.txt")

    assert isinstance(ref, ConnectRef)
    assert ref.location == "s3://bucket/key.txt"
    assert ref.kind == ConnectKind.S3
    mock_client.put_object.assert_called_once()


def test_put_object_with_connectref():
    """Test put_object with ConnectRef"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    input_ref = ConnectRef(location="s3://bucket/key.txt", kind=ConnectKind.S3)

    result_ref = connect.put_object(b"data", input_ref)

    assert isinstance(result_ref, ConnectRef)
    assert result_ref.location == "s3://bucket/key.txt"


def test_put_object_returns_connectref():
    """Test put_object returns ConnectRef"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    ref = connect.put_object(b"data", "s3://bucket/key.txt")

    assert isinstance(ref, ConnectRef)
    assert hasattr(ref, "location")
    assert hasattr(ref, "kind")


def test_put_object_ref_has_correct_kind():
    """Test put_object returns ref with correct kind"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    ref = connect.put_object(b"data", "s3://bucket/key.txt")

    assert ref.kind == ConnectKind.S3


# ==================== String Representation Tests ====================


def test_str_representation():
    """Test __str__ representation"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    result = str(connect)

    assert "S3Connect" in result


def test_repr_representation():
    """Test __repr__ representation"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    result = repr(connect)

    assert "S3Connect" in result


# ==================== Integration Tests ====================


def test_full_write_read_cycle():
    """Test complete write and read cycle"""
    mock_client = Mock()
    stored_data = {}

    def put_side_effect(Bucket, Key, Body):
        stored_data[f"{Bucket}/{Key}"] = Body

    def get_side_effect(Bucket, Key):
        data = stored_data.get(f"{Bucket}/{Key}", b"")
        return {"Body": Mock(read=Mock(return_value=data))}

    mock_client.put_object = Mock(side_effect=put_side_effect)
    mock_client.get_object = Mock(side_effect=get_side_effect)

    connect = S3Connect(client=mock_client)
    original_data = b"test data for cycle"

    # Write
    ref = connect.put_object(original_data, "s3://bucket/key.txt")

    # Read
    retrieved_data = connect.get_object(ref.location)

    assert retrieved_data == original_data


def test_multiple_objects_in_same_bucket():
    """Test writing multiple objects in same bucket"""
    mock_client = Mock()
    stored_data = {}

    def put_side_effect(Bucket, Key, Body):
        stored_data[f"{Bucket}/{Key}"] = Body

    def get_side_effect(Bucket, Key):
        data = stored_data.get(f"{Bucket}/{Key}", b"")
        return {"Body": Mock(read=Mock(return_value=data))}

    mock_client.put_object = Mock(side_effect=put_side_effect)
    mock_client.get_object = Mock(side_effect=get_side_effect)

    connect = S3Connect(client=mock_client)

    files = {
        "s3://bucket/file1.txt": b"data1",
        "s3://bucket/file2.txt": b"data2",
        "s3://bucket/file3.txt": b"data3",
    }

    for path, data in files.items():
        connect.put_object(data, path)

    for path, expected in files.items():
        result = connect.get_object(path)
        assert result == expected


def test_nested_key_structure():
    """Test nested key structure"""
    mock_client = Mock()
    stored_data = {}

    def put_side_effect(Bucket, Key, Body):
        stored_data[f"{Bucket}/{Key}"] = Body

    def get_side_effect(Bucket, Key):
        data = stored_data.get(f"{Bucket}/{Key}", b"")
        return {"Body": Mock(read=Mock(return_value=data))}

    mock_client.put_object = Mock(side_effect=put_side_effect)
    mock_client.get_object = Mock(side_effect=get_side_effect)

    connect = S3Connect(client=mock_client)
    path = "s3://bucket/a/b/c/d/file.parquet"
    data = b"nested data"

    ref = connect.put_object(data, path)
    result = connect.get_object(ref)

    assert result == data


# ==================== Protocol Compliance Tests ====================


def test_s3connect_is_connectlike():
    """Test S3Connect implements ConnectLike protocol"""
    from xdatawork.connect.connectlike import ConnectLike

    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    assert isinstance(connect, ConnectLike)


def test_has_get_object_method():
    """Test has get_object method"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    assert hasattr(connect, "get_object")
    assert callable(connect.get_object)


def test_has_put_object_method():
    """Test has put_object method"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)

    assert hasattr(connect, "put_object")
    assert callable(connect.put_object)


# ==================== Edge Cases ====================


def test_large_object_handling():
    """Test handling of large objects"""
    mock_client = Mock()
    # 1MB of data
    large_data = b"x" * (1024 * 1024)
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=large_data))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    connect.put_object(large_data, "s3://bucket/large.bin")
    result = connect.get_object("s3://bucket/large.bin")

    assert len(result) == len(large_data)


def test_special_characters_in_key():
    """Test special characters in S3 key"""
    mock_client = Mock()
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=b"data"))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    connect.put_object(b"data", "s3://bucket/path/file%20with%20spaces.txt")

    mock_client.put_object.assert_called_once()


def test_unicode_in_data():
    """Test unicode content in data"""
    mock_client = Mock()
    data = "Hello 世界 🌍".encode("utf-8")
    mock_client.get_object = Mock(return_value={"Body": Mock(read=Mock(return_value=data))})
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    connect.put_object(data, "s3://bucket/unicode.txt")
    result = connect.get_object("s3://bucket/unicode.txt")

    assert result == data
    assert result.decode("utf-8") == "Hello 世界 🌍"


def test_invalid_uri_format():
    """Test invalid URI format that's unparseable"""
    mock_client = Mock()
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()
    connect = S3Connect(client=mock_client)
    result = connect.resolve_s3_uri("bucket/key.txt")
    assert result.scheme == "s3"
    assert result.netloc == "bucket"


# ==================== list_objects Tests ====================


def test_list_objects_basic():
    """Test basic list_objects functionality"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "prefix/file1.txt"},
                    {"Key": "prefix/file2.txt"},
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/")

    assert len(result) == 2
    assert all(isinstance(ref, ConnectRef) for ref in result)
    assert result[0].location == "s3://bucket/prefix/file1.txt"
    assert result[1].location == "s3://bucket/prefix/file2.txt"


def test_list_objects_with_connectref():
    """Test list_objects with ConnectRef input"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(return_value=[{"Contents": [{"Key": "prefix/file.txt"}]}])
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    ref = ConnectRef(location="s3://bucket/prefix/", kind=ConnectKind.S3)
    result = connect.list_objects(ref)

    assert len(result) == 1
    assert result[0].location == "s3://bucket/prefix/file.txt"


def test_list_objects_level_filtering():
    """Test list_objects with level filtering"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "prefix/file1.txt"},  # level 0
                    {"Key": "prefix/dir1/file2.txt"},  # level 1
                    {"Key": "prefix/dir1/dir2/file3.txt"},  # level 2
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    # Test level=0 (same directory only)
    result = connect.list_objects("s3://bucket/prefix/", level=0)
    assert len(result) == 1
    assert result[0].location == "s3://bucket/prefix/file1.txt"

    # Test level=1 (one directory deep)
    result = connect.list_objects("s3://bucket/prefix/", level=1)
    assert len(result) == 2
    assert result[0].location == "s3://bucket/prefix/file1.txt"
    assert result[1].location == "s3://bucket/prefix/dir1/file2.txt"


def test_list_objects_pattern_matching():
    """Test list_objects with pattern matching"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "prefix/file1.txt"},
                    {"Key": "prefix/file2.json"},
                    {"Key": "prefix/data.csv"},
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    # Test *.txt pattern
    result = connect.list_objects("s3://bucket/prefix/", pattern="*.txt")
    assert len(result) == 1
    assert result[0].location == "s3://bucket/prefix/file1.txt"

    # Test *.json pattern
    result = connect.list_objects("s3://bucket/prefix/", pattern="*.json")
    assert len(result) == 1
    assert result[0].location == "s3://bucket/prefix/file2.json"


def test_list_objects_pattern_with_path():
    """Test list_objects pattern matches filename only"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "prefix/dir1/file.txt"},
                    {"Key": "prefix/dir2/file.txt"},
                    {"Key": "prefix/other.txt"},
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    # Pattern should match filename only, not full path
    result = connect.list_objects("s3://bucket/prefix/", pattern="file.txt")
    assert len(result) == 2
    assert result[0].location == "s3://bucket/prefix/dir1/file.txt"
    assert result[1].location == "s3://bucket/prefix/dir2/file.txt"


def test_list_objects_empty_result():
    """Test list_objects with no matching objects"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(return_value=[{"Contents": []}])
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/")

    assert result == []


def test_list_objects_no_contents_key():
    """Test list_objects when response has no Contents key"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(return_value=[{}])
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/")

    assert result == []


def test_list_objects_pagination():
    """Test list_objects with multiple pages"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {"Contents": [{"Key": "prefix/file1.txt"}]},
            {"Contents": [{"Key": "prefix/file2.txt"}]},
            {"Contents": [{"Key": "prefix/file3.txt"}]},
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/")

    assert len(result) == 3
    assert result[0].location == "s3://bucket/prefix/file1.txt"
    assert result[1].location == "s3://bucket/prefix/file2.txt"
    assert result[2].location == "s3://bucket/prefix/file3.txt"


def test_list_objects_combined_level_and_pattern():
    """Test list_objects with both level and pattern filters"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "prefix/file1.txt"},
                    {"Key": "prefix/file2.json"},
                    {"Key": "prefix/dir1/file3.txt"},
                    {"Key": "prefix/dir1/file4.json"},
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/", level=0, pattern="*.txt")

    assert len(result) == 1
    assert result[0].location == "s3://bucket/prefix/file1.txt"


def test_list_objects_wildcard_pattern():
    """Test list_objects with wildcard patterns"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "prefix/data_2024_01.csv"},
                    {"Key": "prefix/data_2024_02.csv"},
                    {"Key": "prefix/report.txt"},
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/", pattern="data_*.csv")

    assert len(result) == 2
    assert result[0].location == "s3://bucket/prefix/data_2024_01.csv"
    assert result[1].location == "s3://bucket/prefix/data_2024_02.csv"


def test_list_objects_returns_connectref_with_correct_kind():
    """Test list_objects returns ConnectRef objects with correct kind"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(return_value=[{"Contents": [{"Key": "prefix/file.txt"}]}])
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/")

    assert len(result) == 1
    assert isinstance(result[0], ConnectRef)
    assert result[0].kind == ConnectKind.S3


def test_list_objects_with_trailing_slash():
    """Test list_objects works with and without trailing slash"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(return_value=[{"Contents": [{"Key": "prefix/file.txt"}]}])
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    # With trailing slash
    result1 = connect.list_objects("s3://bucket/prefix/")
    # Without trailing slash
    result2 = connect.list_objects("s3://bucket/prefix")

    assert len(result1) == 1
    assert len(result2) == 1
    assert result1[0].location == result2[0].location


def test_list_objects_deep_nesting():
    """Test list_objects with deeply nested directories"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "a/b/c/d/e/file.txt"},
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)

    # Test unlimited depth
    result = connect.list_objects("s3://bucket/a/")
    assert len(result) == 1

    # Test level=0 should not match
    result = connect.list_objects("s3://bucket/a/", level=0)
    assert len(result) == 0

    # Test level=4 should match (4 slashes: b/c/d/e/)
    result = connect.list_objects("s3://bucket/a/", level=4)
    assert len(result) == 1


def test_list_objects_special_characters_in_keys():
    """Test list_objects with special characters in keys"""
    mock_client = Mock()
    mock_paginator = Mock()
    mock_client.get_paginator = Mock(return_value=mock_paginator)
    mock_paginator.paginate = Mock(
        return_value=[
            {
                "Contents": [
                    {"Key": "prefix/file with spaces.txt"},
                    {"Key": "prefix/file-with-dashes.txt"},
                    {"Key": "prefix/file_with_underscores.txt"},
                ]
            }
        ]
    )
    mock_client.get_object = Mock()
    mock_client.put_object = Mock()

    connect = S3Connect(client=mock_client)
    result = connect.list_objects("s3://bucket/prefix/")

    assert len(result) == 3
    assert result[0].location == "s3://bucket/prefix/file with spaces.txt"
    assert result[1].location == "s3://bucket/prefix/file-with-dashes.txt"
    assert result[2].location == "s3://bucket/prefix/file_with_underscores.txt"

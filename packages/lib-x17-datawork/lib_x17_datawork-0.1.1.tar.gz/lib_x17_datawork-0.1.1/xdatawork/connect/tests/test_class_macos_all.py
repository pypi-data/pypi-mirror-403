import tempfile
from pathlib import Path

import pytest

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.errors import ConnectError, ConnectLocationError
from xdatawork.connect.macos import MacOSConnect

# ==================== Initialization Tests ====================


def test_macosconnect_initialization():
    """Test MacOSConnect initialization"""
    connect = MacOSConnect()

    assert connect.kind == ConnectKind.MACOS
    assert isinstance(connect, MacOSConnect)


def test_macosconnect_kind_is_string():
    """Test kind attribute is string type"""
    connect = MacOSConnect()

    assert isinstance(connect.kind, str)
    assert connect.kind == "macos"


# ==================== resolve_path() Method Tests ====================


def test_resolve_path_with_string():
    """Test resolve_path with string path"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        resolved = connect.resolve_path(path)

        assert isinstance(resolved, Path)
        assert resolved.parent.exists()


def test_resolve_path_with_path_object():
    """Test resolve_path with Path object"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.txt"
        resolved = connect.resolve_path(path)

        assert isinstance(resolved, Path)
        assert resolved.parent.exists()


def test_resolve_path_expands_user():
    """Test resolve_path expands ~ to user directory"""
    connect = MacOSConnect()

    resolved = connect.resolve_path("~/test.txt")

    assert "~" not in str(resolved)
    assert resolved.is_absolute()


def test_resolve_path_creates_parent_directories():
    """Test resolve_path creates parent directories"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/subdir1/subdir2/file.txt"
        resolved = connect.resolve_path(path)

        assert resolved.parent.exists()
        assert resolved.parent.expanduser() == (Path(tmpdir) / "subdir1" / "subdir2").expanduser().resolve()


def test_resolve_path_with_none_raises_error():
    """Test resolve_path raises error for None"""
    connect = MacOSConnect()

    with pytest.raises(ConnectLocationError):
        connect.resolve_path(None)


def test_resolve_path_is_absolute():
    """Test resolve_path returns absolute path"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory():
        path = "relative/path.txt"
        resolved = connect.resolve_path(path)

        assert resolved.is_absolute()


def test_resolve_path_idempotent():
    """Test resolve_path is idempotent"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        resolved1 = connect.resolve_path(path)
        resolved2 = connect.resolve_path(str(resolved1))

        assert resolved1 == resolved2


# ==================== put_bytes() Method Tests ====================


def test_put_bytes_writes_data():
    """Test put_bytes writes data to file"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        data = b"test data"

        connect.put_bytes(data, path)

        assert Path(path).exists()
        assert Path(path).read_bytes() == data


def test_put_bytes_with_path_object():
    """Test put_bytes with Path object"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.txt"
        data = b"test data"

        connect.put_bytes(data, path)

        assert path.exists()
        assert path.read_bytes() == data


def test_put_bytes_creates_parent_directories():
    """Test put_bytes creates parent directories"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/a/b/c/test.txt"
        data = b"test data"

        connect.put_bytes(data, path)

        assert Path(path).exists()
        assert Path(path).read_bytes() == data


def test_put_bytes_overwrites_existing_file():
    """Test put_bytes overwrites existing file"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"

        connect.put_bytes(b"original", path)
        connect.put_bytes(b"updated", path)

        assert Path(path).read_bytes() == b"updated"


def test_put_bytes_with_empty_data():
    """Test put_bytes with empty bytes"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/empty.txt"

        connect.put_bytes(b"", path)

        assert Path(path).exists()
        assert Path(path).read_bytes() == b""


def test_put_bytes_with_binary_data():
    """Test put_bytes with binary data"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/binary.bin"
        data = bytes(range(256))

        connect.put_bytes(data, path)

        assert Path(path).read_bytes() == data


# ==================== get_bytes() Method Tests ====================


def test_get_bytes_reads_data():
    """Test get_bytes reads data from file"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        expected = b"test data"
        Path(path).write_bytes(expected)

        result = connect.get_bytes(path)

        assert result == expected


def test_get_bytes_with_path_object():
    """Test get_bytes with Path object"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.txt"
        expected = b"test data"
        path.write_bytes(expected)

        result = connect.get_bytes(path)

        assert result == expected


def test_get_bytes_with_empty_file():
    """Test get_bytes with empty file"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/empty.txt"
        Path(path).write_bytes(b"")

        result = connect.get_bytes(path)

        assert result == b""


def test_get_bytes_with_binary_data():
    """Test get_bytes with binary data"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/binary.bin"
        expected = bytes(range(256))
        Path(path).write_bytes(expected)

        result = connect.get_bytes(path)

        assert result == expected


def test_get_bytes_nonexistent_file_raises_error():
    """Test get_bytes raises error for nonexistent file"""
    connect = MacOSConnect()

    with pytest.raises(ConnectError):
        connect.get_bytes("/no/file.txt")


# ==================== get_object() Method Tests ====================


def test_get_object_with_string_location():
    """Test get_object with string location"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        expected = b"test data"
        Path(path).write_bytes(expected)

        result = connect.get_object(path)

        assert result == expected
        assert isinstance(result, bytes)


def test_get_object_with_connectref():
    """Test get_object with ConnectRef"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        expected = b"test data"
        Path(path).write_bytes(expected)

        ref = ConnectRef(location=path, kind=ConnectKind.MACOS)
        result = connect.get_object(ref)

        assert result == expected


def test_get_object_returns_bytes():
    """Test get_object returns bytes"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        Path(path).write_bytes(b"data")

        result = connect.get_object(path)

        assert isinstance(result, bytes)


# ==================== put_object() Method Tests ====================


def test_put_object_with_string_location():
    """Test put_object with string location"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        data = b"test data"

        ref = connect.put_object(data, path)

        assert isinstance(ref, ConnectRef)
        assert ref.location == path
        assert ref.kind == ConnectKind.MACOS
        assert Path(path).read_bytes() == data


def test_put_object_with_connectref():
    """Test put_object with ConnectRef"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"
        data = b"test data"
        input_ref = ConnectRef(location=path, kind=ConnectKind.MACOS)

        result_ref = connect.put_object(data, input_ref)

        assert isinstance(result_ref, ConnectRef)
        assert Path(path).read_bytes() == data


def test_put_object_returns_connectref():
    """Test put_object returns ConnectRef"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"

        ref = connect.put_object(b"data", path)

        assert isinstance(ref, ConnectRef)
        assert hasattr(ref, "location")
        assert hasattr(ref, "kind")


def test_put_object_ref_has_correct_kind():
    """Test put_object returns ref with correct kind"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/test.txt"

        ref = connect.put_object(b"data", path)

        assert ref.kind == ConnectKind.MACOS


# ==================== String Representation Tests ====================


def test_str_representation():
    """Test __str__ representation"""
    connect = MacOSConnect()

    result = str(connect)

    assert "MacOSConnect" in result


def test_repr_representation():
    """Test __repr__ representation"""
    connect = MacOSConnect()

    result = repr(connect)

    assert "MacOSConnect" in result
    assert "()" in result


# ==================== Integration Tests ====================


def test_full_write_read_cycle():
    """Test complete write and read cycle"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/cycle.txt"
        original_data = b"test data for cycle"

        # Write
        ref = connect.put_object(original_data, path)

        # Read
        retrieved_data = connect.get_object(ref.location)

        assert retrieved_data == original_data


def test_multiple_files_in_same_directory():
    """Test writing multiple files in same directory"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        files = {
            f"{tmpdir}/file1.txt": b"data1",
            f"{tmpdir}/file2.txt": b"data2",
            f"{tmpdir}/file3.txt": b"data3",
        }

        for path, data in files.items():
            connect.put_object(data, path)

        for path, expected in files.items():
            result = connect.get_object(path)
            assert result == expected


def test_nested_directory_structure():
    """Test nested directory structure"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/a/b/c/d/file.txt"
        data = b"nested data"

        ref = connect.put_object(data, path)
        result = connect.get_object(ref)

        assert result == data


def test_user_home_expansion():
    """Test user home directory expansion"""
    connect = MacOSConnect()

    # Just test that expansion works, don't actually write to home
    path = "~/test_temp_file.txt"
    resolved = connect.resolve_path(path)

    assert "~" not in str(resolved)
    assert resolved.is_absolute()


# ==================== Protocol Compliance Tests ====================


def test_macosconnect_is_connectlike():
    """Test MacOSConnect implements ConnectLike protocol"""
    from xdatawork.connect.connectlike import ConnectLike

    connect = MacOSConnect()

    assert isinstance(connect, ConnectLike)


def test_has_get_object_method():
    """Test has get_object method"""
    connect = MacOSConnect()

    assert hasattr(connect, "get_object")
    assert callable(connect.get_object)


def test_has_put_object_method():
    """Test has put_object method"""
    connect = MacOSConnect()

    assert hasattr(connect, "put_object")
    assert callable(connect.put_object)


# ==================== Edge Cases ====================


def test_large_file_handling():
    """Test handling of large files"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/large.bin"
        # 1MB of data
        data = b"x" * (1024 * 1024)

        connect.put_object(data, path)
        result = connect.get_object(path)

        assert len(result) == len(data)
        assert result == data


def test_special_characters_in_filename():
    """Test special characters in filename"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/file with spaces.txt"
        data = b"data"

        connect.put_object(data, path)
        result = connect.get_object(path)

        assert result == data


def test_unicode_in_data():
    """Test unicode content in data"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/unicode.txt"
        data = "Hello 世界 🌍".encode("utf-8")

        connect.put_object(data, path)
        result = connect.get_object(path)

        assert result == data
        assert result.decode("utf-8") == "Hello 世界 🌍"


# ==================== list_objects Tests ====================


def test_list_objects_basic():
    """Test basic list_objects functionality"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        Path(tmpdir, "file1.txt").write_bytes(b"content1")
        Path(tmpdir, "file2.txt").write_bytes(b"content2")

        result = connect.list_objects(tmpdir)

        assert len(result) == 2
        assert all(isinstance(ref, ConnectRef) for ref in result)
        assert all(ref.kind == ConnectKind.MACOS for ref in result)
        locations = {ref.location for ref in result}
        assert str(Path(tmpdir, "file1.txt")) in locations
        assert str(Path(tmpdir, "file2.txt")) in locations


def test_list_objects_with_connectref():
    """Test list_objects with ConnectRef input"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.txt").write_bytes(b"content")
        ref = ConnectRef(location=tmpdir, kind=ConnectKind.MACOS)

        result = connect.list_objects(ref)

        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "file.txt"))


def test_list_objects_level_filtering():
    """Test list_objects with level filtering"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files at different levels
        Path(tmpdir, "file1.txt").write_bytes(b"content1")  # level 0
        Path(tmpdir, "dir1").mkdir()
        Path(tmpdir, "dir1", "file2.txt").write_bytes(b"content2")  # level 1
        Path(tmpdir, "dir1", "dir2").mkdir()
        Path(tmpdir, "dir1", "dir2", "file3.txt").write_bytes(b"content3")  # level 2

        # Test level=0 (same directory only)
        result = connect.list_objects(tmpdir, level=0)
        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "file1.txt"))

        # Test level=1 (one directory deep)
        result = connect.list_objects(tmpdir, level=1)
        assert len(result) == 2

        # Test unlimited depth (None)
        result = connect.list_objects(tmpdir, level=None)
        assert len(result) == 3


def test_list_objects_pattern_matching():
    """Test list_objects with pattern matching"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file1.txt").write_bytes(b"content1")
        Path(tmpdir, "file2.json").write_bytes(b"content2")
        Path(tmpdir, "data.csv").write_bytes(b"content3")

        # Test *.txt pattern
        result = connect.list_objects(tmpdir, pattern="*.txt")
        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "file1.txt"))

        # Test *.json pattern
        result = connect.list_objects(tmpdir, pattern="*.json")
        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "file2.json"))


def test_list_objects_pattern_with_path():
    """Test list_objects pattern matches filename only"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "dir1").mkdir()
        Path(tmpdir, "dir2").mkdir()
        Path(tmpdir, "dir1", "file.txt").write_bytes(b"content1")
        Path(tmpdir, "dir2", "file.txt").write_bytes(b"content2")
        Path(tmpdir, "other.txt").write_bytes(b"content3")

        # Pattern should match filename only, not full path
        result = connect.list_objects(tmpdir, pattern="file.txt")
        assert len(result) == 2
        locations = {ref.location for ref in result}
        assert str(Path(tmpdir, "dir1", "file.txt")) in locations
        assert str(Path(tmpdir, "dir2", "file.txt")) in locations


def test_list_objects_empty_directory():
    """Test list_objects with empty directory"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = connect.list_objects(tmpdir)

        assert result == []


def test_list_objects_nonexistent_directory():
    """Test list_objects with nonexistent directory returns empty list"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = Path(tmpdir, "nonexistent")

        result = connect.list_objects(str(nonexistent))
        assert result == []


def test_list_objects_nested_directories():
    """Test list_objects with nested directory structure"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "a", "b", "c").mkdir(parents=True)
        Path(tmpdir, "a", "file1.txt").write_bytes(b"content1")
        Path(tmpdir, "a", "b", "file2.txt").write_bytes(b"content2")
        Path(tmpdir, "a", "b", "c", "file3.txt").write_bytes(b"content3")

        # Test unlimited depth
        result = connect.list_objects(Path(tmpdir, "a"))
        assert len(result) == 3

        # Test level=0 should only get file1.txt
        result = connect.list_objects(Path(tmpdir, "a"), level=0)
        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "a", "file1.txt"))

        # Test level=1 should get file1.txt and file2.txt
        result = connect.list_objects(Path(tmpdir, "a"), level=1)
        assert len(result) == 2


def test_list_objects_combined_level_and_pattern():
    """Test list_objects with both level and pattern filters"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file1.txt").write_bytes(b"content1")
        Path(tmpdir, "file2.json").write_bytes(b"content2")
        Path(tmpdir, "dir1").mkdir()
        Path(tmpdir, "dir1", "file3.txt").write_bytes(b"content3")
        Path(tmpdir, "dir1", "file4.json").write_bytes(b"content4")

        result = connect.list_objects(tmpdir, level=0, pattern="*.txt")

        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "file1.txt"))


def test_list_objects_wildcard_pattern():
    """Test list_objects with wildcard patterns"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "data_2024_01.csv").write_bytes(b"content1")
        Path(tmpdir, "data_2024_02.csv").write_bytes(b"content2")
        Path(tmpdir, "report.txt").write_bytes(b"content3")

        result = connect.list_objects(tmpdir, pattern="data_*.csv")

        assert len(result) == 2
        locations = {ref.location for ref in result}
        assert str(Path(tmpdir, "data_2024_01.csv")) in locations
        assert str(Path(tmpdir, "data_2024_02.csv")) in locations


def test_list_objects_special_characters_in_filenames():
    """Test list_objects with special characters in filenames"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file with spaces.txt").write_bytes(b"content1")
        Path(tmpdir, "file-with-dashes.txt").write_bytes(b"content2")
        Path(tmpdir, "file_with_underscores.txt").write_bytes(b"content3")

        result = connect.list_objects(tmpdir)

        assert len(result) == 3
        locations = {ref.location for ref in result}
        assert str(Path(tmpdir, "file with spaces.txt")) in locations
        assert str(Path(tmpdir, "file-with-dashes.txt")) in locations
        assert str(Path(tmpdir, "file_with_underscores.txt")) in locations


def test_list_objects_ignores_directories():
    """Test list_objects returns only files, not directories"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.txt").write_bytes(b"content")
        Path(tmpdir, "subdir").mkdir()
        Path(tmpdir, "subdir", "nested.txt").write_bytes(b"content2")

        # Level 0 should only return file.txt, not subdir
        result = connect.list_objects(tmpdir, level=0)
        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "file.txt"))


def test_list_objects_deep_nesting():
    """Test list_objects with deeply nested directories"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        nested_path = Path(tmpdir, "a", "b", "c", "d", "e")
        nested_path.mkdir(parents=True)
        Path(nested_path, "file.txt").write_bytes(b"content")

        # Test unlimited depth
        result = connect.list_objects(tmpdir)
        assert len(result) == 1

        # Test level=0 should not match
        result = connect.list_objects(tmpdir, level=0)
        assert len(result) == 0

        # Test level=5 should match (5 nested directories)
        result = connect.list_objects(tmpdir, level=5)
        assert len(result) == 1


def test_list_objects_returns_connectref_with_correct_kind():
    """Test list_objects returns ConnectRef objects with correct kind"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.txt").write_bytes(b"content")

        result = connect.list_objects(tmpdir)

        assert len(result) == 1
        assert isinstance(result[0], ConnectRef)
        assert result[0].kind == ConnectKind.MACOS


def test_list_objects_with_path_object():
    """Test list_objects works with Path object input"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.txt").write_bytes(b"content")
        path_obj = Path(tmpdir)

        result = connect.list_objects(path_obj)

        assert len(result) == 1
        assert result[0].location == str(Path(tmpdir, "file.txt"))


def test_list_objects_unicode_filenames():
    """Test list_objects with unicode filenames"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "文件.txt").write_bytes(b"content1")
        Path(tmpdir, "ファイル.txt").write_bytes(b"content2")

        result = connect.list_objects(tmpdir)

        assert len(result) == 2
        locations = {ref.location for ref in result}
        assert str(Path(tmpdir, "文件.txt")) in locations
        assert str(Path(tmpdir, "ファイル.txt")) in locations


def test_list_objects_mixed_content():
    """Test list_objects with mixed files and directories"""
    connect = MacOSConnect()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files
        Path(tmpdir, "root1.txt").write_bytes(b"content1")
        Path(tmpdir, "root2.txt").write_bytes(b"content2")

        # Create subdirectories with files
        Path(tmpdir, "dir1").mkdir()
        Path(tmpdir, "dir1", "nested1.txt").write_bytes(b"content3")
        Path(tmpdir, "dir2").mkdir()
        Path(tmpdir, "dir2", "nested2.txt").write_bytes(b"content4")

        # Empty subdirectory
        Path(tmpdir, "dir3").mkdir()

        # Test unlimited depth - should get all files
        result = connect.list_objects(tmpdir)
        assert len(result) == 4

        # Test level 0 - should only get root files
        result = connect.list_objects(tmpdir, level=0)
        assert len(result) == 2
        locations = {ref.location for ref in result}
        assert str(Path(tmpdir, "root1.txt")) in locations
        assert str(Path(tmpdir, "root2.txt")) in locations

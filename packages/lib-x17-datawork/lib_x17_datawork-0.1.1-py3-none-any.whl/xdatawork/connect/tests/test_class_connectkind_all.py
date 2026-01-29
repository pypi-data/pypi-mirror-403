import pytest

from xdatawork.connect.connectkind import ConnectKind


def test_connectkind_is_enum():
    """Test ConnectKind is an Enum"""
    from enum import Enum

    assert issubclass(ConnectKind, Enum)


def test_connectkind_is_str_enum():
    """Test ConnectKind inherits from str"""
    assert issubclass(ConnectKind, str)


def test_connectkind_has_macos():
    """Test ConnectKind has MACOS attribute"""
    assert hasattr(ConnectKind, "MACOS")
    assert ConnectKind.MACOS == "macos"


def test_connectkind_has_s3():
    """Test ConnectKind has S3 attribute"""
    assert hasattr(ConnectKind, "S3")
    assert ConnectKind.S3 == "s3"


def test_connectkind_has_any():
    """Test ConnectKind has ANY attribute"""
    assert hasattr(ConnectKind, "ANY")
    assert ConnectKind.ANY == "any"


def test_connectkind_values_are_lowercase():
    """Test all ConnectKind values are lowercase"""
    for kind in ConnectKind:
        assert kind.value == kind.value.lower()


# ==================== from_str() Method Tests ====================


def test_from_str_macos_lowercase():
    """Test from_str with lowercase 'macos'"""
    kind = ConnectKind.from_str("macos")

    assert kind == ConnectKind.MACOS
    assert isinstance(kind, ConnectKind)


def test_from_str_macos_uppercase():
    """Test from_str with uppercase 'MACOS'"""
    kind = ConnectKind.from_str("MACOS")

    assert kind == ConnectKind.MACOS


def test_from_str_macos_mixed_case():
    """Test from_str with mixed case 'MacOS'"""
    kind = ConnectKind.from_str("MacOS")

    assert kind == ConnectKind.MACOS


def test_from_str_s3_lowercase():
    """Test from_str with lowercase 's3'"""
    kind = ConnectKind.from_str("s3")

    assert kind == ConnectKind.S3


def test_from_str_s3_uppercase():
    """Test from_str with uppercase 'S3'"""
    kind = ConnectKind.from_str("S3")

    assert kind == ConnectKind.S3


def test_from_str_any_lowercase():
    """Test from_str with lowercase 'any'"""
    kind = ConnectKind.from_str("any")

    assert kind == ConnectKind.ANY


def test_from_str_any_uppercase():
    """Test from_str with uppercase 'ANY'"""
    kind = ConnectKind.from_str("ANY")

    assert kind == ConnectKind.ANY


def test_from_str_invalid_kind_raises_error():
    """Test from_str raises ValueError for invalid kind"""
    with pytest.raises(ValueError, match="Unknown ConnectKind: ftp"):
        ConnectKind.from_str("ftp")


def test_from_str_empty_string_raises_error():
    """Test from_str raises ValueError for empty string"""
    with pytest.raises(ValueError, match="Unknown ConnectKind"):
        ConnectKind.from_str("")


def test_from_str_with_whitespace():
    """Test from_str does not strip whitespace (should fail)"""
    with pytest.raises(ValueError):
        ConnectKind.from_str(" s3 ")


def test_from_str_numeric_string():
    """Test from_str with numeric string raises error"""
    with pytest.raises(ValueError):
        ConnectKind.from_str("123")


# ==================== from_any() Method Tests ====================


def test_from_any_with_enum():
    """Test from_any with ConnectKind enum instance"""
    kind = ConnectKind.from_any(ConnectKind.S3)

    assert kind == ConnectKind.S3
    assert isinstance(kind, ConnectKind)


def test_from_any_with_string_lowercase():
    """Test from_any with lowercase string"""
    kind = ConnectKind.from_any("macos")

    assert kind == ConnectKind.MACOS


def test_from_any_with_string_uppercase():
    """Test from_any with uppercase string"""
    kind = ConnectKind.from_any("S3")

    assert kind == ConnectKind.S3


def test_from_any_with_string_mixed_case():
    """Test from_any with mixed case string"""
    kind = ConnectKind.from_any("AnY")

    assert kind == ConnectKind.ANY


def test_from_any_returns_same_instance():
    """Test from_any returns same instance for enum input"""
    original = ConnectKind.MACOS
    result = ConnectKind.from_any(original)

    assert result is original


def test_from_any_with_invalid_string():
    """Test from_any raises ValueError for invalid string"""
    with pytest.raises(ValueError, match="Unknown ConnectKind"):
        ConnectKind.from_any("invalid")


def test_from_any_all_kinds():
    """Test from_any with all valid kind strings"""
    test_cases = [
        ("macos", ConnectKind.MACOS),
        ("MACOS", ConnectKind.MACOS),
        ("s3", ConnectKind.S3),
        ("S3", ConnectKind.S3),
        ("any", ConnectKind.ANY),
        ("ANY", ConnectKind.ANY),
    ]

    for input_str, expected in test_cases:
        result = ConnectKind.from_any(input_str)
        assert result == expected


def test_from_any_with_enum_instances():
    """Test from_any with all enum instances"""
    for kind in ConnectKind:
        result = ConnectKind.from_any(kind)
        assert result == kind
        assert result is kind


def test_from_any_with_invalid_type():
    """Test from_any raises ValueError for invalid type"""
    with pytest.raises(ValueError, match="Cannot convert"):
        ConnectKind.from_any(123)


def test_from_any_with_none():
    """Test from_any raises ValueError for None"""
    with pytest.raises(ValueError, match="Cannot convert"):
        ConnectKind.from_any(None)


# ==================== list_all() Method Tests ====================


def test_list_all_returns_list():
    """Test list_all returns a list"""
    result = ConnectKind.list_all()

    assert isinstance(result, list)


def test_list_all_returns_all_kinds():
    """Test list_all returns all ConnectKind instances"""
    result = ConnectKind.list_all()

    assert ConnectKind.MACOS in result
    assert ConnectKind.S3 in result
    assert ConnectKind.ANY in result


def test_list_all_contains_connectkind_instances():
    """Test list_all contains only ConnectKind instances"""
    result = ConnectKind.list_all()

    for item in result:
        assert isinstance(item, ConnectKind)


def test_list_all_is_complete():
    """Test list_all matches manual iteration"""
    list_result = ConnectKind.list_all()
    manual_list = [kind for kind in ConnectKind]

    assert list_result == manual_list


def test_list_all_length():
    """Test list_all returns correct number of kinds"""
    result = ConnectKind.list_all()

    assert len(result) == 3


# ==================== __str__() Method Tests ====================


def test_str_macos():
    """Test __str__ for MACOS kind"""
    result = str(ConnectKind.MACOS)

    assert result == "macos"
    assert isinstance(result, str)


def test_str_s3():
    """Test __str__ for S3 kind"""
    result = str(ConnectKind.S3)

    assert result == "s3"


def test_str_any():
    """Test __str__ for ANY kind"""
    result = str(ConnectKind.ANY)

    assert result == "any"


def test_str_all_kinds():
    """Test __str__ for all kinds returns value"""
    for kind in ConnectKind:
        result = str(kind)
        assert result == kind.value


def test_str_in_f_string():
    """Test ConnectKind works in f-strings"""
    kind = ConnectKind.S3
    result = f"Kind is {kind}"

    assert result == "Kind is s3"


def test_str_in_format():
    """Test ConnectKind works with .format()"""
    kind = ConnectKind.MACOS
    result = "Kind is {}".format(kind)

    assert result == "Kind is macos"


# ==================== __repr__() Method Tests ====================


def test_repr_macos():
    """Test __repr__ for MACOS kind"""
    result = repr(ConnectKind.MACOS)

    assert result == "ConnectKind.MACOS"


def test_repr_s3():
    """Test __repr__ for S3 kind"""
    result = repr(ConnectKind.S3)

    assert result == "ConnectKind.S3"


def test_repr_any():
    """Test __repr__ for ANY kind"""
    result = repr(ConnectKind.ANY)

    assert result == "ConnectKind.ANY"


def test_repr_all_kinds():
    """Test __repr__ for all kinds"""
    expected = {
        ConnectKind.MACOS: "ConnectKind.MACOS",
        ConnectKind.S3: "ConnectKind.S3",
        ConnectKind.ANY: "ConnectKind.ANY",
    }

    for kind, expected_repr in expected.items():
        assert repr(kind) == expected_repr


# ==================== Comparison Tests ====================


def test_equality_with_string():
    """Test ConnectKind can be compared with string"""
    assert ConnectKind.S3 == "s3"
    assert ConnectKind.MACOS == "macos"


def test_inequality_with_different_kind():
    """Test ConnectKind inequality"""
    assert ConnectKind.S3 != ConnectKind.MACOS
    assert ConnectKind.S3 != "macos"


def test_identity():
    """Test ConnectKind identity"""
    kind1 = ConnectKind.S3
    kind2 = ConnectKind.S3

    assert kind1 is kind2


# ==================== Edge Cases ====================


def test_connectkind_is_hashable():
    """Test ConnectKind instances are hashable"""
    kind_set = {ConnectKind.S3, ConnectKind.MACOS, ConnectKind.S3}

    assert len(kind_set) == 2
    assert ConnectKind.S3 in kind_set
    assert ConnectKind.MACOS in kind_set


def test_connectkind_in_dict():
    """Test ConnectKind can be used as dict key"""
    kind_dict = {
        ConnectKind.S3: "Amazon S3",
        ConnectKind.MACOS: "Local macOS",
    }

    assert kind_dict[ConnectKind.S3] == "Amazon S3"
    assert kind_dict[ConnectKind.MACOS] == "Local macOS"


def test_connectkind_iteration():
    """Test iterating over ConnectKind"""
    kinds = list(ConnectKind)

    assert len(kinds) >= 3
    assert all(isinstance(k, ConnectKind) for k in kinds)

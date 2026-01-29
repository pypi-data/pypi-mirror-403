"""
Tests for interface factory error classes
"""

import pytest

from xdatawork.interface.factory import (
    InterfaceAlreadyRegisteredError,
    InterfaceNotFoundError,
)

# ==================== InterfaceNotFoundError Tests ====================


def test_interfacenotfounderror_is_keyerror():
    """Test InterfaceNotFoundError inherits from KeyError"""
    assert issubclass(InterfaceNotFoundError, KeyError)


def test_interfacenotfounderror_can_be_raised():
    """Test InterfaceNotFoundError can be raised"""
    with pytest.raises(InterfaceNotFoundError):
        raise InterfaceNotFoundError("interface not found")


def test_interfacenotfounderror_with_message():
    """Test InterfaceNotFoundError preserves error message"""
    msg = "Interface 'test' not found"
    with pytest.raises(InterfaceNotFoundError, match=msg):
        raise InterfaceNotFoundError(msg)


def test_interfacenotfounderror_can_be_caught_as_keyerror():
    """Test InterfaceNotFoundError can be caught as KeyError"""
    try:
        raise InterfaceNotFoundError("error")
    except KeyError:
        pass  # Should catch it


def test_interfacenotfounderror_str_representation():
    """Test InterfaceNotFoundError string representation"""
    error = InterfaceNotFoundError("myinterface not found")
    assert "myinterface not found" in str(error)


def test_interfacenotfounderror_with_empty_message():
    """Test InterfaceNotFoundError with empty message"""
    with pytest.raises(InterfaceNotFoundError):
        raise InterfaceNotFoundError("")


def test_interfacenotfounderror_equality():
    """Test InterfaceNotFoundError equality comparison"""
    error1 = InterfaceNotFoundError("same message")
    error2 = InterfaceNotFoundError("same message")
    # Exceptions compare by identity, not value
    assert error1 != error2
    assert type(error1) is type(error2)


# ==================== InterfaceAlreadyRegisteredError Tests ====================


def test_interfacealreadyregisterederror_is_keyerror():
    """Test InterfaceAlreadyRegisteredError inherits from KeyError"""
    assert issubclass(InterfaceAlreadyRegisteredError, KeyError)


def test_interfacealreadyregisterederror_can_be_raised():
    """Test InterfaceAlreadyRegisteredError can be raised"""
    with pytest.raises(InterfaceAlreadyRegisteredError):
        raise InterfaceAlreadyRegisteredError("interface already registered")


def test_interfacealreadyregisterederror_with_message():
    """Test InterfaceAlreadyRegisteredError preserves error message"""
    msg = "Interface 'test' already registered"
    with pytest.raises(InterfaceAlreadyRegisteredError, match=msg):
        raise InterfaceAlreadyRegisteredError(msg)


def test_interfacealreadyregisterederror_can_be_caught_as_keyerror():
    """Test InterfaceAlreadyRegisteredError can be caught as KeyError"""
    try:
        raise InterfaceAlreadyRegisteredError("error")
    except KeyError:
        pass  # Should catch it


def test_interfacealreadyregisterederror_str_representation():
    """Test InterfaceAlreadyRegisteredError string representation"""
    error = InterfaceAlreadyRegisteredError("myinterface already registered")
    assert "myinterface already registered" in str(error)


def test_interfacealreadyregisterederror_with_empty_message():
    """Test InterfaceAlreadyRegisteredError with empty message"""
    with pytest.raises(InterfaceAlreadyRegisteredError):
        raise InterfaceAlreadyRegisteredError("")


def test_interfacealreadyregisterederror_equality():
    """Test InterfaceAlreadyRegisteredError equality comparison"""
    error1 = InterfaceAlreadyRegisteredError("same message")
    error2 = InterfaceAlreadyRegisteredError("same message")
    # Exceptions compare by identity, not value
    assert error1 != error2
    assert type(error1) is type(error2)


# ==================== Error Inheritance Tests ====================


def test_both_errors_inherit_from_keyerror():
    """Test both error classes inherit from KeyError"""
    assert issubclass(InterfaceNotFoundError, KeyError)
    assert issubclass(InterfaceAlreadyRegisteredError, KeyError)


def test_errors_are_distinct_types():
    """Test error classes are distinct types"""
    assert InterfaceNotFoundError != InterfaceAlreadyRegisteredError


def test_errors_can_be_distinguished_in_except():
    """Test errors can be caught separately"""
    caught_not_found = False
    caught_already_registered = False

    try:
        raise InterfaceNotFoundError("test")
    except InterfaceNotFoundError:
        caught_not_found = True
    except InterfaceAlreadyRegisteredError:
        caught_already_registered = True

    assert caught_not_found
    assert not caught_already_registered

    caught_not_found = False
    caught_already_registered = False

    try:
        raise InterfaceAlreadyRegisteredError("test")
    except InterfaceNotFoundError:
        caught_not_found = True
    except InterfaceAlreadyRegisteredError:
        caught_already_registered = True

    assert not caught_not_found
    assert caught_already_registered


# ==================== Exception Chaining Tests ====================


def test_interfacenotfounderror_with_cause():
    """Test InterfaceNotFoundError with cause chain"""
    original = KeyError("original error")
    try:
        raise InterfaceNotFoundError("wrapped error") from original
    except InterfaceNotFoundError as e:
        assert e.__cause__ is original


def test_interfacealreadyregisterederror_with_cause():
    """Test InterfaceAlreadyRegisteredError with cause chain"""
    original = KeyError("original error")
    try:
        raise InterfaceAlreadyRegisteredError("wrapped error") from original
    except InterfaceAlreadyRegisteredError as e:
        assert e.__cause__ is original

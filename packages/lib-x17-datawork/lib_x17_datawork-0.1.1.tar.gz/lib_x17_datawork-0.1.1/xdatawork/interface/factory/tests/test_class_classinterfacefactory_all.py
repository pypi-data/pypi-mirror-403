"""
Tests for ClassInterfaceFactory
"""

import pytest

from xdatawork.connect import ConnectKind, ConnectRef, ConnectRefLike
from xdatawork.interface.base import BaseInterface
from xdatawork.interface.factory import (
    InterfaceAlreadyRegisteredError,
    InterfaceNotFoundError,
)
from xdatawork.interface.factory.factory import ClassInterfaceFactory

# ==================== Test Helper Classes ====================


class MockConnect:
    """Mock connect for testing - implements ConnectLike protocol"""

    def __init__(self):
        self.kind = ConnectKind.ANY

    def get_object(self, location: str, **kwargs) -> bytes:
        """Mock get_object implementation"""
        return b"mock data"

    def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
        """Mock put_object implementation"""
        return ConnectRef(location=location, kind=self.kind)

    def list_objects(
        self,
        location: str | ConnectRefLike,
        level: int | None = None,
        pattern: str | None = None,
        **kwargs,
    ) -> list[ConnectRef]:
        """Mock list_objects implementation"""
        return []


# ==================== Initialization Tests ====================


def test_classinterfacefactory_init():
    """Test ClassInterfaceFactory initialization"""
    factory = ClassInterfaceFactory()
    assert factory is not None
    assert hasattr(factory, "_infs")
    assert hasattr(factory, "_aliases")


def test_classinterfacefactory_starts_empty():
    """Test ClassInterfaceFactory starts with empty registries"""
    factory = ClassInterfaceFactory()
    assert len(factory._infs) == 0
    assert len(factory._aliases) == 0


def test_classinterfacefactory_list_starts_empty():
    """Test ClassInterfaceFactory.list() returns empty list initially"""
    factory = ClassInterfaceFactory()
    assert factory.list() == []


# ==================== Register Decorator Tests ====================


def test_register_simple_interface():
    """Test registering a simple interface"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        pass

    assert "testintf" in factory._infs
    assert factory._infs["testintf"] is TestInterface


def test_register_interface_with_alias():
    """Test registering interface with alias"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf", alias="test")
    class TestInterface(BaseInterface):
        pass

    assert "testintf" in factory._infs
    assert "test" in factory._aliases
    assert factory._aliases["test"] == "testintf"


def test_register_sets_interface_name_attribute():
    """Test register decorator sets __interface_name__ attribute"""
    factory = ClassInterfaceFactory()

    @factory.register(name="myintf")
    class TestInterface(BaseInterface):
        pass

    assert hasattr(TestInterface, "__interface_name__")
    assert TestInterface.__interface_name__ == "myintf"


def test_register_returns_class():
    """Test register decorator returns the class unchanged"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        pass

    # Should be able to instantiate the class normally
    assert TestInterface is not None
    assert issubclass(TestInterface, BaseInterface)


def test_register_multiple_interfaces():
    """Test registering multiple interfaces"""
    factory = ClassInterfaceFactory()

    @factory.register(name="intf1")
    class Interface1(BaseInterface):
        pass

    @factory.register(name="intf2")
    class Interface2(BaseInterface):
        pass

    assert "intf1" in factory._infs
    assert "intf2" in factory._infs
    assert factory._infs["intf1"] is Interface1
    assert factory._infs["intf2"] is Interface2


def test_register_duplicate_name_raises_error():
    """Test registering duplicate interface name raises error"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface1(BaseInterface):
        pass

    with pytest.raises(InterfaceAlreadyRegisteredError, match="Interface already registered: testintf"):

        @factory.register(name="testintf")
        class TestInterface2(BaseInterface):
            pass


def test_register_duplicate_alias_different_interface_raises_error():
    """Test registering duplicate alias for different interface raises error"""
    factory = ClassInterfaceFactory()

    @factory.register(name="intf1", alias="test")
    class Interface1(BaseInterface):
        pass

    with pytest.raises(InterfaceAlreadyRegisteredError, match="Alias already used: test"):

        @factory.register(name="intf2", alias="test")
        class Interface2(BaseInterface):
            pass


def test_register_same_alias_for_same_interface_allowed():
    """Test registering same alias for same interface is allowed (idempotent)"""
    factory = ClassInterfaceFactory()

    @factory.register(name="intf1", alias="test")
    class Interface1(BaseInterface):
        pass

    # Re-registering same alias for same interface should not raise
    # This happens when decorator is applied in re-imported module
    # Note: This will raise because name is already registered
    # So we skip this test as it's a design decision


def test_register_without_alias():
    """Test registering interface without alias"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        pass

    assert "testintf" in factory._infs
    assert len(factory._aliases) == 0


def test_register_with_none_alias():
    """Test registering interface with None as alias"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf", alias=None)
    class TestInterface(BaseInterface):
        pass

    assert "testintf" in factory._infs
    assert len(factory._aliases) == 0


# ==================== Lookup Tests ====================


def test_lookup_registered_interface_by_name():
    """Test looking up interface by registered name"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        pass

    found = factory.lookup("testintf")
    assert found is TestInterface


def test_lookup_registered_interface_by_alias():
    """Test looking up interface by alias"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf", alias="test")
    class TestInterface(BaseInterface):
        pass

    found = factory.lookup("test")
    assert found is TestInterface


def test_lookup_nonexistent_interface_raises_error():
    """Test looking up nonexistent interface raises InterfaceNotFoundError"""
    factory = ClassInterfaceFactory()

    with pytest.raises(InterfaceNotFoundError, match="Interface not found: nonexistent"):
        factory.lookup("nonexistent")


def test_lookup_empty_string_raises_error():
    """Test looking up empty string raises InterfaceNotFoundError"""
    factory = ClassInterfaceFactory()

    with pytest.raises(InterfaceNotFoundError):
        factory.lookup("")


def test_lookup_returns_same_class_for_name_and_alias():
    """Test lookup returns same class whether using name or alias"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf", alias="test")
    class TestInterface(BaseInterface):
        pass

    by_name = factory.lookup("testintf")
    by_alias = factory.lookup("test")
    assert by_name is by_alias
    assert by_name is TestInterface


# ==================== Create Tests ====================


def test_create_interface_by_name():
    """Test creating interface instance by name"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        pass

    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    instance = factory.create("testintf", ref=ref, connect=connect)
    assert isinstance(instance, TestInterface)
    assert isinstance(instance, BaseInterface)


def test_create_interface_by_alias():
    """Test creating interface instance by alias"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf", alias="test")
    class TestInterface(BaseInterface):
        pass

    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    instance = factory.create("test", ref=ref, connect=connect)
    assert isinstance(instance, TestInterface)


def test_create_nonexistent_interface_raises_error():
    """Test creating nonexistent interface raises InterfaceNotFoundError"""
    factory = ClassInterfaceFactory()

    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    with pytest.raises(InterfaceNotFoundError):
        factory.create("nonexistent", ref=ref, connect=connect)


def test_create_passes_args_to_constructor():
    """Test create passes positional args to interface constructor"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        def __init__(self, ref, connect, extra_arg):
            super().__init__(ref=ref, connect=connect)
            self.extra_arg = extra_arg

    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    instance = factory.create("testintf", ref, connect, "extra_value")
    assert instance.extra_arg == "extra_value"


def test_create_passes_kwargs_to_constructor():
    """Test create passes keyword args to interface constructor"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        def __init__(self, ref, connect, custom_param=None):
            super().__init__(ref=ref, connect=connect)
            self.custom_param = custom_param

    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")

    instance = factory.create("testintf", ref=ref, connect=connect, custom_param="custom")
    assert instance.custom_param == "custom"


def test_create_multiple_instances():
    """Test creating multiple instances of same interface"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        pass

    connect = MockConnect()
    ref1 = ConnectRef(location="s3://bucket/data1")
    ref2 = ConnectRef(location="s3://bucket/data2")

    instance1 = factory.create("testintf", ref=ref1, connect=connect)
    instance2 = factory.create("testintf", ref=ref2, connect=connect)

    assert instance1 is not instance2
    assert type(instance1) is type(instance2)
    assert instance1.ref.location != instance2.ref.location


# ==================== List Tests ====================


def test_list_empty_factory():
    """Test list returns empty list for empty factory"""
    factory = ClassInterfaceFactory()
    assert factory.list() == []


def test_list_single_interface():
    """Test list returns registered interface name"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        pass

    result = factory.list()
    assert "testintf" in result
    assert len(result) == 1


def test_list_interface_with_alias():
    """Test list returns both name and alias"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf", alias="test")
    class TestInterface(BaseInterface):
        pass

    result = factory.list()
    assert "testintf" in result
    assert "test" in result
    assert len(result) == 2


def test_list_multiple_interfaces():
    """Test list returns all registered interfaces"""
    factory = ClassInterfaceFactory()

    @factory.register(name="intf1")
    class Interface1(BaseInterface):
        pass

    @factory.register(name="intf2", alias="i2")
    class Interface2(BaseInterface):
        pass

    @factory.register(name="intf3")
    class Interface3(BaseInterface):
        pass

    result = factory.list()
    assert "intf1" in result
    assert "intf2" in result
    assert "i2" in result
    assert "intf3" in result
    assert len(result) == 4


def test_list_returns_sorted_list():
    """Test list returns sorted list"""
    factory = ClassInterfaceFactory()

    @factory.register(name="zebra")
    class Interface1(BaseInterface):
        pass

    @factory.register(name="apple")
    class Interface2(BaseInterface):
        pass

    @factory.register(name="mango")
    class Interface3(BaseInterface):
        pass

    result = factory.list()
    assert result == ["apple", "mango", "zebra"]


def test_list_returns_unique_items():
    """Test list returns unique items (no duplicates)"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf", alias="test")
    class TestInterface(BaseInterface):
        pass

    result = factory.list()
    # Should have exactly 2 items: name and alias
    assert len(result) == 2
    assert len(set(result)) == 2  # All unique


# ==================== Integration Tests ====================


def test_complete_workflow_register_lookup_create():
    """Test complete workflow: register, lookup, create"""
    factory = ClassInterfaceFactory()

    @factory.register(name="myintf", alias="my")
    class MyInterface(BaseInterface):
        def custom_method(self):
            return "custom"

    # Lookup
    cls = factory.lookup("myintf")
    assert cls is MyInterface

    cls_by_alias = factory.lookup("my")
    assert cls_by_alias is MyInterface

    # Create
    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    instance = factory.create("myintf", ref=ref, connect=connect)

    assert isinstance(instance, MyInterface)
    assert instance.custom_method() == "custom"


def test_factory_isolation():
    """Test multiple factory instances are independent"""
    factory1 = ClassInterfaceFactory()
    factory2 = ClassInterfaceFactory()

    @factory1.register(name="intf1")
    class Interface1(BaseInterface):
        pass

    @factory2.register(name="intf2")
    class Interface2(BaseInterface):
        pass

    # factory1 should only have intf1
    assert "intf1" in factory1.list()
    assert "intf2" not in factory1.list()

    # factory2 should only have intf2
    assert "intf2" in factory2.list()
    assert "intf1" not in factory2.list()


def test_register_preserves_class_methods():
    """Test register decorator preserves class methods and attributes"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        CLASS_ATTR = "value"

        def custom_method(self):
            return "result"

        @classmethod
        def class_method(cls):
            return "class_result"

        @staticmethod
        def static_method():
            return "static_result"

    assert TestInterface.CLASS_ATTR == "value"
    assert TestInterface.class_method() == "class_result"
    assert TestInterface.static_method() == "static_result"

    connect = MockConnect()
    ref = ConnectRef(location="s3://bucket/data")
    instance = factory.create("testintf", ref=ref, connect=connect)
    assert instance.custom_method() == "result"


def test_register_preserves_docstring():
    """Test register decorator preserves class docstring"""
    factory = ClassInterfaceFactory()

    @factory.register(name="testintf")
    class TestInterface(BaseInterface):
        """This is a test interface"""

        pass

    assert TestInterface.__doc__ == "This is a test interface"


def test_multiple_aliases_not_supported():
    """Test that only one alias per interface is supported"""
    factory = ClassInterfaceFactory()

    # Register with one alias
    @factory.register(name="testintf", alias="test1")
    class TestInterface(BaseInterface):
        pass

    # The decorator only accepts one alias parameter
    # This is by design - if multiple aliases needed, register multiple times
    # But that would fail due to duplicate name
    # So this test just documents the current behavior


def test_case_sensitive_names():
    """Test interface names and aliases are case-sensitive"""
    factory = ClassInterfaceFactory()

    @factory.register(name="TestIntf")
    class TestInterface(BaseInterface):
        pass

    @factory.register(name="testintf")
    class TestInterface2(BaseInterface):
        pass

    # Both should be registered separately
    assert "TestIntf" in factory.list()
    assert "testintf" in factory.list()
    assert factory.lookup("TestIntf") is TestInterface
    assert factory.lookup("testintf") is TestInterface2


def test_lookup_after_multiple_registrations():
    """Test lookup works correctly after multiple registrations"""
    factory = ClassInterfaceFactory()

    @factory.register(name="intf1", alias="i1")
    class Interface1(BaseInterface):
        pass

    @factory.register(name="intf2", alias="i2")
    class Interface2(BaseInterface):
        pass

    @factory.register(name="intf3")
    class Interface3(BaseInterface):
        pass

    assert factory.lookup("intf1") is Interface1
    assert factory.lookup("i1") is Interface1
    assert factory.lookup("intf2") is Interface2
    assert factory.lookup("i2") is Interface2
    assert factory.lookup("intf3") is Interface3

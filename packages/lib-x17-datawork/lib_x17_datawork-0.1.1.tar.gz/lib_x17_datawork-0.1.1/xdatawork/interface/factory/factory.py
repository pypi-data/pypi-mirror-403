from __future__ import annotations

from typing import Any

from .error import (
    InterfaceAlreadyRegisteredError,
    InterfaceNotFoundError,
)


class ClassInterfaceFactory:
    """
    描述:
    - 接口工厂类，用于注册和创建接口实例。
    - 支持装饰器注册和别名机制。
    - 单例模式，通过 InterfaceFactory 访问。

    方法:
    - register: 装饰器，注册接口类
    - lookup: 查找已注册的接口类
    - create: 创建接口实例
    - list: 列出所有注册的接口名称和别名

    例子:
    ```python
        from xdatawork.interface.factory import InterfaceFactory
        from xdatawork.interface.base import BaseInterface

        @InterfaceFactory.register(name="myintf", alias="my")
        class MyInterface(BaseInterface):
            pass

        # 通过名称创建
        intf1 = InterfaceFactory.create("myintf", ref=ref, connect=connect)

        # 通过别名创建
        intf2 = InterfaceFactory.create("my", ref=ref, connect=connect)

        # 列出所有接口
        all_intfs = InterfaceFactory.list()
    ```
    """

    def __init__(self) -> None:
        self._infs: dict[str, type] = {}
        self._aliases: dict[str, str] = {}

    def register(
        self,
        name: str,
        alias: str | None = None,
    ):
        def deco(cls):
            if name in self._infs:
                msg = f"Interface already registered: {name}"
                raise InterfaceAlreadyRegisteredError(msg)
            else:
                self._infs[name] = cls
            if alias is not None:
                if alias in self._aliases and (self._aliases[alias] != name):
                    msg = f"Alias already used: {alias}"
                    raise InterfaceAlreadyRegisteredError(msg)
                self._aliases[alias] = name
            cls.__interface_name__ = name
            return cls

        return deco

    def lookup(
        self,
        name: str,
    ) -> type:
        if name in self._infs:
            return self._infs[name]
        if name in self._aliases:
            return self._infs[self._aliases[name]]
        msg = f"Interface not found: {name}"
        raise InterfaceNotFoundError(msg)

    def create(
        self,
        name: str,
        *args,
        **kwargs,
    ) -> Any:
        return self.lookup(name)(*args, **kwargs)

    def list(self) -> list[str]:
        keys = self._infs.keys()
        aliases = self._aliases.keys()
        items = list(keys) + list(aliases)
        return sorted(set(items))

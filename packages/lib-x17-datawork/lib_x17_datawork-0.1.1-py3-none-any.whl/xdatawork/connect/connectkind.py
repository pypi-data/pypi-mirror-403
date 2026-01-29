from __future__ import annotations

from enum import Enum


class ConnectKind(str, Enum):
    """
    描述:
    - 连接类型枚举类。
    - 定义支持的连接类型：本地文件系统和 Amazon S3。
    - 继承自 str 和 Enum，可以直接与字符串比较。

    属性:
    - MACOS: 本地 macOS 文件系统连接类型 ("macos")
    - S3: Amazon S3 连接类型 ("s3")
    - ANY: 通用连接类型 ("any")

    方法:
    - from_str(string): 从字符串创建 ConnectKind 实例（不区分大小写）。
    - from_any(value): 从 ConnectKind 实例或字符串创建 ConnectKind 实例。
    - list_all(): 列出所有支持的 ConnectKind 实例。
    - __str__(): 返回连接类型的字符串值。
    - __repr__(): 返回连接类型的表示形式。

    例子:
    ```python
        from xdatawork.connect.kind.connectkind import ConnectKind

        # 使用枚举值
        kind = ConnectKind.MACOS
        print(kind)  # macos
        print(repr(kind))  # ConnectKind.MACOS

        # 从字符串创建（不区分大小写）
        kind = ConnectKind.from_str("s3")
        print(kind)  # s3

        kind = ConnectKind.from_str("MACOS")
        print(kind)  # macos

        # 字符串比较
        if ConnectKind.S3 == "s3":
            print("Matched!")  # 输出: Matched!

        # 无效连接类型会抛出 ValueError
        try:
            ConnectKind.from_str("ftp")
        except ValueError as e:
            print(f"Error: {e}")  # Error: Unknown ConnectKind: ftp
    ```
    """

    MACOS = "macos"
    S3 = "s3"
    ANY = "any"

    @classmethod
    def from_str(
        cls,
        string: str,
    ) -> ConnectKind:
        for kind in cls:
            if kind.value.lower() == string.lower():
                return kind
        raise ValueError(f"Unknown ConnectKind: {string}")

    @classmethod
    def from_any(
        cls,
        value: ConnectKind | str,
    ) -> ConnectKind:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_str(value)
        raise ValueError(f"Cannot convert {value} to ConnectKind")

    @classmethod
    def list_all(cls) -> list[ConnectKind]:
        return [kind for kind in cls]

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

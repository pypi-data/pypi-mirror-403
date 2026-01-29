from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from xdatawork.connect.connectkind import ConnectKind


@runtime_checkable
class ConnectRefLike(Protocol):
    """
    描述:
    - 连接引用接口协议。
    - 定义连接引用对象的基本属性和方法。
    - 用于表示存储位置的元数据。

    属性:
    - location: 存储位置的字符串表示。
    """

    location: str
    kind: Optional[ConnectKind]

    def to(self, rel: str) -> ConnectRefLike: ...

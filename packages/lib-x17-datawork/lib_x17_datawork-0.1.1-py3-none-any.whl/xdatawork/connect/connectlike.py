from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectreflike import ConnectRefLike


@runtime_checkable
class ConnectLike(Protocol):
    """
    描述:
    - 连接接口协议，定义存储连接的基本操作。
    - 支持对象的读取和写入操作。
    - 实现类可以是 S3、本地文件系统或其他存储后端。
    - 使用 @runtime_checkable 装饰器支持运行时类型检查。

    方法:
    - get_object(location, **kwargs): 从指定位置获取对象数据。
    - put_object(data, location, **kwargs): 将数据写入指定位置并返回引用。

    例子:
    ```python
        from xdatawork.connect import ConnectLike

        class MyConnect:
            def get_object(self, location: str, **kwargs) -> bytes:
                return b"data"

            def put_object(self, data: bytes, location: str, **kwargs) -> ConnectRef:
                return ConnectRef(location=location)

        # 运行时检查
        connect = MyConnect()
        assert isinstance(connect, ConnectLike)
    ```
    """

    kind: ConnectKind

    def get_object(
        self,
        location: str,
        **kwargs: Any,
    ) -> bytes: ...

    def put_object(
        self,
        data: bytes,
        location: str,
        **kwargs: Any,
    ) -> ConnectRefLike: ...

    def list_objects(
        self,
        location: str | ConnectRefLike,
        level: int | None = None,
        pattern: str | None = None,
        **kwargs: Any,
    ) -> list[ConnectRefLike]: ...

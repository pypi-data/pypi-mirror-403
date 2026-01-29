from __future__ import annotations

from typing import Any, Dict, Optional

from xdatawork.artifact.errors import (
    ArtifactReadError,
    ArtifactWriteError,
)
from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.serde.format.dataformat import DataFormat
from xdatawork.serde.serde.serdelike import SerDeLike


class Artifact:
    """
    描述:
        数据制品类，用于管理数据引用、内容和元数据

    属性:
        ref: ConnectRefLike, 数据引用对象
        data: Any, 数据内容（可选）
        meta: Dict[str, Any], 元数据（可选）

    方法:
        from_dict(data): 从字典创建Artifact实例
        write(connect, serialiser, format): 写入数据到存储
        read(connect, deserialiser, format): 从存储读取数据
        describe(): 返回制品描述信息
        to_dict(): 转换为字典格式

    例子:
        ```python
        from xfintech.connect.artifact import Artifact
        from xfintech.connect.common.connectref import ConnectRef

        # 创建制品
        ref = ConnectRef(location="s3://bucket/data.json")
        artifact = Artifact(ref=ref, data={"key": "value"})

        # 写入数据
        artifact.write(connect=s3_connect, serialiser=json_serialiser, format="json")

        # 读取数据
        artifact2 = Artifact(ref=ref)
        artifact2.read(connect=s3_connect, deserialiser=json_deserialiser, format="json")
        ```
    """

    def __init__(
        self,
        ref: ConnectRefLike | Dict[str, str],
        connect: ConnectLike,
        data: Any | None = None,
    ) -> None:
        self.ref: ConnectRefLike = self._resolve_ref(ref)
        self.connect: ConnectLike = self._resolve_connect(connect)
        self.data: Any | None = data

    def _resolve_ref(
        self,
        ref: ConnectRefLike | Dict[str, str],
    ) -> ConnectRefLike:
        if isinstance(ref, ConnectRef):
            return ref
        if isinstance(ref, dict):
            return ConnectRef.from_dict(ref)
        msg = f"Invalid ref: {type(ref)}, expected ConnectRefLike or dict"
        raise TypeError(msg)

    def _resolve_connect(
        self,
        connect: ConnectLike,
    ) -> ConnectLike:
        if not isinstance(connect, ConnectLike):
            msg = f"Invalid connect: {type(connect)}, expected ConnectLike"
            raise TypeError(msg)
        return connect

    def __str__(self) -> str:
        return str(self.ref)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(ref={self.ref})"

    def get_data(self) -> Any | None:
        return self.data

    def read(
        self,
        serde: Optional[SerDeLike] = None,
        format: Optional[DataFormat | str] = None,
        **kwargs: Any,
    ) -> "Artifact":
        try:
            result = self.connect.get_object(
                location=self.ref.location,
                **kwargs,
            )
        except Exception as e:
            msg = f"Failed to read artifact from {self.ref.location}: {e}"
            raise ArtifactReadError(msg) from e

        if isinstance(serde, SerDeLike):
            self.data = serde.deserialise(
                result,
                format=format,
                **kwargs,
            )
            return self
        else:
            self.data = result
            return self

    def write(
        self,
        serde: Optional[SerDeLike] = None,
        format: Optional[DataFormat | str] = None,
        **kwargs: Any,
    ) -> None:
        if serde:
            payload = serde.serialise(
                self.data,
                format=format,
                **kwargs,
            )
        else:
            payload = self.data
        try:
            self.ref = self.connect.put_object(
                data=payload,
                location=self.ref.location,
                **kwargs,
            )
        except Exception as e:
            msg = f"Failed to write artifact to {self.ref.location}: {e}"
            raise ArtifactWriteError(msg) from e
        return self

    def describe(self) -> Dict[str, Any]:
        return {
            "ref": {
                "location": self.ref.location,
                "kind": str(self.ref.kind),
            },
            "connect": {
                "kind": str(self.connect.kind),
            },
            "data": {
                "type": str(type(self.data).__name__),
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ref": {
                "location": self.ref.location,
                "kind": self.ref.kind,
            },
            "connect": {
                "kind": self.connect.kind,
            },
            "data": {
                "type": type(self.data).__name__,
            },
        }
        return result

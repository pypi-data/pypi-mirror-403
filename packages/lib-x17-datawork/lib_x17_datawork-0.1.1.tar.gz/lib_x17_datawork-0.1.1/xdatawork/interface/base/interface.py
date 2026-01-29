from __future__ import annotations

from typing import Any

from xdatawork.artifact.artifact import Artifact
from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.partitionkind import PartitionKind


class BaseInterface:
    """
    描述:
    - 数据接口基类，提供数据访问的抽象层。
    - 支持分区感知、父子层次结构和连接管理。
    - 可通过 InterfaceFactory 注册自定义接口类型。

    属性:
    - ref: ConnectRef 引用对象，指向数据位置
    - connect: ConnectLike 连接对象，用于实际数据访问
    - parent: 父接口（可选），用于连接继承
    - partition_fields: 分区字段列表
    - partition_kind: 分区类型（自动从 partition_fields 推断）

    方法:
    - list_refs: 列出数据引用
    - list_artifacts: 列出数据构件
    - describe: 返回接口描述信息
    - to_dict: 序列化为字典

    例子:
    ```python
        from xdatawork.interface import BaseInterface
        from xdatawork.connect import S3Connect

        # 创建连接
        connect = S3Connect()

        # 创建接口
        interface = BaseInterface(
            ref={"location": "s3://bucket/data/"},
            connect=connect,
            partition_fields=["year", "month"]
        )

        # 列出引用
        refs = interface.list_refs(level=1)

        # 列出构件
        artifacts = interface.list_artifacts(pattern="*.parquet")
    ```
    """

    def __init__(
        self,
        ref: ConnectRefLike,
        connect: ConnectLike | None = None,
        parent: BaseInterface | None = None,
        partition_fields: list[str] | str | None = None,
    ) -> None:
        self.parent: BaseInterface | None = self._resolve_parent(parent)
        self.ref: ConnectRef = self._resolve_ref(ref)
        self.connect: ConnectLike = self._resolve_connect(connect)
        self.partition_fields: list[str] = self._resolve_partition_fields(partition_fields)
        self.partition_kind: PartitionKind = self._resolve_partition_kind()

    def _resolve_parent(
        self,
        parent: BaseInterface | None,
    ) -> BaseInterface | None:
        if parent is None:
            return None
        if not isinstance(parent, BaseInterface):
            msg = f"Invalid parent: {type(parent)}, must be BaseInterface"
            raise TypeError(msg)
        return parent

    def _resolve_ref(
        self,
        ref: ConnectRefLike | dict[str, str] | None,
    ) -> ConnectRef:
        if ref is None:
            raise ValueError("ref cannot be None")
        else:
            if isinstance(ref, ConnectRef):
                return ref
            if isinstance(ref, dict):
                return ConnectRef.from_dict(ref)
            msg = f"Invalid ref: {type(ref)}, expected ConnectRefLike or dict"
            raise TypeError(msg)

    def _resolve_connect(
        self,
        connect: ConnectLike | None,
    ) -> ConnectLike:
        if connect is None:
            if self.parent is not None:
                return self.parent.connect
            else:
                msg = "connect cannot be None if parent is None"
                raise ValueError(msg)
        if not isinstance(connect, ConnectLike):
            msg = f"Invalid connect: {type(connect)}, expected ConnectLike"
            raise TypeError(msg)
        return connect

    def _resolve_partition_fields(
        self,
        partition_fields: list[str] | str | None,
    ) -> list[str]:
        result = []
        if partition_fields is None:
            return result
        if isinstance(partition_fields, str):
            for field in partition_fields.split(","):
                field = field.strip()
                if field:
                    result.append(field)
            return result
        if isinstance(partition_fields, list):
            for field in partition_fields:
                result.append(str(field).strip())
            return result
        msg = f"Partition fields expects list[str] or str, got {type(partition_fields)}"
        raise TypeError(msg)

    def _resolve_partition_kind(self) -> PartitionKind:
        if not self.partition_fields:
            return PartitionKind.NON_PARTITIONED
        else:
            return PartitionKind.from_partition_fields(self.partition_fields)

    def list_refs(
        self,
        level: int | None = None,
        pattern: str | None = None,
    ) -> list[ConnectRef]:
        """
        列出指定位置的引用。

        参数:
        - level: 列出的层级深度，None 表示所有层级
        - pattern: 文件名模式匹配（支持通配符）

        返回:
        - ConnectRef 列表

        注意:
        - 当前版本不支持分区过滤，请参考 PARTITION_FILTERING_PLAN.md
        """
        connectrefs = self.connect.list_objects(
            location=self.ref.location,
            level=level,
            pattern=pattern,
        )
        return connectrefs

    def list_artifacts(
        self,
        level: int | None = None,
        pattern: str | None = None,
    ) -> list[Artifact]:
        """
        列出指定位置的构件（Artifact）。

        参数:
        - level: 列出的层级深度，None 表示所有层级
        - pattern: 文件名模式匹配（支持通配符）

        返回:
        - Artifact 列表

        说明:
        - Artifact 是对 ConnectRef 的封装，提供数据读写功能
        """
        artifacts = []
        connectrefs: list[ConnectRef] = self.list_refs(
            level=level,
            pattern=pattern,
        )
        for connectref in connectrefs:
            artifact = Artifact(
                ref=connectref,
                connect=self.connect,
            )
            artifacts.append(artifact)
        return artifacts

    def describe(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ref": self.ref.describe(),
            "partition_kind": self.partition_kind.value,
        }
        if self.parent is not None:
            result["parent"] = self.parent.describe()
        if self.connect is not None:
            result["connect"] = str(self.connect.kind)
        if self.partition_fields:
            result["partition_fields"] = self.partition_fields
        return result

    def to_dict(self) -> dict[str, Any]:
        result = {
            "ref": self.ref.to_dict(),
            "partition_fields": self.partition_fields,
            "partition_kind": self.partition_kind.value,
        }
        if self.parent is not None:
            result["parent"] = self.parent.to_dict()
        else:
            result["parent"] = None
        if self.connect is not None:
            result["connect"] = str(self.connect.kind)
        else:
            result["connect"] = None
        return result

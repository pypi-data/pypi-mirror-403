from __future__ import annotations

from typing import Any, Mapping

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectreflike import ConnectRefLike


class ConnectRef(ConnectRefLike):
    """
    描述:
    - 连接引用数据类，表示存储对象的位置引用。
    - 包含位置信息和可选的类型标识。
    - 支持 Hive 风格的分区识别（如 year=2024/month=01）。
    - 提供路径操作、序列化和分区元数据跟踪功能。
    - 实现了相等性比较和哈希方法。

    属性:
    - location: 存储位置字符串或 URI。
    - kind: 连接类型（如 's3', 'macos', 'any' 等），可选。
    - partition_fields: 要跟踪的分区字段名称列表。
    - partitions: 分区字段到值的字典映射。在 partition_fields 中指定但在 location 中未找到的字段将具有 None 值。
    - n_exist_partitions: 在 location 路径中实际找到的分区数量。
    - n_design_partitions: 设计的分区字段总数（预期的）。
    - is_partitioned: 如果指定了 partition_fields 且至少存在一个分区，则为 True。
    - full_partitioned: 如果在 location 中找到了所有设计的分区字段，则为 True。

    方法:
    - from_dict: 从字典创建 ConnectRef 实例。
    - to_dict: 将 ConnectRef 实例序列化为字典。
    - to: 通过附加相对路径创建新的引用。
    - list_partition_fields: 返回分区字段名称列表。
    - get_partition: 获取指定分区字段的值，支持默认值。
    - describe: 返回包含位置、类型和分区信息的描述字典。

    例子:
    ```python
        from xdatawork.connect.connectref import ConnectRef
        from xdatawork.connect.connectkind import ConnectKind

        # 基本引用（无分区）
        ref = ConnectRef(location="s3://bucket/key", kind=ConnectKind.S3)

        # 带分区跟踪的引用
        ref = ConnectRef(
            location="s3://bucket/data/year=2024/month=01/file.parquet",
            kind=ConnectKind.S3,
            partition_fields=["year", "month"]
        )
        ref.partitions  # {'year': '2024', 'month': '01'}
        ref.is_partitioned  # True
        ref.full_partitioned  # True

        # 部分分区场景（例如，不完整的数据回填）
        ref = ConnectRef(
            location="s3://bucket/data/year=2024/file.parquet",
            kind=ConnectKind.S3,
            partition_fields=["year", "month", "day"]
        )
        ref.partitions  # {'year': '2024', 'month': None, 'day': None}
        ref.n_exist_partitions  # 1
        ref.n_design_partitions  # 3
        ref.full_partitioned  # False

        # 路径导航
        base = ConnectRef(location="s3://bucket", kind=ConnectKind.S3)
        data_ref = base.to("data/file.parquet")

        # 序列化
        data = ref.to_dict()
        restored = ConnectRef.from_dict(data)

        # 分区访问
        ref.get_partition("year")  # '2024'
        ref.get_partition("missing", default="N/A")  # 'N/A'

        # 逗号分隔的分区字段字符串
        ref = ConnectRef(
            location="s3://bucket/year=2024/month=01/file.parquet",
            partition_fields="year,month"
        )
    ```
    """

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConnectRef:
        if "location" not in data:
            raise KeyError("'location' is required in data")
        location = data["location"]
        kindtext = data.get("kind")
        partition_fields = data.get("partition_fields")
        kind = ConnectKind.from_any(kindtext) if kindtext else None
        return cls(
            location=location,
            kind=kind,
            partition_fields=partition_fields,
        )

    def __init__(
        self,
        location: str,
        kind: ConnectKind | str | None = None,
        partition_fields: list[str] | str | None = None,
    ) -> None:
        self.location = location
        self.kind = self._resolve_kind(kind)
        self.partition_fields = self._resolve_partition_fields(partition_fields)
        self.partitions = self._resolve_partitions(self.partition_fields)
        self.n_exist_partitions = self._resolve_n_exist_partitions()
        self.n_design_partitions = self._resolve_n_design_partitions()
        self.is_partitioned = self._resolve_is_partitioned()
        self.full_partitioned = self._resolve_full_partitioned()

    def _resolve_kind(
        self,
        kind: ConnectKind | None,
    ) -> ConnectKind | None:
        if kind is None:
            return None
        else:
            return ConnectKind.from_any(kind)

    def _resolve_partition_fields(
        self,
        fields: list[str] | str | None,
    ) -> list[str]:
        result = []
        if fields is None:
            return result
        if isinstance(fields, str):
            for field in fields.split(","):
                field = field.strip()
                if field:
                    result.append(field)
            return result
        if isinstance(fields, list):
            for field in fields:
                result.append(str(field).strip())
            return result
        msg = f"Partition fields expects list[str] or str, got {type(fields)}"
        raise TypeError(msg)

    def _resolve_partitions(
        self,
        partition_fields: list[str] | str | None,
    ) -> dict[str, str | None]:
        results = {field: None for field in partition_fields}
        segments = self.location.split("/")
        for segment in segments:
            if "=" in segment:
                key, value = segment.split("=", 1)
                key = key.strip("'\" ")
                value = value.strip("'\" ")
                if key in results:
                    results[key] = value
        return results

    def _resolve_n_exist_partitions(self) -> int:
        count = 0
        for v in self.partitions.values():
            if v is not None:
                count += 1
        return count

    def _resolve_n_design_partitions(self) -> int:
        return len(self.partitions)

    def _resolve_is_partitioned(self) -> bool:
        return self.n_design_partitions > 0 and self.n_exist_partitions > 0

    def _resolve_full_partitioned(self) -> bool:
        return self.n_design_partitions > 0 and self.n_exist_partitions >= self.n_design_partitions

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConnectRef):
            return NotImplemented
        return self.location == other.location and self.kind == other.kind and self.partitions == other.partitions

    def __hash__(self) -> int:
        partition_tuple = tuple(sorted(self.partitions.items()))
        return hash((self.location, self.kind, partition_tuple))

    def __str__(self) -> str:
        return f"{self.location}"

    def __repr__(self) -> str:
        parts = [f"location={self.location!r}"]
        if self.kind:
            parts.append(f"kind={self.kind.value!r}")
        if self.partitions:
            parts.append(f"partitions={self.partitions}")
        return f"{self.__class__.__name__}({', '.join(parts)})"

    def to(self, rel: str) -> ConnectRef:
        old = self.location.rstrip("/")
        rel = rel.lstrip("/")
        return ConnectRef(location=f"{old}/{rel}", kind=self.kind, partition_fields=list(self.partitions.keys()))

    def list_partition_fields(self) -> list[str]:
        return list(self.partitions.keys())

    def get_partition(
        self,
        field: str,
        default: str | None = None,
    ) -> str | None:
        return self.partitions.get(field, default)

    def describe(self) -> dict[str, str | None]:
        result = {
            "location": self.location,
            "is_partitioned": str(self.is_partitioned),
        }
        if self.kind is not None:
            result["kind"] = self.kind.value
        for field, value in self.partitions.items():
            result.setdefault("partitions", {})
            result["partitions"][field] = value
        return result

    def to_dict(self) -> dict[str, str | None]:
        result = {
            "location": self.location,
            "kind": self.kind.value if self.kind else None,
            "partitions": self.partitions,
            "is_partitioned": self.is_partitioned,
        }
        return result

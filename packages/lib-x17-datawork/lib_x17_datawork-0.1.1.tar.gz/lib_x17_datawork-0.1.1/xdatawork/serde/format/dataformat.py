from __future__ import annotations

from enum import Enum


class DataFormat(str, Enum):
    """
    描述:
    - 序列化和反序列化格式枚举类。
    - 定义支持的数据格式：Parquet、CSV 和 JSON。
    - 继承自 str 和 Enum，可以直接与字符串比较。

    属性:
    - PARQUET: Parquet 格式 ("parquet")
    - CSV: CSV 格式 ("csv")
    - JSON: JSON 格式 ("json")

    方法:
    - from_str(string): 从字符串创建 DataFormat 实例（不区分大小写）。
    - from_any(value): 从 DataFormat 实例或字符串创建 DataFormat 实例。
    - list_all(): 列出所有支持的 DataFormat 实例。
    - __str__(): 返回格式的字符串值。
    - __repr__(): 返回格式的表示形式。

    例子:
    ```python
        from xfintech.serde.common.dataformat import DataFormat

        # 使用枚举值
        fmt = DataFormat.PARQUET
        print(fmt)  # parquet
        print(repr(fmt))  # DataFormat.PARQUET

        # 从字符串创建（不区分大小写）
        fmt = DataFormat.from_str("csv")
        print(fmt)  # csv

        fmt = DataFormat.from_str("JSON")
        print(fmt)  # json

        # 字符串比较
        if DataFormat.PARQUET == "parquet":
            print("Matched!")  # 输出: Matched!

        # 无效格式会抛出 ValueError
        try:
            DataFormat.from_str("xml")
        except ValueError as e:
            print(f"Error: {e}")  # Error: Unknown DataFormat: xml
    ```
    """

    BYTES = "bytes"
    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"
    TOML = "toml"
    TEXT = "text"

    @classmethod
    def from_str(
        cls,
        value: str,
    ) -> DataFormat:
        for fmt in DataFormat:
            if fmt.value.lower() == value.lower():
                return fmt
        raise ValueError(f"Unknown DataFormat: {value}")

    @classmethod
    def from_any(
        cls,
        value: DataFormat | str,
    ) -> DataFormat:
        if isinstance(value, DataFormat):
            return value
        return cls.from_str(value)

    @classmethod
    def list_all(cls) -> list[DataFormat]:
        return [fmt for fmt in cls]

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

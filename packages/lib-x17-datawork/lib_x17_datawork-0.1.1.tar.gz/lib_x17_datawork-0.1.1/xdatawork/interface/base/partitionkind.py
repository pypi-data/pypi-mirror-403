from __future__ import annotations

from enum import Enum


class PartitionKind(str, Enum):
    """
    描述:
    - 分区类型枚举，定义数据接口的分区策略。

    取值:
    - NON_PARTITIONED: 无分区数据
    - DATE_PARTITIONED: 按日期分区 (YYYY-MM-DD 格式)
    - DATETIME_PARTITIONED: 按日期时间分区 (YYYY-MM-DD HH:MM:SS 格式)
    - YEAR_MONTH_PARTITIONED: 按年月分区 (year=YYYY/month=MM)
    - HIVE_PARTITIONED: Hive 风格多级分区 (如 year=YYYY/month=MM/day=DD)
    - SNAPSHOT_PARTITIONED: 快照分区 (snapshotdate=YYYY-MM-DD)
    - CUSTOM_PARTITIONED: 自定义分区策略
    """

    NON_PARTITIONED = "NON_PARTITIONED"
    DATE_PARTITIONED = "DATE_PARTITIONED"
    DATETIME_PARTITIONED = "DATETIME_PARTITIONED"
    YEAR_MONTH_PARTITIONED = "YEAR_MONTH_PARTITIONED"
    HIVE_PARTITIONED = "HIVE_PARTITIONED"
    SNAPSHOT_PARTITIONED = "SNAPSHOT_PARTITIONED"
    CUSTOM_PARTITIONED = "CUSTOM_PARTITIONED"

    @classmethod
    def from_str(
        cls,
        value: str,
    ) -> PartitionKind:
        for kind in PartitionKind:
            if kind.value.lower() == value.lower():
                return kind
        raise ValueError(f"Unknown PartitionKind: {value}")

    @classmethod
    def from_any(
        cls,
        value: PartitionKind | str,
    ) -> PartitionKind:
        if isinstance(value, PartitionKind):
            return value
        return cls.from_str(value)

    @classmethod
    def from_partition_fields(
        cls,
        partition_fields: list[str],
    ) -> PartitionKind:
        """
        根据分区字段推断分区类型。

        参数:
        - partition_fields: 分区字段列表

        返回:
        - PartitionKind: 推断的分区类型
        """
        if not partition_fields:
            return cls.NON_PARTITIONED

        # 单字段分区类型推断
        if len(partition_fields) == 1:
            field = partition_fields[0].lower()
            if field == "date":
                return cls.DATE_PARTITIONED
            if field == "datetime":
                return cls.DATETIME_PARTITIONED
            if field == "snapshotdate":
                return cls.SNAPSHOT_PARTITIONED

        # 多字段分区类型推断
        if len(partition_fields) == 2:
            fields = [f.lower() for f in partition_fields]
            if "year" in fields and "month" in fields:
                return cls.YEAR_MONTH_PARTITIONED

        # Hive 风格分区 (包含 year/month/day 等)
        hive_fields = {"year", "month", "day", "hour"}
        if any(f.lower() in hive_fields for f in partition_fields):
            return cls.HIVE_PARTITIONED

        # 默认为自定义分区
        return cls.CUSTOM_PARTITIONED

    @classmethod
    def list_all(cls) -> list[PartitionKind]:
        return [kind for kind in cls]

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

from __future__ import annotations

from datetime import date, datetime

from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.interface import BaseInterface
from xdatawork.interface.factory import InterfaceFactory
from xdatawork.interface.instance.noneptn import NonePTN


@InterfaceFactory.register(
    name="snapshotdateptn",
    alias="ssdptn",
)
class SnapshotdatePTN(BaseInterface):
    """
    描述:
    - 快照日期分区接口，用于管理按快照日期分区的数据。
    - 支持快照日期范围过滤和日期格式验证。

    属性:
    - partition_fields: 固定为 ["snapshotdate"]
    - partition_kind: 自动设置为 SNAPSHOT_PARTITIONED

    方法:
    - list_snapshotdate_refs: 列出指定快照日期范围内的引用

    例子:
    ```python
        from xdatawork.interface import SnapshotdatePTN
        from xdatawork.connect import S3Connect

        connect = S3Connect()
        interface = SnapshotdatePTN(
            ref={"location": "s3://bucket/snapshots/"},
            connect=connect
        )

        # 列出特定快照日期范围的数据
        refs = interface.list_snapshotdate_refs(
            min="2024-01-01",
            max="2024-01-31"
        )
    ```
    """

    DATE_FORMAT = "%Y-%m-%d"

    def __init__(
        self,
        ref: ConnectRefLike,
        connect: ConnectLike | None = None,
        parent: BaseInterface | None = None,
    ) -> None:
        super().__init__(
            ref=ref,
            connect=connect,
            parent=parent,
            partition_fields=["snapshotdate"],
        )
        self.key = "snapshotdateptn"

    def resolve_date(
        self,
        value: date | str | None = None,
    ) -> date | None:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            value = value.strip()
            try:
                return datetime.strptime(
                    value,
                    self.DATE_FORMAT,
                ).date()
            except (ValueError, TypeError):
                return None
        return None

    def list_snapshotdate_refs(
        self,
        min: date | str | None = None,  # YYYY-MM-DD
        max: date | str | None = None,  # YYYY-MM-DD
    ) -> list[ConnectRef]:
        result = []
        min_date_obj: date | None = self.resolve_date(min)
        max_date_obj: date | None = self.resolve_date(max)
        for ref in self.list_refs():
            snapshotdate_iso = ref.get_partition("snapshotdate", None)
            if snapshotdate_iso is None:
                continue
            snapshotdate_obj = self.resolve_date(snapshotdate_iso)
            if snapshotdate_obj is None:
                continue
            if min_date_obj is not None and snapshotdate_obj < min_date_obj:
                continue
            if max_date_obj is not None and snapshotdate_obj > max_date_obj:
                continue
            result.append(ref)
        return result

    def get_subinterface(
        self,
        snapshotdate: date | str | None = None,  # YYYY-MM-DD
    ) -> NonePTN:
        snapshotdate_obj: date | None = self.resolve_date(snapshotdate)
        if snapshotdate_obj is None:
            msg = f"Invalid snapshotdate: {snapshotdate}"
            raise ValueError(msg)
        snapshotdate_iso = snapshotdate_obj.strftime(self.DATE_FORMAT)
        return NonePTN(
            ref=self.ref.to(rel=f"snapshotdate={snapshotdate_iso}"),
            connect=self.connect,
            parent=self,
        )

from __future__ import annotations

from datetime import date, datetime

from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.interface import BaseInterface
from xdatawork.interface.factory import InterfaceFactory
from xdatawork.interface.instance.noneptn import NonePTN


@InterfaceFactory.register(
    name="dateptn",
    alias="dtptn",
)
class DatePTN(BaseInterface):
    """
    描述:
    - 日期分区接口，用于管理按日期分区的数据。
    - 支持日期范围过滤和日期格式验证。

    属性:
    - partition_fields: 固定为 ["date"]
    - partition_kind: 自动设置为 DATE_PARTITIONED

    方法:
    - list_date_refs: 列出指定日期范围内的引用

    例子:
    ```python
        from xdatawork.interface import DatePTN
        from xdatawork.connect import S3Connect

        connect = S3Connect()
        interface = DatePTN(
            ref={"location": "s3://bucket/data/"},
            connect=connect
        )

        # 列出特定日期范围的数据
        refs = interface.list_date_refs(
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
            partition_fields=["date"],
        )
        self.key = "dateptn"

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

    def list_date_refs(
        self,
        min: date | str | None = None,  # YYYY-MM-DD
        max: date | str | None = None,  # YYYY-MM-DD
    ) -> list[ConnectRef]:
        result = []
        min_date_obj: date | None = self.resolve_date(min)
        max_date_obj: date | None = self.resolve_date(max)
        for ref in self.list_refs():
            date_iso = ref.get_partition("date", None)
            if date_iso is None:
                continue
            date_obj = self.resolve_date(date_iso)
            if date_obj is None:
                continue
            if min_date_obj is not None and date_obj < min_date_obj:
                continue
            if max_date_obj is not None and date_obj > max_date_obj:
                continue
            result.append(ref)
        return result

    def get_subinterface(
        self,
        date: date | str | None = None,  # YYYY-MM-DD
    ) -> NonePTN:
        date_obj: date | None = self.resolve_date(date)
        if date_obj is None:
            msg = f"Invalid date: {date}"
            raise ValueError(msg)
        date_iso = date_obj.strftime(self.DATE_FORMAT)
        return NonePTN(
            ref=self.ref.to(rel=f"date={date_iso}"),
            connect=self.connect,
            parent=self,
        )

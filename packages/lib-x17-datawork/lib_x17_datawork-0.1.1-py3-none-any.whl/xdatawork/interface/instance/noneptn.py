from __future__ import annotations

from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.interface.base.interface import BaseInterface
from xdatawork.interface.factory import InterfaceFactory


@InterfaceFactory.register(
    name="noneptn",
    alias="none",
)
class NonePTN(BaseInterface):
    """
    描述:
    - 日期分区接口，用于管理按日期分区的数据。
    - 支持日期范围过滤和日期格式验证。

    属性:
    - partition_fields: 固定为 ["date"]
    - partition_kind: 自动设置为 DATE_PARTITIONED

    例子:
    ```python
        from xdatawork.interface import NonePTN
        from xdatawork.connect import S3Connect

        connect = S3Connect()
        interface = NonePTN(
            ref={"location": "s3://bucket/data/"},
            connect=connect
        )

        # 列出特定日期范围的数据
        refs = interface.list_refs()
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
            partition_fields=None,
        )
        self.key = "noneptn"

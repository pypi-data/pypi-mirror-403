from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.connect.errors import (
    ConnectError,
    ConnectLocationError,
)


class MacOSConnect(ConnectLike):
    """
    描述:
    - macOS 本地文件系统连接实现类。
    - 实现了 ConnectLike 协议，用于与本地文件系统进行交互。
    - 支持读取和写入本地文件。
    - 自动处理路径解析、用户目录展开和父目录创建。
    - 适用于 macOS 和其他 Unix-like 系统。

    属性:
    - kind: 连接类型标识，固定为 "macos"。

    例子:
    ```python
        from xdatawork.connect.macos import MacOSConnect

        connect = MacOSConnect()

        # 写入数据到本地文件
        ref = connect.put_object(b"data", "/path/to/file.txt")

        # 读取本地文件
        data = connect.get_object("/path/to/file.txt")

        # 使用 Path 对象
        from pathlib import Path
        ref = connect.put_object(b"data", Path("~/data/file.txt"))

        # 支持用户目录展开
        data = connect.get_object("~/documents/data.bin")
    ```
    """

    def __init__(self) -> None:
        self.kind: str = ConnectKind.MACOS

    def resolve_path(
        self,
        location: str | Path,
    ) -> Path:
        if location in (None, ""):
            msg = "location cannot be empty"
            raise ConnectLocationError(msg)
        if isinstance(location, Path):
            location = location
        else:
            location = Path(location)
        location = location.expanduser().resolve(
            strict=False,
        )
        try:
            location.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
        except Exception:
            # Ignore directory creation errors (e.g., permission / read-only FS).
            # Let callers handle file open/read/write errors and raise
            # ConnectError with a clearer message.
            pass
        return location

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def put_bytes(
        self,
        data: bytes,
        location: str | Path,
        **kwargs: Any,
    ) -> None:
        path = self.resolve_path(location)
        try:
            with path.open("wb") as f:
                f.write(data)
        except Exception as e:
            raise ConnectError(str(e)) from e

    def get_bytes(
        self,
        location: str | Path,
        **kwargs: Any,
    ) -> bytes:
        path = self.resolve_path(location)
        try:
            with path.open("rb") as f:
                return f.read()
        except Exception as e:
            raise ConnectError(str(e)) from e

    def get_object(
        self,
        location: str | ConnectRefLike,
        **kwargs: Any,
    ) -> bytes:
        if isinstance(location, ConnectRefLike):
            location = location.location
        return self.get_bytes(
            location,
            **kwargs,
        )

    def put_object(
        self,
        data: bytes,
        location: str | ConnectRefLike,
        **kwargs: Any,
    ) -> ConnectRef:
        if isinstance(location, ConnectRefLike):
            location = location.location
        self.put_bytes(
            data,
            location,
            **kwargs,
        )
        return ConnectRef(
            location=str(location),
            kind=self.kind,
        )

    def list_objects(
        self,
        location: str | ConnectRefLike,
        level: int | None = None,
        pattern: str | None = None,
        **kwargs: Any,
    ) -> list[ConnectRefLike]:
        if isinstance(location, ConnectRefLike):
            location = location.location
        # Ensure the root path is absolute and normalized
        rootdir = os.path.abspath(os.path.expanduser(location))
        results = []
        for root, dirs, files in os.walk(rootdir):
            relpath = os.path.relpath(root, rootdir)
            if relpath == ".":
                currentlevel = 0
            else:
                currentlevel = relpath.count(os.sep) + 1
            if level is not None and currentlevel >= level:
                dirs[:] = []
            for name in files:
                filelevel = currentlevel
                if level is not None and filelevel > level:
                    continue
                full_path = os.path.join(root, name)
                if pattern:
                    if not fnmatch.fnmatch(full_path, f"*{pattern}"):
                        continue
                results.append(
                    ConnectRef(
                        location=full_path,
                        kind=self.kind,
                    )
                )
        return results

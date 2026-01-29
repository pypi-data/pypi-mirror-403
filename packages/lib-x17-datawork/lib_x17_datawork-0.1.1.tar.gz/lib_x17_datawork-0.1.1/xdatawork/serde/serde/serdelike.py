from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from xdatawork.serde.format.dataformat import DataFormat


@runtime_checkable
class SerDeLike(Protocol):
    SUPPORTED_SER_SOURCE: set[type]
    SUPPORTED_DE_SOURCE: set[type]
    SUPPORTED_FORMAT: set[DataFormat]

    @staticmethod
    def deserialise(
        data: Any,
        format: str | DataFormat,
        **kwargs: Any,
    ) -> Any: ...

    @staticmethod
    def serialise(
        data: Any,
        format: str | DataFormat,
        **kwargs: Any,
    ) -> Any: ...

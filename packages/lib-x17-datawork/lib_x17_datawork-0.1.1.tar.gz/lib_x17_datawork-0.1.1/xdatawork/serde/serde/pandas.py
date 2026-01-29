from __future__ import annotations

from io import BytesIO, StringIO
from typing import Any

import pandas as pd

from xdatawork.serde.format.dataformat import DataFormat
from xdatawork.serde.serde.errors import (
    SerDeFailedError,
    SerDeImportError,
    SerDeNotSupportedError,
    SerDeTypeError,
)
from xdatawork.serde.serde.serdelike import SerDeLike


class SerDePandas(SerDeLike):
    SUPPORTED_SER_SOURCE = {pd.DataFrame}
    SUPPORTED_DE_SOURCE = {bytes}
    SUPPORTED_FORMAT = {
        DataFormat.PARQUET,
        DataFormat.CSV,
        DataFormat.JSON,
    }

    # ================================================================
    # SERIALISATION
    # ================================================================

    @staticmethod
    def serialise(
        data: pd.DataFrame,
        format: DataFormat | str,
        **kwargs: Any,
    ) -> bytes:
        if type(data) not in SerDePandas.SUPPORTED_SER_SOURCE:
            msg = f"SerDePandas.serialise expects {SerDePandas.SUPPORTED_SER_SOURCE}, got {type(data)}"
            raise SerDeTypeError(msg)
        format = DataFormat.from_any(format)
        if format == DataFormat.PARQUET:
            return SerDePandas.to_parquet(data, **kwargs)
        elif format == DataFormat.CSV:
            return SerDePandas.to_csv(data, **kwargs)
        elif format == DataFormat.JSON:
            return SerDePandas.to_json(data, **kwargs)
        else:
            msg = f"SerDePandas.serialise supports {SerDePandas.SUPPORTED_FORMAT}, got {format}"
            raise SerDeNotSupportedError(msg)

    @staticmethod
    def to_parquet(
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> bytes:
        kwargs.setdefault("index", False)
        kwargs.setdefault("engine", "pyarrow")
        kwargs.setdefault("coerce_timestamps", "us")
        kwargs.setdefault("allow_truncated_timestamps", True)
        buffer = BytesIO()
        try:
            data.to_parquet(buffer, **kwargs)
            return buffer.getvalue()
        except ImportError as e:
            msg = "'pyarrow' is required for parquet serialization, install via 'pip install pyarrow'."
            raise SerDeImportError(msg) from e
        except Exception as e:
            msg = f"Failed to serialize data: {e}"
            raise SerDeFailedError(msg) from e

    @staticmethod
    def to_csv(
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> bytes:
        kwargs.setdefault("index", False)
        encoding = kwargs.pop("encoding", "utf-8")
        try:
            text: str = data.to_csv(**kwargs)
            return text.encode(encoding)
        except Exception as e:
            msg = f"Failed to serialize data: {e}"
            raise SerDeFailedError(msg) from e

    @staticmethod
    def to_json(
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> bytes:
        encoding = kwargs.pop("encoding", "utf-8")
        orient = kwargs.pop("orient", "records")
        lines = kwargs.pop("lines", False)
        try:
            text: str = data.to_json(
                orient=orient,
                lines=lines,
                **kwargs,
            )
            return text.encode(encoding)
        except Exception as e:
            msg = f"Failed to serialize data: {e}"
            raise SerDeFailedError(msg) from e

    # ================================================================
    # DESERIALISATION
    # ================================================================

    @staticmethod
    def deserialise(
        data: bytes,
        format: DataFormat | str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        if type(data) not in SerDePandas.SUPPORTED_DE_SOURCE:
            msg = f"SerDePandas.deserialise expects {SerDePandas.SUPPORTED_DE_SOURCE}, got {type(data)}"
            raise SerDeTypeError(msg)
        format = DataFormat.from_any(format)
        if format == DataFormat.PARQUET:
            return SerDePandas.from_parquet(data, **kwargs)
        elif format == DataFormat.CSV:
            return SerDePandas.from_csv(data, **kwargs)
        elif format == DataFormat.JSON:
            return SerDePandas.from_json(data, **kwargs)
        else:
            msg = f"SerDePandas.deserialise supports {SerDePandas.SUPPORTED_FORMAT}, got {format}"
            raise SerDeNotSupportedError(msg)

    @staticmethod
    def from_parquet(
        data: bytes,
        **kwargs: Any,
    ) -> pd.DataFrame:
        kwargs.setdefault("engine", "pyarrow")
        buffer = BytesIO(data)
        try:
            output = pd.read_parquet(buffer, **kwargs)
            return output
        except ImportError as e:
            msg = "'pyarrow' is required for parquet deserialization, install via 'pip install pyarrow'."
            raise SerDeImportError(msg) from e
        except Exception as e:
            msg = f"Failed to deserialize data: {e}"
            raise SerDeFailedError(msg) from e

    @staticmethod
    def from_csv(
        data: bytes,
        **kwargs: Any,
    ) -> pd.DataFrame:
        encoding = kwargs.pop("encoding", "utf-8")
        try:
            buffer = StringIO(data.decode(encoding))
            return pd.read_csv(buffer, **kwargs)
        except Exception as e:
            msg = f"Failed to deserialize data: {e}"
            raise SerDeFailedError(msg) from e

    @staticmethod
    def from_json(
        data: bytes,
        **kwargs: Any,
    ) -> pd.DataFrame:
        encoding = kwargs.pop("encoding", "utf-8")
        orient = kwargs.pop("orient", "records")
        lines = kwargs.pop("lines", False)
        try:
            text = data.decode(encoding)
            buf = StringIO(text)
            return pd.read_json(
                buf,
                orient=orient,
                lines=lines,
                **kwargs,
            )
        except Exception as e:
            msg = f"Failed to deserialize data: {e}"
            raise SerDeFailedError(msg) from e

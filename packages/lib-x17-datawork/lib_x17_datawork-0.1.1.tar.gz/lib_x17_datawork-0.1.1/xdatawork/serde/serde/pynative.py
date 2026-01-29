from __future__ import annotations

import json
from typing import Any, Mapping

import tomlkit

from xdatawork.serde.format.dataformat import DataFormat
from xdatawork.serde.serde.errors import (
    SerDeFailedError,
    SerDeImportError,
    SerDeNotSupportedError,
    SerDeTypeError,
)
from xdatawork.serde.serde.serdelike import SerDeLike


class SerDePynative(SerDeLike):
    SUPPORTED_SER_SOURCE = {dict, list}
    SUPPORTED_DE_SOURCE = {bytes}
    SUPPORTED_FORMAT = {DataFormat.TOML, DataFormat.JSON}

    # ================================================================
    # SERIALISATION
    # ================================================================
    @staticmethod
    def serialise(
        data: dict | list | Mapping,
        format: DataFormat | str,
        **kwargs: Any,
    ) -> bytes:
        if type(data) not in SerDePynative.SUPPORTED_SER_SOURCE:
            msg = f"SerDePynative.serialise expects {SerDePynative.SUPPORTED_SER_SOURCE}, got {type(data)}"
            raise SerDeTypeError(msg)
        format = DataFormat.from_any(format)
        if format == DataFormat.TOML:
            return SerDePynative.to_toml(data, **kwargs)
        elif format == DataFormat.JSON:
            return SerDePynative.to_json(data, **kwargs)
        elif format == DataFormat.TEXT:
            return SerDePynative.to_text(data, **kwargs)
        else:
            msg = f"SerDePynative.serialise supports {SerDePynative.SUPPORTED_FORMAT}, got {format}"
            raise SerDeNotSupportedError(msg)

    @staticmethod
    def to_toml(
        data: dict | list,
        **kwargs: Any,
    ) -> bytes:
        kwargs.setdefault("sort_keys", True)
        try:
            tomltext = tomlkit.dumps(data, **kwargs)
            return tomltext.encode("utf-8")
        except ImportError as e:
            msg = "'tomlkit' is required for TOML serialisation, install via 'pip install tomlkit'"
            raise SerDeImportError(msg) from e
        except Exception as e:
            msg = f"Failed to serialise data to TOML: {e}"
            raise SerDeFailedError(msg) from e

    @staticmethod
    def to_json(
        data: Any,
        **kwargs: Any,
    ) -> bytes:
        encoding = kwargs.pop("encoding", "utf-8")
        kwargs.setdefault("ensure_ascii", False)
        kwargs.setdefault("indent", 4)
        kwargs.setdefault("sort_keys", True)
        try:
            payload = json.dumps(
                data,
                **kwargs,
            )
            return payload.encode(encoding)
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
    ) -> dict | list:
        if type(data) not in SerDePynative.SUPPORTED_DE_SOURCE:
            msg = f"SerDePynative.deserialise expects {SerDePynative.SUPPORTED_DE_SOURCE}, got {type(data)}"
            raise SerDeTypeError(msg)
        format = DataFormat.from_any(format)
        if format == DataFormat.TOML:
            return SerDePynative.from_toml(data, **kwargs)
        elif format == DataFormat.JSON:
            return SerDePynative.from_json(data, **kwargs)
        else:
            msg = f"SerDePynative.deserialise supports {SerDePynative.SUPPORTED_FORMAT}, got {format}"
            raise SerDeNotSupportedError(msg)

    @staticmethod
    def from_toml(
        data: bytes,
        **kwargs: Any,
    ) -> dict | list:
        encoding = kwargs.pop("encoding", "utf-8")
        tomltext = data.decode(encoding)
        try:
            return tomlkit.loads(tomltext, **kwargs)
        except ImportError as e:
            msg = "'tomlkit' is required for TOML deserialisation, install via 'pip install tomlkit'"
            raise SerDeImportError(msg) from e
        except Exception as e:
            msg = f"Failed to deserialise data from TOML: {e}"
            raise SerDeFailedError(msg) from e

    @staticmethod
    def from_json(
        data: bytes,
        **kwargs: Any,
    ) -> dict | list:
        encoding = kwargs.pop("encoding", "utf-8")
        jsontext = data.decode(encoding)
        try:
            return json.loads(jsontext, **kwargs)
        except Exception as e:
            msg = f"Failed to deserialise data from JSON: {e}"
            raise SerDeFailedError(msg) from e

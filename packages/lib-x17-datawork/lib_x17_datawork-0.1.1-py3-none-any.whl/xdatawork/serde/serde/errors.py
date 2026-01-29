from __future__ import annotations


class SerDeTypeError(TypeError):
    """
    当输入数据类型不符合预期时抛出（例如期望 bytes 但收到 str）。
    """

    pass


class SerDeImportError(ImportError):
    """
    当必需的库未安装时抛出（例如 pyarrow）。
    """

    pass


class SerDeNotSupportedError(TypeError):
    """
    当请求的数据格式不被支持时抛出。
    """

    pass


class SerDeFailedError(Exception):
    """
    当反序列化过程中发生错误时抛出。
    """

    pass

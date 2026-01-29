from __future__ import annotations


class ConnectLocationError(KeyError):
    """连接位置错误异常类。"""

    pass


class ConnectDependencyImportError(ImportError):
    """依赖未安装错误异常类。"""

    pass


class ConnectClientError(Exception):
    """S3 连接客户端错误异常类。"""

    pass


class ConnectClientInvalid(TypeError):
    """S3 连接客户端无效错误异常类。"""

    pass


class ConnectError(Exception):
    """通用连接错误异常类。"""

    pass

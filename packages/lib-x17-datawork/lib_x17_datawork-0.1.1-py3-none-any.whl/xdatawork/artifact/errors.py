from __future__ import annotations


class ArtifactReadError(Exception):
    """
    当从存储读取数据制品时发生错误时抛出。
    """

    pass


class ArtifactWriteError(Exception):
    """
    当从存储写入数据制品时发生错误时抛出。
    """

    pass

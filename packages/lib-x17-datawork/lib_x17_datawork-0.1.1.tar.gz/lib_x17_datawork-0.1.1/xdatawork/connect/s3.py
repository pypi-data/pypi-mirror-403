from __future__ import annotations

import fnmatch
from typing import Any, Optional
from urllib.parse import ParseResult, urlparse

from xdatawork.connect.connectkind import ConnectKind
from xdatawork.connect.connectlike import ConnectLike
from xdatawork.connect.connectref import ConnectRef
from xdatawork.connect.connectreflike import ConnectRefLike
from xdatawork.connect.errors import (
    ConnectClientError,
    ConnectClientInvalid,
    ConnectDependencyImportError,
    ConnectError,
    ConnectLocationError,
)


class S3Connect(ConnectLike):
    """
    描述:
    - AWS S3 存储连接实现类。
    - 实现了 ConnectLike 协议，用于与 AWS S3 存储进行交互。
    - 支持从 S3 读取和写入对象数据。
    - 自动处理 S3 URI 解析和客户端初始化。
    - 可以使用自定义 boto3 客户端或自动创建默认客户端。

    属性:
    - kind: 连接类型标识，固定为 "s3"。
    - _client: boto3 S3 客户端实例。

    例子:
    ```python
        from xdatawork.connect.s3 import S3Connect

        # 使用默认客户端
        connect = S3Connect()

        # 写入数据
        ref = connect.put_object(b"data", "s3://bucket/key")

        # 读取数据
        data = connect.get_object("s3://bucket/key")

        # 使用自定义客户端
        import boto3
        custom_client = boto3.client('s3', region_name='us-west-2')
        connect = S3Connect(client=custom_client)
    ```
    """

    def __init__(
        self,
        client: Optional[object] = None,
    ) -> None:
        self.kind = ConnectKind.S3
        self._client: object = self._resolve_client(client)

    def _resolve_client(
        self,
        client: Optional[object] = None,
    ) -> object:
        if not client:
            # Create default boto3 S3 client
            try:
                import boto3

                client = boto3.client("s3")
            except ImportError as e:
                msg = f"boto3 is required for {self.__class__.__name__}. Install it with 'pip install boto3'."
                raise ConnectDependencyImportError(msg) from e
            except Exception as e:
                msg = "default s3 client creation failed"
                raise ConnectClientError(msg) from e
        self._validate_client(client)
        return client

    def _validate_client(
        self,
        client: object,
    ) -> None:
        try:
            required_methods = ["put_object", "get_object"]
            for method in required_methods:
                if not hasattr(client, method):
                    msg = f"provided s3 client has no '{method}' method"
                    raise ConnectClientInvalid(msg)
                if not callable(getattr(client, method)):
                    msg = f"provided s3 client '{method}' method not callable"
                    raise ConnectClientInvalid(msg)
        except AssertionError as e:
            msg = "provided s3 client is invalid"
            raise ConnectClientInvalid(msg) from e

    def resolve_s3_uri(
        self,
        location: str,
    ) -> ParseResult:
        if not location.startswith("s3://"):
            location = "s3://" + location
        try:
            location = urlparse(location)
        except Exception as e:
            msg = f"invalid s3 location: {location}"
            raise ConnectLocationError(msg) from e
        if location.scheme != "s3":
            msg = f"s3 location must start with s3:// : {location.geturl()}"
            raise ConnectLocationError(msg)
        if not location.netloc:
            msg = f"s3 location missing bucket: {location.geturl()}"
            raise ConnectLocationError(msg)
        if not location.path:
            msg = f"s3 location missing key: {location.geturl()}"
            raise ConnectLocationError(msg)
        return location

    def resolve_bucket(
        self,
        location: str,
    ) -> str:
        res = self.resolve_s3_uri(location)
        if not res.netloc:
            msg = f"s3 location missing bucket: {location}"
            raise ConnectLocationError(msg)
        return res.netloc

    def resolve_key(
        self,
        location: str,
    ) -> str:
        res = self.resolve_s3_uri(location)
        if not res.path:
            msg = f"s3 location missing key: {location}"
            raise ConnectLocationError(msg)
        return res.path.lstrip("/")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def put_bytes(
        self,
        data: bytes,
        location: str,
        **kwargs: Any,
    ) -> None:
        try:
            self._client.put_object(
                Bucket=self.resolve_bucket(location),
                Key=self.resolve_key(location),
                Body=data,
                **kwargs,
            )
        except Exception as e:
            raise ConnectError(str(e)) from e

    def get_bytes(
        self,
        location: str,
        **kwargs: Any,
    ) -> bytes:
        try:
            response = self._client.get_object(
                Bucket=self.resolve_bucket(location),
                Key=self.resolve_key(location),
                **kwargs,
            )
            return response["Body"].read()
        except Exception as e:
            raise ConnectError(str(e)) from e

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

    def list_objects(
        self,
        location: str | ConnectRefLike,
        level: int | None = None,
        pattern: str | None = None,
        **kwargs: Any,
    ) -> list[ConnectRefLike]:
        if isinstance(location, ConnectRefLike):
            location = location.location
        bucket = self.resolve_bucket(location)
        prefix = self.resolve_key(location)
        paginator = self._client.get_paginator("list_objects_v2")
        results = []
        # Start paginating through the bucket
        for page in paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
        ):
            if "Contents" not in page:
                continue
            for obj in page["Contents"]:
                key = obj["Key"]
                rel = key[len(prefix) :]
                currentlevel = rel.count("/")
                if level is not None and currentlevel > level:
                    continue
                if pattern:
                    if not fnmatch.fnmatch(key, f"*{pattern}"):
                        continue
                # Construct full S3 URI
                s3_uri = f"s3://{bucket}/{key}"
                results.append(
                    ConnectRef(
                        location=s3_uri,
                        kind=self.kind,
                    )
                )
        return results

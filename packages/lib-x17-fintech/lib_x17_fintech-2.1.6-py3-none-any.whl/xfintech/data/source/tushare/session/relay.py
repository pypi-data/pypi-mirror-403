from __future__ import annotations

import gzip
import hashlib
import hmac
import io
import secrets
import time
from typing import Any, Callable, Dict, Optional

import pandas as pd
import requests

from xfintech.data.relay.client import RelayClient


class TushareRelayClient(RelayClient):
    """
    描述:
    - Tushare 中继服务客户端类，用于通过中继服务器访问 Tushare 数据。
    - 实现 HMAC-SHA256 签名认证机制，确保请求安全性。
    - 支持数据压缩和 Parquet 格式传输，提高数据传输效率。
    - 提供健康检查功能，确保服务可用性。

    属性:
    - url: str, 中继服务器 URL 地址。
    - secret: str, 用于 HMAC 签名的密钥。
    - timeout: int, 请求超时时间（秒），默认 180 秒。
    - DEFAULT_TIMEOUT: int = 180, 默认超时时间常量。

    方法:
    - call(method, limit, offset, params): 调用 Tushare API 方法并返回 DataFrame。
    - check_health(): 检查中继服务器健康状态。
    - canonical_json(value): 生成规范化的 JSON 字节串用于签名。

    例子:
    ```python
        from xfintech.data.source.tushare.session import TushareRelayClient

        # 创建中继客户端
        client = TushareRelayClient(
            url="https://relay.example.com",
            secret="your-secret-key",
            timeout=120
        )

        # 调用 API 获取数据
        df = client.call(
            method="daily",
            limit=100,
            offset=0,
            params={"ts_code": "000001.SZ", "start_date": "20240101"}
        )
        print(df.head())
    ```
    """

    def __init__(
        self,
        url: str,
        secret: str,
        timeout: Optional[int] = None,
    ) -> None:
        super().__init__(
            url=url,
            secret=secret,
            timeout=timeout,
        )

    def call(
        self,
        method: str,
        limit: int | None,
        offset: int | None,
        params: Dict[str, Any],
    ) -> pd.DataFrame:
        payload: Dict[str, Any] = {
            "path": f"{method}",
            "params": params,
            "limit": limit,
            "offset": offset,
        }
        body = self.canonical_json(payload)
        nonce = secrets.token_hex(16)
        timestamp = str(int(time.time()))
        msg = f"{nonce}.{timestamp}.".encode("utf-8") + body
        sig = hmac.new(
            self.secret.encode("utf-8"),
            msg,
            hashlib.sha256,
        ).hexdigest()
        url = f"{self.url}/v2/tushare/call"
        response = requests.post(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-YNONCE": nonce,
                "X-YTS": timestamp,
                "X-YSIGN": sig,
                "X-Format": "parquet",
                "X-Compression": "zstd+gzip",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        parquet_bytes = gzip.decompress(response.content)
        return pd.read_parquet(io.BytesIO(parquet_bytes))

    def refresh(
        self,
    ) -> bool:
        try:
            payload: Dict[str, Any] = {}
            body = self.canonical_json(payload)
            nonce = secrets.token_hex(16)
            timestamp = str(int(time.time()))
            msg = f"{nonce}.{timestamp}.".encode("utf-8") + body
            sig = hmac.new(
                self.secret.encode("utf-8"),
                msg,
                hashlib.sha256,
            ).hexdigest()
            url = f"{self.url}/v2/tushare/refresh"
            response = requests.post(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-YNONCE": nonce,
                    "X-YTS": timestamp,
                    "X-YSIGN": sig,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "ok":
                msg = f"Refresh returned non-ok status: {data}"
                raise RuntimeError(msg)
            return True
        except Exception as e:
            msg = f"Tushare refresh failed: {e}"
            raise RuntimeError(msg) from e

    def check_health(
        self,
    ) -> bool:
        try:
            url = f"{self.url}/health"
            response = requests.get(
                url,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            health = data.get("status") == "ok"
            if not health:
                raise RuntimeError("Health check returned non-ok status.")
            return True
        except Exception as e:
            raise RuntimeError(f"Health check failed: {e}") from e


class RelayConnection:
    """
    描述:
    - Tushare 中继连接类，提供动态方法调用接口。
    - 通过魔术方法 __getattr__ 实现类似 Tushare Pro API 的调用方式。
    - 自动将方法调用转发到 TushareRelayClient 进行处理。

    属性:
    - client: TushareRelayClient, 中继客户端实例。

    方法:
    - 动态方法: 通过属性访问自动创建对应的 API 调用方法。

    例子:
    ```python
        from xfintech.data.source.tushare.session import TushareRelayClient, RelayConnection

        # 创建客户端和连接
        client = TushareRelayClient(
            url="https://relay.example.com",
            secret="your-secret-key"
        )
        connection = RelayConnection(client=client)

        # 使用类似 Tushare Pro API 的方式调用
        # 等同于 pro.daily() 的调用方式
        df = connection.daily(
            ts_code="000001.SZ",
            start_date="20240101",
            end_date="20240131",
            limit=100,
            offset=0
        )
        print(df.head())

        # 调用其他方法
        df_basic = connection.stock_basic(
            exchange="SSE",
            list_status="L"
        )
    ```
    """

    def __init__(
        self,
        client: TushareRelayClient,
    ) -> None:
        self.client = client

    def __getattr__(
        self,
        method: str,
    ) -> Callable[..., pd.DataFrame]:
        def _call(
            *,
            limit: int | None = None,
            offset: int | None = None,
            **params: Any,
        ) -> pd.DataFrame:
            return self.client.call(
                method=method,
                limit=limit,
                offset=offset,
                params=params,
            )

        return _call

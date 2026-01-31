from __future__ import annotations

import json
from typing import Any, Optional

from xfintech.data.relay.clientlike import RelayClientLike


class RelayClient(RelayClientLike):
    """
    描述:
    - 中继客户端基类，提供通用的中继服务器连接功能。
    - 实现 URL、密钥和超时时间的验证与解析。
    - 提供规范化 JSON 序列化方法，确保数据格式一致性。
    - 作为具体中继客户端实现的基础类，子类需实现 call() 方法。

    属性:
    - url: str, 中继服务器 URL 地址（自动移除尾部斜杠）。
    - secret: str, 用于认证的密钥（自动去除首尾空格）。
    - timeout: int, 请求超时时间（秒），默认 180 秒。
    - DEFAULT_TIMEOUT: int = 180, 默认超时时间常量。

    方法:
    - canonical_json(value): 将数据转换为规范化的 JSON 字节串（键排序、无空格）。
    - call(): 抽象方法，由子类实现具体的 API 调用逻辑。

    例子:
    ```python
        from xfintech.data.relay.client import RelayClient

        # 创建子类实现
        class MyRelayClient(RelayClient):
            def call(self):
                # 实现具体的调用逻辑
                return {"result": "success"}

        # 使用客户端
        client = MyRelayClient(
            url="https://relay.example.com",
            secret="my-secret-key",
            timeout=120
        )

        # URL 自动处理尾部斜杠
        print(client.url)  # 输出: https://relay.example.com

        # 规范化 JSON 序列化
        data = {"name": "test", "value": 42}
        json_bytes = client.canonical_json(data)
        print(json_bytes)  # 输出: b'{"name":"test","value":42}'
    ```
    """

    DEFAULT_TIMEOUT = 180

    def __init__(
        self,
        url: str,
        secret: str,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        self.url = self._resolve_url(url)
        self.secret = self._resolve_secret(secret)
        self.timeout = self._resolve_timeout(timeout)

    def _resolve_url(
        self,
        url: str,
    ) -> str:
        if not url:
            msg = "Relay URL must be provided."
            raise ValueError(msg)
        return url.rstrip("/")

    def _resolve_secret(
        self,
        secret: str,
    ) -> str:
        if not secret:
            msg = "Relay secret must be provided."
            raise ValueError(msg)
        secret = secret.strip()
        if not secret:
            msg = "Relay secret must be provided."
            raise ValueError(msg)
        return secret

    def _resolve_timeout(
        self,
        timeout: Optional[int],
    ) -> int:
        if not timeout:
            return self.DEFAULT_TIMEOUT
        if not isinstance(timeout, int):
            msg = "Timeout must be an integer."
            raise ValueError(msg)
        if timeout <= 0:
            return self.DEFAULT_TIMEOUT
        return timeout

    def canonical_json(
        self,
        value: Any,
    ) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    def call(self) -> Any:
        raise NotImplementedError()

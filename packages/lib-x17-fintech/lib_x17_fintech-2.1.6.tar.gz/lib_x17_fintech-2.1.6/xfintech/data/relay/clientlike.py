from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RelayClientLike(Protocol):
    """
    描述:
    - 中继客户端协议接口，定义中继客户端必须实现的核心属性和方法。
    - 使用 Protocol 实现结构化类型检查（structural typing）。
    - 任何实现这些属性和方法的类都会被视为符合 RelayClientLike 协议。

    属性:
    - url: str, 中继服务器 URL 地址。
    - secret: str, 用于认证的密钥。
    - timeout: int, 请求超时时间（秒）。

    方法:
    - call(): 执行 API 调用并返回结果。

    例子:
    ```python
        from xfintech.data.relay.clientlike import RelayClientLike

        # 任何实现这些属性和方法的类都符合 RelayClientLike 协议
        class MyClient:
            def __init__(self):
                self.url = "https://api.example.com"
                self.secret = "my-secret"
                self.timeout = 180

            def call(self):
                return {"result": "success"}

        # 类型检查会通过
        client: RelayClientLike = MyClient()
    ```
    """

    url: str
    secret: str
    timeout: int

    def call(self) -> Any: ...

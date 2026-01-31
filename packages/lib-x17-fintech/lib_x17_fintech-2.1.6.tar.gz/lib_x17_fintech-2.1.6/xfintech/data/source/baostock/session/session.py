from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional

import baostock as bs
import pandas as pd

from xfintech.data.source.baostock.session.relay import (
    BaostockRelayClient,
    RelayConnection,
)


class Session:
    """
    描述:
    - Baostock 数据源会话管理类，支持直接连接和通过中继服务器连接两种模式。
    - 提供连接管理、状态跟踪和描述功能。
    - 支持会话持续时间跟踪，记录连接开始和结束时间。

    属性:
    - id: str, 会话唯一标识符（UUID 前 8 位）。
    - mode: str, 连接模式，"direct" 或 "relay"。
    - connection: object, Baostock 连接对象（bs 或 RelayConnection）。
    - start_at: pd.Timestamp, 会话开始时间。
    - finish_at: pd.Timestamp, 会话结束时间。
    - relay_url: str | None, 中继服务器 URL（relay 模式下必填）。
    - relay_secret: str | None, 中继服务器密钥（relay 模式下必填）。

    方法:
    - connect(): 建立连接，根据模式创建 direct 或 relay 连接。
    - disconnect(): 断开连接并记录结束时间。
    - start(): 记录会话开始时间。
    - end(): 记录会话结束时间。
    - get_start_iso(): 返回 ISO 格式的开始时间。
    - get_finish_iso(): 返回 ISO 格式的结束时间。
    - describe(): 返回会话描述信息（敏感信息已脱敏）。
    - to_dict(): 返回会话的完整字典表示。

    属性 (Property):
    - duration: float, 会话持续时间（秒）。
    - connected: bool, 是否已连接。

    例子:
    ```python
        from xfintech.data.source.baostock.session import Session

        # 直接连接模式
        session = Session(mode="direct")
        print(f"会话 ID: {session.id}")
        print(f"连接状态: {session.connected}")

        # 使用 Baostock API
        df = session.connection.query_history_k_data_plus(
            code="sh.600000",
            fields="date,code,open,high,low,close",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        # 查看会话信息
        print(session.describe())
        print(f"会话持续时间: {session.duration} 秒")

        # 关闭连接
        session.disconnect()

        # 中继连接模式
        relay_session = Session(
            mode="relay",
            relay_url="https://relay.example.com",
            relay_secret="your-relay-secret"
        )
        df = relay_session.connection.query_history_k_data_plus(
            code="sh.600000",
            fields="date,code,open,high,low,close"
        )
    ```
    """

    def __init__(
        self,
        mode: Literal["direct", "relay"] = "direct",
        relay_url: str | None = None,
        relay_secret: str | None = None,
    ) -> None:
        self._credential = None
        self.mode = self._resolve_mode(mode)
        self.id = str(uuid.uuid4())[:8]
        self.connection = None
        self.start_at = None
        self.finish_at = None
        self.relay_url = self._resolve_relay_url(
            relay_url,
            self.mode,
        )
        self.relay_secret = self._resolve_relay_secret(
            relay_secret,
            self.mode,
        )
        self.connect()

    def _resolve_mode(
        self,
        mode: Literal["direct", "relay"],
    ) -> str:
        mode = mode.lower()
        if not mode:
            return "direct"
        if mode not in ["direct", "relay"]:
            msg = f"Unsupported mode: {mode}"
            raise ValueError(msg)
        return mode

    def _resolve_relay_url(
        self,
        url: str | None,
        mode: str,
    ) -> str | None:
        if mode == "relay":
            if not url:
                msg = "URL must be provided in relay mode."
                raise ValueError(msg)
            return url
        else:
            return None

    def _resolve_relay_secret(
        self,
        secret: str | None,
        mode: str,
    ) -> str | None:
        if mode == "relay":
            if not secret:
                msg = "Secret must be provided in relay mode."
                raise ValueError(msg)
            return secret
        else:
            return None

    @property
    def duration(self) -> float:
        if not self.start_at:
            return 0.0
        if not self.finish_at:
            now = datetime.now()
            delta = now - self.start_at
            return delta.total_seconds()
        delta = self.finish_at - self.start_at
        return delta.total_seconds()

    @property
    def connected(self) -> bool:
        return self.connection is not None

    def __str__(self) -> str:
        return f"{self.id}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(connected={self.connected}, mode={self.mode})"

    def start(self) -> None:
        self.start_at = pd.Timestamp.now()

    def get_start_iso(self) -> Optional[str]:
        if self.start_at is None:
            return None
        return self.start_at.isoformat()

    def end(self) -> None:
        self.finish_at = pd.Timestamp.now()

    def get_finish_iso(self) -> Optional[str]:
        if self.finish_at is None:
            return None
        return self.finish_at.isoformat()

    def connect(self) -> object:
        if self.connected:
            return self.connection
        if self.mode == "direct":
            bs.login()
            self.connection = bs
        else:
            client = BaostockRelayClient(
                url=self.relay_url,
                secret=self.relay_secret,
            )
            client.check_health()
            self.connection = RelayConnection(
                client=client,
            )
        self.start()
        return self.connection

    def disconnect(self) -> None:
        if self.mode == "direct":
            bs.logout()
        self.connection = None
        self.end()

    def refresh(self) -> None:
        if self.mode == "relay" and self.connected:
            self.connection.client.refresh()
        else:
            self.disconnect()
            self.connect()

    def describe(self) -> Dict[str, Any]:
        start_at_iso = self.get_start_iso()
        finish_at_iso = self.get_finish_iso()
        result = {}
        result["id"] = self.id
        result["mode"] = self.mode
        if self.mode == "relay":
            result["relay"] = {
                "url": self.relay_url,
                "secret": "******",
            }
        result["connected"] = self.connected
        if start_at_iso:
            result["start_at"] = start_at_iso
        if finish_at_iso:
            result["finish_at"] = finish_at_iso
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "connected": self.connected,
            "mode": self.mode,
            "relay": {
                "url": self.relay_url,
                "secret": "******" if self.relay_secret else None,
            },
            "start_at": self.get_start_iso(),
            "finish_at": self.get_finish_iso(),
            "duration": self.duration,
        }

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional


class Params:
    """
    描述:
    - 动态参数容器类，用于灵活存储和管理键值对数据。
    - 支持通过属性访问和字典访问两种方式操作数据。
    - 提供数据序列化功能，确保复杂对象可转换为 JSON 兼容格式。
    - 可用于 API 请求参数、配置管理等场景。

    属性:
    - 动态属性: 通过 **kwargs 传入的任意键值对都会成为实例属性。

    方法:
    - from_dict(data): 从字典创建 Params 实例。
    - get(key, default): 获取属性值，如果不存在返回默认值。
    - set(key, value): 设置属性值。
    - describe(): 返回序列化后的字典，所有值转换为 JSON 兼容格式。
    - to_dict(): 返回原始值的字典表示。
    - ensure_serialisable(value): 静态方法，将复杂对象转换为可序列化格式。

    例子:
    ```python
        from xfintech.data.common.params import Params
        from datetime import datetime

        # 创建参数实例
        params = Params(symbol="AAPL", start_date=datetime(2024, 1, 1), limit=100)

        # 通过属性访问
        print(params.symbol)  # 输出: AAPL

        # 通过 get 方法访问
        limit = params.get("limit", 50)
        print(limit)  # 输出: 100

        # 检查属性是否存在
        if "symbol" in params:
            print("包含 symbol 属性")

        # 序列化为字典（日期转换为字符串）
        serialized = params.describe()
        print(serialized)  # 输出: {'symbol': 'AAPL', 'start_date': '2024-01-01', 'limit': 100}

        # 从字典创建实例
        new_params = Params.from_dict({"ticker": "TSLA", "quantity": 10})
        print(new_params.ticker)  # 输出: TSLA
    ```
    """

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> Params:
        if isinstance(data, Params):
            return data
        return cls(**data)

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def identifier(self) -> str:
        result = self.describe()
        dna = json.dumps(
            result,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(dna.encode("utf-8")).hexdigest()

    def __contains__(
        self,
        key: str,
    ) -> bool:
        return hasattr(self, key)

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"

    def keys(self) -> Any:
        result = []
        for key in self.__dict__.keys():
            if not key.startswith("_"):
                result.append(key)
        return result

    def values(self) -> Any:
        result = []
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result.append(value)
        return result

    def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Any:
        return getattr(self, key, default)

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        setattr(self, key, value)

    def items(
        self,
    ) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = value
        return result

    @staticmethod
    def ensure_serialisable(
        value: Any,
    ) -> Any:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        elif isinstance(value, Params):
            return value.to_dict()
        elif isinstance(value, dict):
            return {k: Params.ensure_serialisable(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [Params.ensure_serialisable(v) for v in value]
        elif isinstance(value, (int, float, str, bool, type(None))):
            return value
        else:
            return str(value)

    def describe(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = self.ensure_serialisable(value)
        return result

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = value
        return result

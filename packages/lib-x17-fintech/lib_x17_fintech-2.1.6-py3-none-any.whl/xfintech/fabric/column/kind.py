from __future__ import annotations

from enum import Enum
from typing import Any


class ColumnKind(str, Enum):
    """
    描述:
    - 列字段数据类型枚举类。

    参数:
    - INTEGER: 整数类型
    - FLOAT: 浮点数类型
    - STRING: 字符串类型（默认类型，未知类型将使用此类型）
    - BOOLEAN: 布尔类型
    - CATEGORICAL: 类别类型
    - DATETIME: 日期时间类型
    - DATE: 日期类型

    属性:
    - value: str, 列字段数据类型的字符串表示。
    - name: str, 列字段数据类型的名称。

    方法:
    - _missing_(value): 处理缺失值，支持不区分大小写的字符串匹配。
    - from_any(value): 从任意类型创建 ColumnKind 实例。
    - from_str(string): 从字符串创建 ColumnKind 实例（不区分大小写）。
    - __str__(): 返回列字段数据类型的字符串表示。
    - __repr__(): 返回列字段数据类型的表示形式。
    - __eq__(other): 支持与字符串的比较（不区分大小写）。
    - __ne__(value): 不等于比较。

    例子:
    ```python
        from xfintech.fabric.column.kind import ColumnKind

        # 使用枚举值
        kind = ColumnKind.INTEGER
        print(kind)  # Integer
        print(repr(kind))  # ColumnKind.INTEGER

        # 从字符串创建（不区分大小写）
        kind = ColumnKind.from_str("float")
        print(kind)  # Float

        kind = ColumnKind.from_str("STRING")
        print(kind)  # String

        # 从任意类型创建
        kind = ColumnKind.from_any("boolean")
        print(kind)  # Boolean

        kind = ColumnKind.from_any(ColumnKind.CATEGORICAL)
        print(kind)  # Categorical
    ```
    """

    INTEGER = "Integer"
    FLOAT = "Float"
    STRING = "String"
    BOOLEAN = "Boolean"
    CATEGORICAL = "Categorical"
    DATETIME = "Datetime"
    DATE = "Date"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return ColumnKind.STRING

    @classmethod
    def from_str(cls, string: str) -> ColumnKind:
        for dkind in ColumnKind:
            if dkind.value.lower() == string.lower():
                return dkind
        return ColumnKind.STRING

    @classmethod
    def from_any(cls, value: Any) -> ColumnKind:
        if isinstance(value, ColumnKind):
            return value
        if isinstance(value, str):
            return cls.from_str(value)
        return ColumnKind.STRING

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)

    def __ne__(self, value):
        return not self.__eq__(value)

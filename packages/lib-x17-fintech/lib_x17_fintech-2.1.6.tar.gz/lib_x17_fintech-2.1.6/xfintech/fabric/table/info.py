from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind


class TableInfo:
    """
    描述:
    - 表信息。

    参数:
    - name: str, optional, 表名称。 默认为空字符串。
    - desc: str, optional, 表描述信息。 默认为空字符串。
    - meta: Dict[str, Any], optional, 表元数据。 默认为None。
    - columns: List[ColumnInfo], optional, 列字段信息列表。 默认为空。

    属性:
    - name: str, 表名称，统一为小写。
    - desc: str, 表描述信息。
    - meta: Dict[str, Any], 表元数据。
    - columns: Dict[str, ColumnInfo], 列字段信息字典，键为列名称（小写）。

    方法:
    - from_dict(data): 从字典创建 TableInfo 实例。
    - get_column(name): 根据列名称获取 ColumnInfo 实例。
    - remove_column(name): 根据列名称移除 ColumnInfo 实例。
    - add_column(column): 添加 ColumnInfo 实例。
    - update_column(name, new, kind, desc, meta): 更新列字段信息。
    - rename_column(old, new): 重命名列字段。
    - list_columns(): 列出所有 ColumnInfo 实例。
    - describe(): 返回表信息的描述字典。
    - to_dict(): 返回表信息的字典表示。

    例子:
    ```python
        from xfintech.fabric.table.info import TableInfo
        from xfintech.fabric.column.info import ColumnInfo
        from xfintech.fabric.column.kind import ColumnKind

        table = TableInfo(
            desc="日线行情表",
            meta={"source": "tushare"},
            columns=[
                ColumnInfo(
                    name="price",
                    kind="Float",
                    desc="收盘价",
                ),
                ColumnInfo(
                    name="volume",
                    kind=ColumnKind.INTEGER,
                    desc="成交量",
                    meta={"unit": "shares"},
                ),
            ],
        )
        print(table.describe())
    ```
    """

    _NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "TableInfo":
        return cls(
            name=data.get("name"),
            desc=data.get("desc"),
            meta=data.get("meta"),
            columns=data.get("columns"),
        )

    def __init__(
        self,
        name: Optional[str] = None,
        desc: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        columns: Optional[List[ColumnInfo | Dict[str, Any]]] = None,
    ):
        self.name = self._resolve_name(name)
        self.desc = self._resolve_desc(desc)
        self.meta = self._resolve_meta(meta)
        self.columns = self._resolve_columns(columns)

    def _resolve_name(
        self,
        value: Optional[str],
    ) -> str:
        if not value:
            return ""
        else:
            value = value.strip()
            if not self._NAME_PATTERN.match(value):
                raise ValueError(f"Invalid table name: {value}")
            else:
                return value.lower()

    def _resolve_desc(
        self,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return ""
        else:
            return value.strip()

    def _resolve_meta(
        self,
        meta: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if meta is None:
            return None
        resolved: Dict[str, Any] = {}
        for k, v in meta.items():
            if isinstance(v, bytes):
                v = v.decode("utf8")
            if isinstance(k, bytes):
                k = k.decode("utf8")
            resolved[k] = v
        return resolved

    def _resolve_columns(
        self,
        columns: Optional[List[ColumnInfo | Dict[str, Any]]],
    ) -> Dict[str, ColumnInfo]:
        if columns is None:
            return {}

        resolved: Dict[str, ColumnInfo] = {}
        for item in columns:
            if isinstance(item, ColumnInfo):
                resolved[item.name] = item
            elif isinstance(item, dict):
                col = ColumnInfo.from_dict(item)
                resolved[col.name] = col
            else:
                raise TypeError(f"Invalid column type: {type(item)}")
        return resolved

    @property
    def identifier(self) -> str:
        result = {}
        result["name"] = self.name
        result["desc"] = self.desc
        result["columns"] = []
        values = sorted(
            self.columns.values(),
            key=lambda c: c.name,
        )
        for col in values:
            result["columns"].append(
                {
                    "name": col.name,
                    "kind": col.kind.value,
                }
            )
        dna = json.dumps(
            result,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(dna.encode("utf-8")).hexdigest()

    def __str__(self) -> str:
        return self.columns.__str__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

    def get_column(
        self,
        name: str,
    ) -> Optional[ColumnInfo]:
        return self.columns.get(name.lower())

    def remove_column(
        self,
        name: str,
    ) -> "TableInfo":
        key = name.lower()
        if key in self.columns:
            del self.columns[key]
        return self

    def add_column(
        self,
        column: ColumnInfo | Dict[str, Any],
    ) -> "TableInfo":
        if isinstance(column, dict):
            column = ColumnInfo.from_dict(column)
        self.columns[column.name] = column
        return self

    def update_column(
        self,
        name: str,
        new: Optional[str] = None,
        kind: Optional[ColumnKind | str] = None,
        desc: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "TableInfo":
        oldkey = name.lower()
        if oldkey in self.columns:
            self.columns[oldkey].update(
                kind=kind,
                desc=desc,
                meta=meta,
            )
            if new is not None:
                self.rename_column(
                    old=name,
                    new=new,
                )
        return self

    def rename_column(
        self,
        old: str,
        new: str,
    ) -> "TableInfo":
        oldkey = old.lower()
        newkey = new.lower()
        if oldkey in self.columns:
            self.columns[oldkey].update(name=new)
            self.columns[newkey] = self.columns[oldkey]
            del self.columns[oldkey]
        return self

    def list_columns(self) -> List[ColumnInfo]:
        return list(self.columns.values())

    def list_column_names(self) -> List[str]:
        return list(self.columns.keys())

    def describe(self) -> Dict[str, Any]:
        result = {}
        if self.name:
            result["name"] = self.name
        if self.desc:
            result["desc"] = self.desc
        if self.meta:
            result["meta"] = self.meta
        if self.columns:
            result["columns"] = [c.describe() for c in self.list_columns()]
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "name": self.name,
            "desc": self.desc,
            "meta": self.meta,
            "columns": [c.to_dict() for c in self.list_columns()],
        }

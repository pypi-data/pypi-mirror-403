from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Optional

from xfintech.fabric.column.kind import ColumnKind


class ColumnInfo:
    """
    描述:
    - 列字段信息。

    参数:
    - name: str, 列字段名称
    - kind: ColumnKind | str, optional, 列字段数据类型。 默认为 ColumnKind.STRING。
    - desc: str, optional, 列字段描述信息。 默认为""。
    - meta: Dict[str, Any], optional, 列字段元数据。 默认为None。

    属性:
    - name: str, 列字段名称，小写存储。
    - kind: ColumnKind, 列字段数据类型。
    - desc: str, 列字段描述信息。
    - meta: Dict[str, Any] | None, 列字段元数据。
    - identifier: str, 列字段唯一标识符，通过 SHA256 哈希生成。

    方法:
    - from_dict(data): 从字典创建 ColumnInfo 实例。
    - add_desc(desc): 添加或更新列字段描述信息。
    - add_meta(key, value): 添加或更新列字段元数据。
    - add_kind(kind): 添加或更新列字段数据类型。
    - update(name, kind, desc, meta): 更新列字段信息。
    - describe(): 返回列字段信息的描述字典。
    - to_dict(): 返回列字段信息的字典表示。

    例子:
    ```python
        from xfintech.fabric.column.kind import ColumnKind
        from xfintech.fabric.column.info import ColumnInfo

        f = ColumnInfo(
            name="price",
            kind="Float",
            desc="股票价格",
            meta=None,
        )

        f2 = ColumnInfo.from_dict({
            "name": "volume",
            "kind": "Integer",
            "desc": "交易量",
            "meta": {"unit": "shares"},
        })
    ```
    """

    _NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    _DEFAULT_KIND = ColumnKind.STRING

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> ColumnInfo:
        return cls(
            name=data["name"],
            kind=data.get("kind"),
            desc=data.get("desc"),
            meta=data.get("meta"),
        )

    def __init__(
        self,
        name: str,
        kind: Optional[ColumnKind | str] = None,
        desc: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.name = self._resolve_name(name)
        self.kind = self._resolve_kind(kind)
        self.desc = self._resolve_desc(desc)
        self.meta = self._resolve_meta(meta)

    def _resolve_name(
        self,
        value: str,
    ) -> str:
        if not self._NAME_PATTERN.match(value):
            raise ValueError(f"Invalid column name: {value}")
        return value.lower()

    def _resolve_kind(
        self,
        value: Optional[ColumnKind | str],
    ) -> ColumnKind:
        if value is None:
            return self._DEFAULT_KIND
        if isinstance(value, ColumnKind):
            return value
        try:
            return ColumnKind.from_str(value)
        except ValueError as e:
            raise ValueError(f"Invalid column kind: {value!r}") from e

    def _resolve_desc(
        self,
        value: Optional[str],
    ) -> Optional[str]:
        if value is not None:
            return value.strip()
        else:
            return ""

    def _resolve_meta(
        self,
        meta: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if meta is not None:
            resolved: Dict[str, Any] = {}
            for k, v in meta.items():
                if isinstance(v, bytes):
                    v = v.decode("utf8")
                if isinstance(k, bytes):
                    k = k.decode("utf8")
                resolved[k] = v
            return resolved
        else:
            return None

    @property
    def identifier(self) -> str:
        dna = json.dumps(
            {
                "name": self.name,
                "kind": str(self.kind),
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(dna.encode("utf-8")).hexdigest()

    def __str__(self) -> str:
        return f"{self.name}: {self.kind}"

    def __repr__(self) -> str:
        return self.to_dict().__repr__()

    def add_desc(self, desc: str) -> "ColumnInfo":
        self.update(desc=desc)
        return self

    def add_meta(self, key: str, value: Any) -> "ColumnInfo":
        if self.meta is None:
            self.meta = {}
        self.meta[key] = value
        return self

    def add_kind(self, kind: ColumnKind | str) -> "ColumnInfo":
        self.update(kind=kind)
        return self

    def update(
        self,
        name: Optional[str] = None,
        kind: Optional[ColumnKind | str] = None,
        desc: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "ColumnInfo":
        if name is not None:
            self.name = self._resolve_name(name)
        if kind is not None:
            self.kind = self._resolve_kind(kind)
        if desc is not None:
            self.desc = self._resolve_desc(desc)
        if meta is not None:
            if self.meta is None:
                self.meta = {}
            self.meta.update(self._resolve_meta(meta))
        return self

    def describe(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "kind": str(self.kind),
        }
        if self.desc:
            result["desc"] = self.desc
        if self.meta:
            result["meta"] = self.meta
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "name": self.name,
            "kind": str(self.kind),
            "desc": self.desc,
            "meta": self.meta,
        }

from __future__ import annotations

import hashlib
import pickle
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class Cache:
    """
    描述:
    - 文件缓存管理器，用于避免重复的 API 调用和数据处理。
    - 使用 pickle 序列化存储任意 Python 对象。
    - 使用 MD5 哈希将缓存键转换为文件名。
    - 自动创建和管理缓存目录。
    - 每个 Cache 实例有唯一标识符，避免冲突。

    属性:
    - identifier: str, 缓存实例的唯一标识符（12位十六进制）。
    - path: Path, 缓存文件存储路径。
    - DEFAULT_PARENT: Path, 类常量，默认缓存根目录为 /tmp/xfintech/。

    方法:
    - get(unit): 获取缓存值，不存在或出错返回 None。
    - set(unit, value): 设置缓存值。
    - get_unit(unit): 获取缓存单元的文件路径（MD5哈希）。
    - list(): 返回所有缓存文件的哈希键列表。
    - clear(): 清空所有缓存文件。
    - describe(): 返回缓存详细信息。
    - to_dict(): 返回缓存信息字典。
    - __contains__(unit): 支持 'in' 操作符检查缓存是否存在。
    - __str__(): 返回缓存路径字符串。
    - __repr__(): 返回对象的详细字符串表示。

    例子:
    ```python
        from xfintech.data.common.cache import Cache

        # 基本用法
        cache = Cache()
        cache.set("api_result", {"data": [1, 2, 3]})
        result = cache.get("api_result")
        print(result)  # {"data": [1, 2, 3]}

        # 检查缓存是否存在
        if "api_result" in cache:
            data = cache.get("api_result")

        # 自定义缓存路径
        cache = Cache(path="/custom/cache/path")

        # 列出所有缓存键
        keys = cache.list()
        print(f"缓存数量: {len(keys)}")

        # 获取缓存信息
        info = cache.to_dict()
        print(f"缓存路径: {info['path']}")
        print(f"缓存标识: {info['identifier']}")

        # 清空缓存
        cache.clear()

        # 缓存任意对象
        cache.set("user", {"name": "张三", "age": 30})
        cache.set("numbers", [1, 2, 3, 4, 5])
        cache.set("dataframe", pd.DataFrame(...))

        # 缓存失败返回 None
        result = cache.get("nonexistent")  # None
    ```
    """

    DEFAULT_PARENT = Path("/tmp/xfintech/")

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> Cache:
        if isinstance(data, Cache):
            return data
        return cls(
            path=data.get("path"),
        )

    def __init__(
        self,
        identifier: Optional[str] = None,
        path: Optional[str | Path] = None,
    ) -> None:
        self.identifier: str = self._resolve_identifier(identifier)
        self.path: Path = self._resolve_path(path)

    def _resolve_identifier(
        self,
        identifier: Optional[str] = None,
    ) -> str:
        if identifier is not None:
            return identifier
        return uuid.uuid4().hex[0:12]

    def _resolve_path(
        self,
        path: str | Path | None,
    ) -> Path:
        if path is not None:
            path = Path(path) / self.identifier
        else:
            path = self.DEFAULT_PARENT / self.identifier
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_unit(self, unit: str) -> Path:
        key = unit.encode("utf-8")
        hashed = hashlib.md5(
            key,
            usedforsecurity=False,
        ).hexdigest()
        return self.path / f"{hashed}.pkl"

    def __contains__(self, unit: str) -> bool:
        path = self.get_unit(unit)
        return path.exists()

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path})"

    def get(
        self,
        unit: str,
    ) -> Optional[Any]:
        unitpath = self.get_unit(unit)
        if not unitpath.exists():
            return None
        try:
            with unitpath.open("rb") as f:
                payload = pickle.load(f)
                value = payload.get("value")
            return value
        except Exception:
            return None

    def set(
        self,
        unit: str,
        value: Any,
    ) -> None:
        unitpath = self.get_unit(unit)
        payload = {"value": value}
        with unitpath.open("wb") as f:
            pickle.dump(payload, f)

    def list(
        self,
    ) -> List[str]:
        keys = []
        for file in self.path.glob("*.pkl"):
            keys.append(file.stem)
        return keys

    def clear(self) -> None:
        for file in self.path.glob("*.pkl"):
            try:
                file.unlink()
            except Exception:
                pass

    def describe(
        self,
    ) -> Dict[str, Any]:
        return self.to_dict()

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "path": str(self.path),
            "units": self.list(),
        }

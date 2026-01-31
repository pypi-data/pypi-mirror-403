from __future__ import annotations

from typing import Any, Dict


class Paginate:
    """
    描述:
    - 分页器类，用于管理数据分页请求。
    - 支持配置每页大小、总限制和偏移量。
    - 提供方法重置偏移量和获取下一页偏移量。

    属性:
    - pagesize: int, 每页数据大小，默认为 5000。
    - pagelimit: int, 总数据限制，默认为 10000。
    - offset: int, 当前数据偏移量，默认为 0。

    方法:
    - reset(): 重置偏移量为 0。
    - next(): 将偏移量增加一个页面大小，并返回新的偏移量。
    - describe(): 返回分页器配置信息字典（排除零值）。
    - to_dict(): 返回包含所有配置的完整字典。
    - from_dict(data): 从字典创建 Paginate 实例。

    例子:
    ```python
        from xfintech.data.common.paginate import Paginate

        # 创建分页器实例
        paginator = Paginate(pagesize=1000, pagelimit=5000)

        # 获取第一页数据（offset=0）
        print(f"当前偏移量: {paginator.offset}")  # 输出: 当前偏移量: 0

        # 移动到下一页
        new_offset = paginator.next()
        print(f"新的偏移量: {new_offset}")  # 输出: 新的偏移量: 1000

        # 继续翻页
        paginator.next()
        print(f"第三页偏移量: {paginator.offset}")  # 输出: 第三页偏移量: 2000

        # 重置到第一页
        paginator.reset()
        print(f"重置后偏移量: {paginator.offset}")  # 输出: 重置后偏移量: 0

        # 从字典创建
        new_paginator = Paginate.from_dict({
            "pagesize": 500,
            "pagelimit": 2000,
            "offset": 1000
        })
    ```
    """

    DEFAULT_PAGESIZE: int = 5000
    DEFAULT_PAGELIMIT: int = 10000
    DEFAULT_OFFSET: int = 0

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> Paginate:
        if isinstance(data, Paginate):
            return data
        return cls(
            pagelimit=data.get("pagelimit"),
            pagesize=data.get("pagesize"),
            offset=data.get("offset"),
        )

    def __init__(
        self,
        pagelimit: int = 10000,
        pagesize: int = 5000,
        offset: int = 0,
    ) -> None:
        self.pagelimit = self._resolve_pagelimit(pagelimit)
        self.pagesize = self._resolve_pagesize(pagesize)
        self.offset = self._resolve_offset(offset)

    def _resolve_pagelimit(
        self,
        pagelimit: int,
    ) -> int:
        if pagelimit and pagelimit > 0:
            return pagelimit
        else:
            return self.DEFAULT_PAGELIMIT

    def _resolve_pagesize(
        self,
        pagesize: int,
    ) -> int:
        if pagesize and pagesize > 0:
            return pagesize
        else:
            return self.DEFAULT_PAGESIZE

    def _resolve_offset(
        self,
        offset: int,
    ) -> int:
        if offset and offset >= 0:
            return offset
        else:
            return self.DEFAULT_OFFSET

    def reset(self) -> None:
        self.offset = 0

    def next(self) -> int:
        self.offset += self.pagesize
        return self.offset

    def describe(self) -> Dict[str, Any]:
        result = {}
        if self.pagesize:
            result["pagesize"] = self.pagesize
        if self.pagelimit:
            result["pagelimit"] = self.pagelimit
        if self.offset:
            result["offset"] = self.offset
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pagesize": self.pagesize,
            "pagelimit": self.pagelimit,
            "offset": self.offset,
        }

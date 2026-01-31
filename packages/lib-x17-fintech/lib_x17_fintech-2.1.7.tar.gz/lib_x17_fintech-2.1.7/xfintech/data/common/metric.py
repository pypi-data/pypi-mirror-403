from __future__ import annotations

import traceback
from typing import Dict, List, Optional

import pandas as pd


class Metric:
    """
    描述:
    - 用于跟踪操作执行时间和错误的工具类。
    - 支持上下文管理器模式，自动记录开始和结束时间。
    - 可以在执行过程中标记关键时间点（marks）。
    - 自动捕获并保存上下文管理器中发生的异常信息。
    - 提供多种格式的时间和状态数据输出。

    属性:
    - start_at: Optional[pd.Timestamp], 开始时间戳。
    - finish_at: Optional[pd.Timestamp], 结束时间戳。
    - marks: Dict[str, pd.Timestamp], 命名时间标记点的字典。
    - errors: List[str], 捕获的异常堆栈信息列表。
    - duration: float, 只读属性，返回执行时长（秒），如果未结束则返回至当前时间的时长。

    方法:
    - start(): 记录开始时间。
    - finish(): 记录结束时间。
    - mark(name): 在当前时间记录一个命名标记点。
    - reset(): 重置所有状态（时间、标记、错误）。
    - get_start_iso(): 返回 ISO 格式的开始时间字符串。
    - get_finish_iso(): 返回 ISO 格式的结束时间字符串。
    - get_mark_iso(): 返回所有标记点的 ISO 格式时间字典。
    - describe(): 返回包含非空字段的状态字典。
    - to_dict(): 返回包含所有字段的完整状态字典。

    例子:
    ```python
        from xfintech.data.common.metric import Metric
        import time

        # 作为上下文管理器使用
        with Metric() as m:
            time.sleep(0.1)
            m.mark("checkpoint_1")
            time.sleep(0.1)
            m.mark("checkpoint_2")
    ```
    """

    def __init__(self) -> None:
        self.start_at: Optional[pd.Timestamp] = None
        self.finish_at: Optional[pd.Timestamp] = None
        self.marks: Dict[str, pd.Timestamp] = {}
        self.errors: List[str] = []

    @property
    def duration(self) -> float:
        if not self.start_at:
            return 0.0
        if not self.finish_at:
            now = pd.Timestamp.now()
            return (now - self.start_at).total_seconds()
        diff = self.finish_at - self.start_at
        return diff.total_seconds()

    def reset(self) -> None:
        self.start_at = None
        self.finish_at = None
        self.marks = {}
        self.errors = []

    def __enter__(self) -> Metric:
        self.reset()
        self.start()
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> bool:
        if exc_val:
            tb = traceback.format_exception(
                exc_type,
                exc_val,
                exc_tb,
            )
            self.errors = [line.rstrip("\n") for line in tb]
        self.finish()
        return False

    def start(self) -> None:
        self.start_at = pd.Timestamp.now()

    def get_start_iso(self) -> Optional[str]:
        if self.start_at is None:
            return None
        return self.start_at.isoformat()

    def finish(self) -> None:
        self.finish_at = pd.Timestamp.now()

    def get_finish_iso(self) -> Optional[str]:
        if self.finish_at is None:
            return None
        return self.finish_at.isoformat()

    def mark(self, name: str) -> None:
        self.marks[name] = pd.Timestamp.now()

    def get_mark_iso(self) -> Dict[str, str]:
        result = {}
        for k, v in self.marks.items():
            result[k] = v.isoformat()
        return result

    def describe(self) -> Dict[str, Optional[object]]:
        result = {}
        if self.start_at is not None:
            result["started_at"] = self.get_start_iso()
        if self.finish_at is not None:
            result["finished_at"] = self.get_finish_iso()
        result["duration"] = self.duration
        if self.errors:
            result["errors"] = self.errors
        if self.marks:
            result["marks"] = self.get_mark_iso()
        return result

    def to_dict(self) -> Dict[str, Optional[object]]:
        return {
            "started_at": self.get_start_iso(),
            "finished_at": self.get_finish_iso(),
            "duration": self.duration,
            "errors": self.errors,
            "marks": self.get_mark_iso(),
        }

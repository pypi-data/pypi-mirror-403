from __future__ import annotations

import random
import time
from typing import Any, Dict, Optional


class Coolant:
    """
    描述:
    - 冷却器类，用于在操作之间添加延迟（冷却时间）。
    - 支持固定间隔冷却和随机抖动功能。
    - 可配置基础间隔时间和抖动范围。
    - 主要用于限制 API 调用频率或避免请求风暴。

    属性:
    - interval: int, 基础冷却间隔时间（秒），0 表示不冷却，默认为 0。
    - use_jitter: bool, 是否启用随机抖动，默认为 False。
    - jitter_min: float, 最小抖动时间（秒），默认为 0.1 秒。
    - jitter_max: float, 最大抖动时间（秒），默认为 3.0 秒。
    - DEFAULT_INTERVAL: int, 类常量，默认间隔时间为 0。
    - DEFAULT_JITTER_MIN: float, 类常量，默认最小抖动时间为 0.1 秒。
    - DEFAULT_JITTER_MAX: float, 类常量，默认最大抖动时间为 3.0 秒。

    方法:
    - cool(): 执行冷却操作，包括基础间隔和可选的抖动。
    - jitter(): 执行随机抖动延迟（内部方法）。

    例子:
    ```python
        from xfintech.data.common.coolant import Coolant
        import time

        # 基本用法：固定间隔冷却
        coolant = Coolant(interval=2)
        start = time.time()
        coolant.cool()
        elapsed = time.time() - start
        print(f"冷却时间: {elapsed:.2f}秒")  # 约 2.0 秒

        # 使用抖动：在基础间隔上添加随机延迟
        coolant = Coolant(interval=1, use_jitter=True)
        coolant.cool()  # 等待 1 秒 + 0.1~3.0 秒随机抖动

        # 自定义抖动范围
        coolant = Coolant(
            interval=2,
            use_jitter=True,
            jitter_min=0.5,
            jitter_max=1.5
        )
        coolant.cool()  # 等待 2 秒 + 0.5~1.5 秒随机抖动

        # 仅抖动，无固定间隔
        coolant = Coolant(interval=0, use_jitter=True)
        coolant.cool()  # 仅等待 0.1~3.0 秒随机抖动

        # 不冷却
        coolant = Coolant(interval=0)
        coolant.cool()  # 立即返回，不等待

        # 在循环中使用
        coolant = Coolant(interval=1, use_jitter=True)
        for i in range(5):
            # 执行某些操作
            print(f"任务 {i}")
            coolant.cool()  # 每次操作后冷却
    ```
    """

    DEFAULT_INTERVAL = 0
    DEFAULT_JITTER_MIN = 0.1
    DEFAULT_JITTER_MAX = 3.0

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> Coolant:
        if isinstance(data, Coolant):
            return data
        return cls(
            interval=data.get("interval"),
            use_jitter=data.get("use_jitter"),
            jitter_min=data.get("jitter_min"),
            jitter_max=data.get("jitter_max"),
        )

    def __init__(
        self,
        interval: Optional[int] = None,
        use_jitter: Optional[bool] = False,
        jitter_min: Optional[float | int] = None,
        jitter_max: Optional[float | int] = None,
    ) -> None:
        self.interval: int = self._resolve_interval(interval)
        self.use_jitter: bool = use_jitter
        self.jitter_min: float = self._resolve_jitter_min(jitter_min)
        self.jitter_max: float = self._resolve_jitter_max(jitter_max)

    def _resolve_interval(
        self,
        interval: Optional[int] = None,
    ) -> int:
        if interval is not None:
            return interval
        else:
            return self.DEFAULT_INTERVAL

    def _resolve_jitter_min(
        self,
        value: Optional[float | int] = None,
    ) -> float:
        if self.use_jitter:
            if value is not None:
                return float(value)
            else:
                return float(self.DEFAULT_JITTER_MIN)
        else:
            return 0.0

    def _resolve_jitter_max(
        self,
        value: Optional[float | int] = None,
    ) -> float:
        if self.use_jitter:
            if value is not None:
                return float(value)
            else:
                return float(self.DEFAULT_JITTER_MAX)
        else:
            return 0.0

    def __str__(self) -> str:
        return str(self.interval)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(interval={self.interval!r}, use_jitter={self.use_jitter!r}, "

    def jitter(self) -> None:
        if self.use_jitter:
            delay = random.uniform(
                self.jitter_min,
                self.jitter_max,
            )
            time.sleep(round(delay, 1))

    def cool(self) -> None:
        if self.interval <= 0:
            self.jitter()  # Still apply jitter even if interval is 0
            return
        time.sleep(round(self.interval, 1))
        self.jitter()

    def describe(self) -> Dict[str, Any]:
        result = {}
        result["interval"] = self.interval
        result["use_jitter"] = self.use_jitter
        if self.use_jitter:
            result["jitter_min"] = self.jitter_min
            result["jitter_max"] = self.jitter_max
        return result

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "interval": self.interval,
            "use_jitter": self.use_jitter,
            "jitter_min": self.jitter_min,
            "jitter_max": self.jitter_max,
        }
        return result

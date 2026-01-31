from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, Tuple, Type

import backoff


class Retry:
    """
    描述:
    - 函数重试装饰器类，用于自动重试失败的函数调用。
    - 支持固定间隔和指数退避两种重试策略。
    - 可配置重试次数、等待时间、退避系数和异常类型。
    - 支持添加随机抖动（jitter）以避免重试风暴。
    - 基于 backoff 库实现，提供可靠的重试机制。

    属性:
    - retry: int, 最大重试次数，0 表示不重试。
    - wait: float, 等待时间（秒），在固定间隔模式下为间隔时间，在指数退避模式下为基础时间。
    - rate: float, 退避系数，1.0 使用固定间隔，其他值使用指数退避。
    - exceptions: tuple[Type[BaseException], ...], 需要触发重试的异常类型元组。
    - jitter: bool, 是否启用随机抖动。
    - jitter_fn: Callable[[float], float] | None, 抖动函数，None 表示不使用抖动。

    方法:
    - __call__(func): 装饰器方法，将重试逻辑应用到目标函数。
    - __str__(): 返回重试次数的字符串表示。
    - __repr__(): 返回对象的完整字符串表示。
    - describe(): 返回配置信息的字典。
    - to_dict(): 返回包含所有配置信息的字典。

    例子:
    ```python
        from xfintech.data.common.retry import Retry

        # 指数退避重试
        @Retry(retry=5, wait=1.0, rate=2.0)
        def api_call():
            # 失败时等待时间：1s, 2s, 4s, 8s, 16s
            return "API 响应"

        # 不使用抖动
        @Retry(retry=3, wait=1.0, jitter=False)
        def precise_timing_call():
            # 精确的固定间隔，无随机抖动
            return "结果"

        # 不重试（retry=0）
        @Retry(retry=0)
        def no_retry_func():
            # 等同于没有装饰器，直接执行
            return "立即执行"

        # 使用 Retry 类作为变量
        def my_function():
            pass
        retry = Retry(retry=3, wait=1.0)
        wrapped = retry(my_function)
    ```
    """

    DEFAULT_RETRY = 0
    DEFAULT_WAIT = 0.0
    DEFAULT_RATE = 1.0

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> Retry:
        return cls(
            retry=data.get("retry"),
            wait=data.get("wait"),
            rate=data.get("rate"),
            exceptions=data.get("exceptions"),
            jitter=data.get("jitter"),
        )

    def __init__(
        self,
        retry: int = 0,
        wait: float = 0,
        rate: float = 1.0,
        exceptions: Iterable[Type[BaseException] | str] = None,
        jitter: bool = True,
    ) -> None:
        self.retry = self._resolve_retry(retry)
        self.wait = self._resolve_wait(wait)
        self.rate = self._resolve_rate(rate)
        self.exceptions = self._resolve_exceptions(exceptions)
        self.jitter = self._resolve_jitter(jitter)
        self.jitter_fn = self._resolve_jitter_fn()

    def _resolve_retry(
        self,
        retry: int,
    ) -> int:
        if retry is None:
            return self.DEFAULT_RETRY
        else:
            return max(0, retry)

    def _resolve_wait(
        self,
        wait: float,
    ) -> float:
        if wait is None:
            return self.DEFAULT_WAIT
        return max(0.0, float(wait))

    def _resolve_rate(
        self,
        rate: float,
    ) -> float:
        if rate is None:
            return self.DEFAULT_RATE
        return max(1.0, float(rate))

    def _resolve_jitter(
        self,
        jitter: bool,
    ) -> bool:
        if jitter is None:
            return True
        return jitter

    def _resolve_jitter_fn(
        self,
    ) -> Callable[[float], float] | None:
        if self.jitter:
            return backoff.full_jitter
        return None

    def _resolve_exceptions(
        self,
        exceptions: Iterable[Type[BaseException] | str] | None,
    ) -> Tuple[Type[BaseException], ...]:
        if not exceptions:
            return (Exception,)
        resolved: List[Type[BaseException]] = []
        for exc in exceptions:
            if isinstance(exc, str):
                exc_type = globals().get(exc)
                if exc_type and issubclass(exc_type, BaseException):
                    resolved.append(exc_type)
            elif issubclass(exc, BaseException):
                resolved.append(exc)
        return tuple(resolved)

    def __call__(
        self,
        func: Callable,
    ) -> Callable:
        if self.retry <= 0:
            return func
        if self.rate == 1.0:
            deco = backoff.on_exception(
                backoff.constant,
                self.exceptions,
                max_tries=self.retry,
                interval=self.wait,
                jitter=self.jitter_fn,
            )
        else:
            deco = backoff.on_exception(
                backoff.expo,
                self.exceptions,
                max_tries=self.retry,
                base=self.wait,
                factor=self.rate,
                jitter=self.jitter_fn,
            )
        wrapped_function = deco(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return wrapped_function(*args, **kwargs)

        return wrapper

    def __str__(self) -> str:
        return f"{self.retry}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(retry={self.retry}, "
            f"wait={self.wait}, rate={self.rate}, "
            f"exceptions={self.exceptions})"
        )

    def describe(self) -> Dict[str, Any]:
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "retry": self.retry,
            "wait": self.wait,
            "rate": self.rate,
            "exceptions": [exc.__name__ for exc in self.exceptions],
        }

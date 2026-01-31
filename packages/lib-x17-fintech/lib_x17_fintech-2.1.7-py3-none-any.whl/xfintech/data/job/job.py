from __future__ import annotations

from typing import Any, Dict, Optional

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.metric import Metric
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job.joblike import JobLike
from xfintech.fabric.table.info import TableInfo


class Job(JobLike):
    """
    描述:
    - 作业基类，用于管理数据请求任务的执行、重试、缓存和监控。
    - 集成参数管理、分页、冷却、重试、缓存和性能度量等功能。
    - 提供完整的作业生命周期管理，包括初始化、执行、重置等。
    - 子类需实现 _run() 方法来定义具体的执行逻辑。

    属性:
    - name: str, 作业名称。
    - key: str, 作业唯一标识键。
    - source: Optional[TableInfo], 数据源表信息。
    - target: Optional[TableInfo], 目标表信息。
    - params: Params, 作业参数对象。
    - coolant: Coolant, 冷却控制对象，用于速率限制。
    - paginate: Paginate, 分页管理对象。
    - retry: Retry, 重试策略对象。
    - cache: Optional[Cache], 缓存管理对象。
    - metric: Metric, 性能度量对象，记录执行时间和错误。

    方法:
    - run(): 执行作业，包含重试逻辑和性能度量。
    - _run(): 抽象方法，子类必须实现具体的执行逻辑。
    - markpoint(name): 在 metric 中标记检查点。
    - cool(): 执行冷却等待。
    - get_params(): 获取作业参数字典。
    - get_cache(unit): 从缓存获取数据。
    - set_cache(unit, data): 将数据保存到缓存。
    - reset(): 重置 metric 和清空缓存。
    - describe(): 返回作业描述信息（不包含敏感数据）。
    - to_dict(): 返回作业完整信息字典。

    例子:
    ```python
        from xfintech.data.job.job import Job
        from xfintech.data.common.params import Params

        # 创建自定义作业
        class MyDataJob(Job):
            def _run(self):
                # 实现具体的数据获取逻辑
                data = fetch_data(self.params)
                return data

        # 使用作业
        job = MyDataJob(
            name="daily_data",
            key="daily_data_001",
            params={"symbol": "AAPL", "date": "20240115"},
            retry={"max_retries": 3, "interval": 5},
            cache=True  # 启用缓存
        )

        # 执行作业
        result = job.run()

        # 查看执行信息
        print(f"执行耗时: {job.metric.duration} 秒")
        print(job.describe())
    ```
    """

    def __init__(
        self,
        name: str,
        key: str,
        source: Optional[TableInfo] = None,
        target: Optional[TableInfo] = None,
        params: Optional[Params | Dict[str, Any]] = None,
        coolant: Optional[Coolant | Dict[str, Any]] = None,
        paginate: Optional[Paginate | Dict[str, Any]] = None,
        retry: Optional[Retry | Dict[str, Any]] = None,
        cache: Optional[Cache | Dict[str, str] | bool] = None,
    ) -> None:
        self.name: str = name
        self.key: str = key
        self.source: Optional[TableInfo] = source
        self.target: Optional[TableInfo] = target
        self.params: Params = self._resolve_params(params)
        self.coolant: Coolant = self._resolve_coolant(coolant)
        self.paginate: Paginate = self._resolve_paginate(paginate)
        self.retry: Retry = self._resolve_retry(retry)
        self.cache: Optional[Cache] = self._resolve_cache(cache)
        self.metric: Metric = Metric()
        self.markpoint("init[OK]")

    def _resolve_params(
        self,
        params: Optional[Params | Dict[str, Any]],
    ) -> Params:
        if params is None:
            return Params()
        if isinstance(params, dict):
            return Params(**params)
        return params

    def _resolve_coolant(
        self,
        coolant: Optional[Coolant | Dict[str, Any]],
    ) -> Coolant:
        if coolant is None:
            return Coolant()
        if isinstance(coolant, dict):
            return Coolant.from_dict(coolant)
        return coolant

    def _resolve_paginate(
        self,
        paginate: Optional[Paginate | Dict[str, Any]],
    ) -> Paginate:
        if paginate is None:
            paginate = Paginate()
        if isinstance(paginate, dict):
            paginate = Paginate.from_dict(paginate)
        paginate.reset()
        return paginate

    def _resolve_retry(
        self,
        retry: Optional[Retry | Dict[str, Any]],
    ) -> Retry:
        if retry is None:
            return Retry()
        if isinstance(retry, dict):
            return Retry.from_dict(retry)
        return retry

    def _resolve_cache(
        self,
        cache: Optional[Cache | Dict[str, str] | bool],
    ) -> Optional[Cache]:
        if isinstance(cache, bool):
            if cache:
                return Cache(identifier=self.name)
            else:
                return None
        if isinstance(cache, dict):
            return Cache.from_dict(cache)
        if isinstance(cache, Cache):
            return cache
        return None

    def run(self) -> Any:
        wrapped = self.retry(self._run)
        with self.metric:
            return wrapped()

    def _run(self) -> object:
        msg = "Subclasses must implement this method."
        raise NotImplementedError(msg)

    def markpoint(
        self,
        name: str,
    ) -> None:
        self.metric.mark(name)

    def cool(self) -> None:
        self.coolant.cool()

    def get_params(self) -> Dict[str, Any]:
        return self.params.to_dict()

    def get_cache(
        self,
        unit: str,
        default: Any = None,
    ) -> Optional[Any]:
        if self.cache:
            result = self.cache.get(unit)
            if result is not None:
                return result
        return default

    def set_cache(
        self,
        unit: str,
        data: Any,
    ) -> None:
        if self.cache:
            self.cache.set(unit, data)

    def reset(self) -> None:
        self.metric.reset()
        if self.cache:
            self.cache.clear()

    def definition(self) -> Dict[str, Any]:
        result = {}
        if self.source:
            result["source"] = self.source.describe()
        if self.target:
            result["target"] = self.target.describe()
        return result

    def specification(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "key": self.key,
            "params": self.params.describe(),
            "coolant": self.coolant.describe(),
            "paginate": self.paginate.describe(),
            "retry": self.retry.describe(),
            "metric": self.metric.describe(),
        }
        if self.cache:
            result["cache"] = self.cache.describe()
        return result

    def describe(self) -> Dict[str, Any]:
        result = self.specification()
        if self.source:
            result["source"] = self.source.describe()
        if self.target:
            result["target"] = self.target.describe()
        return result

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "key": self.key,
            "params": self.params.to_dict(),
            "coolant": self.coolant.to_dict(),
            "paginate": self.paginate.to_dict(),
            "retry": self.retry.to_dict(),
            "metric": self.metric.to_dict(),
        }
        if self.source:
            result["source"] = self.source.to_dict()
        if self.target:
            result["target"] = self.target.to_dict()
        if self.cache:
            result["cache"] = self.cache.to_dict()
        return result

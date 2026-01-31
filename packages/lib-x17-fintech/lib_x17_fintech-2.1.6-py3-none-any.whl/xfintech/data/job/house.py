from __future__ import annotations

from typing import Any

from xfintech.data.job.errors import (
    JobAlreadyRegisteredError,
    JobNameError,
    JobNotFoundError,
)


class House:
    """
    描述:
    - Job 注册和管理容器，提供 Job 类的注册、查找和创建功能。
    - 支持 Job 别名机制，允许一个 Job 类有多个访问名称。
    - 所有名称不区分大小写，自动归一化处理。
    - 提供装饰器模式注册 Job 类。

    参数:
    - 无参数。

    属性:
    - _jobs: dict[str, type], Job 名称到类的映射字典。
    - _aliases: dict[str, str], 别名到 Job 名称的映射字典。

    方法:
    - register(name, alias=None, replace=False): 装饰器方法，注册 Job 类。
    - lookup(name): 根据名称或别名查找 Job 类。
    - create(name, *args, **kwargs): 根据名称创建 Job 实例。
    - list(): 返回所有已注册的 Job 名称列表。

    例子:
    ```python
        from xfintech.data.job.house import House

        # 创建 House 实例
        house = House()

        # 使用装饰器注册 Job
        @house.register("stock_daily", alias="daily")
        class StockDailyJob:
            def __init__(self, symbol):
                self.symbol = symbol

            def run(self):
                return f"Running daily job for {self.symbol}"

        # 查找 Job 类
        JobClass = house.lookup("stock_daily")
        print(JobClass)  # <class 'StockDailyJob'>

        # 通过别名查找
        JobClass = house.lookup("daily")
        print(JobClass)  # <class 'StockDailyJob'>

        # 创建 Job 实例
        job = house.create("stock_daily", symbol="AAPL")
        print(job.run())  # Running daily job for AAPL

        # 通过别名创建
        job = house.create("daily", symbol="TSLA")
        print(job.run())  # Running daily job for TSLA

        # 列出所有注册的 Job
        jobs = house.list()
        print(jobs)  # ['stock_daily']

        # 名称不区分大小写
        JobClass = house.lookup("STOCK_DAILY")
        JobClass = house.lookup("Stock_Daily")

        # 替换已注册的 Job
        @house.register("stock_daily", replace=True)
        class NewStockDailyJob:
            pass

        # 错误处理示例
        from xfintech.data.job.errors import JobNotFoundError
        try:
            house.lookup("nonexistent")
        except JobNotFoundError as e:
            print(f"Error: {e}")  # Error: job not found: nonexistent
    ```
    """

    def __init__(self) -> None:
        self._jobs: dict[str, type] = {}
        self._aliases: dict[str, str] = {}

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        if not isinstance(name, str):
            raise JobNameError(f"job name must be str, got {type(name)}")
        key = name.strip().lower()
        if not key:
            raise JobNameError("job name cannot be empty")
        return key

    def register(
        self,
        name: str,
        alias: str | None = None,
        replace: bool = False,
        strict: bool = False,
    ):
        namekey = self._normalize_name(name)

        def deco(cls):
            name_in_use = namekey in self._jobs
            if (not replace) and (name_in_use):
                if strict:
                    msg = f"Job already registered: {namekey}"
                    raise JobAlreadyRegisteredError(msg)
            else:
                self._jobs[namekey] = cls

            if alias is not None:
                aliaskey = self._normalize_name(alias)
                aliaskey_in_use = aliaskey in self._aliases
                if (not replace) and (aliaskey_in_use) and (self._aliases[aliaskey] != namekey):
                    msg = f"Alias already used: {aliaskey}"
                    raise JobAlreadyRegisteredError(msg)
                self._aliases[aliaskey] = namekey

            cls.__job_name__ = namekey
            return cls

        return deco

    def lookup(
        self,
        name: str,
    ) -> type:
        key = self._normalize_name(name)
        if key in self._jobs:
            return self._jobs[key]
        if key in self._aliases:
            return self._jobs[self._aliases[key]]
        raise JobNotFoundError(f"job not found: {name}")

    def create(
        self,
        name: str,
        *args,
        **kwargs,
    ) -> Any:
        return self.lookup(name)(*args, **kwargs)

    def list(self) -> list[str]:
        keys = self._jobs.keys()
        aliases = self._aliases.keys()
        items = list(keys) + list(aliases)
        return sorted(set(items))

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class JobLike(Protocol):
    """
    描述:
    - 作业协议接口，定义作业类必须实现的核心方法。
    - 使用 Protocol 实现结构化类型检查（structural typing）。
    - 任何实现这些方法的类都会被视为符合 JobLike 协议。

    方法:
    - run(): 执行作业并返回结果。
    - _run(): 内部执行逻辑，由子类实现。
    - describe(): 返回作业描述信息字典。
    - to_dict(): 返回作业完整信息字典。

    例子:
    ```python
        from xfintech.data.job.joblike import JobLike

        # 任何实现这些方法的类都符合 JobLike 协议
        class MyJob:
            def run(self) -> Any:
                return self._run()

            def _run(self) -> Any:
                return {"result": "success"}

            def describe(self) -> Dict[str, Any]:
                return {"name": "MyJob"}

            def to_dict(self) -> Dict[str, Any]:
                return {"name": "MyJob", "status": "active"}

        # 类型检查会通过
        job: JobLike = MyJob()
        result = job.run()
    ```
    """

    def run(self) -> Any: ...
    def _run(self) -> Any: ...
    def describe(self) -> Dict[str, Any]: ...
    def to_dict(self) -> Dict[str, Any]: ...

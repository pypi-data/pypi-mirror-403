from __future__ import annotations


class JobNotFoundError(KeyError):
    """
    描述:
    - Job 未找到异常，当尝试查找不存在的 Job 名称或别名时抛出。
    - 继承自 KeyError，表示键查找失败。

    参数:
    - message: str, 错误信息，通常包含未找到的 Job 名称。

    方法:
    - 继承自 KeyError 的所有方法。

    例子:
    ```python
        from xfintech.data.job.house import House
        from xfintech.data.job.errors import JobNotFoundError

        house = House()

        try:
            house.lookup("nonexistent_job")
        except JobNotFoundError as e:
            print(f"Error: {e}")  # Error: job not found: nonexistent_job
    ```
    """

    pass


class JobAlreadyRegisteredError(KeyError):
    """
    描述:
    - Job 已注册异常，当尝试注册已存在的 Job 名称或别名时抛出（replace=False）。
    - 继承自 KeyError，表示键冲突。

    参数:
    - message: str, 错误信息，通常包含冲突的 Job 名称或别名。

    方法:
    - 继承自 KeyError 的所有方法。

    例子:
    ```python
        from xfintech.data.job.house import House
        from xfintech.data.job.errors import JobAlreadyRegisteredError

        house = House()

        @house.register("my_job")
        class MyJob:
            pass

        # 尝试重复注册会抛出异常
        try:
            @house.register("my_job")
            class AnotherJob:
                pass
        except JobAlreadyRegisteredError as e:
            print(f"Error: {e}")  # Error: Job already registered: my_job

        # 使用 replace=True 可以覆盖
        @house.register("my_job", replace=True)
        class ReplacedJob:
            pass
    ```
    """

    pass


class JobNameError(ValueError):
    """
    描述:
    - Job 名称错误异常，当提供的 Job 名称格式不正确时抛出。
    - 继承自 ValueError，表示值不合法。
    - 名称必须是非空字符串。

    参数:
    - message: str, 错误信息，描述名称错误的原因。

    方法:
    - 继承自 ValueError 的所有方法。

    例子:
    ```python
        from xfintech.data.job.house import House
        from xfintech.data.job.errors import JobNameError

        house = House()

        # 空字符串名称会抛出异常
        try:
            @house.register("")
            class MyJob:
                pass
        except JobNameError as e:
            print(f"Error: {e}")  # Error: job name cannot be empty

        # 非字符串类型会抛出异常
        try:
            @house.register(123)
            class MyJob:
                pass
        except JobNameError as e:
            print(f"Error: {e}")  # Error: job name must be str, got <class 'int'>
    ```
    """

    pass

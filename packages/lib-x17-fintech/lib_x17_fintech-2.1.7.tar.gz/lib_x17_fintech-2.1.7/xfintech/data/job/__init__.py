from xfintech.data.job.errors import (
    JobAlreadyRegisteredError,
    JobNameError,
    JobNotFoundError,
)
from xfintech.data.job.house import House
from xfintech.data.job.joblike import JobLike

JobHouse = House()  # 创建一个全局的 JobHouse 实例

__all__ = [
    "JobNotFoundError",
    "JobAlreadyRegisteredError",
    "JobNameError",
    "JobHouse",
    "JobLike",
]

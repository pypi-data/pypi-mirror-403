from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job import JobHouse
from xfintech.data.source.tushare.job import TushareJob
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.stockpledge.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class StockPledge(TushareJob):
    """
    描述:
    - 获取A股上市公司股权质押统计数据
    - API文档: https://tushare.pro/document/2?doc_id=110
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 1000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'stockpledge'。
    - key: str, 作业键 '/tushare/stockpledge'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 可选, 股票代码
        - end_date: str, 可选, 截止日期（YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=1000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回股权质押统计数据DataFrame。
    - _run(): 内部执行逻辑，处理参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.stockpledge import StockPledge

    session = Session(credential="your_token")
    pledge = StockPledge(
        session=session,
        params={"ts_code": "000014.SZ"},
    )
    df = pledge.run()
    ```
    """

    def __init__(
        self,
        session: Session,
        params: Optional[Params | Dict[str, Any]] = None,
        coolant: Optional[Coolant | Dict[str, Any]] = None,
        retry: Optional[Retry | Dict[str, Any]] = None,
        cache: Optional[Cache | Dict[str, str] | bool] = None,
    ) -> None:
        super().__init__(
            name=NAME,
            key=KEY,
            session=session,
            source=SOURCE,
            target=TARGET,
            params=params,
            coolant=coolant,
            paginate=PAGINATE,
            retry=retry,
            cache=cache,
        )

    def _run(self) -> pd.DataFrame:
        cached = self._load_cache()
        if cached is not None:
            return cached

        # Prepare payload dict
        payload = self.params.to_dict()
        payload = self._parse_date_params(
            payload,
            keys=["end_date"],
        )
        payload = self._parse_string_params(
            payload,
            keys=["ts_code"],
        )
        all_fields = self.source.list_column_names()
        payload["fields"] = ",".join(all_fields)

        # Fetch and transform data
        data = self._fetchall(
            api=self.connection.pledge_stat,
            **payload,
        )
        result = self.transform(data)
        self._save_cache(result)
        return result

    # Transform logic
    def transform(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = self.target.list_column_names()
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        transformed = {}
        transformed["code"] = data["ts_code"].astype(str)
        transformed["datecode"] = data["end_date"].astype(str)
        transformed["date"] = pd.to_datetime(
            data["end_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        transformed["pledge_count"] = pd.to_numeric(
            data["pledge_count"],
            errors="coerce",
        ).astype("Int64")
        numeric_fields = [
            "unrest_pledge",
            "rest_pledge",
            "total_share",
            "pledge_ratio",
        ]
        for col in numeric_fields:
            if col in data.columns:
                transformed[col] = pd.to_numeric(
                    data[col],
                    errors="coerce",
                )

        for col in cols:
            if col not in transformed:
                transformed[col] = pd.NA

        # Select target columns, drop duplicates, and sort
        out = pd.DataFrame(transformed)
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code", "date"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

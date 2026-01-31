from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job import JobHouse
from xfintech.data.source.baostock.job import BaostockJob
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.stock.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class Stock(BaostockJob):
    """
    描述:
    - 获取上市股票基本信息
    - 返回所有沪深A股上市公司的基础信息
    - 包括股票代码、股票名称、交易状态等信息
    - API文档: http://www.baostock.com/mainContent?file=StockBasicInfoAPI.md
    - SCALE: CrossSection
    - TYPE: Partitioned
    - PAGINATE: 10000 rows / 100 pages

    属性:
    - name: str, 作业名称 'stock'。
    - key: str, 作业键 '/baostock/stock'。
    - session: Session, Baostock会话对象。
    - source: TableInfo, 源表信息（BaoStock原始格式）。
    - target: TableInfo, 目标表信息（xfintech格式）。
    - params: Params, 查询参数。
        - day: str, 可选, 指定交易日（YYYY-MM-DD 或 YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=10000, pagelimit=100）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回股票基本信息DataFrame。
    - _run(): 内部执行逻辑，处理日期参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - list_codes(): 返回所有股票代码列表。
    - list_names(): 返回所有股票名称列表。

    例子:
    ```python
        from xfintech.data.source.baostock.session import Session
        from xfintech.data.source.baostock.stock.stock import Stock

        session = Session()
        job = Stock(
            session=session,
            params={"day": "20260110"}
        )
        df = job.run()
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
            keys=["day"],
        )

        # Fetch data from API
        data = self._fetchall(
            api=self.connection.query_all_stock,
            **payload,
        )
        result = self.transform(data)
        self._save_cache(result)
        return result

    def transform(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = self.target.list_column_names()
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        out = data.copy()
        out["code"] = out["code"].astype(str)
        out["trade_status"] = out["tradeStatus"].astype(str)
        out["name"] = out["code_name"].astype(str)

        # Finalize output
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

    def list_codes(self) -> List[str]:
        df = self.run()
        return sorted(df["code"].unique().tolist())

    def list_names(self) -> List[str]:
        df = self.run()
        return sorted(df["name"].unique().tolist())

    def list_tradeable_codes(
        self,
        type: Optional[Literal["0", "1"]] = None,
    ) -> List[str]:
        df = self.run()
        if type is None:
            return sorted(df["code"].unique().tolist())
        else:
            type = str(type)
            tradeable_df = df[df["trade_status"] == type]
            return sorted(tradeable_df["code"].unique().tolist())

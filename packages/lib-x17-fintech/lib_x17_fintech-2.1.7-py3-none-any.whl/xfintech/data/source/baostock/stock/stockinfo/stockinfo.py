from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job import JobHouse
from xfintech.data.source.baostock.job import BaostockJob
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.stockinfo.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class StockInfo(BaostockJob):
    """
    描述:
    - 获取证券基本资料
    - 包括证券代码、证券名称、上市日期、退市日期、证券类型、上市状态等信息
    - 支持按代码或名称查询（模糊查询）
    - API文档: http://www.baostock.com/mainContent?file=stockBasic.md
    - SCALE: CrossSection
    - TYPE: Static
    - PAGINATE: 10000 rows / 100 pages

    属性:
    - name: str, 作业名称 'stockinfo'。
    - key: str, 作业键 '/baostock/stockinfo'。
    - session: Session, Baostock会话对象。
    - source: TableInfo, 源表信息（BaoStock原始格式）。
    - target: TableInfo, 目标表信息（xfintech格式）。
    - params: Params, 查询参数。
        - code: str, 可选, 股票代码（如 "sh.600000"）
        - code_name: str, 可选, 股票名称（支持模糊查询）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=10000, pagelimit=100）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回证券基本资料DataFrame。
    - _run(): 内部执行逻辑，处理参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - list_codes(): 返回所有证券代码列表。
    - list_names(): 返回所有证券名称列表。

    例子:
    ```python
        from xfintech.data.source.baostock.session import Session
        from xfintech.data.source.baostock.stock.stockinfo import StockInfo

        session = Session()

        # 获取指定股票的基本资料
        job = StockInfo(
            session=session,
            params={"code": "sh.600000"}
        )
        df = job.run()

        # 按名称模糊查询
        job = StockInfo(
            session=session,
            params={"code_name": "浦发"}
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
        payload = self._parse_string_params(
            payload,
            keys=["code", "code_name"],
        )

        # Fetch data from API
        data = self._fetchall(
            api=self.connection.query_stock_basic,
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
        out["name"] = out["code_name"].astype(str)
        out["ipo_date"] = out["ipoDate"].astype(str)
        out["delist_date"] = out["outDate"].astype(str)

        # Convert type and status to integers
        out["security_type"] = (
            pd.to_numeric(
                out["type"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )  # 1 股票 2 基金 3 债券 4 权证 5 期权 6 指数 7 理财产品 8 其他
        out["list_status"] = (
            pd.to_numeric(
                out["status"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

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
        type: int | str = None,
    ) -> List[str]:
        df = self.run()
        active_df = df[df["list_status"] == 1]
        if type is not None:
            active_df = active_df[active_df["security_type"] == int(type)]
        return sorted(active_df["code"].unique().tolist())

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job import JobHouse
from xfintech.data.source.tushare.job import TushareJob
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.stockipo.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class StockIpo(TushareJob):
    """
    描述:
    - 获取新股发行上市信息的作业类。
    - 支持按日期范围、交易日期或年份查询IPO数据。
    - 用户需要至少120积分才可以调取 <br>
    - 单次最大2000条, 总量不限制 <br>
    - API文档: https://tushare.pro/document/2?doc_id=123
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 2000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'ipo'。
    - key: str, 作业键 '/tushare/ipo'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数（start_date, end_date, trade_date, year等）。
        - start_date: str, 可选, 开始日期（YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYYMMDD）
        - trade_date: str, 可选, 交易日期（YYYYMMDD）
        - year: str, 可选, 年份（YYYY）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=2000, pagelimit=5）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回IPO信息DataFrame。
    - _run(): 内部执行逻辑，处理日期参数转换。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - list_codes(): 返回所有IPO股票代码列表（排序）。
    - list_names(): 返回所有IPO股票名称列表（排序）。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.stockipo import StockIpo

        # 创建会话
        session = Session(credential="your_token")

        # 查询2023年的IPO信息
        job = StockIpo(session=session, params={"year": "2023"}, cache=True)
        df = job.run()
        print(f"2023年共 {len(df)} 只新股上市")

        # 查询特定日期范围
        job = StockIpo(
            session=session,
            params={"start_date": "20230101", "end_date": "20230630"}
        )
        df = job.run()

        # 查询特定交易日
        job = StockIpo(session=session, params={"trade_date": "20230315"})
        df = job.run()

        # 获取IPO股票代码列表
        codes = job.list_codes()
        print(f"IPO代码: {codes[:5]}")

        # 获取IPO股票名称列表
        names = job.list_names()
        print(f"IPO名称: {names[:5]}")
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
            keys=[
                "trade_date",
                "start_date",
                "end_date",
            ],
        )
        payload = self._parse_year_params(
            payload,
            key="year",
        )
        all_fields = SOURCE.list_column_names()
        payload["fields"] = ",".join(all_fields)

        # Fetch data from Tushare API
        df = self._fetchall(
            api=self.connection.new_share,
            **payload,
        )
        result = self.transform(df)
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

        out = data.copy()
        out["code"] = out["ts_code"].astype(str)
        out["sub_code"] = out["sub_code"].astype(str)
        out["name"] = out["name"].astype(str)

        # IPO date conversions
        out["ipo_datecode"] = (
            pd.to_datetime(
                out["ipo_date"],
                format="%Y%m%d",
                errors="coerce",
            )
            .dt.strftime("%Y%m%d")
            .astype(str)
        )
        out["ipo_date"] = pd.to_datetime(
            out["ipo_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        # Issue date conversions
        out["issue_datecode"] = (
            pd.to_datetime(
                out["issue_date"],
                format="%Y%m%d",
                errors="coerce",
            )
            .dt.strftime("%Y%m%d")
            .astype(str)
        )
        out["issue_date"] = pd.to_datetime(
            out["issue_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        # Numeric conversions
        out["amount"] = pd.to_numeric(
            out["amount"],
            errors="coerce",
        )
        out["market_amount"] = pd.to_numeric(
            out["market_amount"],
            errors="coerce",
        )
        out["price"] = pd.to_numeric(
            out["price"],
            errors="coerce",
        )
        out["pe"] = pd.to_numeric(
            out["pe"],
            errors="coerce",
        )
        out["limit_amount"] = pd.to_numeric(
            out["limit_amount"],
            errors="coerce",
        )
        out["funds"] = pd.to_numeric(
            out["funds"],
            errors="coerce",
        )
        out["ballot"] = pd.to_numeric(
            out["ballot"],
            errors="coerce",
        )

        # Select target columns, drop duplicates, and sort
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

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job import JobHouse
from xfintech.data.source.baostock.job import BaostockJob
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.tradedate.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class TradeDate(BaostockJob):
    """
    描述:
    - 获取交易日历数据
    - 包括交易所的交易日期和非交易日期信息
    - 支持年份查询和日期范围查询
    - API文档: http://www.baostock.com/mainContent?file=StockBasicInfoAPI.md
    - SCALE: CrossSection
    - TYPE: Static
    - PAGINATE: 10000 rows / 100 pages

    属性:
    - name: str, 作业名称 'tradedate'。
    - key: str, 作业键 '/baostock/tradedate'。
    - session: Session, Baostock会话对象。
    - source: TableInfo, 源表信息（BaoStock原始格式）。
    - target: TableInfo, 目标表信息（xfintech格式）。
    - params: Params, 查询参数。
        - start_date: str, 可选, 开始日期（YYYY-MM-DD 或 YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYY-MM-DD 或 YYYYMMDD）
        - year: str | int, 可选, 年份（YYYY）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=10000, pagelimit=100）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回交易日历DataFrame。
    - _run(): 内部执行逻辑，处理日期参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - list_dates(): 返回所有日期列表。
    - list_datecodes(): 返回所有日期代码列表。
    - list_open_dates(): 返回交易日列表。
    - list_open_datecodes(): 返回交易日代码列表。
    - check(session, value): 检查指定日期是否为交易日。

    例子:
    ```python
        from xfintech.data.source.baostock.session import Session
        from xfintech.data.source.baostock.stock.tradedate import TradeDate

        session = Session()

        # 获取2026年交易日历
        job = TradeDate(session=session, params={"year": "2026"})
        df = job.run()

        # 获取指定日期范围
        job = TradeDate(
            session=session,
            params={
                "start_date": "20260101",
                "end_date": "20260131"
            }
        )
        df = job.run()

        # 检查是否为交易日
        is_trading = TradeDate.check(session, "2026-01-10")
    ```
    """

    @classmethod
    def check(
        cls,
        session: Session,
        value: Optional[datetime | date | str] = None,
    ) -> bool:
        if isinstance(value, datetime):
            value = value.date()
        elif isinstance(value, date):
            pass
        elif isinstance(value, str):
            if "-" in value:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            else:
                value = datetime.strptime(value, "%Y%m%d").date()
        else:
            value = datetime.now().date()

        datecode = value.strftime("%Y-%m-%d")
        job = cls(
            session=session,
            params={
                "start_date": datecode,
                "end_date": datecode,
            },
        )
        result = job.run()
        return not result.empty

    def __init__(
        self,
        session: Session,
        params: Optional[Params | Dict[str, Any]] = None,
        coolant: Optional[Coolant | Dict[str, Any]] = None,
        retry: Optional[Retry | Dict[str, Any]] = None,
        cache: Optional[Cache | Dict[str, Any] | bool] = None,
    ) -> None:
        super().__init__(
            session=session,
            name=NAME,
            key=KEY,
            source=SOURCE,
            target=TARGET,
            params=params,
            paginate=PAGINATE,
            coolant=coolant,
            retry=retry,
            cache=cache,
        )

    def _run(self) -> pd.DataFrame:
        cached = self._load_cache()
        if cached is not None:
            return cached

        payload = self.params.to_dict()
        payload = self._parse_date_params(
            payload,
            keys=["start_date", "end_date"],
        )
        payload = self._parse_year_params(
            payload,
            key="year",
        )
        data = self._fetchall(
            api=self.connection.query_trade_dates,
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

        out = data.copy()
        out["dt"] = pd.to_datetime(
            out["calendar_date"],
            format="%Y-%m-%d",
            errors="coerce",
        )
        out["date"] = out["dt"].dt.strftime("%Y-%m-%d")
        out["datecode"] = out["dt"].dt.strftime("%Y%m%d")
        out["exchange"] = "ALL"
        out["previous"] = out["dt"].shift(1).dt.strftime("%Y-%m-%d")
        out["is_open"] = out["is_trading_day"].astype(int).eq(1)
        out["year"] = out["dt"].dt.year.fillna(0).astype(int)
        out["month"] = out["dt"].dt.month.fillna(0).astype(int)
        out["day"] = out["dt"].dt.day.fillna(0).astype(int)
        out["week"] = out["dt"].dt.isocalendar().week.fillna(0).astype(int)
        out["weekday"] = out["dt"].dt.day_name().fillna("").str[:3]
        out["quarter"] = out["dt"].dt.quarter.fillna(0).astype(int)

        # Clean up temporary columns
        out.drop(columns=["dt"], inplace=True)
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["datecode"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

    def list_dates(self) -> list[str]:
        df = self.run()
        return sorted(df["date"].unique().tolist())

    def list_datecodes(self) -> list[str]:
        df = self.run()
        return sorted(df["datecode"].unique().tolist())

    def list_open_dates(self) -> list[str]:
        df = self.run()
        return sorted(df.loc[df["is_open"], "date"].unique().tolist())

    def list_open_datecodes(self) -> list[str]:
        df = self.run()
        return sorted(df.loc[df["is_open"], "datecode"].unique().tolist())

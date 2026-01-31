from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job import JobHouse
from xfintech.data.source.tushare.job import TushareJob
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.tradedate.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class TradeDate(TushareJob):
    """
    描述:
    - 交易日历数据，包括交易所的交易日期和非交易日期
    - API文档: https://tushare.pro/document/2?doc_id=26

    属性:
    - name: 模块名称 = "tradedate"
    - key: 模块键 = "/tushare/tradedate"
    - source: 源数据表结构
    - target: 目标数据表结构
    - paginate: 分页设置 (pagesize=1000, pagelimit=10)

    参数:
    - session: Session, 必需, Tushare会话对象
    - params: Params | dict, 可选, 查询参数
        - exchange: str, 可选, 交易所代码 (SSE/SZSE/CFFEX/SHFE/CZCE/DCE/INE)
        - year: str | int, 可选, 年份 (YYYY)
        - start_date: str, 可选, 开始日期 (YYYYMMDD)
        - end_date: str, 可选, 结束日期 (YYYYMMDD)
        - is_open: str | int, 可选, 是否交易日 (0=休市, 1=交易)
    - coolant: Coolant | dict, 可选, 请求冷却配置
    - retry: Retry | dict, 可选, 重试配置
    - cache: Cache | dict | bool, 可选, 缓存配置

    方法:
    - run() -> pd.DataFrame: 运行作业并返回数据
    - transform(data: pd.DataFrame) -> pd.DataFrame: 转换数据格式
    - list_dates() -> list[str]: 返回所有日期列表
    - list_datecodes() -> list[str]: 返回所有日期代码列表
    - list_open_dates() -> list[str]: 返回交易日列表
    - list_open_datecodes() -> list[str]: 返回交易日代码列表
    - check(session, value) -> bool: 检查指定日期是否为交易日

    例子:
        ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.tradedate import TradeDate

        session = Session(credential="your_token")

        # 获取2023年交易日历
        job = TradeDate(session=session, params={"year": "2023"})
        df = job.run()

        # 获取指定日期范围
        job = TradeDate(
            session=session,
            params={
                "start_date": "20230101",
                "end_date": "20231231",
                "exchange": "SSE"
            }
        )
        df = job.run()

        # 获取交易日列表
        dates = job.list_open_dates()

        # 检查是否为交易日
        is_trading = TradeDate.check(session, "2023-01-03")
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

        datecode = value.strftime("%Y%m%d")
        job = cls(
            session=session,
            params={
                "start_date": datecode,
                "end_date": datecode,
                "is_open": "1",
            },
        )
        result = job.run()
        return not result.empty and datecode in result["datecode"].values

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
        fields = SOURCE.list_column_names()
        payload["fields"] = ",".join(fields)

        # Fetch data based on is_open parameter
        if "is_open" in payload:
            df = self._fetchall(
                api=self.connection.trade_cal,
                **payload,
            )
        else:
            # Fetch both trading and non-trading days
            df_open = self._fetchall(
                api=self.connection.trade_cal,
                is_open="1",
                **payload,
            )
            df_close = self._fetchall(
                api=self.connection.trade_cal,
                is_open="0",
                **payload,
            )
            df = pd.concat([df_open, df_close], ignore_index=True)

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
        out["dt"] = pd.to_datetime(
            out["cal_date"],
            format="%Y%m%d",
            errors="coerce",
        )
        out["date"] = out["dt"].dt.strftime("%Y-%m-%d")
        out["datecode"] = out["cal_date"].astype(str)
        out["is_open"] = out["is_open"].astype(int).eq(1)
        out["previous"] = pd.to_datetime(
            out["pretrade_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["exchange"] = "ALL"
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

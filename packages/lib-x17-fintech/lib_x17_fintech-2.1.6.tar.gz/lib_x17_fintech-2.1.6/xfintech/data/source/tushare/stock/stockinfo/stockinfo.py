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
from xfintech.data.source.tushare.stock.stockinfo.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class StockInfo(TushareJob):
    """
    描述:
    - 获取上市股票基本信息（包含财务数据）
    - 数据从历史某个时点开始
    - 单次最大7000条，可以根据交易日期参数循环获取历史数据
    - API文档: https://tushare.pro/document/2?doc_id=262
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 7000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'stockinfo'。
    - key: str, 作业键 '/tushare/stockinfo'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数
        - ts_code: str, 可选, TS股票代码
        - trade_date: str, 可选, 交易日期(YYYYMMDD)
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=7000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回股票基本信息DataFrame。
    - _run(): 内部执行逻辑，处理交易日期查询。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - list_codes(): 返回所有股票代码列表。
    - list_names(): 返回所有股票名称列表（排序）。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.stockinfo import StockInfo

        # 创建会话
        session = Session(credential="your_token")

        # 查询特定交易日的股票信息
        job = StockInfo(session=session, params={"trade_date": "20230101"}, cache=True)
        df = job.run()
        print(f"共 {len(df)} 支股票")

        # 查询特定股票的信息
        job = StockInfo(session=session, params={"ts_code": "000001.SZ"})
        df = job.run()

        # 获取股票代码列表
        codes = job.list_codes()
        print(f"股票代码: {codes[:5]}")

        # 获取股票名称列表
        names = job.list_names()
        print(f"股票名称: {names[:5]}")
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
            keys=["trade_date"],
        )
        all_fields = self.source.list_column_names()
        payload["fields"] = ",".join(all_fields)

        # Fetch and transform data
        data = self._fetchall(
            api=self.connection.bak_basic,
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
        out["code"] = out["ts_code"].astype(str)
        out["name"] = out["name"].astype(str)

        # Trade date conversions
        out["date"] = pd.to_datetime(
            out["trade_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["datecode"] = out["trade_date"].astype(str)

        # List date conversions
        out["list_datecode"] = (
            pd.to_datetime(
                out["list_date"],
                format="%Y%m%d",
                errors="coerce",
            )
            .dt.strftime("%Y%m%d")
            .astype(str)
        )
        out["list_date"] = pd.to_datetime(
            out["list_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        # Basic string conversions
        out["industry"] = out["industry"].astype(str)
        out["area"] = out["area"].astype(str)

        # Numeric conversions
        numeric_fields = [
            "pe",
            "float_share",
            "total_share",
            "total_assets",
            "liquid_assets",
            "fixed_assets",
            "reserved",
            "reserved_pershare",
            "eps",
            "bvps",
            "pb",
            "undp",
            "per_undp",
            "rev_yoy",
            "profit_yoy",
            "gpr",
            "npr",
            "holder_num",
        ]
        for field in numeric_fields:
            if field in out.columns:
                out[field] = pd.to_numeric(
                    out[field],
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

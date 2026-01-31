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
from xfintech.data.source.tushare.stock.capflowths.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class CapflowTHS(TushareJob):
    """
    描述:
    - 获取同花顺个股资金流向数据
    - API文档: https://tushare.pro/document/2?doc_id=348
    - 提供5日主力净额数据
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 6000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'thscapflow'。
    - key: str, 作业键 '/tushare/thscapflow'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 可选, 股票代码
        - trade_date: str, 可选, 交易日期（YYYYMMDD）
        - start_date: str, 可选, 开始日期（YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=6000, pagelimit=5）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回资金流向DataFrame。
    - _run(): 内部执行逻辑，处理日期参数。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.capflowths import CapflowTHS

        # 创建会话
        session = Session(credential="your_token")

        # 获取单只股票资金流向数据
        job = CapflowTHS(
            session=session,
            params={
                "ts_code": "000001.SZ",
                "start_date": "20241001",
                "end_date": "20241031"
            }
        )
        df = job.run()
        print(f"共 {len(df)} 条资金流向数据")

        # 获取某个交易日全市场资金流向
        job = CapflowTHS(session=session, params={"trade_date": "20241011"})
        df = job.run()

        # 获取多只股票资金流向
        job = CapflowTHS(
            session=session,
            params={
                "ts_code": "000001.SZ,000002.SZ,600000.SH",
                "start_date": "20241001",
                "end_date": "20241011"
            }
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
            keys=["trade_date", "start_date", "end_date"],
        )
        payload = self._parse_string_params(
            payload,
            keys=["ts_code"],
        )
        # Fetch and transform data
        data = self._fetchall(
            api=self.connection.moneyflow_ths,
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
        out["code"] = out["ts_code"].astype(str)
        out["date"] = pd.to_datetime(
            out["trade_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["datecode"] = out["trade_date"].astype(str)
        out["name"] = out["name"].astype(str)
        out["percent_change"] = pd.to_numeric(out["pct_change"], errors="coerce")

        # Convert numeric fields
        numeric_fields = [
            "latest",
            "net_amount",
            "net_d5_amount",
            "buy_lg_amount",
            "buy_lg_amount_rate",
            "buy_md_amount",
            "buy_md_amount_rate",
            "buy_sm_amount",
            "buy_sm_amount_rate",
        ]
        for field in numeric_fields:
            out[field] = pd.to_numeric(out[field], errors="coerce")

        # Select target columns, drop duplicates, and sort
        out = out[cols].drop_duplicates()
        return out.sort_values(["code", "date"]).reset_index(drop=True)

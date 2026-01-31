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
from xfintech.data.source.tushare.stock.marketindexcapflowdc.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class MarketIndexCapflowDC(TushareJob):
    """
    描述:
    - 获取东方财富大盘资金流向数据
    - 统计上证和深证指数收盘价和涨跌幅
    - 按超大单、大单、中单、小单分类统计主力资金净流入
    - API文档: https://tushare.pro/document/2?doc_id=345
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 3000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'marketindexcapflowdc'。
    - key: str, 作业键 '/tushare/marketindexcapflowdc'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - trade_date: str, 可选, 交易日期（YYYYMMDD）
        - start_date: str, 可选, 开始日期（YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=3000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回大盘资金流向DataFrame。
    - _run(): 内部执行逻辑，处理日期参数。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.marketindexcapflowdc import MarketIndexCapflowDC

        # 创建会话
        session = Session(credential="your_token")

        # 获取单个交易日大盘资金流向
        job = MarketIndexCapflowDC(
            session=session,
            params={"trade_date": "20240927"}
        )
        df = job.run()
        print(f"上证收盘: {df.iloc[0]['close_sh']}")
        print(f"主力净流入: {df.iloc[0]['net_amount']}")

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
        # Fetch and transform data
        data = self._fetchall(
            api=self.connection.moneyflow_mkt_dc,
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
        out["date"] = pd.to_datetime(
            out["trade_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["datecode"] = out["trade_date"].astype(str)

        # Rename pct_change fields to percent_change
        out["percent_change_sh"] = pd.to_numeric(
            out["pct_change_sh"],
            errors="coerce",
        )
        out["percent_change_sz"] = pd.to_numeric(
            out["pct_change_sz"],
            errors="coerce",
        )

        # Convert numeric fields
        numeric_fields = [
            "close_sh",
            "close_sz",
            "net_amount",
            "net_amount_rate",
            "buy_elg_amount",
            "buy_elg_amount_rate",
            "buy_lg_amount",
            "buy_lg_amount_rate",
            "buy_md_amount",
            "buy_md_amount_rate",
            "buy_sm_amount",
            "buy_sm_amount_rate",
        ]
        for field in numeric_fields:
            out[field] = pd.to_numeric(
                out[field],
                errors="coerce",
            )

        # Finalize output
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["date"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

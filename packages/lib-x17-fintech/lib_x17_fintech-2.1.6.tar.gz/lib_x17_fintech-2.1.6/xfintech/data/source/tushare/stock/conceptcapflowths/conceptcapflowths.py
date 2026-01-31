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
from xfintech.data.source.tushare.stock.conceptcapflowths.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class ConceptCapflowTHS(TushareJob):
    """
    描述:
    - 获取同花顺概念板块每日资金流向数据
    - 统计概念板块的资金流入流出情况
    - 包含板块指数、领涨股、公司数量等信息
    - 单次最大提取5000行记录
    - 积分要求：5000积分可以调取
    - API文档: https://tushare.pro/document/2?doc_id=371
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 5000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'conceptcapflowths'。
    - key: str, 作业键 '/tushare/conceptcapflowths'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 可选, 概念代码(支持多个概念，逗号分隔)
        - trade_date: str, 可选, 交易日期（YYYYMMDD）
        - start_date: str, 可选, 开始日期（YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=5000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回概念板块资金流向DataFrame。
    - _run(): 内部执行逻辑，处理日期参数。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.conceptcapflowths import ConceptCapflowTHS

        # 创建会话
        session = Session(credential="your_token")

        # 获取某日全部概念板块资金流向
        job = ConceptCapflowTHS(
            session=session,
            params={"trade_date": "20241201"}
        )
        df = job.run()
        print(f"共 {len(df)} 条概念板块资金流向数据")

        # 获取指定概念板块资金流向
        job = ConceptCapflowTHS(
            session=session,
            params={
                "ts_code": "885748.TI",
                "start_date": "20241101",
                "end_date": "20241231"
            }
        )
        df = job.run()

        # 获取多个概念板块数据
        job = ConceptCapflowTHS(
            session=session,
            params={
                "ts_code": "885748.TI,886008.TI,885426.TI",
                "start_date": "20241101",
                "end_date": "20241201"
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
            api=self.connection.moneyflow_cnt_ths,
            **payload,
        )
        result = self.transform(data)
        self._save_cache(result)
        return result

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
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
        out["lead_stock"] = out["lead_stock"].astype(str)
        out["close"] = pd.to_numeric(
            out["close_price"],
            errors="coerce",
        )
        out["percent_change"] = pd.to_numeric(
            out["pct_change"],
            errors="coerce",
        )

        # Convert numeric fields
        numeric_fields = [
            "industry_index",
            "company_num",
            "pct_change_stock",
            "net_buy_amount",
            "net_sell_amount",
            "net_amount",
        ]
        for field in numeric_fields:
            out[field] = pd.to_numeric(
                out[field],
                errors="coerce",
            )

        # Finalize output
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code", "date"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

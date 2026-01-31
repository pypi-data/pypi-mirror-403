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
from xfintech.data.source.tushare.stock.industrycapflowths.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class IndustryCapflowTHS(TushareJob):
    """
    描述:
    - 获取同花顺行业资金流向数据
    - 统计各行业板块的资金流入流出情况
    - 包含行业指数、领涨股、公司数量等信息
    - 每日盘后更新
    - 单次最大提取5000行记录
    - API文档: https://tushare.pro/document/2?doc_id=343
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 5000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'thsindustrycapflow'。
    - key: str, 作业键 '/tushare/thsindustrycapflow'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 可选, 代码
        - trade_date: str, 可选, 交易日期（YYYYMMDD）
        - start_date: str, 可选, 开始日期（YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=5000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回行业资金流向DataFrame。
    - _run(): 内部执行逻辑，处理日期参数。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.industrycapflowths import IndustryCapflowTHS

        # 创建会话
        session = Session(credential="your_token")

        # 获取当日所有行业资金流向
        job = IndustryCapflowTHS(session=session, params={"trade_date": "20240927"})
        df = job.run()
        print(f"共 {len(df)} 个行业资金流向数据")

        # 获取指定行业代码的资金流向
        job = IndustryCapflowTHS(
            session=session,
            params={
                "ts_code": "881267.TI",
                "start_date": "20240901",
                "end_date": "20240930"
            }
        )
        df = job.run()

        # 获取指定日期区间的所有行业数据
        job = IndustryCapflowTHS(
            session=session,
            params={
                "start_date": "20240920",
                "end_date": "20240927"
            }
        )
        df = job.run()
        print(df[["code", "date", "industry", "net_amount", "percent_change"]])
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
            api=self.connection.moneyflow_ind_ths,
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
        out["percent_change"] = pd.to_numeric(
            out["pct_change"],
            errors="coerce",
        )
        out["percent_change_stock"] = pd.to_numeric(
            out["pct_change_stock"],
            errors="coerce",
        )

        # Convert numeric fields
        numeric_fields = [
            "close",
            "close_price",
            "net_buy_amount",
            "net_sell_amount",
            "net_amount",
        ]
        for field in numeric_fields:
            out[field] = pd.to_numeric(
                out[field],
                errors="coerce",
            )

        # Convert company_num to integer
        out["company_num"] = (
            pd.to_numeric(
                out["company_num"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

        # Finalize output
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code", "date"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

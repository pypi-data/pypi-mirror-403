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
from xfintech.data.source.tushare.stock.stockpledgedetail.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class StockPledgeDetail(TushareJob):
    """
    描述:
    - 获取A股上市公司股权质押明细数据
    - API文档: https://tushare.pro/document/2?doc_id=111
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 1000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'stockpledgedetail'。
    - key: str, 作业键 '/tushare/stockpledgedetail'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 必需, 股票代码
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=1000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回股权质押明细数据DataFrame。
    - _run(): 内部执行逻辑，处理参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    注意:
    - 此数据为个股数据（scale='individual'），ts_code为必需参数
    - 包含股东名称、质押数量、质押时间、解押情况等详细信息
    - 需要至少500积分才可以调取

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.stockpledgedetail import StockPledgeDetail

    session = Session(credential="your_token")
    detail = StockPledgeDetail(
        session=session,
        params={"ts_code": "000014.SZ"},
    )
    df = detail.run()
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
            keys=["ts_code"],
        )
        fields = SOURCE.list_column_names()
        payload["fields"] = ",".join(fields)

        # Call Tushare API via session
        data = self._fetchall(
            api=self.connection.pledge_detail,
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

        # Build transformed dictionary
        transformed = {}
        transformed["code"] = data["ts_code"].astype(str)
        transformed["holder_name"] = data["holder_name"].astype(str)
        transformed["is_release"] = data["is_release"].astype(str)
        transformed["pledgor"] = data["pledgor"].astype(str)
        transformed["is_buyback"] = data["is_buyback"].astype(str)

        # Date field transformations
        date_fields = [
            ("ann_date", "ann_date", "ann_datecode"),
            ("start_date", "start_date", "start_datecode"),
            ("end_date", "end_date", "end_datecode"),
            ("release_date", "release_date", "release_datecode"),
        ]

        for source_field, target_field, datecode_field in date_fields:
            if source_field in data.columns:
                transformed[target_field] = pd.to_datetime(
                    data[source_field],
                    format="%Y%m%d",
                    errors="coerce",
                ).dt.strftime("%Y-%m-%d")
                transformed[datecode_field] = data[source_field]

        # Numeric field transformations
        for field in [
            "pledge_amount",
            "holding_amount",
            "pledged_amount",
            "p_total_ratio",
            "h_total_ratio",
        ]:
            if field in data.columns:
                transformed[field] = pd.to_numeric(
                    data[field],
                    errors="coerce",
                )

        for col in cols:
            if col not in transformed:
                transformed[col] = pd.NA

        out = pd.DataFrame(transformed)
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

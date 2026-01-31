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
from xfintech.data.source.tushare.stock.stockdividend.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class StockDividend(TushareJob):
    """
    描述:
    - 获取A股上市公司分红送股数据
    - API文档: https://tushare.pro/document/2?doc_id=103
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 1000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'stockdividend'。
    - key: str, 作业键 '/tushare/stockdividend'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 可选, TS代码
        - ann_date: str, 可选, 公告日（YYYYMMDD）
        - record_date: str, 可选, 股权登记日期（YYYYMMDD）
        - ex_date: str, 可选, 除权除息日（YYYYMMDD）
        - imp_ann_date: str, 可选, 实施公告日（YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=1000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回分红送股数据DataFrame。
    - _run(): 内部执行逻辑，处理参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.stockdividend import StockDividend

    session = Session(credential="your_token")
    dividend = StockDividend(
        session=session,
        params={"ts_code": "600848.SH"},
    )
    df = dividend.run()
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
                "ann_date",
                "record_date",
                "ex_date",
                "imp_ann_date",
            ],
        )
        payload = self._parse_string_params(
            payload,
            keys=["ts_code"],
        )
        fields = SOURCE.list_column_names()
        payload["fields"] = ",".join(fields)

        # Fetch and transform data
        data = self._fetchall(
            api=self.connection.dividend,
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

        transformed = {}
        transformed["code"] = data["ts_code"].astype(str)
        if "end_date" in data.columns:
            transformed["end_date"] = data["end_date"].astype(str)
        if "div_proc" in data.columns:
            transformed["div_proc"] = data["div_proc"].astype(str)
        date_field_mappings = [
            ("ann_date", "ann_date", "ann_datecode"),
            ("record_date", "record_date", "record_datecode"),
            ("ex_date", "ex_date", "ex_datecode"),
            ("pay_date", "pay_date", "pay_datecode"),
            ("div_listdate", "div_listdate", "div_listdatecode"),
            ("imp_ann_date", "imp_ann_date", "imp_ann_datecode"),
            ("base_date", "base_date", "base_datecode"),
        ]
        for source_col, target_date, target_datecode in date_field_mappings:
            if source_col in data.columns:
                transformed[target_datecode] = data[source_col].astype(str)
                transformed[target_date] = pd.to_datetime(
                    data[source_col],
                    format="%Y%m%d",
                    errors="coerce",
                ).dt.strftime("%Y-%m-%d")

        # Convert numeric fields
        numeric_fields = [
            "stk_div",
            "stk_bo_rate",
            "stk_co_rate",
            "cash_div",
            "cash_div_tax",
            "base_share",
        ]
        for col in numeric_fields:
            if col in data.columns:
                transformed[col] = pd.to_numeric(
                    data[col],
                    errors="coerce",
                )
        for col in cols:
            if col not in transformed:
                transformed[col] = pd.NA

        # Select target columns, drop duplicates, and sort
        out = pd.DataFrame(transformed)
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code", "ann_date"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

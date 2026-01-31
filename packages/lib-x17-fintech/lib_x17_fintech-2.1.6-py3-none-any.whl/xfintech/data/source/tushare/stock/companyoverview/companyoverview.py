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
from xfintech.data.source.tushare.stock.companyoverview.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class CompanyOverview(TushareJob):
    """
    描述:
    - 获取A股上市公司业绩快报数据
    - API文档: https://tushare.pro/document/2?doc_id=46
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 1000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'companyoverview'。
    - key: str, 作业键 '/tushare/companyoverview'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 必需, 股票代码（如'000001.SZ'）
        - ann_date: str, 可选, 公告日期（YYYYMMDD）
        - start_date: str, 可选, 公告开始日期（YYYYMMDD）
        - end_date: str, 可选, 公告结束日期（YYYYMMDD）
        - period: str, 可选, 报告期（如20171231表示年报，20170630半年报）
        - year: str, 可选, 报告年度（YYYY）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=1000, pagelimit=100）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回业绩快报DataFrame。
    - _run(): 内部执行逻辑，处理日期参数。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    注意:
    - 此数据为个股级别（scale='individual'），必须指定ts_code参数
    - 业绩快报包含营业收入、净利润、总资产等关键财务指标
    - API文档: https://tushare.pro/document/2?doc_id=46

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.companyoverview import CompanyOverview

    session = Session(credential="your_token")
    overview = CompanyOverview(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "start_date": "20200101",
            "end_date": "20201231",
        },
    )
    df = overview.run()
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
            keys=["ann_date", "start_date", "end_date"],
        )
        payload = self._parse_string_params(
            payload,
            keys=["ts_code"],
        )
        payload = self._parse_year_params(
            payload,
            key="year",
        )
        payload = self._parse_period_params(
            payload,
            key="period",
        )
        fields = SOURCE.list_column_names()
        payload["fields"] = ",".join(fields)

        # Fetch and transform data
        data = self._fetchall(
            api=self.connection.express_vip,
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
        transformed["datecode"] = data["end_date"].astype(str)
        transformed["date"] = pd.to_datetime(
            data["end_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        # Convert other date fields
        for col in ["ann_date"]:
            transformed[col] = pd.to_datetime(
                data[col],
                format="%Y%m%d",
                errors="coerce",
            ).dt.strftime("%Y-%m-%d")

        # Convert string fields
        for col in [
            "perf_summary",
            "remark",
            "is_audit",
        ]:
            if col in data.columns:
                transformed[col] = data[col].astype(str)

        # Convert numeric fields - all performance express items
        numeric_fields = [
            "revenue",
            "operate_profit",
            "total_profit",
            "n_income",
            "total_assets",
            "total_hldr_eqy_exc_min_int",
            "diluted_eps",
            "diluted_roe",
            "yoy_net_profit",
            "bps",
            "yoy_sales",
            "yoy_op",
            "yoy_tp",
            "yoy_dedu_np",
            "yoy_eps",
            "yoy_roe",
            "growth_assets",
            "yoy_equity",
            "growth_bps",
            "or_last_year",
            "op_last_year",
            "tp_last_year",
            "np_last_year",
            "eps_last_year",
            "open_net_assets",
            "open_bps",
        ]
        for col in numeric_fields:
            if col in data.columns:
                transformed[col] = pd.to_numeric(data[col], errors="coerce")

        # Ensure all target columns exist (add missing ones with NaN)
        for col in cols:
            if col not in transformed:
                transformed[col] = pd.NA

        # Select target columns, drop duplicates, and sort
        out = pd.DataFrame(transformed)
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code", "date"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

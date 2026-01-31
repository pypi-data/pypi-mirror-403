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
from xfintech.data.source.tushare.stock.companybusiness.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class CompanyBusiness(TushareJob):
    """
    描述:
    - 获取A股上市公司主营业务构成数据（个股级别数据，需要指定ts_code）
    - API文档: https://tushare.pro/document/2?doc_id=81
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 9000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'companybusiness'。
    - key: str, 作业键 '/tushare/companybusiness'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 必需, 股票代码（如'000001.SZ'）
        - year: str, 可选, 报告年度（YYYY）
        - start_date: str, 可选, 报告期开始日期（YYYYMMDD）
        - end_date: str, 可选, 报告期结束日期（YYYYMMDD）
        - period: str, 可选, 报告期（YYYYMMDD）
        - type: str, 可选, 类型：P按产品 D按地区 I按行业
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=9000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回主营业务构成DataFrame。
    - _run(): 内部执行逻辑，处理参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.companybusiness import CompanyBusiness

    session = Session(credential="your_token")
    business = CompanyBusiness(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "period": "20201231",
            "type": "P",
        },
    )
    df = business.run()
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
            keys=["start_date", "end_date"],
        )
        payload = self._parse_string_params(
            payload,
            keys=["ts_code", "type"],
        )
        payload = self._parse_year_params(
            payload,
            key="year",
        )
        payload = self._parse_period_params(
            payload,
            key="period",
        )

        # Add fields if not provided
        if "fields" not in payload:
            fields = self.source.list_column_names()
            payload["fields"] = ",".join(fields)

        # Fetch data from API
        data = self._fetchall(
            api=self.connection.fina_mainbz_vip,
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
        out["datecode"] = out["end_date"].astype(str)

        # Convert date fields
        out["date"] = pd.to_datetime(
            out["end_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["end_date"] = pd.to_datetime(
            out["end_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        # Convert string fields
        string_fields = ["bz_item", "curr_type", "update_flag"]
        for field in string_fields:
            if field in out.columns:
                out[field] = out[field].astype(str)

        # Convert numeric fields
        numeric_fields = ["bz_sales", "bz_profit", "bz_cost"]
        for field in numeric_fields:
            if field in out.columns:
                out[field] = pd.to_numeric(
                    out[field],
                    errors="coerce",
                )

        # Ensure all target columns are present
        for col in cols:
            if col not in out.columns:
                out[col] = pd.NA

        # Finalize output
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

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
from xfintech.data.source.tushare.stock.company.constant import (
    EXCHANGES,
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class Company(TushareJob):
    """
    描述:
    - 获取上市公司基本信息的作业类。
    - 支持按交易所（SSE/SZSE/BSE）查询公司信息。
    - 单次提取4500条, 可以根据交易所分批提取
    - API文档: https://tushare.pro/document/2?doc_id=112
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 4500 rows / 1000 pages

    属性:
    - name: str, 作业名称 'company'。
    - key: str, 作业键 '/tushare/stockcompany'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数（ts_code, exchange等）。
        - ts_code: str, 可选, TS股票代码
        - exchange: str, 可选, 交易所 SSE上交所 SZSE深交所 BSE北交所
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=4500, pagelimit=5）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回公司信息DataFrame。
    - _run(): 内部执行逻辑，处理多交易所查询。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - list_codes(): 返回所有股票代码列表。
    - list_names(): 返回所有公司名称列表（排序）。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.company import Company

        session = Session(credential="your_token")
        job = Company(session=session, cache=True)
        df = job.run()

        codes = job.list_codes()
        print(f"股票代码: {codes[:5]}")

        names = job.list_names()
        print(f"公司名称: {names[:5]}")
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
        all_fields = self.source.list_column_names()
        payload["fields"] = ",".join(all_fields)

        # Prepare payloads for each exchange
        payloads = []
        if "exchange" not in payload:
            for exchange in EXCHANGES:
                payloads.append(
                    {
                        **payload,
                        "exchange": exchange,
                    }
                )
        else:
            payloads.append(payload)

        # Fetch data from API
        result = []
        for payload in payloads:
            df = self._fetchall(
                api=self.connection.stock_company,
                **payload,
            )
            result.append(df)

        # Combine results
        df = pd.concat(result, ignore_index=True)
        result = self.transform(df)
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
        out["stockcode"] = out["ts_code"].astype(str)
        out["company_name"] = out["com_name"].astype(str)
        out["company_id"] = out["com_id"].astype(str)
        out["exchange"] = out["exchange"].astype(str)
        out["chairman"] = out["chairman"].astype(str)
        out["manager"] = out["manager"].astype(str)
        out["secretary"] = out["secretary"].astype(str)
        out["reg_capital"] = pd.to_numeric(
            out["reg_capital"],
            errors="coerce",
        )
        out["setup_date"] = pd.to_datetime(
            out["setup_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["province"] = out["province"].astype(str)
        out["city"] = out["city"].astype(str)
        out["introduction"] = out["introduction"].astype(str)
        out["website"] = out["website"].astype(str)
        out["email"] = out["email"].astype(str)
        out["office"] = out["office"].astype(str)
        out["employees"] = pd.to_numeric(
            out["employees"],
            errors="coerce",
        ).astype("Int64")
        out["main_business"] = out["main_business"].astype(str)
        out["business_scope"] = out["business_scope"].astype(str)

        # Finalize output
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["stockcode"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

    def list_codes(self) -> List[str]:
        df = self.run()
        return sorted(df["stockcode"].unique().tolist())

    def list_names(self) -> List[str]:
        df = self.run()
        return sorted(df["company_name"].unique().tolist())

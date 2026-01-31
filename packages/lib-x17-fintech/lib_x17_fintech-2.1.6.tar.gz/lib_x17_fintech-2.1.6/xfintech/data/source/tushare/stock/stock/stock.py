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
from xfintech.data.source.tushare.stock.stock.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    STATUSES,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class Stock(TushareJob):
    """
    描述:
    - 获取上市股票基本信息的作业类。
    - 支持按交易所（SSE/SZSE/BSE）和股票状态（上市/退市/暂停）查询股票信息。
    - 自动处理多个交易所和状态的数据合并。
    - 提供股票代码列表查询功能。
    - API文档: https://tushare.pro/document/2?doc_id=25
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 4000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'stock'。
    - key: str, 作业键 '/tushare/stock'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数（ts_code, list_status等）。
        - ts_code: str, 可选, 股票代码
        - list_status: str, 可选, 股票状态（L=上市 D=退市 P=暂停）
        - exchange: str, 可选, 交易所代码（SSE/SZSE/BSE）
        - name: str, 可选, 股票名称
        - market: str, 可选, 市场类型
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=4000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回股票信息DataFrame。
    - _run(): 内部执行逻辑，处理多交易所查询。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - list_codes(): 返回所有股票代码列表。
    - list_names(): 返回所有股票名称列表（排序）。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.stock import Stock

        # 创建会话
        session = Session(credential="your_token")

        # 查询所有状态的股票信息
        job = Stock(session=session, cache=True)
        df = job.run()
        print(f"共 {len(df)} 支股票")

        # 查询特定状态的股票（L=上市 D=退市 P=暂停）
        job = Stock(session=session, params={"list_status": "L"})
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
        param = self.params.to_dict()
        all_fields = self.source.list_column_names()
        param["fields"] = ",".join(all_fields)
        payloads = []
        if "list_status" in param:
            payloads.append(param)
        else:
            for status in STATUSES:
                payloads.append(
                    {
                        **param,
                        "list_status": status,
                    }
                )

        # Prepare payloads for each exchange
        result = []
        for payload in payloads:
            df = self._fetchall(
                api=self.connection.stock_basic,
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
        out["code"] = out["ts_code"].astype(str)
        out["name"] = out["name"].astype(str)
        out["symbol"] = out["symbol"].astype(str)
        out["area"] = out["area"].astype(str)
        out["industry"] = out["industry"].astype(str)
        out["fullname"] = out["fullname"].astype(str)
        out["enname"] = out["enname"].astype(str)
        out["cnspell"] = out["cnspell"].astype(str)
        out["market"] = out["market"].astype(str)
        out["exchange"] = out["exchange"].astype(str)
        out["currency"] = out["curr_type"].astype(str)
        out["list_status"] = out["list_status"].astype(str)
        out["list_date"] = pd.to_datetime(
            out["list_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["delist_date"] = pd.to_datetime(
            out["delist_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        out["is_hs"] = out["is_hs"].astype(str)
        out["ace_name"] = out["act_name"].astype(str)
        out["ace_type"] = out["act_ent_type"].astype(str)

        # Finalize output
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

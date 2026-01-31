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
from xfintech.data.source.tushare.stock.techindex.constant import (
    _IN_BFQ_COLS,
    _IN_HFQ_COLS,
    _IN_QFQ_COLS,
    _OUT_BA_COLS,
    _OUT_FA_COLS,
    _OUT_MAIN_COLS,
    _OUT_NA_COLS,
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class TechIndex(TushareJob):
    """
    描述:
    - 获取A股股票技术面因子数据
    - 技术面因子包括动量、波动率、成交量、趋势等多个维度
    - 因子数据由Tushare自行生产
    - 5000积分每分钟可以请求30次,
    - API文档: https://tushare.pro/document/2?doc_id=328
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 10000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'techindex'。
    - key: str, 作业键 '/tushare/techindex'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 可选, 股票代码
        - trade_date: str, 可选, 特定交易日期（YYYYMMDD）
        - start_date: str, 可选, 开始日期（YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYYMMDD）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=10000, pagelimit=1000）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回技术面因子DataFrame。
    - _run(): 内部执行逻辑，处理日期参数。
    - transform(data): 转换数据格式，将源格式转为目标格式。
    - na_transform(data): 转换N/A因子数据格式。
    - ba_transform(data): 转换前复权因子数据格式。
    - fa_transform(data): 转换后复权因子数据格式。
    - slice_main(data): 切片主因子数据。
    - slice_na(data): 切片N/A因子数据。
    - slice_ba(data): 切片前复权因子数据。
    - slice_fa(data): 切片后复权因子数据。

    例子:
    ```python
        from xfintech.data.source.tushare.session import Session
        from xfintech.data.source.tushare.stock.techindex import TechIndex

        # 创建会话
        session = Session(credential="your_token")

        # 获取单只股票全部技术面因子
        job = TechIndex(
            session=session,
            params={"ts_code": "000001.SZ"}
        )
        df = job.run()
        print(f"共 {len(df)} 条技术面因子数据")

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

        # Fetch data from API
        data = self._fetchall(
            api=self.connection.stk_factor_pro,
            **payload,
        )
        result = self.transform(data)
        self._save_cache(result)
        return result

    def _transform_main(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = [item.name for item in _OUT_MAIN_COLS]
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        # Create a copy and transform
        transformed = {}
        transformed["code"] = data["ts_code"].astype(str)
        transformed["date"] = pd.to_datetime(
            data["trade_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        transformed["datecode"] = data["trade_date"].astype(str)
        transformed["change"] = pd.to_numeric(data["change"], errors="coerce")
        transformed["percent_change"] = pd.to_numeric(data["pct_chg"], errors="coerce")
        transformed["volume"] = pd.to_numeric(data["vol"], errors="coerce")
        transformed["amount"] = pd.to_numeric(data["amount"], errors="coerce")
        transformed["turnover_rate"] = pd.to_numeric(data["turnover_rate"], errors="coerce")
        transformed["turnover_rate_f"] = pd.to_numeric(data["turnover_rate_f"], errors="coerce")
        transformed["volume_ratio"] = pd.to_numeric(data["volume_ratio"], errors="coerce")
        transformed["pe"] = pd.to_numeric(data["pe"], errors="coerce")
        transformed["pe_ttm"] = pd.to_numeric(data["pe_ttm"], errors="coerce")
        transformed["pb"] = pd.to_numeric(data["pb"], errors="coerce")
        transformed["ps"] = pd.to_numeric(data["ps"], errors="coerce")
        transformed["ps_ttm"] = pd.to_numeric(data["ps_ttm"], errors="coerce")
        transformed["dv_ratio"] = pd.to_numeric(data["dv_ratio"], errors="coerce")
        transformed["dv_ttm"] = pd.to_numeric(data["dv_ttm"], errors="coerce")
        transformed["total_share"] = pd.to_numeric(data["total_share"], errors="coerce")
        transformed["float_share"] = pd.to_numeric(data["float_share"], errors="coerce")
        transformed["free_share"] = pd.to_numeric(data["free_share"], errors="coerce")
        transformed["total_mv"] = pd.to_numeric(data["total_mv"], errors="coerce")
        transformed["circle_mv"] = pd.to_numeric(data["circ_mv"], errors="coerce")
        transformed["adj_factor"] = pd.to_numeric(data["adj_factor"], errors="coerce")
        transformed["downdays"] = pd.to_numeric(data["downdays"], errors="coerce")
        transformed["updays"] = pd.to_numeric(data["updays"], errors="coerce")
        transformed["lowdays"] = pd.to_numeric(data["lowdays"], errors="coerce")
        transformed["topdays"] = pd.to_numeric(data["topdays"], errors="coerce")
        return pd.DataFrame(transformed)

    def _transform_na(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = [item.name for item in _OUT_NA_COLS]
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        # Create a copy and transform
        transformed = {}
        for col in _IN_BFQ_COLS:
            src = col.name
            dst = src.replace("_bfq", "")
            if src in data.columns:
                transformed[dst] = pd.to_numeric(
                    data[src],
                    errors="coerce",
                )
            else:
                transformed[dst] = pd.NA
        return pd.DataFrame(transformed)

    def _transform_ba(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = [item.name for item in _OUT_BA_COLS]
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        # Create a copy and transform
        transformed = {}
        for col in _IN_HFQ_COLS:
            src = col.name
            dst = "ba_" + src.replace("_hfq", "")
            if src in data.columns:
                transformed[dst] = pd.to_numeric(
                    data[src],
                    errors="coerce",
                )
            else:
                transformed[dst] = pd.NA
        return pd.DataFrame(transformed)

    def _transform_fa(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = [item.name for item in _OUT_FA_COLS]
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        # Create a copy and transform
        transformed = {}
        for col in _IN_QFQ_COLS:
            src = col.name
            dst = "fa_" + src.replace("_qfq", "")
            if src in data.columns:
                transformed[dst] = pd.to_numeric(
                    data[src],
                    errors="coerce",
                )
            else:
                transformed[dst] = pd.NA
        return pd.DataFrame(transformed)

    def transform(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = self.target.list_column_names()
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        main_df = self._transform_main(data)
        na_df = self._transform_na(data)
        ba_df = self._transform_ba(data)
        fa_df = self._transform_fa(data)
        result = pd.concat([main_df, na_df, ba_df, fa_df], axis=1)
        return result[cols].reset_index(drop=True)

    def slice_main(
        self,
        data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        if data is not None:
            df = data
        else:
            df = self.run()
        maincols = [item.name for item in _OUT_MAIN_COLS]
        if df.empty:
            return pd.DataFrame(columns=maincols)
        else:
            return df[maincols].copy().reset_index(drop=True)

    def slice_na(
        self,
        data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        if data is not None:
            df = data
        else:
            df = self.run()
        nacols = [item.name for item in _OUT_MAIN_COLS + _OUT_NA_COLS]
        if df.empty:
            return pd.DataFrame(columns=nacols)
        else:
            return df[nacols].copy().reset_index(drop=True)

    def slice_ba(
        self,
        data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        if data is not None:
            df = data
        else:
            df = self.run()
        bacols = [item.name for item in _OUT_MAIN_COLS + _OUT_BA_COLS]
        if df.empty:
            return pd.DataFrame(columns=bacols)
        else:
            return df[bacols].copy().reset_index(drop=True)

    def slice_fa(
        self,
        data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        if data is not None:
            df = data
        else:
            df = self.run()
        facols = [item.name for item in _OUT_MAIN_COLS + _OUT_FA_COLS]
        if df.empty:
            return pd.DataFrame(columns=facols)
        else:
            return df[facols].copy().reset_index(drop=True)

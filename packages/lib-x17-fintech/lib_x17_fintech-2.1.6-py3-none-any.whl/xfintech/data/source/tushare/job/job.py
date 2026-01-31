from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job.job import Job
from xfintech.data.source.tushare.session.session import Session
from xfintech.fabric.table.info import TableInfo


class TushareJob(Job):
    """
    描述:
    - Tushare 数据源作业类，继承自 Job 基类。
    - 专门用于从 Tushare API 获取金融数据。
    - 自动处理连接管理、分页获取、重试和缓存等功能。
    - 支持批量数据获取并自动合并为 DataFrame。

    属性:
    - connection: Any, Tushare API 连接对象，从 session 中获取。
    - 继承 Job 类的所有属性（name, key, params, coolant, paginate, retry, cache, metric）。

    方法:
    - _resolve_connection(session): 从 session 解析并验证连接对象。
    - _fetchall(api, **params): 分页获取所有数据并合并为 DataFrame。

    例子:
    ```python
        from xfintech.data.source.tushare.job import TushareJob
        from xfintech.data.source.tushare.session import Session

        # 创建 session
        session = Session(credential="your_token")

        # 创建作业
        job = TushareJob(
            name="stock_basic",
            key="stock_basic_001",
            session=session,
            params={"exchange": "SSE"},
            paginate={"pagesize": 1000, "pagelimit": 10},
            retry={"retry": 3, "wait": 1},
            cache=True
        )

        # 在子类中实现 _run 方法来调用 _fetchall
        class StockBasicJob(TushareJob):
            def _run(self):
                return self._fetchall(
                    api=self.connection.stock_basic,
                    **self.get_params()
                )
    ```
    """

    def __init__(
        self,
        name: str,
        key: str,
        session: Session,
        source: Optional[TableInfo] = None,
        target: Optional[TableInfo] = None,
        params: Optional[Params | Dict[str, Any]] = None,
        coolant: Optional[Coolant | Dict[str, Any]] = None,
        paginate: Optional[Paginate | Dict[str, Any]] = None,
        retry: Optional[Retry | Dict[str, Any]] = None,
        cache: Optional[Cache | Dict[str, str] | bool] = None,
    ) -> None:
        super().__init__(
            name=name,
            key=key,
            source=source,
            target=target,
            params=params,
            coolant=coolant,
            paginate=paginate,
            retry=retry,
            cache=cache,
        )
        self.connection = self._resolve_connection(
            session,
        )

    def _resolve_connection(
        self,
        session: Session,
    ) -> Any:
        connection = getattr(session, "connection", None)
        if connection is None:
            msg = "No active connection found in session."
            raise ConnectionError(msg)
        self.markpoint("_resolve_connection[OK]")
        return connection

    def _parse_date_params(
        self,
        payload: Dict[str, Any],
        keys: List[str],
    ) -> Dict[str, Any]:
        payload = payload.copy()
        for key in keys:
            if key in payload:
                value = payload.get(key)
                if isinstance(value, datetime):
                    payload[key] = value.strftime("%Y%m%d")
                elif isinstance(value, date):
                    payload[key] = value.strftime("%Y%m%d")
                elif isinstance(value, str):
                    if "-" in value:
                        dt = datetime.strptime(value, "%Y-%m-%d")
                        payload[key] = dt.strftime("%Y%m%d")
                    else:
                        payload[key] = value
        return payload

    def _parse_string_params(
        self,
        payload: Dict[str, Any],
        keys: List[str],
    ) -> Dict[str, Any]:
        payload = payload.copy()
        for key in keys:
            if key in payload:
                value = payload.get(key)
                if isinstance(value, str):
                    payload[key] = value
        return payload

    def _parse_year_params(
        self,
        payload: Dict[str, Any],
        key: List[str],
    ) -> Dict[str, Any]:
        payload = payload.copy()
        if key not in payload:
            return payload
        else:
            year = str(payload.pop(key))
            if year.isdigit() and len(year) == 4:
                payload["start_date"] = f"{year}0101"
                payload["end_date"] = f"{year}1231"
            return payload

    def _parse_period_params(
        self,
        payload: Dict[str, Any],
        key: int | str,  # example "2023-1"
    ) -> Dict[str, Any]:
        payload = payload.copy()
        if key not in payload:
            return payload
        else:
            period = str(payload.pop(key))

            # If already in YYYYMMDD format, just set it
            if len(period) == 8 and period.isdigit():
                payload["period"] = period
                return payload

            # Parse YYYY-Q format
            parts = period.split("-")
            if len(parts) != 2:
                # Invalid format, skip conversion
                return payload

            year = parts[0]
            quarter = parts[1]
            valid_year = len(year) == 4 and year.isdigit()
            valid_quarter = quarter in ["1", "2", "3", "4"]
            if valid_year and valid_quarter:
                if quarter == "1":
                    payload["period"] = f"{year}0331"
                elif quarter == "2":
                    payload["period"] = f"{year}0630"
                elif quarter == "3":
                    payload["period"] = f"{year}0930"
                elif quarter == "4":
                    payload["period"] = f"{year}1231"
            return payload

    def _fetchall(
        self,
        api: Callable,
        **params: Any,
    ) -> pd.DataFrame:
        """
        分页获取所有数据并合并为单个 DataFrame。

        参数:
        - api: Callable, Tushare API 方法，必须接受 limit 和 offset 参数。
        - **params: Any, 传递给 API 方法的其他参数。

        返回:
        - pd.DataFrame: 合并后的完整数据，如果没有数据则返回空 DataFrame。

        说明:
        - 自动处理分页逻辑，直到获取所有数据或达到 pagelimit。
        - 每页之间会执行冷却等待（coolant.cool()）。
        - 使用 metric 记录每页的获取进度。
        """
        # self.paginate.reset()
        batch: List[pd.DataFrame] = []
        for pagenum in range(self.paginate.pagelimit):
            try:
                result = api(
                    limit=self.paginate.pagesize,
                    offset=self.paginate.offset,
                    **params,
                )
            except Exception as e:
                self.markpoint(f"_fetchall[pagenum={pagenum}, ERROR]")
                raise e

            # Check for empty result
            if result is None or len(result) == 0:
                break

            batch.append(result)
            self.markpoint(f"_fetchall[pagenum={pagenum}, OK]")

            # Check if have fetched all data
            if len(result) < self.paginate.pagesize:
                break

            self.paginate.next()
            self.coolant.cool()

        if batch:
            self.markpoint("_fetchall[OK]")
            return pd.concat(batch, ignore_index=True)
        else:
            return pd.DataFrame()

    def _load_cache(
        self,
    ) -> Optional[pd.DataFrame]:
        if self.cache:
            cached = self.cache.get(self.params.identifier)
            if cached is not None:
                self.markpoint("load_cache[OK]")
                return cached
        return None

    def _save_cache(
        self,
        data: pd.DataFrame,
    ) -> None:
        if self.cache:
            self.markpoint("_save_cache[OK]")
            self.cache.set(self.params.identifier, data)

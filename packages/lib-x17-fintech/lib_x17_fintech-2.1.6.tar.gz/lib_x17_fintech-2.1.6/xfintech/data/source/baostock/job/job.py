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
from xfintech.data.source.baostock.session.session import Session
from xfintech.fabric.table.info import TableInfo


class BaostockJob(Job):
    """
    描述:
    - Baostock 数据源作业类，继承自 Job 基类。
    - 专门用于从 Baostock API 获取金融数据。
    - 自动处理连接管理、数据获取、重试和缓存等功能。
    - 支持 Direct 模式（直接连接）和 Relay 模式（中继服务器）。
    - 自动检测 Direct/Relay 模式并处理 ResultSet 或 DataFrame。
    - 支持日期格式自动转换（YYYYMMDD → YYYY-MM-DD）。

    属性:
    - connection: Any, Baostock API 连接对象，从 session 中获取。
    - 继承 Job 类的所有属性（name, key, params, coolant, paginate, retry, cache, metric）。

    方法:
    - _resolve_connection(session): 从 session 解析并验证连接对象。
    - _fetchall(api, **params): 获取所有数据并自动处理 Direct/Relay 模式。
    - _parse_date_params(payload, keys): 解析日期参数，支持多种格式。
    - _parse_string_params(payload, keys): 解析字符串参数。

    例子:
    ```python
        from xfintech.data.source.baostock.job import BaostockJob
        from xfintech.data.source.baostock.session import Session

        # 创建 session
        session = Session()

        # 创建作业
        job = BaostockJob(
            name="minuteline",
            key="/baostock/minuteline",
            session=session,
            params={"code": "sh.600000", "start_date": "20240101"},
            paginate={"pagesize": 100, "pagelimit": 1000},
            retry={"retry": 3, "wait": 1},
            cache=True
        )

        # 在子类中实现 _run 方法来调用 _fetchall
        class MinutelineJob(BaostockJob):
            def _run(self):
                params = self.get_params()
                params = self._parse_date_params(params, ["start_date", "end_date"])
                return self._fetchall(
                    api=self.connection.query_history_k_data_plus,
                    **params
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

    def _parse_date_params(
        self,
        payload: Dict[str, Any],
        keys: List[str],
    ) -> Dict[str, Any]:
        payload = payload.copy()
        for key in keys:
            if key in payload:
                value = payload.get(key)
                if isinstance(value, (date, datetime)):
                    payload[key] = value.strftime("%Y-%m-%d")
                if isinstance(value, date):
                    payload[key] = value.strftime("%Y-%m-%d")
                if isinstance(value, str):
                    if "-" in value:  # YYYY-MM-DD
                        payload[key] = value
                    else:  # YYYYMMDD
                        dt = datetime.strptime(value, "%Y%m%d")
                        payload[key] = dt.strftime("%Y-%m-%d")
        return payload

    def _parse_year_params(
        self,
        payload: Dict[str, Any],
        key: str,
    ) -> Dict[str, Any]:
        payload = payload.copy()
        if key not in payload:
            return payload
        else:
            year = str(payload.pop(key))
            if year.isdigit() and len(year) == 4:
                payload["start_date"] = f"{year}-01-01"
                payload["end_date"] = f"{year}-12-31"
            return payload

    def _fetchall(
        self,
        api: Callable,
        **params: Any,
    ) -> pd.DataFrame:
        """
        描述:
        - 使用迭代器获取所有数据并合并为单个 DataFrame。

        参数:
        - api: Callable, Baostock API 方法（如 connection.query_history_k_data_plus）
        - **params: Any, 传递给 API 方法的参数

        返回:
        - pd.DataFrame: 合并后的完整数据，如果没有数据或出错则返回空 DataFrame。

        说明:
        - Direct 模式：调用 api(**params) 返回 ResultSet，使用 get_data() 获取所有数据
        - Relay 模式：relay 在服务端执行完整的 get_data()，直接返回 DataFrame
        - 自动检测返回类型并处理
        - Baostock 默认每页 10,000 行 (BAOSTOCK_PER_PAGE_COUNT)
        - API 调用数 = ceil(总行数 / 10,000)

        """
        self.paginate.reset()
        result = api(**params)
        self.markpoint("_fetchall[api_called]")

        # Relay mode will return DataFrame directly
        if isinstance(result, pd.DataFrame):
            self.markpoint(f"_fetchall[relay_mode, rows={len(result)}]")
            return result

        # Direct mode will return ResultSet
        else:
            if result.error_code != "0":
                errcode = result.error_code
                errmsg = result.error_msg
                self.markpoint(f"_fetchall[ERROR: code={errcode}, msg={errmsg}]")
                return pd.DataFrame()
            data = result.get_data()
            self.markpoint(f"_fetchall[direct_mode, rows={len(data)}]")
            return data

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

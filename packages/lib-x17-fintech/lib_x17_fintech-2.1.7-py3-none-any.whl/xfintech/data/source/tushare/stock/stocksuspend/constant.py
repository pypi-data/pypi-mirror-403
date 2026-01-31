from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "suspend_d"
URL = "https://tushare.pro/document/2?doc_id=214"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "TS股票代码",
    },
    "start_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "开始日期(YYYYMMDD)",
    },
    "end_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "结束日期(YYYYMMDD)",
    },
    "trade_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "交易日期(YYYYMMDD)",
    },
}

# Exported constants
NAME = "stocksuspend"
KEY = "/tushare/stocksuspend"
PAGINATE = {
    "pagesize": 1000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="股票停复牌信息（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "crosssection",
    },
    name=SOURCE_NAME,
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS股票代码"),
        ColumnInfo(name="trade_date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="suspend_timing", kind=ColumnKind.STRING, desc="日内停牌时间段"),
        ColumnInfo(name="suspend_type", kind=ColumnKind.STRING, desc="停复牌类型"),
    ],
)
TARGET = TableInfo(
    desc="股票停复牌信息（标准格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    name=NAME,
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="交易日期字符串"),
        ColumnInfo(name="suspend_timing", kind=ColumnKind.STRING, desc="日内停牌时间段"),
        ColumnInfo(name="suspend_type", kind=ColumnKind.STRING, desc="停复牌类型"),
    ],
)

from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "stock_st"
URL = "https://tushare.pro/document/2?doc_id=397"
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
    "year": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "年份(YYYY)",
    },
}

# Exported constants
NAME = "stockst"
KEY = "/tushare/stockst"
PAGINATE = {
    "pagesize": 1000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="ST股票列表（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS股票代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="trade_date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="type", kind=ColumnKind.STRING, desc="ST类型"),
        ColumnInfo(name="type_name", kind=ColumnKind.STRING, desc="ST类型名称"),
    ],
)
TARGET = TableInfo(
    desc="ST股票列表（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="交易日期字符串"),
        ColumnInfo(name="type", kind=ColumnKind.STRING, desc="ST类型"),
        ColumnInfo(name="type_name", kind=ColumnKind.STRING, desc="ST类型名称"),
    ],
)

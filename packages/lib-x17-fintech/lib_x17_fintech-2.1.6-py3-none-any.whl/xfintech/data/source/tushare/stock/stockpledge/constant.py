from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "pledge_stat"
URL = "https://tushare.pro/document/2?doc_id=110"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票代码",
    },
    "end_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "截止日期",
    },
}

# Exported constants
NAME = "stockpledge"
KEY = "/tushare/stockpledge"
PAGINATE = {
    "pagesize": 1000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="股权质押统计数据（Tushare格式）",
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
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS代码"),
        ColumnInfo(name="end_date", kind=ColumnKind.STRING, desc="截止日期"),
        ColumnInfo(name="pledge_count", kind=ColumnKind.INTEGER, desc="质押次数"),
        ColumnInfo(name="unrest_pledge", kind=ColumnKind.FLOAT, desc="无限售股质押数量（万）"),
        ColumnInfo(name="rest_pledge", kind=ColumnKind.FLOAT, desc="限售股份质押数量（万）"),
        ColumnInfo(name="total_share", kind=ColumnKind.FLOAT, desc="总股本"),
        ColumnInfo(name="pledge_ratio", kind=ColumnKind.FLOAT, desc="质押比例"),
    ],
)

TARGET = TableInfo(
    desc="股权质押统计数据（标准格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    name=NAME,
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="截止日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="截止日期代码"),
        ColumnInfo(name="pledge_count", kind=ColumnKind.INTEGER, desc="质押次数"),
        ColumnInfo(name="unrest_pledge", kind=ColumnKind.FLOAT, desc="无限售股质押数量（万）"),
        ColumnInfo(name="rest_pledge", kind=ColumnKind.FLOAT, desc="限售股份质押数量（万）"),
        ColumnInfo(name="total_share", kind=ColumnKind.FLOAT, desc="总股本"),
        ColumnInfo(name="pledge_ratio", kind=ColumnKind.FLOAT, desc="质押比例"),
    ],
)

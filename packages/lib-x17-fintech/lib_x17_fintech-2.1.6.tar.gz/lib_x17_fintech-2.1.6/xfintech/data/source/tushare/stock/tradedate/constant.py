from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "trade_cal"
URL = "https://tushare.pro/document/2?doc_id=26"
EXCHANGES = [
    "SSE",
    "SZSE",
    "CFFEX",
    "SHFE",
    "CZCE",
    "DCE",
    "INE",
]
ARGS = {
    "exchange": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": f"交易所: {EXCHANGES}",
    },
    "start_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "开始日期: YYYYMMDD",
    },
    "end_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "结束日期: YYYYMMDD",
    },
    "is_open": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "是否交易: 0=休市, 1=交易",
    },
    "year": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "年份(YYYY)",
    },
}

# Exported constants
NAME = "tradedate"
KEY = "/tushare/tradedate"
PAGINATE = {
    "pagesize": 1000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="交易日历数据，包括交易所的交易日期和非交易日期",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="exchange", kind=ColumnKind.STRING, desc="交易所"),
        ColumnInfo(name="cal_date", kind=ColumnKind.STRING, desc="日历日期"),
        ColumnInfo(name="is_open", kind=ColumnKind.INTEGER, desc="是否交易"),
        ColumnInfo(name="pretrade_date", kind=ColumnKind.STRING, desc="上一个交易日"),
    ],
)
TARGET = TableInfo(
    desc="交易日历数据，包括日期信息和交易状态",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="日期代码:YYYYMMDD"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="日期:YYYY-MM-DD"),
        ColumnInfo(name="exchange", kind=ColumnKind.STRING, desc="交易所"),
        ColumnInfo(name="previous", kind=ColumnKind.STRING, desc="前一个交易日"),
        ColumnInfo(name="is_open", kind=ColumnKind.BOOLEAN, desc="是否交易日"),
        ColumnInfo(name="year", kind=ColumnKind.INTEGER, desc="年份"),
        ColumnInfo(name="month", kind=ColumnKind.INTEGER, desc="月份"),
        ColumnInfo(name="day", kind=ColumnKind.INTEGER, desc="日"),
        ColumnInfo(name="week", kind=ColumnKind.INTEGER, desc="周数"),
        ColumnInfo(name="weekday", kind=ColumnKind.STRING, desc="星期几"),
        ColumnInfo(name="quarter", kind=ColumnKind.INTEGER, desc="季度"),
    ],
)

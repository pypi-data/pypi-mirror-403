from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "baostock"
SOURCE_NAME = "query_trade_dates"
URL = "http://www.baostock.com/mainContent?file=stockKData.md"
ARGS = {
    "start_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "开始日期: YYYY-MM-DD",
    },
    "end_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "结束日期: YYYY-MM-DD",
    },
    "year": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "年份(YYYY)",
    },
}

# Exported constants
NAME = "tradedate"
KEY = "/baostock/tradedate"
PAGINATE = {
    "pagesize": 10000,
    "pagelimit": 100,
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
        ColumnInfo(name="calendar_date", kind=ColumnKind.STRING, desc="交易日期:YYYY-MM-DD"),
        ColumnInfo(name="is_trading_day", kind=ColumnKind.BOOLEAN, desc="是否交易"),
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

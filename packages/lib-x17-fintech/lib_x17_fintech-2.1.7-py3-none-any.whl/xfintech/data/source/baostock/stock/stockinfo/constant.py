from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "baostock"
SOURCE_NAME = "query_stock_basic"
URL = "http://www.baostock.com/mainContent?file=stockBasic.md"
ARGS = {
    "code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "A股股票代码，sh或sz.+6位数字代码",
    },
    "code_name": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票名称，支持模糊查询",
    },
}

# Exported constants
NAME = "stockinfo"
KEY = "/baostock/stockinfo"
PAGINATE = {
    "pagesize": 10000,
    "pagelimit": 100,
}
SOURCE = TableInfo(
    desc="证券基本资料（BaoStock格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="证券代码"),
        ColumnInfo(name="code_name", kind=ColumnKind.STRING, desc="证券名称"),
        ColumnInfo(name="ipoDate", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="outDate", kind=ColumnKind.STRING, desc="退市日期"),
        ColumnInfo(name="type", kind=ColumnKind.STRING, desc="证券类型"),
        ColumnInfo(name="status", kind=ColumnKind.STRING, desc="上市状态"),
    ],
)
TARGET = TableInfo(
    desc="证券基本资料（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="证券代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="证券名称"),
        ColumnInfo(name="ipo_date", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="delist_date", kind=ColumnKind.STRING, desc="退市日期"),
        ColumnInfo(name="security_type", kind=ColumnKind.INTEGER, desc="证券类型(1:股票/2:指数/3:其它/4:可转债/5:ETF)"),
        ColumnInfo(name="list_status", kind=ColumnKind.INTEGER, desc="上市状态(1:上市/0:退市)"),
    ],
)

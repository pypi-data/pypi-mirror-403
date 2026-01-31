from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "baostock"
SOURCE_NAME = "query_all_stock"
URL = "http://www.baostock.com/mainContent?file=StockBasicInfoAPI.md"
ARGS = {
    "day": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "指定交易日(YYYYMMDD)，默认当前交易日",
    },
}

# Exported constants
NAME = "stock"
KEY = "/baostock/stock"
PAGINATE = {
    "pagesize": 10000,
    "pagelimit": 100,
}
SOURCE = TableInfo(
    desc="上市股票基本信息（Baostock格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="TS代码"),
        ColumnInfo(name="tradeStatus", kind=ColumnKind.STRING, desc="交易状态"),
        ColumnInfo(name="code_name", kind=ColumnKind.STRING, desc="股票名称"),
    ],
)
TARGET = TableInfo(
    desc="上市公司基本信息（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="TS代码"),
        ColumnInfo(name="trade_status", kind=ColumnKind.STRING, desc="交易状态"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
    ],
)

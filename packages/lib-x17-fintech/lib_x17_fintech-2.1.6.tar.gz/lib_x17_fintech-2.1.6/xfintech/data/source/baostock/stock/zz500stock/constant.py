"""
Constants for ZZ500Stock module.

This module defines the source and target schemas for the Baostock ZZ500 constituent stocks data.
"""

from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "baostock"
SOURCE_NAME = "query_zz500_stocks"
URL = "http://www.baostock.com/mainContent?file=zz500Stock.md"
ARGS = {}

# Exported constants
NAME = "zz500stock"
KEY = "/baostock/zz500stock"
PAGINATE = {
    "pagesize": 10000,
    "pagelimit": 100,
}
SOURCE = TableInfo(
    desc="中证500成分股（BaoStock格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="updateDate", kind=ColumnKind.STRING, desc="更新日期"),
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="证券代码"),
        ColumnInfo(name="code_name", kind=ColumnKind.STRING, desc="证券名称"),
    ],
)
TARGET = TableInfo(
    desc="中证500成分股（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="update_date", kind=ColumnKind.STRING, desc="更新日期"),
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="证券代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="证券名称"),
    ],
)

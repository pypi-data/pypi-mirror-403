from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "adj_factor"
URL = "https://tushare.pro/document/2?doc_id=28"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票代码",
    },
    "trade_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "特定交易日期(YYYYMMDD)",
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
}

# Exported constants
NAME = "adjfactor"
KEY = "/tushare/adjfactor"
PAGINATE = {
    "pagesize": 2000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="A股复权因子数据（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="trade_date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="adj_factor", kind=ColumnKind.FLOAT, desc="复权因子"),
    ],
)
TARGET = TableInfo(
    desc="A股复权因子数据（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="交易日期代码(YYYYMMDD)"),
        ColumnInfo(name="adj_factor", kind=ColumnKind.FLOAT, desc="复权因子"),
    ],
)

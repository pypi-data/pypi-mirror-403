from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "weekly"
URL = "https://tushare.pro/document/2?doc_id=144"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票代码",
    },
    "trade_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "交易日期(YYYYMMDD)",
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
NAME = "weekline"
KEY = "/tushare/weekline"
PAGINATE = {
    "pagesize": 6000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="A股周线行情数据（Tushare格式）",
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
        ColumnInfo(name="open", kind=ColumnKind.FLOAT, desc="周开盘价"),
        ColumnInfo(name="high", kind=ColumnKind.FLOAT, desc="周最高价"),
        ColumnInfo(name="low", kind=ColumnKind.FLOAT, desc="周最低价"),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT, desc="周收盘价"),
        ColumnInfo(name="pre_close", kind=ColumnKind.FLOAT, desc="上周收盘价"),
        ColumnInfo(name="change", kind=ColumnKind.FLOAT, desc="周涨跌额"),
        ColumnInfo(name="pct_chg", kind=ColumnKind.FLOAT, desc="周涨跌幅"),
        ColumnInfo(name="vol", kind=ColumnKind.FLOAT, desc="周成交量(手)"),
        ColumnInfo(name="amount", kind=ColumnKind.FLOAT, desc="周成交额(千元)"),
    ],
)
TARGET = TableInfo(
    desc="A股周线行情数据（xfintech格式）",
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
        ColumnInfo(name="open", kind=ColumnKind.FLOAT, desc="开盘价(元)"),
        ColumnInfo(name="high", kind=ColumnKind.FLOAT, desc="最高价(元)"),
        ColumnInfo(name="low", kind=ColumnKind.FLOAT, desc="最低价(元)"),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT, desc="收盘价(元)"),
        ColumnInfo(name="pre_close", kind=ColumnKind.FLOAT, desc="昨收价(元)"),
        ColumnInfo(name="change", kind=ColumnKind.FLOAT, desc="涨跌额(元)"),
        ColumnInfo(name="percent_change", kind=ColumnKind.FLOAT, desc="涨跌幅(%)"),
        ColumnInfo(name="volume", kind=ColumnKind.FLOAT, desc="成交量(手)"),
        ColumnInfo(name="amount", kind=ColumnKind.FLOAT, desc="成交额(千元)"),
    ],
)

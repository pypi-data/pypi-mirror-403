from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "new_share"
URL = "https://tushare.pro/document/2?doc_id=123"
ARGS = {
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
NAME = "stockipo"
KEY = "/tushare/stockipo"
PAGINATE = {
    "pagesize": 2000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="新股发行上市信息（Tushare格式）",
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
        ColumnInfo(name="sub_code", kind=ColumnKind.STRING, desc="申购代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="ipo_date", kind=ColumnKind.STRING, desc="发行日期"),
        ColumnInfo(name="issue_date", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="amount", kind=ColumnKind.FLOAT, desc="发行总量(万股)"),
        ColumnInfo(name="market_amount", kind=ColumnKind.FLOAT, desc="上网发行量(万股)"),
        ColumnInfo(name="price", kind=ColumnKind.FLOAT, desc="发行价格"),
        ColumnInfo(name="pe", kind=ColumnKind.FLOAT, desc="发行市盈率"),
        ColumnInfo(name="limit_amount", kind=ColumnKind.FLOAT, desc="个人申购上限(万股)"),
        ColumnInfo(name="funds", kind=ColumnKind.FLOAT, desc="募集资金(亿元)"),
        ColumnInfo(name="ballot", kind=ColumnKind.FLOAT, desc="中签率(%)"),
    ],
)
TARGET = TableInfo(
    desc="新股发行上市信息（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="TS股票代码"),
        ColumnInfo(name="sub_code", kind=ColumnKind.STRING, desc="申购代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="ipo_date", kind=ColumnKind.STRING, desc="发行日期"),
        ColumnInfo(name="ipo_datecode", kind=ColumnKind.STRING, desc="发行日期代码"),
        ColumnInfo(name="issue_date", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="issue_datecode", kind=ColumnKind.STRING, desc="上市日期代码"),
        ColumnInfo(name="amount", kind=ColumnKind.FLOAT, desc="发行总量(万股)"),
        ColumnInfo(name="market_amount", kind=ColumnKind.FLOAT, desc="上网发行量(万股)"),
        ColumnInfo(name="price", kind=ColumnKind.FLOAT, desc="发行价格"),
        ColumnInfo(name="pe", kind=ColumnKind.FLOAT, desc="发行市盈率"),
        ColumnInfo(name="limit_amount", kind=ColumnKind.FLOAT, desc="个人申购上限(万股)"),
        ColumnInfo(name="funds", kind=ColumnKind.FLOAT, desc="募集资金(亿元)"),
        ColumnInfo(name="ballot", kind=ColumnKind.FLOAT, desc="中签率(%)"),
    ],
)

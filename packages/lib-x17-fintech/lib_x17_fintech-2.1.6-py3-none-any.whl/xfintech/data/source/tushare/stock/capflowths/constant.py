from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "moneyflow_ths"
URL = "https://tushare.pro/document/2?doc_id=348"
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
NAME = "capflowths"
KEY = "/tushare/capflowths"
PAGINATE = {
    "pagesize": 6000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="同花顺个股资金流向数据（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="trade_date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="pct_change", kind=ColumnKind.FLOAT, desc="涨跌幅"),
        ColumnInfo(name="latest", kind=ColumnKind.FLOAT, desc="最新价"),
        ColumnInfo(name="net_amount", kind=ColumnKind.FLOAT, desc="资金净流入(万元)"),
        ColumnInfo(name="net_d5_amount", kind=ColumnKind.FLOAT, desc="5日主力净额(万元)"),
        ColumnInfo(name="buy_lg_amount", kind=ColumnKind.FLOAT, desc="今日大单净流入额(万元)"),
        ColumnInfo(name="buy_lg_amount_rate", kind=ColumnKind.FLOAT, desc="今日大单净流入占比(%)"),
        ColumnInfo(name="buy_md_amount", kind=ColumnKind.FLOAT, desc="今日中单净流入额(万元)"),
        ColumnInfo(name="buy_md_amount_rate", kind=ColumnKind.FLOAT, desc="今日中单净流入占比(%)"),
        ColumnInfo(name="buy_sm_amount", kind=ColumnKind.FLOAT, desc="今日小单净流入额(万元)"),
        ColumnInfo(name="buy_sm_amount_rate", kind=ColumnKind.FLOAT, desc="今日小单净流入占比(%)"),
    ],
)
TARGET = TableInfo(
    desc="同花顺个股资金流向数据（xfintech标准格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期 (YYYY-MM-DD)"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="交易日期 (YYYYMMDD)"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="percent_change", kind=ColumnKind.FLOAT, desc="涨跌幅"),
        ColumnInfo(name="latest", kind=ColumnKind.FLOAT, desc="最新价"),
        ColumnInfo(name="net_amount", kind=ColumnKind.FLOAT, desc="资金净流入(万元)"),
        ColumnInfo(name="net_d5_amount", kind=ColumnKind.FLOAT, desc="5日主力净额(万元)"),
        ColumnInfo(name="buy_lg_amount", kind=ColumnKind.FLOAT, desc="今日大单净流入额(万元)"),
        ColumnInfo(name="buy_lg_amount_rate", kind=ColumnKind.FLOAT, desc="今日大单净流入占比(%)"),
        ColumnInfo(name="buy_md_amount", kind=ColumnKind.FLOAT, desc="今日中单净流入额(万元)"),
        ColumnInfo(name="buy_md_amount_rate", kind=ColumnKind.FLOAT, desc="今日中单净流入占比(%)"),
        ColumnInfo(name="buy_sm_amount", kind=ColumnKind.FLOAT, desc="今日小单净流入额(万元)"),
        ColumnInfo(name="buy_sm_amount_rate", kind=ColumnKind.FLOAT, desc="今日小单净流入占比(%)"),
    ],
)

from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "moneyflow_mkt_dc"
URL = "https://tushare.pro/document/2?doc_id=345"
ARGS = {
    "trade_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "交易日期(YYYYMMDD)",
    },
    "start_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "开始日期",
    },
    "end_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "结束日期",
    },
}

# Exported constants
NAME = "marketindexcapflowdc"
KEY = "/tushare/marketindexcapflowdc"
PAGINATE = {
    "pagesize": 3000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="东方财富大盘资金流向数据（tushare格式）",
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
        ColumnInfo(name="close_sh", kind=ColumnKind.FLOAT, desc="上证收盘价（点）"),
        ColumnInfo(name="pct_change_sh", kind=ColumnKind.FLOAT, desc="上证涨跌幅(%)"),
        ColumnInfo(name="close_sz", kind=ColumnKind.FLOAT, desc="深证收盘价（点）"),
        ColumnInfo(name="pct_change_sz", kind=ColumnKind.FLOAT, desc="深证涨跌幅(%)"),
        ColumnInfo(name="net_amount", kind=ColumnKind.FLOAT, desc="今日主力净流入净额（元）"),
        ColumnInfo(name="net_amount_rate", kind=ColumnKind.FLOAT, desc="今日主力净流入净占比%"),
        ColumnInfo(name="buy_elg_amount", kind=ColumnKind.FLOAT, desc="今日超大单净流入净额（元）"),
        ColumnInfo(name="buy_elg_amount_rate", kind=ColumnKind.FLOAT, desc="今日超大单净流入净占比%"),
        ColumnInfo(name="buy_lg_amount", kind=ColumnKind.FLOAT, desc="今日大单净流入净额（元）"),
        ColumnInfo(name="buy_lg_amount_rate", kind=ColumnKind.FLOAT, desc="今日大单净流入净占比%"),
        ColumnInfo(name="buy_md_amount", kind=ColumnKind.FLOAT, desc="今日中单净流入净额（元）"),
        ColumnInfo(name="buy_md_amount_rate", kind=ColumnKind.FLOAT, desc="今日中单净流入净占比%"),
        ColumnInfo(name="buy_sm_amount", kind=ColumnKind.FLOAT, desc="今日小单净流入净额（元）"),
        ColumnInfo(name="buy_sm_amount_rate", kind=ColumnKind.FLOAT, desc="今日小单净流入净占比%"),
    ],
)
TARGET = TableInfo(
    desc="东方财富大盘资金流向数据（xfinbatch标准格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="交易日期代码(YYYYMMDD)"),
        ColumnInfo(name="close_sh", kind=ColumnKind.FLOAT, desc="上证收盘价（点）"),
        ColumnInfo(name="percent_change_sh", kind=ColumnKind.FLOAT, desc="上证涨跌幅(%)"),
        ColumnInfo(name="close_sz", kind=ColumnKind.FLOAT, desc="深证收盘价（点）"),
        ColumnInfo(name="percent_change_sz", kind=ColumnKind.FLOAT, desc="深证涨跌幅(%)"),
        ColumnInfo(name="net_amount", kind=ColumnKind.FLOAT, desc="今日主力净流入净额（元）"),
        ColumnInfo(name="net_amount_rate", kind=ColumnKind.FLOAT, desc="今日主力净流入净占比%"),
        ColumnInfo(name="buy_elg_amount", kind=ColumnKind.FLOAT, desc="今日超大单净流入净额（元）"),
        ColumnInfo(name="buy_elg_amount_rate", kind=ColumnKind.FLOAT, desc="今日超大单净流入净占比%"),
        ColumnInfo(name="buy_lg_amount", kind=ColumnKind.FLOAT, desc="今日大单净流入净额（元）"),
        ColumnInfo(name="buy_lg_amount_rate", kind=ColumnKind.FLOAT, desc="今日大单净流入净占比%"),
        ColumnInfo(name="buy_md_amount", kind=ColumnKind.FLOAT, desc="今日中单净流入净额（元）"),
        ColumnInfo(name="buy_md_amount_rate", kind=ColumnKind.FLOAT, desc="今日中单净流入净占比%"),
        ColumnInfo(name="buy_sm_amount", kind=ColumnKind.FLOAT, desc="今日小单净流入净额（元）"),
        ColumnInfo(name="buy_sm_amount_rate", kind=ColumnKind.FLOAT, desc="今日小单净流入净占比%"),
    ],
)

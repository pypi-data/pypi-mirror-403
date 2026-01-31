from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "moneyflow_ind_dc"
URL = "https://tushare.pro/document/2?doc_id=344"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "代码",
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
    "content_type": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "资金类型(行业、概念、地域)",
    },
}

# Exported constants
NAME = "conceptcapflowdc"
KEY = "/tushare/conceptcapflowdc"
PAGINATE = {
    "pagesize": 5000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="东财概念及行业板块资金流向数据（Tushare格式）",
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
        ColumnInfo(name="content_type", kind=ColumnKind.STRING, desc="数据类型"),
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="DC板块代码（行业、概念、地域）"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="板块名称"),
        ColumnInfo(name="pct_change", kind=ColumnKind.FLOAT, desc="板块涨跌幅（%）"),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT, desc="板块最新指数"),
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
        ColumnInfo(name="buy_sm_amount_stock", kind=ColumnKind.STRING, desc="今日主力净流入最大股"),
        ColumnInfo(name="rank", kind=ColumnKind.INTEGER, desc="序号"),
    ],
)
TARGET = TableInfo(
    desc="东财概念及行业板块资金流向数据（xfintech标准格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="板块代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="交易日期代码(YYYYMMDD)"),
        ColumnInfo(name="content_type", kind=ColumnKind.STRING, desc="数据类型"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="板块名称"),
        ColumnInfo(name="percent_change", kind=ColumnKind.FLOAT, desc="板块涨跌幅（%）"),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT, desc="板块最新指数"),
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
        ColumnInfo(name="buy_sm_amount_stock", kind=ColumnKind.STRING, desc="今日主力净流入最大股"),
        ColumnInfo(name="rank", kind=ColumnKind.INTEGER, desc="序号"),
    ],
)

from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "moneyflow_cnt_ths"
URL = "https://tushare.pro/document/2?doc_id=371"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "概念代码(支持多个概念同时提取，逗号分隔)",
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
NAME = "conceptcapflowths"
KEY = "/tushare/conceptcapflowths"
PAGINATE = {
    "pagesize": 5000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="同花顺概念板块资金流向数据（Tushare格式）",
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
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="板块代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="板块名称"),
        ColumnInfo(name="lead_stock", kind=ColumnKind.STRING, desc="领涨股票名称"),
        ColumnInfo(name="close_price", kind=ColumnKind.FLOAT, desc="最新价"),
        ColumnInfo(name="pct_change", kind=ColumnKind.FLOAT, desc="行业涨跌幅"),
        ColumnInfo(name="industry_index", kind=ColumnKind.FLOAT, desc="板块指数"),
        ColumnInfo(name="company_num", kind=ColumnKind.INTEGER, desc="公司数量"),
        ColumnInfo(name="pct_change_stock", kind=ColumnKind.FLOAT, desc="领涨股涨跌幅"),
        ColumnInfo(name="net_buy_amount", kind=ColumnKind.FLOAT, desc="流入资金(亿元)"),
        ColumnInfo(name="net_sell_amount", kind=ColumnKind.FLOAT, desc="流出资金(亿元)"),
        ColumnInfo(name="net_amount", kind=ColumnKind.FLOAT, desc="净额(亿元)"),
    ],
)
TARGET = TableInfo(
    desc="同花顺概念板块资金流向数据（xfintech标准格式）",
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
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="板块名称"),
        ColumnInfo(name="lead_stock", kind=ColumnKind.STRING, desc="领涨股票名称"),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT, desc="最新价"),
        ColumnInfo(name="percent_change", kind=ColumnKind.FLOAT, desc="行业涨跌幅"),
        ColumnInfo(name="industry_index", kind=ColumnKind.FLOAT, desc="板块指数"),
        ColumnInfo(name="company_num", kind=ColumnKind.INTEGER, desc="公司数量"),
        ColumnInfo(name="pct_change_stock", kind=ColumnKind.FLOAT, desc="领涨股涨跌幅"),
        ColumnInfo(name="net_buy_amount", kind=ColumnKind.FLOAT, desc="流入资金(亿元)"),
        ColumnInfo(name="net_sell_amount", kind=ColumnKind.FLOAT, desc="流出资金(亿元)"),
        ColumnInfo(name="net_amount", kind=ColumnKind.FLOAT, desc="净额(亿元)"),
    ],
)

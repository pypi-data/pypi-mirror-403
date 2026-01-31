from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "moneyflow"
URL = "https://tushare.pro/document/2?doc_id=170"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票代码(支持多个股票同时提取，逗号分隔)",
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
NAME = "capflow"
KEY = "/tushare/capflow"
PAGINATE = {
    "pagesize": 6000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="A股日线个股资金流向数据（tushare格式）",
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
        ColumnInfo(name="buy_sm_vol", kind=ColumnKind.FLOAT, desc="小单买入量(手)"),
        ColumnInfo(name="buy_sm_amount", kind=ColumnKind.FLOAT, desc="小单买入金额(万元)"),
        ColumnInfo(name="sell_sm_vol", kind=ColumnKind.FLOAT, desc="小单卖出量(手)"),
        ColumnInfo(name="sell_sm_amount", kind=ColumnKind.FLOAT, desc="小单卖出金额(万元)"),
        ColumnInfo(name="buy_md_vol", kind=ColumnKind.FLOAT, desc="中单买入量(手)"),
        ColumnInfo(name="buy_md_amount", kind=ColumnKind.FLOAT, desc="中单买入金额(万元)"),
        ColumnInfo(name="sell_md_vol", kind=ColumnKind.FLOAT, desc="中单卖出量(手)"),
        ColumnInfo(name="sell_md_amount", kind=ColumnKind.FLOAT, desc="中单卖出金额(万元)"),
        ColumnInfo(name="buy_lg_vol", kind=ColumnKind.FLOAT, desc="大单买入量(手)"),
        ColumnInfo(name="buy_lg_amount", kind=ColumnKind.FLOAT, desc="大单买入金额(万元)"),
        ColumnInfo(name="sell_lg_vol", kind=ColumnKind.FLOAT, desc="大单卖出量(手)"),
        ColumnInfo(name="sell_lg_amount", kind=ColumnKind.FLOAT, desc="大单卖出金额(万元)"),
        ColumnInfo(name="buy_elg_vol", kind=ColumnKind.FLOAT, desc="特大单买入量(手)"),
        ColumnInfo(name="buy_elg_amount", kind=ColumnKind.FLOAT, desc="特大单买入金额(万元)"),
        ColumnInfo(name="sell_elg_vol", kind=ColumnKind.FLOAT, desc="特大单卖出量(手)"),
        ColumnInfo(name="sell_elg_amount", kind=ColumnKind.FLOAT, desc="特大单卖出金额(万元)"),
        ColumnInfo(name="net_mf_vol", kind=ColumnKind.FLOAT, desc="净流入量(手)"),
        ColumnInfo(name="net_mf_amount", kind=ColumnKind.FLOAT, desc="净流入金额(万元)"),
    ],
)
TARGET = TableInfo(
    desc="A股日线个股资金流向数据（xfinbatch标准格式）",
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
        ColumnInfo(name="buy_sm_vol", kind=ColumnKind.FLOAT, desc="小单买入量(手)"),
        ColumnInfo(name="buy_sm_amount", kind=ColumnKind.FLOAT, desc="小单买入金额(万元)"),
        ColumnInfo(name="sell_sm_vol", kind=ColumnKind.FLOAT, desc="小单卖出量(手)"),
        ColumnInfo(name="sell_sm_amount", kind=ColumnKind.FLOAT, desc="小单卖出金额(万元)"),
        ColumnInfo(name="buy_md_vol", kind=ColumnKind.FLOAT, desc="中单买入量(手)"),
        ColumnInfo(name="buy_md_amount", kind=ColumnKind.FLOAT, desc="中单买入金额(万元)"),
        ColumnInfo(name="sell_md_vol", kind=ColumnKind.FLOAT, desc="中单卖出量(手)"),
        ColumnInfo(name="sell_md_amount", kind=ColumnKind.FLOAT, desc="中单卖出金额(万元)"),
        ColumnInfo(name="buy_lg_vol", kind=ColumnKind.FLOAT, desc="大单买入量(手)"),
        ColumnInfo(name="buy_lg_amount", kind=ColumnKind.FLOAT, desc="大单买入金额(万元)"),
        ColumnInfo(name="sell_lg_vol", kind=ColumnKind.FLOAT, desc="大单卖出量(手)"),
        ColumnInfo(name="sell_lg_amount", kind=ColumnKind.FLOAT, desc="大单卖出金额(万元)"),
        ColumnInfo(name="buy_elg_vol", kind=ColumnKind.FLOAT, desc="特大单买入量(手)"),
        ColumnInfo(name="buy_elg_amount", kind=ColumnKind.FLOAT, desc="特大单买入金额(万元)"),
        ColumnInfo(name="sell_elg_vol", kind=ColumnKind.FLOAT, desc="特大单卖出量(手)"),
        ColumnInfo(name="sell_elg_amount", kind=ColumnKind.FLOAT, desc="特大单卖出金额(万元)"),
        ColumnInfo(name="net_mf_vol", kind=ColumnKind.FLOAT, desc="净流入量(手)"),
        ColumnInfo(name="net_mf_amount", kind=ColumnKind.FLOAT, desc="净流入金额(万元)"),
    ],
)

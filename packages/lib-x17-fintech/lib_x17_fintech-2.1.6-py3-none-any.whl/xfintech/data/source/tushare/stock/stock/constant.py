from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "stock_basic"
URL = "https://tushare.pro/document/2?doc_id=25"
EXCHANGES = ["SSE", "SZSE", "BSE"]
STATUSES = ["L", "D", "P"]
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "TS股票代码",
    },
    "name": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票名称",
    },
    "list_status": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": f"上市状态{STATUSES}",
    },
    "exchange": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": f"交易所{EXCHANGES}",
    },
    "market": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "市场类型",
    },
}

# Exported constants
NAME = "stock"
KEY = "/tushare/stock"
PAGINATE = {
    "pagesize": 4000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="上市股票基本信息（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS代码"),
        ColumnInfo(name="symbol", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="area", kind=ColumnKind.STRING, desc="地域"),
        ColumnInfo(name="industry", kind=ColumnKind.STRING, desc="所属行业"),
        ColumnInfo(name="fullname", kind=ColumnKind.STRING, desc="股票全称"),
        ColumnInfo(name="enname", kind=ColumnKind.STRING, desc="英文全称"),
        ColumnInfo(name="cnspell", kind=ColumnKind.STRING, desc="拼音缩写"),
        ColumnInfo(name="market", kind=ColumnKind.STRING, desc="市场类型(主板/创业板/科创板/CDR)"),
        ColumnInfo(name="exchange", kind=ColumnKind.STRING, desc="交易所代码"),
        ColumnInfo(name="curr_type", kind=ColumnKind.STRING, desc="交易货币"),
        ColumnInfo(name="list_status", kind=ColumnKind.STRING, desc="上市状态 L上市 D退市 P暂停上市"),
        ColumnInfo(name="list_date", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="delist_date", kind=ColumnKind.STRING, desc="退市日期"),
        ColumnInfo(name="is_hs", kind=ColumnKind.STRING, desc="是否沪深港通标"),
        ColumnInfo(name="act_name", kind=ColumnKind.STRING, desc="实控人名称"),
        ColumnInfo(name="act_ent_type", kind=ColumnKind.STRING, desc="实控人企业性质"),
    ],
)
TARGET = TableInfo(
    desc="上市公司基本信息（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="TS代码"),
        ColumnInfo(name="symbol", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="area", kind=ColumnKind.STRING, desc="地域"),
        ColumnInfo(name="industry", kind=ColumnKind.STRING, desc="所属行业"),
        ColumnInfo(name="fullname", kind=ColumnKind.STRING, desc="股票全称"),
        ColumnInfo(name="enname", kind=ColumnKind.STRING, desc="英文全称"),
        ColumnInfo(name="cnspell", kind=ColumnKind.STRING, desc="拼音缩写"),
        ColumnInfo(name="market", kind=ColumnKind.STRING, desc="市场类型(主板/创业板/科创板/CDR)"),
        ColumnInfo(name="exchange", kind=ColumnKind.STRING, desc="交易所代码"),
        ColumnInfo(name="currency", kind=ColumnKind.STRING, desc="交易货币"),
        ColumnInfo(name="list_status", kind=ColumnKind.STRING, desc="上市状态 L上市 D退市 P暂停上市"),
        ColumnInfo(name="list_date", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="delist_date", kind=ColumnKind.STRING, desc="退市日期"),
        ColumnInfo(name="is_hs", kind=ColumnKind.STRING, desc="是否沪深港通标"),
        ColumnInfo(name="ace_name", kind=ColumnKind.STRING, desc="实控人名称"),
        ColumnInfo(name="ace_type", kind=ColumnKind.STRING, desc="实控人企业性质"),
    ],
)

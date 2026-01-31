from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "stock_company"
URL = "https://tushare.pro/document/2?doc_id=112"
EXCHANGES = ["SSE", "SZSE", "BSE"]
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "TS股票代码",
    },
    "exchange": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": f"交易所{EXCHANGES}",
    },
}

# Exported constants
NAME = "company"
KEY = "/tushare/stockcompany"
PAGINATE = {
    "pagesize": 4500,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="上市公司基本信息（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "static",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS股票代码"),
        ColumnInfo(name="com_name", kind=ColumnKind.STRING, desc="公司全称"),
        ColumnInfo(name="com_id", kind=ColumnKind.STRING, desc="统一社会信用代码"),
        ColumnInfo(name="exchange", kind=ColumnKind.STRING, desc="交易所"),
        ColumnInfo(name="short_name", kind=ColumnKind.STRING, desc="公司简称"),
        ColumnInfo(name="chairman", kind=ColumnKind.STRING, desc="法人代表"),
        ColumnInfo(name="manager", kind=ColumnKind.STRING, desc="总经理"),
        ColumnInfo(name="secretary", kind=ColumnKind.STRING, desc="董秘"),
        ColumnInfo(name="reg_capital", kind=ColumnKind.FLOAT, desc="注册资本(万元)"),
        ColumnInfo(name="setup_date", kind=ColumnKind.STRING, desc="注册日期"),
        ColumnInfo(name="province", kind=ColumnKind.STRING, desc="所在省份"),
        ColumnInfo(name="city", kind=ColumnKind.STRING, desc="所在城市"),
        ColumnInfo(name="introduction", kind=ColumnKind.STRING, desc="公司介绍"),
        ColumnInfo(name="website", kind=ColumnKind.STRING, desc="公司主页"),
        ColumnInfo(name="email", kind=ColumnKind.STRING, desc="电子邮件"),
        ColumnInfo(name="office", kind=ColumnKind.STRING, desc="办公室"),
        ColumnInfo(name="employees", kind=ColumnKind.INTEGER, desc="员工人数"),
        ColumnInfo(name="main_business", kind=ColumnKind.STRING, desc="主要业务及产品"),
        ColumnInfo(name="business_scope", kind=ColumnKind.STRING, desc="经营范围"),
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
        ColumnInfo(name="stockcode", kind=ColumnKind.STRING, desc="TS股票代码"),
        ColumnInfo(name="company_name", kind=ColumnKind.STRING, desc="公司全称"),
        ColumnInfo(name="company_id", kind=ColumnKind.STRING, desc="统一社会信用代码"),
        ColumnInfo(name="exchange", kind=ColumnKind.STRING, desc="交易所"),
        ColumnInfo(name="chairman", kind=ColumnKind.STRING, desc="法人代表"),
        ColumnInfo(name="manager", kind=ColumnKind.STRING, desc="总经理"),
        ColumnInfo(name="secretary", kind=ColumnKind.STRING, desc="董秘"),
        ColumnInfo(name="reg_capital", kind=ColumnKind.FLOAT, desc="注册资本(万元)"),
        ColumnInfo(name="setup_date", kind=ColumnKind.STRING, desc="注册日期"),
        ColumnInfo(name="province", kind=ColumnKind.STRING, desc="所在省份"),
        ColumnInfo(name="city", kind=ColumnKind.STRING, desc="所在城市"),
        ColumnInfo(name="introduction", kind=ColumnKind.STRING, desc="公司介绍"),
        ColumnInfo(name="website", kind=ColumnKind.STRING, desc="公司主页"),
        ColumnInfo(name="email", kind=ColumnKind.STRING, desc="电子邮件"),
        ColumnInfo(name="office", kind=ColumnKind.STRING, desc="办公室"),
        ColumnInfo(name="employees", kind=ColumnKind.INTEGER, desc="员工人数"),
        ColumnInfo(name="main_business", kind=ColumnKind.STRING, desc="主要业务及产品"),
        ColumnInfo(name="business_scope", kind=ColumnKind.STRING, desc="经营范围"),
    ],
)

from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "bak_basic"
URL = "https://tushare.pro/document/2?doc_id=262"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "TS股票代码",
    },
    "trade_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "交易日期YYYYMMDD",
    },
}

# Exported constants
NAME = "stockinfo"
KEY = "/tushare/stockinfo"
PAGINATE = {
    "pagesize": 7000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="上市股票基本信息（Tushare格式）",
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
        ColumnInfo(name="industry", kind=ColumnKind.STRING, desc="所属行业"),
        ColumnInfo(name="area", kind=ColumnKind.STRING, desc="地域"),
        ColumnInfo(name="pe", kind=ColumnKind.FLOAT, desc="市盈率（动）"),
        ColumnInfo(name="float_share", kind=ColumnKind.FLOAT, desc="流通股本（亿）"),
        ColumnInfo(name="total_share", kind=ColumnKind.FLOAT, desc="总股本（亿）"),
        ColumnInfo(name="total_assets", kind=ColumnKind.FLOAT, desc="总资产（亿）"),
        ColumnInfo(name="liquid_assets", kind=ColumnKind.FLOAT, desc="流动资产（亿）"),
        ColumnInfo(name="fixed_assets", kind=ColumnKind.FLOAT, desc="固定资产（亿）"),
        ColumnInfo(name="reserved", kind=ColumnKind.FLOAT, desc="公积金"),
        ColumnInfo(name="reserved_pershare", kind=ColumnKind.FLOAT, desc="每股公积金"),
        ColumnInfo(name="eps", kind=ColumnKind.FLOAT, desc="每股收益"),
        ColumnInfo(name="bvps", kind=ColumnKind.FLOAT, desc="每股净资产"),
        ColumnInfo(name="pb", kind=ColumnKind.FLOAT, desc="市净率"),
        ColumnInfo(name="list_date", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="undp", kind=ColumnKind.FLOAT, desc="未分配利润"),
        ColumnInfo(name="per_undp", kind=ColumnKind.FLOAT, desc="每股未分配利润"),
        ColumnInfo(name="rev_yoy", kind=ColumnKind.FLOAT, desc="收入同比（%）"),
        ColumnInfo(name="profit_yoy", kind=ColumnKind.FLOAT, desc="利润同比（%）"),
        ColumnInfo(name="gpr", kind=ColumnKind.FLOAT, desc="毛利率（%）"),
        ColumnInfo(name="npr", kind=ColumnKind.FLOAT, desc="净利润率（%）"),
        ColumnInfo(name="holder_num", kind=ColumnKind.INTEGER, desc="股东人数"),
    ],
)
TARGET = TableInfo(
    desc="上市股票基本信息（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="name", kind=ColumnKind.STRING, desc="股票名称"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="交易日期"),
        ColumnInfo(name="list_date", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="list_datecode", kind=ColumnKind.STRING, desc="上市日期"),
        ColumnInfo(name="industry", kind=ColumnKind.STRING, desc="所属行业"),
        ColumnInfo(name="area", kind=ColumnKind.STRING, desc="地域"),
        ColumnInfo(name="pe", kind=ColumnKind.FLOAT, desc="市盈率（动）"),
        ColumnInfo(name="float_share", kind=ColumnKind.FLOAT, desc="流通股本（亿）"),
        ColumnInfo(name="total_share", kind=ColumnKind.FLOAT, desc="总股本（亿）"),
        ColumnInfo(name="total_assets", kind=ColumnKind.FLOAT, desc="总资产（亿）"),
        ColumnInfo(name="liquid_assets", kind=ColumnKind.FLOAT, desc="流动资产（亿）"),
        ColumnInfo(name="fixed_assets", kind=ColumnKind.FLOAT, desc="固定资产（亿）"),
        ColumnInfo(name="reserved", kind=ColumnKind.FLOAT, desc="公积金"),
        ColumnInfo(name="reserved_pershare", kind=ColumnKind.FLOAT, desc="每股公积金"),
        ColumnInfo(name="eps", kind=ColumnKind.FLOAT, desc="每股收益"),
        ColumnInfo(name="bvps", kind=ColumnKind.FLOAT, desc="每股净资产"),
        ColumnInfo(name="pb", kind=ColumnKind.FLOAT, desc="市净率"),
        ColumnInfo(name="undp", kind=ColumnKind.FLOAT, desc="未分配利润"),
        ColumnInfo(name="per_undp", kind=ColumnKind.FLOAT, desc="每股未分配利润"),
        ColumnInfo(name="rev_yoy", kind=ColumnKind.FLOAT, desc="收入同比（%）"),
        ColumnInfo(name="profit_yoy", kind=ColumnKind.FLOAT, desc="利润同比（%）"),
        ColumnInfo(name="gpr", kind=ColumnKind.FLOAT, desc="毛利率（%）"),
        ColumnInfo(name="npr", kind=ColumnKind.FLOAT, desc="净利润率（%）"),
        ColumnInfo(name="holder_num", kind=ColumnKind.INTEGER, desc="股东人数"),
    ],
)

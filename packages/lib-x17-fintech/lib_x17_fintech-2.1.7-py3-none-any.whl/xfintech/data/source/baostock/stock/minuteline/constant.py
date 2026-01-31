from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "baostock"
SOURCE_NAME = "query_history_k_data_plus"
URL = "http://www.baostock.com/mainContent?file=stockKData.md"
ARGS = {
    "code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票代码(支持多个股票同时提取，逗号分隔)",
    },
    "start": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "开始日期(YYYYMMDD)",
    },
    "end": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "结束日期(YYYYMMDD)",
    },
    "frequency": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "5=5分钟、15=15分钟、30=30分钟、60=60分钟",
    },
    "adjustflag": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "复权类型，默认不复权：3；1：后复权；2：前复权",
    },
}

# Exported constants
NAME = "minuteline"
KEY = "/baostock/minuteline"
PAGINATE = {
    "pagesize": 10000,
    "pagelimit": 100,
}
SOURCE = TableInfo(
    desc="A股分钟线行情数据（BaoStock格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "individual",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="证券代码	格式：sh.600000。sh：上海，sz：深圳"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期: 格式：YYYY-MM-DD"),
        ColumnInfo(name="time", kind=ColumnKind.STRING, desc="交易时间, 格式：YYYYMMDDHHMMSSsss"),
        ColumnInfo(name="open", kind=ColumnKind.FLOAT, desc="开盘价"),
        ColumnInfo(name="high", kind=ColumnKind.FLOAT, desc="最高价"),
        ColumnInfo(name="low", kind=ColumnKind.FLOAT, desc="最低价"),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT, desc="收盘价"),
        ColumnInfo(name="volume", kind=ColumnKind.FLOAT, desc="成交量(股)"),
        ColumnInfo(name="amount", kind=ColumnKind.FLOAT, desc="成交额(元)"),
        ColumnInfo(name="adjustflag", kind=ColumnKind.STRING, desc="复权状态: 不复权、前复权、后复权"),
    ],
)
TARGET = TableInfo(
    desc="A股分钟线行情数据（xfintech格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "individual",
    },
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="交易日期: 格式：YYYY-MM-DD"),
        ColumnInfo(name="time", kind=ColumnKind.STRING, desc="交易时间代码: 格式：YYYYMMDDHHMMSSsss"),
        ColumnInfo(name="open", kind=ColumnKind.FLOAT, desc="开盘价"),
        ColumnInfo(name="high", kind=ColumnKind.FLOAT, desc="最高价"),
        ColumnInfo(name="low", kind=ColumnKind.FLOAT, desc="最低价"),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT, desc="收盘价"),
        ColumnInfo(name="volume", kind=ColumnKind.FLOAT, desc="成交量(股)"),
        ColumnInfo(name="amount", kind=ColumnKind.FLOAT, desc="成交额(元)"),
        ColumnInfo(name="adjustflag", kind=ColumnKind.STRING, desc="复权状态: 不复权、前复权、后复权"),
    ],
)

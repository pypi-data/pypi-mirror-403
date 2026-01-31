from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "dividend"
URL = "https://tushare.pro/document/2?doc_id=103"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "TS代码",
    },
    "ann_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "公告日",
    },
    "record_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股权登记日期",
    },
    "ex_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "除权除息日",
    },
    "imp_ann_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "实施公告日",
    },
}

# Exported constants
NAME = "stockdividend"
KEY = "/tushare/stockdividend"
PAGINATE = {
    "pagesize": 1000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="分红送股数据（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "crosssection",
    },
    name=SOURCE_NAME,
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS代码"),
        ColumnInfo(name="end_date", kind=ColumnKind.STRING, desc="分红年度"),
        ColumnInfo(name="ann_date", kind=ColumnKind.STRING, desc="预案公告日"),
        ColumnInfo(name="div_proc", kind=ColumnKind.STRING, desc="实施进度"),
        ColumnInfo(name="stk_div", kind=ColumnKind.FLOAT, desc="每股送转"),
        ColumnInfo(name="stk_bo_rate", kind=ColumnKind.FLOAT, desc="每股送股比例"),
        ColumnInfo(name="stk_co_rate", kind=ColumnKind.FLOAT, desc="每股转增比例"),
        ColumnInfo(name="cash_div", kind=ColumnKind.FLOAT, desc="每股分红（税后）"),
        ColumnInfo(name="cash_div_tax", kind=ColumnKind.FLOAT, desc="每股分红（税前）"),
        ColumnInfo(name="record_date", kind=ColumnKind.STRING, desc="股权登记日"),
        ColumnInfo(name="ex_date", kind=ColumnKind.STRING, desc="除权除息日"),
        ColumnInfo(name="pay_date", kind=ColumnKind.STRING, desc="派息日"),
        ColumnInfo(name="div_listdate", kind=ColumnKind.STRING, desc="红股上市日"),
        ColumnInfo(name="imp_ann_date", kind=ColumnKind.STRING, desc="实施公告日"),
        ColumnInfo(name="base_date", kind=ColumnKind.STRING, desc="基准日"),
        ColumnInfo(name="base_share", kind=ColumnKind.FLOAT, desc="基准股本（万）"),
    ],
)

TARGET = TableInfo(
    desc="分红送股数据（标准格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "crosssection",
    },
    name=NAME,
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="end_date", kind=ColumnKind.STRING, desc="分红年度"),
        ColumnInfo(name="ann_date", kind=ColumnKind.STRING, desc="预案公告日"),
        ColumnInfo(name="ann_datecode", kind=ColumnKind.STRING, desc="预案公告日代码"),
        ColumnInfo(name="div_proc", kind=ColumnKind.STRING, desc="实施进度"),
        ColumnInfo(name="stk_div", kind=ColumnKind.FLOAT, desc="每股送转"),
        ColumnInfo(name="stk_bo_rate", kind=ColumnKind.FLOAT, desc="每股送股比例"),
        ColumnInfo(name="stk_co_rate", kind=ColumnKind.FLOAT, desc="每股转增比例"),
        ColumnInfo(name="cash_div", kind=ColumnKind.FLOAT, desc="每股分红（税后）"),
        ColumnInfo(name="cash_div_tax", kind=ColumnKind.FLOAT, desc="每股分红（税前）"),
        ColumnInfo(name="record_date", kind=ColumnKind.STRING, desc="股权登记日"),
        ColumnInfo(name="record_datecode", kind=ColumnKind.STRING, desc="股权登记日代码"),
        ColumnInfo(name="ex_date", kind=ColumnKind.STRING, desc="除权除息日"),
        ColumnInfo(name="ex_datecode", kind=ColumnKind.STRING, desc="除权除息日代码"),
        ColumnInfo(name="pay_date", kind=ColumnKind.STRING, desc="派息日"),
        ColumnInfo(name="pay_datecode", kind=ColumnKind.STRING, desc="派息日代码"),
        ColumnInfo(name="div_listdate", kind=ColumnKind.STRING, desc="红股上市日"),
        ColumnInfo(name="div_listdatecode", kind=ColumnKind.STRING, desc="红股上市日代码"),
        ColumnInfo(name="imp_ann_date", kind=ColumnKind.STRING, desc="实施公告日"),
        ColumnInfo(name="imp_ann_datecode", kind=ColumnKind.STRING, desc="实施公告日代码"),
        ColumnInfo(name="base_date", kind=ColumnKind.STRING, desc="基准日"),
        ColumnInfo(name="base_datecode", kind=ColumnKind.STRING, desc="基准日代码"),
        ColumnInfo(name="base_share", kind=ColumnKind.FLOAT, desc="基准股本（万）"),
    ],
)

from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "pledge_detail"
URL = "https://tushare.pro/document/2?doc_id=111"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "Y",
        "desc": "股票代码",
    },
}

# Exported constants
NAME = "stockpledgedetail"
KEY = "/tushare/stockpledgedetail"
PAGINATE = {
    "pagesize": 1000,
    "pagelimit": 1000,
}

SOURCE = TableInfo(
    desc="股权质押明细数据（Tushare格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "individual",
    },
    name=SOURCE_NAME,
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS股票代码"),
        ColumnInfo(name="ann_date", kind=ColumnKind.STRING, desc="公告日期"),
        ColumnInfo(name="holder_name", kind=ColumnKind.STRING, desc="股东名称"),
        ColumnInfo(name="pledge_amount", kind=ColumnKind.FLOAT, desc="质押数量（万股）"),
        ColumnInfo(name="start_date", kind=ColumnKind.STRING, desc="质押开始日期"),
        ColumnInfo(name="end_date", kind=ColumnKind.STRING, desc="质押结束日期"),
        ColumnInfo(name="is_release", kind=ColumnKind.STRING, desc="是否已解押"),
        ColumnInfo(name="release_date", kind=ColumnKind.STRING, desc="解押日期"),
        ColumnInfo(name="pledgor", kind=ColumnKind.STRING, desc="质押方"),
        ColumnInfo(name="holding_amount", kind=ColumnKind.FLOAT, desc="持股总数（万股）"),
        ColumnInfo(name="pledged_amount", kind=ColumnKind.FLOAT, desc="质押总数（万股）"),
        ColumnInfo(name="p_total_ratio", kind=ColumnKind.FLOAT, desc="本次质押占总股本比例"),
        ColumnInfo(name="h_total_ratio", kind=ColumnKind.FLOAT, desc="持股总数占总股本比例"),
        ColumnInfo(name="is_buyback", kind=ColumnKind.STRING, desc="是否回购"),
    ],
)

TARGET = TableInfo(
    desc="股权质押明细数据（标准格式）",
    meta={
        "key": KEY,
        "name": NAME,
        "type": "partitioned",
        "scale": "individual",
    },
    name=NAME,
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="ann_date", kind=ColumnKind.STRING, desc="公告日期"),
        ColumnInfo(name="ann_datecode", kind=ColumnKind.STRING, desc="公告日期代码"),
        ColumnInfo(name="holder_name", kind=ColumnKind.STRING, desc="股东名称"),
        ColumnInfo(name="pledge_amount", kind=ColumnKind.FLOAT, desc="质押数量（万股）"),
        ColumnInfo(name="start_date", kind=ColumnKind.STRING, desc="质押开始日期"),
        ColumnInfo(name="start_datecode", kind=ColumnKind.STRING, desc="质押开始日期代码"),
        ColumnInfo(name="end_date", kind=ColumnKind.STRING, desc="质押结束日期"),
        ColumnInfo(name="end_datecode", kind=ColumnKind.STRING, desc="质押结束日期代码"),
        ColumnInfo(name="is_release", kind=ColumnKind.STRING, desc="是否已解押"),
        ColumnInfo(name="release_date", kind=ColumnKind.STRING, desc="解押日期"),
        ColumnInfo(name="release_datecode", kind=ColumnKind.STRING, desc="解押日期代码"),
        ColumnInfo(name="pledgor", kind=ColumnKind.STRING, desc="质押方"),
        ColumnInfo(name="holding_amount", kind=ColumnKind.FLOAT, desc="持股总数（万股）"),
        ColumnInfo(name="pledged_amount", kind=ColumnKind.FLOAT, desc="质押总数（万股）"),
        ColumnInfo(name="p_total_ratio", kind=ColumnKind.FLOAT, desc="本次质押占总股本比例"),
        ColumnInfo(name="h_total_ratio", kind=ColumnKind.FLOAT, desc="持股总数占总股本比例"),
        ColumnInfo(name="is_buyback", kind=ColumnKind.STRING, desc="是否回购"),
    ],
)

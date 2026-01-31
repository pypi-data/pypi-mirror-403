from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "fina_mainbz_vip"
URL = "https://tushare.pro/document/2?doc_id=81"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "股票代码",
    },
    "start_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "报告期开始日期",
    },
    "end_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "报告期结束日期",
    },
    "period": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "报告期(每个季度最后一天的日期)",
    },
    "type": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "类型：P按产品 D按地区 I按行业",
    },
}

# Exported constants
NAME = "companybusiness"
KEY = "/tushare/companybusiness"
PAGINATE = {
    "pagesize": 9000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="A股主营业务构成数据（tushare格式）",
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
        ColumnInfo(name="end_date", kind=ColumnKind.STRING, desc="报告期"),
        ColumnInfo(name="bz_item", kind=ColumnKind.STRING, desc="主营业务来源"),
        ColumnInfo(name="bz_sales", kind=ColumnKind.FLOAT, desc="主营业务收入(元)"),
        ColumnInfo(name="bz_profit", kind=ColumnKind.FLOAT, desc="主营业务利润(元)"),
        ColumnInfo(name="bz_cost", kind=ColumnKind.FLOAT, desc="主营业务成本(元)"),
        ColumnInfo(name="curr_type", kind=ColumnKind.STRING, desc="货币代码"),
        ColumnInfo(name="update_flag", kind=ColumnKind.STRING, desc="是否更新"),
    ],
)
TARGET = TableInfo(
    desc="A股主营业务构成数据（标准格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "crosssection",
    },
    name=NAME,
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="报告期日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="报告期日期代码"),
        ColumnInfo(name="bz_item", kind=ColumnKind.STRING, desc="主营业务来源"),
        ColumnInfo(name="bz_sales", kind=ColumnKind.FLOAT, desc="主营业务收入(元)"),
        ColumnInfo(name="bz_profit", kind=ColumnKind.FLOAT, desc="主营业务利润(元)"),
        ColumnInfo(name="bz_cost", kind=ColumnKind.FLOAT, desc="主营业务成本(元)"),
        ColumnInfo(name="curr_type", kind=ColumnKind.STRING, desc="货币代码"),
        ColumnInfo(name="update_flag", kind=ColumnKind.STRING, desc="是否更新"),
    ],
)

from __future__ import annotations

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo

PROVIDER = "tushare"
SOURCE_NAME = "express_vip"
URL = "https://tushare.pro/document/2?doc_id=46"
ARGS = {
    "ts_code": {
        "type": ColumnKind.STRING,
        "required": "Y",
        "desc": "股票代码",
    },
    "ann_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "公告日期",
    },
    "start_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "公告开始日期",
    },
    "end_date": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "公告结束日期",
    },
    "year": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "年份(YYYY)",
    },
    "period": {
        "type": ColumnKind.STRING,
        "required": "N",
        "desc": "报告期(每个季度最后一天的日期)",
    },
}

# Exported constants
NAME = "companyoverview"
KEY = "/tushare/companyoverview"
PAGINATE = {
    "pagesize": 1000,
    "pagelimit": 1000,
}
SOURCE = TableInfo(
    desc="A股业绩快报数据（tushare格式）",
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
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING, desc="TS股票代码"),
        ColumnInfo(name="ann_date", kind=ColumnKind.STRING, desc="公告日期"),
        ColumnInfo(name="end_date", kind=ColumnKind.STRING, desc="报告期"),
        ColumnInfo(name="revenue", kind=ColumnKind.FLOAT, desc="营业收入(元)"),
        ColumnInfo(name="operate_profit", kind=ColumnKind.FLOAT, desc="营业利润(元)"),
        ColumnInfo(name="total_profit", kind=ColumnKind.FLOAT, desc="利润总额(元)"),
        ColumnInfo(name="n_income", kind=ColumnKind.FLOAT, desc="净利润(元)"),
        ColumnInfo(name="total_assets", kind=ColumnKind.FLOAT, desc="总资产(元)"),
        ColumnInfo(
            name="total_hldr_eqy_exc_min_int",
            kind=ColumnKind.FLOAT,
            desc="股东权益合计(不含少数股东权益)(元)",
        ),
        ColumnInfo(name="diluted_eps", kind=ColumnKind.FLOAT, desc="每股收益(摊薄)(元)"),
        ColumnInfo(name="diluted_roe", kind=ColumnKind.FLOAT, desc="净资产收益率(摊薄)(%)"),
        ColumnInfo(name="yoy_net_profit", kind=ColumnKind.FLOAT, desc="去年同期修正后净利润"),
        ColumnInfo(name="bps", kind=ColumnKind.FLOAT, desc="每股净资产"),
        ColumnInfo(name="yoy_sales", kind=ColumnKind.FLOAT, desc="同比增长率:营业收入"),
        ColumnInfo(name="yoy_op", kind=ColumnKind.FLOAT, desc="同比增长率:营业利润"),
        ColumnInfo(name="yoy_tp", kind=ColumnKind.FLOAT, desc="同比增长率:利润总额"),
        ColumnInfo(name="yoy_dedu_np", kind=ColumnKind.FLOAT, desc="同比增长率:归属母公司股东的净利润"),
        ColumnInfo(name="yoy_eps", kind=ColumnKind.FLOAT, desc="同比增长率:基本每股收益"),
        ColumnInfo(name="yoy_roe", kind=ColumnKind.FLOAT, desc="同比增减:加权平均净资产收益率"),
        ColumnInfo(name="growth_assets", kind=ColumnKind.FLOAT, desc="比年初增长率:总资产"),
        ColumnInfo(name="yoy_equity", kind=ColumnKind.FLOAT, desc="比年初增长率:归属母公司的股东权益"),
        ColumnInfo(name="growth_bps", kind=ColumnKind.FLOAT, desc="比年初增长率:归属于母公司股东的每股净资产"),
        ColumnInfo(name="or_last_year", kind=ColumnKind.FLOAT, desc="去年同期营业收入"),
        ColumnInfo(name="op_last_year", kind=ColumnKind.FLOAT, desc="去年同期营业利润"),
        ColumnInfo(name="tp_last_year", kind=ColumnKind.FLOAT, desc="去年同期利润总额"),
        ColumnInfo(name="np_last_year", kind=ColumnKind.FLOAT, desc="去年同期净利润"),
        ColumnInfo(name="eps_last_year", kind=ColumnKind.FLOAT, desc="去年同期每股收益"),
        ColumnInfo(name="open_net_assets", kind=ColumnKind.FLOAT, desc="期初净资产"),
        ColumnInfo(name="open_bps", kind=ColumnKind.FLOAT, desc="期初每股净资产"),
        ColumnInfo(name="perf_summary", kind=ColumnKind.STRING, desc="业绩简要说明"),
        ColumnInfo(name="is_audit", kind=ColumnKind.INTEGER, desc="是否审计: 1是 0否"),
        ColumnInfo(name="remark", kind=ColumnKind.STRING, desc="备注"),
    ],
)
TARGET = TableInfo(
    desc="A股业绩快报数据（标准格式）",
    meta={
        "provider": PROVIDER,
        "source": SOURCE_NAME,
        "url": URL,
        "args": ARGS,
        "type": "partitioned",
        "scale": "individual",
    },
    name=NAME,
    columns=[
        ColumnInfo(name="code", kind=ColumnKind.STRING, desc="股票代码"),
        ColumnInfo(name="date", kind=ColumnKind.STRING, desc="报告期日期"),
        ColumnInfo(name="datecode", kind=ColumnKind.STRING, desc="报告期日期代码"),
        ColumnInfo(name="ann_date", kind=ColumnKind.STRING, desc="公告日期"),
        ColumnInfo(name="revenue", kind=ColumnKind.FLOAT, desc="营业收入(元)"),
        ColumnInfo(name="operate_profit", kind=ColumnKind.FLOAT, desc="营业利润(元)"),
        ColumnInfo(name="total_profit", kind=ColumnKind.FLOAT, desc="利润总额(元)"),
        ColumnInfo(name="n_income", kind=ColumnKind.FLOAT, desc="净利润(元)"),
        ColumnInfo(name="total_assets", kind=ColumnKind.FLOAT, desc="总资产(元)"),
        ColumnInfo(
            name="total_hldr_eqy_exc_min_int",
            kind=ColumnKind.FLOAT,
            desc="股东权益合计(不含少数股东权益)(元)",
        ),
        ColumnInfo(name="diluted_eps", kind=ColumnKind.FLOAT, desc="每股收益(摊薄)(元)"),
        ColumnInfo(name="diluted_roe", kind=ColumnKind.FLOAT, desc="净资产收益率(摊薄)(%)"),
        ColumnInfo(name="yoy_net_profit", kind=ColumnKind.FLOAT, desc="去年同期修正后净利润"),
        ColumnInfo(name="bps", kind=ColumnKind.FLOAT, desc="每股净资产"),
        ColumnInfo(name="yoy_sales", kind=ColumnKind.FLOAT, desc="同比增长率:营业收入"),
        ColumnInfo(name="yoy_op", kind=ColumnKind.FLOAT, desc="同比增长率:营业利润"),
        ColumnInfo(name="yoy_tp", kind=ColumnKind.FLOAT, desc="同比增长率:利润总额"),
        ColumnInfo(name="yoy_dedu_np", kind=ColumnKind.FLOAT, desc="同比增长率:归属母公司股东的净利润"),
        ColumnInfo(name="yoy_eps", kind=ColumnKind.FLOAT, desc="同比增长率:基本每股收益"),
        ColumnInfo(name="yoy_roe", kind=ColumnKind.FLOAT, desc="同比增减:加权平均净资产收益率"),
        ColumnInfo(name="growth_assets", kind=ColumnKind.FLOAT, desc="比年初增长率:总资产"),
        ColumnInfo(name="yoy_equity", kind=ColumnKind.FLOAT, desc="比年初增长率:归属母公司的股东权益"),
        ColumnInfo(name="growth_bps", kind=ColumnKind.FLOAT, desc="比年初增长率:归属于母公司股东的每股净资产"),
        ColumnInfo(name="or_last_year", kind=ColumnKind.FLOAT, desc="去年同期营业收入"),
        ColumnInfo(name="op_last_year", kind=ColumnKind.FLOAT, desc="去年同期营业利润"),
        ColumnInfo(name="tp_last_year", kind=ColumnKind.FLOAT, desc="去年同期利润总额"),
        ColumnInfo(name="np_last_year", kind=ColumnKind.FLOAT, desc="去年同期净利润"),
        ColumnInfo(name="eps_last_year", kind=ColumnKind.FLOAT, desc="去年同期每股收益"),
        ColumnInfo(name="open_net_assets", kind=ColumnKind.FLOAT, desc="期初净资产"),
        ColumnInfo(name="open_bps", kind=ColumnKind.FLOAT, desc="期初每股净资产"),
        ColumnInfo(name="perf_summary", kind=ColumnKind.STRING, desc="业绩简要说明"),
        ColumnInfo(name="is_audit", kind=ColumnKind.INTEGER, desc="是否审计: 1是 0否"),
        ColumnInfo(name="remark", kind=ColumnKind.STRING, desc="备注"),
    ],
)

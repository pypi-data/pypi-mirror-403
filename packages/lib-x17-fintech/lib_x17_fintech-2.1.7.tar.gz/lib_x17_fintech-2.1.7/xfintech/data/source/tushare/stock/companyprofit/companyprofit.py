from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job import JobHouse
from xfintech.data.source.tushare.job import TushareJob
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.companyprofit.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class CompanyProfit(TushareJob):
    """
    描述:
    - 获取A股上市公司利润表数据
    - API文档: https://tushare.pro/document/2?doc_id=33
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 1000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'companyprofit'。
    - key: str, 作业键 '/tushare/companyprofit'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 必需, 股票代码（如'000001.SZ'）
        - start_date: str, 可选, 开始日期（YYYYMMDD）
        - end_date: str, 可选, 结束日期（YYYYMMDD）
        - period: str, 可选, 报告期（如20171231表示年报，20170630半年报）
        - year: str, 可选, 报告年度（YYYY）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=1000, pagelimit=100）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回利润表DataFrame。
    - _run(): 内部执行逻辑，处理日期参数。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.companyprofit import CompanyProfit

    session = Session(credential="your_token")
    profit = CompanyProfit(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "start_date": "20200101",
            "end_date": "20201231",
        },
    )
    df = profit.run()
    ```
    """

    def __init__(
        self,
        session: Session,
        params: Optional[Params | Dict[str, Any]] = None,
        coolant: Optional[Coolant | Dict[str, Any]] = None,
        retry: Optional[Retry | Dict[str, Any]] = None,
        cache: Optional[Cache | Dict[str, str] | bool] = None,
    ) -> None:
        super().__init__(
            name=NAME,
            key=KEY,
            session=session,
            source=SOURCE,
            target=TARGET,
            params=params,
            coolant=coolant,
            paginate=PAGINATE,
            retry=retry,
            cache=cache,
        )

    def _run(self) -> pd.DataFrame:
        cached = self._load_cache()
        if cached is not None:
            return cached

        # Prepare payload dict
        payload = self.params.to_dict()
        payload = self._parse_date_params(
            payload,
            keys=["ann_date", "start_date", "end_date"],
        )
        payload = self._parse_string_params(
            payload,
            keys=["ts_code"],
        )
        payload = self._parse_year_params(
            payload,
            key="year",
        )
        payload = self._parse_period_params(
            payload,
            key="period",
        )
        fields = SOURCE.list_column_names()
        payload["fields"] = ",".join(fields)

        # Fetch and transform data
        data = self._fetchall(
            api=self.connection.income_vip,
            **payload,
        )
        result = self.transform(data)
        self._save_cache(result)
        return result

    # Transform logic
    def transform(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        cols = self.target.list_column_names()
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)

        transformed = {}
        transformed["code"] = data["ts_code"].astype(str)
        transformed["datecode"] = data["end_date"].astype(str)
        transformed["date"] = pd.to_datetime(
            data["end_date"],
            format="%Y%m%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        # Convert other date fields
        for col in [
            "ann_date",
            "f_ann_date",
            "end_date",
        ]:
            transformed[col] = pd.to_datetime(
                data[col],
                format="%Y%m%d",
                errors="coerce",
            ).dt.strftime("%Y-%m-%d")

        # Convert string fields
        for col in [
            "report_type",
            "comp_type",
            "end_type",
            "update_flag",
        ]:
            transformed[col] = data[col].astype(str)

        # Convert numeric fields
        numeric_fields = [
            "basic_eps",
            "diluted_eps",
            "total_revenue",
            "revenue",
            "int_income",
            "prem_earned",
            "comm_income",
            "n_commis_income",
            "n_oth_income",
            "n_oth_b_income",
            "prem_income",
            "out_prem",
            "une_prem_reser",
            "reins_income",
            "n_sec_tb_income",
            "n_sec_uw_income",
            "n_asset_mg_income",
            "oth_b_income",
            "fv_value_chg_gain",
            "invest_income",
            "ass_invest_income",
            "forex_gain",
            "total_cogs",
            "oper_cost",
            "int_exp",
            "comm_exp",
            "biz_tax_surchg",
            "sell_exp",
            "admin_exp",
            "fin_exp",
            "assets_impair_loss",
            "prem_refund",
            "compens_payout",
            "reser_insur_liab",
            "div_payt",
            "reins_exp",
            "oper_exp",
            "compens_payout_refu",
            "insur_reser_refu",
            "reins_cost_refund",
            "other_bus_cost",
            "operate_profit",
            "non_oper_income",
            "non_oper_exp",
            "nca_disploss",
            "total_profit",
            "income_tax",
            "n_income",
            "n_income_attr_p",
            "minority_gain",
            "oth_compr_income",
            "t_compr_income",
            "compr_inc_attr_p",
            "compr_inc_attr_m_s",
            "ebit",
            "ebitda",
            "insurance_exp",
            "undist_profit",
            "distable_profit",
            "rd_exp",
            "fin_exp_int_exp",
            "fin_exp_int_inc",
            "transfer_surplus_rese",
            "transfer_housing_imprest",
            "transfer_oth",
            "adj_lossgain",
            "withdra_legal_surplus",
            "withdra_legal_pubfund",
            "withdra_biz_devfund",
            "withdra_rese_fund",
            "withdra_oth_ersu",
            "workers_welfare",
            "distr_profit_shrhder",
            "prfshare_payable_dvd",
            "comshare_payable_dvd",
            "capit_comstock_div",
            "net_after_nr_lp_correct",
            "credit_impa_loss",
            "net_expo_hedging_benefits",
            "oth_impair_loss_assets",
            "total_opcost",
            "amodcost_fin_assets",
            "oth_income",
            "asset_disp_income",
            "continued_net_profit",
            "end_net_profit",
        ]
        for col in numeric_fields:
            if col in data.columns:
                transformed[col] = pd.to_numeric(data[col], errors="coerce")

        # Ensure all target columns exist (add missing ones with NaN)
        for col in cols:
            if col not in transformed:
                transformed[col] = pd.NA

        # Select target columns, drop duplicates, and sort
        out = pd.DataFrame(transformed)
        out = out[cols].drop_duplicates()
        out = out.sort_values(by=["code", "date"])
        out = out.reset_index(drop=True)
        self.markpoint("transform[OK]")
        return out

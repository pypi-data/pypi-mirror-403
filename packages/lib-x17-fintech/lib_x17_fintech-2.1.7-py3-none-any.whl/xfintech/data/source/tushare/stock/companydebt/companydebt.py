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
from xfintech.data.source.tushare.stock.companydebt.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class CompanyDebt(TushareJob):
    """
    描述:
    - 获取A股上市公司资产负债表数据
    - API文档: https://tushare.pro/document/2?doc_id=36
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 1000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'companydebt'。
    - key: str, 作业键 '/tushare/companydebt'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 必需, 股票代码（如'000001.SZ'）
        - ann_date: str, 可选, 公告日期（YYYYMMDD）
        - start_date: str, 可选, 公告开始日期（YYYYMMDD）
        - end_date: str, 可选, 公告结束日期（YYYYMMDD）
        - period: str, 可选, 报告期（YYYYMMDD，如2017-01表示第一季度）
        - year: str, 可选, 报告年度（YYYY）
        - report_type: str, 可选, 报告类型（见文档说明）
        - comp_type: str, 可选, 公司类型（1一般工商业 2银行 3保险 4证券）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=1000, pagelimit=100）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回资产负债表DataFrame。
    - _run(): 内部执行逻辑，处理参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.companydebt import CompanyDebt

    session = Session(credential="your_token")
    debt = CompanyDebt(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "start_date": "20200101",
            "end_date": "20201231",
        },
    )
    df = debt.run()
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
            keys=["ts_code", "report_type", "comp_type"],
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
            api=self.connection.balancesheet_vip,
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
            "comp_type",
            "report_type",
            "end_type",
            "update_flag",
        ]:
            transformed[col] = data[col].astype(str)

        # Convert numeric fields
        numeric_fields = [
            "total_share",
            "cap_rese",
            "undistr_porfit",
            "surplus_rese",
            "special_rese",
            "money_cap",
            "trad_asset",
            "notes_receiv",
            "accounts_receiv",
            "oth_receiv",
            "prepayment",
            "div_receiv",
            "int_receiv",
            "inventories",
            "amor_exp",
            "nca_within_1y",
            "sett_rsrv",
            "loanto_oth_bank_fi",
            "premium_receiv",
            "reinsur_receiv",
            "reinsur_res_receiv",
            "pur_resale_fa",
            "oth_cur_assets",
            "total_cur_assets",
            "fa_avail_for_sale",
            "htm_invest",
            "lt_eqt_invest",
            "invest_real_estate",
            "time_deposits",
            "oth_assets",
            "lt_rec",
            "fix_assets",
            "cip",
            "const_materials",
            "fixed_assets_disp",
            "produc_bio_assets",
            "oil_and_gas_assets",
            "intan_assets",
            "r_and_d",
            "goodwill",
            "lt_amor_exp",
            "defer_tax_assets",
            "decr_in_disbur",
            "oth_nca",
            "total_nca",
            "cash_reser_cb",
            "depos_in_oth_bfi",
            "prec_metals",
            "deriv_assets",
            "rr_reins_une_prem",
            "rr_reins_outstd_cla",
            "rr_reins_lins_liab",
            "rr_reins_lthins_liab",
            "refund_depos",
            "ph_pledge_loans",
            "refund_cap_depos",
            "indep_acct_assets",
            "client_depos",
            "client_prov",
            "transac_seat_fee",
            "invest_as_receiv",
            "total_assets",
            "lt_borr",
            "st_borr",
            "cb_borr",
            "depos_ib_deposits",
            "loan_oth_bank",
            "trading_fl",
            "notes_payable",
            "acct_payable",
            "adv_receipts",
            "sold_for_repur_fa",
            "comm_payable",
            "payroll_payable",
            "taxes_payable",
            "int_payable",
            "div_payable",
            "oth_payable",
            "acc_exp",
            "deferred_inc",
            "st_bonds_payable",
            "payable_to_reinsurer",
            "rsrv_insur_cont",
            "acting_trading_sec",
            "acting_uw_sec",
            "non_cur_liab_due_1y",
            "oth_cur_liab",
            "total_cur_liab",
            "bond_payable",
            "lt_payable",
            "specific_payables",
            "estimated_liab",
            "defer_tax_liab",
            "defer_inc_non_cur_liab",
            "oth_ncl",
            "total_ncl",
            "depos_oth_bfi",
            "deriv_liab",
            "depos",
            "agency_bus_liab",
            "oth_liab",
            "prem_receiv_adva",
            "depos_received",
            "ph_invest",
            "reser_une_prem",
            "reser_outstd_claims",
            "reser_lins_liab",
            "reser_lthins_liab",
            "indept_acc_liab",
            "pledge_borr",
            "indem_payable",
            "policy_div_payable",
            "total_liab",
            "treasury_share",
            "ordin_risk_reser",
            "forex_differ",
            "invest_loss_unconf",
            "minority_int",
            "total_hldr_eqy_exc_min_int",
            "total_hldr_eqy_inc_min_int",
            "total_liab_hldr_eqy",
            "lt_payroll_payable",
            "oth_comp_income",
            "oth_eqt_tools",
            "oth_eqt_tools_p_shr",
            "lending_funds",
            "acc_receivable",
            "st_fin_payable",
            "payables",
            "hfs_assets",
            "hfs_sales",
            "cost_fin_assets",
            "fair_value_fin_assets",
            "cip_total",
            "oth_pay_total",
            "long_pay_total",
            "debt_invest",
            "oth_debt_invest",
            "oth_eq_invest",
            "oth_illiq_fin_assets",
            "oth_eq_ppbond",
            "receiv_financing",
            "use_right_assets",
            "lease_liab",
            "contract_assets",
            "contract_liab",
            "accounts_receiv_bill",
            "accounts_pay",
            "oth_rcv_total",
            "fix_assets_total",
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

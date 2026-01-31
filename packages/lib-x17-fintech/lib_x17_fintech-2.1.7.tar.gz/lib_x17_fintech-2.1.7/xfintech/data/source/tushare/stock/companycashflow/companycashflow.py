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
from xfintech.data.source.tushare.stock.companycashflow.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)


@JobHouse.register(KEY, alias=KEY)
class CompanyCashflow(TushareJob):
    """
    描述:
    - 获取A股上市公司现金流量表数据
    - API文档: https://tushare.pro/document/2?doc_id=44
    - SCALE: CrossSection & Individual
    - TYPE: Partitioned
    - PAGINATE: 1000 rows / 1000 pages

    属性:
    - name: str, 作业名称 'companycashflow'。
    - key: str, 作业键 '/tushare/companycashflow'。
    - session: Session, Tushare会话对象。
    - source: TableInfo, 源表信息（Tushare原始格式）。
    - target: TableInfo, 目标表信息（转换后格式）。
    - params: Params, 查询参数。
        - ts_code: str, 必需, 股票代码（如'000001.SZ'）
        - ann_date: str, 可选, 公告日期（YYYYMMDD）
        - start_date: str, 可选, 公告开始日期（YYYYMMDD）
        - end_date: str, 可选, 公告结束日期（YYYYMMDD）
        - period: str, 可选, 报告期（YYYYMMDD，如2017-01表示第一季度）
        - report_type: str, 可选, 报告类型（见文档说明）
        - comp_type: str, 可选, 公司类型（1一般工商业 2银行 3保险 4证券）
    - coolant: Coolant, 请求冷却控制。
    - paginate: Paginate, 分页控制（pagesize=1000, pagelimit=100）。
    - retry: Retry, 重试策略。
    - cache: Cache, 缓存管理。

    方法:
    - run(): 执行作业，返回现金流量表DataFrame。
    - _run(): 内部执行逻辑，处理参数并调用API。
    - transform(data): 转换数据格式，将源格式转为目标格式。

    例子:
    ```python
    from xfintech.data.source.tushare.session import Session
    from xfintech.data.source.tushare.stock.companycashflow import CompanyCashflow

    session = Session(credential="your_token")
    cashflow = CompanyCashflow(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "start_date": "20200101",
            "end_date": "20201231",
        },
    )
    df = cashflow.run()
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
            api=self.connection.cashflow_vip,
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
            "net_profit",
            "finan_exp",
            "c_fr_sale_sg",
            "recp_tax_rends",
            "n_depos_incr_fi",
            "n_incr_loans_cb",
            "n_inc_borr_oth_fi",
            "prem_fr_orig_contr",
            "n_incr_insured_dep",
            "n_reinsur_prem",
            "n_incr_disp_tfa",
            "ifc_cash_incr",
            "n_incr_disp_faas",
            "n_incr_loans_oth_bank",
            "n_cap_incr_repur",
            "c_fr_oth_operate_a",
            "c_inf_fr_operate_a",
            "c_paid_goods_s",
            "c_paid_to_for_empl",
            "c_paid_for_taxes",
            "n_incr_clt_loan_adv",
            "n_incr_dep_cbob",
            "c_pay_claims_orig_inco",
            "pay_handling_chrg",
            "pay_comm_insur_plcy",
            "oth_cash_pay_oper_act",
            "st_cash_out_act",
            "n_cashflow_act",
            "oth_recp_ral_inv_act",
            "c_disp_withdrwl_invest",
            "c_recp_return_invest",
            "n_recp_disp_fiolta",
            "n_recp_disp_sobu",
            "stot_inflows_inv_act",
            "c_pay_acq_const_fiolta",
            "c_paid_invest",
            "n_disp_subs_oth_biz",
            "oth_pay_ral_inv_act",
            "n_incr_pledge_loan",
            "stot_out_inv_act",
            "n_cashflow_inv_act",
            "c_recp_borrow",
            "proc_issue_bonds",
            "oth_cash_recp_ral_fnc_act",
            "stot_cash_in_fnc_act",
            "free_cashflow",
            "c_prepay_amt_borr",
            "c_pay_dist_dpcp_int_exp",
            "incl_dvd_profit_paid_sc_ms",
            "oth_cashpay_ral_fnc_act",
            "stot_cashout_fnc_act",
            "n_cash_flows_fnc_act",
            "eff_fx_flu_cash",
            "n_incr_cash_cash_equ",
            "c_cash_equ_beg_period",
            "c_cash_equ_end_period",
            "c_recp_cap_contrib",
            "incl_cash_rec_saims",
            "uncon_invest_loss",
            "prov_depr_assets",
            "depr_fa_coga_dpba",
            "amort_intang_assets",
            "lt_amort_deferred_exp",
            "decr_deferred_exp",
            "incr_acc_exp",
            "loss_disp_fiolta",
            "loss_scr_fa",
            "loss_fv_chg",
            "invest_loss",
            "decr_def_inc_tax_assets",
            "incr_def_inc_tax_liab",
            "decr_inventories",
            "decr_oper_payable",
            "incr_oper_payable",
            "others",
            "im_net_cashflow_oper_act",
            "conv_debt_into_cap",
            "conv_copbonds_due_within_1y",
            "fa_fnc_leases",
            "im_n_incr_cash_equ",
            "net_dism_capital_add",
            "net_cash_rece_sec",
            "credit_impa_loss",
            "use_right_asset_dep",
            "oth_loss_asset",
            "end_bal_cash",
            "beg_bal_cash",
            "end_bal_cash_equ",
            "beg_bal_cash_equ",
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

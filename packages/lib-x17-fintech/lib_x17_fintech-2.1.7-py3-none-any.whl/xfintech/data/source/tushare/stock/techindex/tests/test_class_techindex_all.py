from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.techindex import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
    TechIndex,
)
from xfintech.data.source.tushare.stock.techindex.constant import (
    _IN_BFQ_COLS,
    _IN_HFQ_COLS,
    _IN_MAIN_COLS,
    _IN_QFQ_COLS,
    _OUT_BA_COLS,
    _OUT_FA_COLS,
    _OUT_MAIN_COLS,
    _OUT_NA_COLS,
)


# ================= Fixtures =================
@pytest.fixture
def mock_session():
    """创建模拟的Tushare会话对象"""
    session = MagicMock()

    # Mock the connection object
    mock_connection = MagicMock()
    mock_connection.stk_factor_pro = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_tushare_data():
    """创建样本Tushare格式数据"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "trade_date": ["20240101", "20240101"],
            "open": [10.5, 20.3],
            "high": [11.0, 21.0],
            "low": [10.2, 20.0],
            "close": [10.8, 20.8],
            "change": [0.3, 0.5],
            "pct_chg": [2.86, 2.46],
            "vol": [100000.0, 200000.0],
            "amount": [108000.0, 416000.0],
            "turnover_rate": [1.5, 2.3],
            "turnover_rate_f": [1.2, 2.0],
            "volume_ratio": [1.1, 1.3],
            "pe": [15.5, 18.2],
            "pe_ttm": [16.0, 18.5],
            "pb": [2.5, 3.2],
            "ps": [3.5, 4.2],
            "ps_ttm": [3.8, 4.5],
            "dv_ratio": [2.5, 3.0],
            "dv_ttm": [2.8, 3.2],
            "total_share": [1000000.0, 2000000.0],
            "float_share": [800000.0, 1600000.0],
            "free_share": [700000.0, 1400000.0],
            "total_mv": [10800000.0, 41600000.0],
            "circ_mv": [8640000.0, 33280000.0],
            "adj_factor": [1.0, 1.0],
            "downdays": [0.0, 1.0],
            "updays": [3.0, 2.0],
            "lowdays": [5.0, 10.0],
            "topdays": [15.0, 20.0],
            # BFQ columns
            "macd_bfq": [0.05, 0.08],
            "macd_dif_bfq": [0.03, 0.05],
            "macd_dea_bfq": [0.02, 0.03],
            # HFQ columns
            "macd_hfq": [0.06, 0.09],
            "macd_dif_hfq": [0.04, 0.06],
            "macd_dea_hfq": [0.02, 0.03],
            # QFQ columns
            "macd_qfq": [0.055, 0.085],
            "macd_dif_qfq": [0.035, 0.055],
            "macd_dea_qfq": [0.02, 0.03],
        }
    )


@pytest.fixture
def sample_transformed_data():
    """创建样本转换后数据"""
    return pd.DataFrame(
        {
            "code": ["000001.SZ", "000002.SZ"],
            "date": ["2024-01-01", "2024-01-01"],
            "datecode": ["20240101", "20240101"],
            "open": [10.5, 20.3],
            "high": [11.0, 21.0],
            "low": [10.2, 20.0],
            "close": [10.8, 20.8],
            "change": [0.3, 0.5],
            "percent_change": [2.86, 2.46],
            "volume": [100000.0, 200000.0],
            "amount": [108000.0, 416000.0],
        }
    )


# ================= 初始化测试 =================
class TestTechIndexInitialization:
    """测试TechIndex类的初始化"""

    def test_init_with_minimal_params(self, mock_session):
        """测试使用最少参数初始化"""
        job = TechIndex(session=mock_session)
        assert job.name == NAME
        assert job.key == KEY
        assert job.source == SOURCE
        assert job.target == TARGET

    def test_init_with_params_dict(self, mock_session):
        """测试使用字典参数初始化"""
        params = {"ts_code": "000001.SZ"}
        job = TechIndex(session=mock_session, params=params)
        assert job.params.get("ts_code") == "000001.SZ"

    def test_init_with_date_params(self, mock_session):
        """测试使用日期参数初始化"""
        params = {
            "ts_code": "000001.SZ",
            "start_date": "20240101",
            "end_date": "20240131",
        }
        job = TechIndex(session=mock_session, params=params)
        assert job.params.get("start_date") == "20240101"
        assert job.params.get("end_date") == "20240131"

    def test_init_with_cache_enabled(self, mock_session):
        """测试启用缓存初始化"""
        job = TechIndex(session=mock_session, cache=True)
        assert job.cache is not None

    def test_init_with_cache_disabled(self, mock_session):
        """测试禁用缓存初始化"""
        job = TechIndex(session=mock_session, cache=False)
        assert job.cache is None

    def test_paginate_settings(self, mock_session):
        """测试分页设置"""
        job = TechIndex(session=mock_session)
        assert job.paginate.pagesize == PAGINATE["pagesize"]
        assert job.paginate.pagelimit == PAGINATE["pagelimit"]


# ================= 转换测试 =================
class TestTechIndexTransform:
    """测试TechIndex的数据转换功能"""

    def test_transform_main_with_valid_data(self, mock_session, sample_tushare_data):
        """测试主数据转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_main(sample_tushare_data)

        assert not result.empty
        assert len(result) == 2
        assert "code" in result.columns
        assert "date" in result.columns
        assert "datecode" in result.columns
        assert result["code"].iloc[0] == "000001.SZ"
        assert result["date"].iloc[0] == "2024-01-01"
        assert result["datecode"].iloc[0] == "20240101"

    def test_transform_main_with_empty_data(self, mock_session):
        """测试空数据的主数据转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_main(pd.DataFrame())

        assert result.empty
        assert len(result.columns) == len(_OUT_MAIN_COLS)

    def test_transform_na_with_valid_data(self, mock_session, sample_tushare_data):
        """测试不复权因子转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_na(sample_tushare_data)

        assert not result.empty
        assert len(result) == 2
        assert "open" in result.columns
        assert "macd" in result.columns
        assert result["macd"].iloc[0] == 0.05

    def test_transform_na_with_empty_data(self, mock_session):
        """测试空数据的不复权因子转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_na(pd.DataFrame())

        assert result.empty
        assert len(result.columns) == len(_OUT_NA_COLS)

    def test_transform_ba_with_valid_data(self, mock_session, sample_tushare_data):
        """测试后复权因子转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_ba(sample_tushare_data)

        assert not result.empty
        assert len(result) == 2
        # BA transform adds ba_ prefix
        assert "ba_macd" in result.columns
        assert result["ba_macd"].iloc[0] == 0.06

    def test_transform_ba_with_empty_data(self, mock_session):
        """测试空数据的后复权因子转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_ba(pd.DataFrame())

        assert result.empty
        assert len(result.columns) == len(_OUT_BA_COLS)

    def test_transform_fa_with_valid_data(self, mock_session, sample_tushare_data):
        """测试前复权因子转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_fa(sample_tushare_data)

        assert not result.empty
        assert len(result) == 2
        # FA transform adds fa_ prefix
        assert "fa_macd" in result.columns
        assert result["fa_macd"].iloc[0] == 0.055

    def test_transform_fa_with_empty_data(self, mock_session):
        """测试空数据的前复权因子转换"""
        job = TechIndex(session=mock_session)
        result = job._transform_fa(pd.DataFrame())

        assert result.empty
        assert len(result.columns) == len(_OUT_FA_COLS)

    def test_transform_complete_with_valid_data(self, mock_session, sample_tushare_data):
        """测试完整数据转换"""
        job = TechIndex(session=mock_session)
        result = job.transform(sample_tushare_data)

        assert not result.empty
        assert len(result) == 2
        # Check all column groups are present
        assert "code" in result.columns  # main
        assert "open" in result.columns  # na
        assert "ba_macd" in result.columns  # ba (with prefix)
        assert "fa_macd" in result.columns  # fa (with prefix)
        # Total columns should match target
        assert len(result.columns) == len(TARGET.list_column_names())

    def test_transform_complete_with_empty_data(self, mock_session):
        """测试空数据的完整转换"""
        job = TechIndex(session=mock_session)
        result = job.transform(pd.DataFrame())

        assert result.empty
        assert len(result.columns) == len(TARGET.list_column_names())

    def test_transform_preserves_column_order(self, mock_session, sample_tushare_data):
        """测试转换保持列顺序"""
        job = TechIndex(session=mock_session)
        result = job.transform(sample_tushare_data)

        expected_columns = TARGET.list_column_names()
        assert list(result.columns) == expected_columns


# ================= Run方法测试 =================
class TestTechIndexRun:
    """测试TechIndex的run方法"""

    def test_run_with_ts_code(self, mock_session, sample_tushare_data):
        """测试使用股票代码运行"""
        job = TechIndex(session=mock_session, params={"ts_code": "000001.SZ"}, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)
            assert not result.empty

    def test_run_with_trade_date_string(self, mock_session, sample_tushare_data):
        """测试使用字符串交易日期运行"""
        job = TechIndex(session=mock_session, params={"trade_date": "20240101"}, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)

    def test_run_with_trade_date_datetime(self, mock_session, sample_tushare_data):
        """测试使用datetime交易日期运行"""
        job = TechIndex(
            session=mock_session,
            params={"trade_date": datetime(2024, 1, 1)},
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)

    def test_run_with_trade_date_date(self, mock_session, sample_tushare_data):
        """测试使用date交易日期运行"""
        job = TechIndex(session=mock_session, params={"trade_date": date(2024, 1, 1)}, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)

    def test_run_with_date_range_string(self, mock_session, sample_tushare_data):
        """测试使用字符串日期范围运行"""
        job = TechIndex(
            session=mock_session,
            params={"start_date": "20240101", "end_date": "20240131"},
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)

    def test_run_with_date_range_datetime(self, mock_session, sample_tushare_data):
        """测试使用datetime日期范围运行"""
        job = TechIndex(
            session=mock_session,
            params={
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 1, 31),
            },
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)

    def test_run_with_date_range_date(self, mock_session, sample_tushare_data):
        """测试使用date日期范围运行"""
        job = TechIndex(
            session=mock_session,
            params={"start_date": date(2024, 1, 1), "end_date": date(2024, 1, 31)},
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)

    def test_run_with_mixed_date_formats(self, mock_session, sample_tushare_data):
        """测试使用混合日期格式运行"""
        job = TechIndex(
            session=mock_session,
            params={"start_date": date(2024, 1, 1), "end_date": "20240131"},
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)

    def test_run_returns_dataframe(self, mock_session, sample_tushare_data):
        """测试run方法返回DataFrame类型"""
        job = TechIndex(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.run()
            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0


# ================= 缓存测试 =================
class TestTechIndexCache:
    """测试TechIndex的缓存功能"""

    def test_cache_disabled_by_default(self, mock_session):
        """测试默认不启用缓存"""
        job = TechIndex(session=mock_session, cache=False)
        assert job.cache is None

    def test_cache_load_returns_none_when_disabled(self, mock_session):
        """测试禁用缓存时_load_cache返回None"""
        job = TechIndex(session=mock_session, cache=False)
        result = job._load_cache()
        assert result is None

    def test_cache_save_does_nothing_when_disabled(self, mock_session, sample_transformed_data):
        """测试禁用缓存时_save_cache不执行操作"""
        job = TechIndex(session=mock_session, cache=False)
        # Should not raise any errors
        job._save_cache(sample_transformed_data)

    def test_run_with_cache_enabled(self, mock_session, sample_tushare_data):
        """测试启用缓存运行"""
        job = TechIndex(
            session=mock_session,
            params={"ts_code": "000001.SZ"},
            cache={"store": "memory"},
        )

        with (
            patch.object(job, "_fetchall", return_value=sample_tushare_data),
            patch.object(job, "_load_cache", return_value=None),
            patch.object(job, "_save_cache") as mock_save,
        ):
            result = job.run()
            assert isinstance(result, pd.DataFrame)
            mock_save.assert_called_once()


# ================= Slice方法测试 =================
class TestTechIndexSlice:
    """测试TechIndex的slice方法"""

    def test_slice_main_without_data(self, mock_session, sample_tushare_data):
        """测试slice_main方法不传入数据"""
        job = TechIndex(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.slice_main()
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert len(result.columns) == len(_OUT_MAIN_COLS)
            assert "code" in result.columns
            assert "date" in result.columns

    def test_slice_main_with_data(self, mock_session, sample_tushare_data):
        """测试slice_main方法传入数据"""
        job = TechIndex(session=mock_session, cache=False)
        full_data = job.transform(sample_tushare_data)
        result = job.slice_main(data=full_data)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result.columns) == len(_OUT_MAIN_COLS)

    def test_slice_na_without_data(self, mock_session, sample_tushare_data):
        """测试slice_na方法不传入数据"""
        job = TechIndex(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.slice_na()
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert len(result.columns) == len(_OUT_MAIN_COLS + _OUT_NA_COLS)
            assert "open" in result.columns
            assert "macd" in result.columns

    def test_slice_na_with_data(self, mock_session, sample_tushare_data):
        """测试slice_na方法传入数据"""
        job = TechIndex(session=mock_session, cache=False)
        full_data = job.transform(sample_tushare_data)
        result = job.slice_na(data=full_data)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result.columns) == len(_OUT_MAIN_COLS + _OUT_NA_COLS)

    def test_slice_ba_without_data(self, mock_session, sample_tushare_data):
        """测试slice_ba方法不传入数据"""
        job = TechIndex(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.slice_ba()
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert len(result.columns) == len(_OUT_MAIN_COLS + _OUT_BA_COLS)
            assert "ba_macd" in result.columns

    def test_slice_ba_with_data(self, mock_session, sample_tushare_data):
        """测试slice_ba方法传入数据"""
        job = TechIndex(session=mock_session, cache=False)
        full_data = job.transform(sample_tushare_data)
        result = job.slice_ba(data=full_data)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result.columns) == len(_OUT_MAIN_COLS + _OUT_BA_COLS)

    def test_slice_fa_without_data(self, mock_session, sample_tushare_data):
        """测试slice_fa方法不传入数据"""
        job = TechIndex(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            result = job.slice_fa()
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert len(result.columns) == len(_OUT_MAIN_COLS + _OUT_FA_COLS)
            assert "fa_macd" in result.columns

    def test_slice_fa_with_data(self, mock_session, sample_tushare_data):
        """测试slice_fa方法传入数据"""
        job = TechIndex(session=mock_session, cache=False)
        full_data = job.transform(sample_tushare_data)
        result = job.slice_fa(data=full_data)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result.columns) == len(_OUT_MAIN_COLS + _OUT_FA_COLS)

    def test_slice_with_empty_data(self, mock_session):
        """测试slice方法处理空数据"""
        job = TechIndex(session=mock_session, cache=False)
        empty_data = job.transform(pd.DataFrame())

        result_main = job.slice_main(data=empty_data)
        result_na = job.slice_na(data=empty_data)
        result_ba = job.slice_ba(data=empty_data)
        result_fa = job.slice_fa(data=empty_data)

        assert result_main.empty
        assert result_na.empty
        assert result_ba.empty
        assert result_fa.empty


# ================= 集成测试 =================
class TestTechIndexIntegration:
    """TechIndex的集成测试"""

    def test_complete_workflow(self, mock_session, sample_tushare_data):
        """测试完整工作流程"""
        job = TechIndex(
            session=mock_session,
            params={"ts_code": "000001.SZ", "start_date": "20240101", "end_date": "20240131"},
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_tushare_data):
            # 运行并获取完整数据
            full_result = job.run()
            assert isinstance(full_result, pd.DataFrame)
            assert not full_result.empty

            # 获取各部分数据
            main_result = job.slice_main(data=full_result)
            na_result = job.slice_na(data=full_result)
            ba_result = job.slice_ba(data=full_result)
            fa_result = job.slice_fa(data=full_result)

            # 验证各部分
            assert not main_result.empty
            assert not na_result.empty
            assert not ba_result.empty
            assert not fa_result.empty

            # 验证行数一致
            assert len(main_result) == len(na_result) == len(ba_result) == len(fa_result)

    def test_module_constants(self):
        """测试模块常量"""
        assert NAME == "techindex"
        assert KEY == "/tushare/techindex"
        assert PAGINATE["pagesize"] == 10000
        assert PAGINATE["pagelimit"] == 1000

    def test_source_table_structure(self):
        """测试源表结构"""
        assert SOURCE.desc == "A股股票技术面因子数据（Tushare格式）"
        assert SOURCE.meta["provider"] == "tushare"
        assert SOURCE.meta["source"] == "stk_factor_pro"
        total_cols = len(_IN_MAIN_COLS) + len(_IN_BFQ_COLS) + len(_IN_HFQ_COLS) + len(_IN_QFQ_COLS)
        assert len(SOURCE.columns) == total_cols

    def test_target_table_structure(self):
        """测试目标表结构"""
        assert TARGET.desc == "A股股票技术面因子数据（xfintech格式）"
        assert TARGET.meta["key"] == KEY
        assert TARGET.meta["name"] == NAME
        total_cols = len(_OUT_MAIN_COLS) + len(_OUT_NA_COLS) + len(_OUT_BA_COLS) + len(_OUT_FA_COLS)
        assert len(TARGET.columns) == total_cols

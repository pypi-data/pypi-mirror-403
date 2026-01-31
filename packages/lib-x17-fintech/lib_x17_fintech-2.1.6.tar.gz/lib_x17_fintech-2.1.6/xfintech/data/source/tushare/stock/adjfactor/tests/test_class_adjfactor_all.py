from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.adjfactor import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
    AdjFactor,
)


@pytest.fixture
def mock_session():
    session = MagicMock()
    mock_connection = MagicMock()
    mock_connection.adj_factor = MagicMock()
    session.connection = mock_connection
    return session


@pytest.fixture
def sample_source_data():
    """创建样本源数据"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "trade_date": ["20241201", "20241201", "20241201"],
            "adj_factor": [1.234567, 2.345678, 3.456789],
        }
    )


# Initialization Tests


class TestAdjFactorInitialization:
    def test_init_basic(self, mock_session):
        """测试基础初始化"""
        job = AdjFactor(session=mock_session)
        assert job.name == NAME
        assert job.key == KEY
        assert job.source == SOURCE
        assert job.target == TARGET

    def test_init_with_params(self, mock_session):
        """测试带参数的初始化"""
        params = {"ts_code": "000001.SZ"}
        job = AdjFactor(session=mock_session, params=params)
        assert job.params.get("ts_code") == "000001.SZ"

    def test_init_with_all_components(self, mock_session):
        """测试带所有组件的初始化"""
        params = {"ts_code": "000001.SZ"}
        coolant = {"interval": 0.1}
        retry = {"max_retries": 3}

        job = AdjFactor(
            session=mock_session,
            params=params,
            coolant=coolant,
            retry=retry,
            cache=False,
        )

        assert job.name == NAME
        assert job.key == KEY
        assert job.params.get("ts_code") == "000001.SZ"

    def test_name_constant(self):
        """测试NAME常量"""
        assert NAME == "adjfactor"

    def test_key_constant(self):
        """测试KEY常量"""
        assert KEY == "/tushare/adjfactor"

    def test_paginate_constant(self):
        """测试PAGINATE常量"""
        assert PAGINATE["pagesize"]
        assert PAGINATE["pagelimit"]

    def test_source_schema(self):
        """测试SOURCE表结构"""
        columns_list = SOURCE.list_columns()
        assert columns_list is not None
        assert len(columns_list) == 3
        column_names = [col.name for col in columns_list]
        assert "ts_code" in column_names
        assert "trade_date" in column_names
        assert "adj_factor" in column_names

    def test_target_schema(self):
        """测试TARGET表结构"""
        columns_list = TARGET.list_columns()
        assert columns_list is not None
        assert len(columns_list) == 4
        column_names = [col.name for col in columns_list]
        assert "code" in column_names
        assert "date" in column_names
        assert "datecode" in column_names
        assert "adj_factor" in column_names


# Transform Tests


class TestAdjFactorTransform:
    def test_transform_basic(self, mock_session, sample_source_data):
        """测试基本转换"""
        job = AdjFactor(session=mock_session)
        result = job.transform(sample_source_data)

        assert "code" in result.columns
        assert "date" in result.columns
        assert "datecode" in result.columns
        assert "adj_factor" in result.columns
        assert len(result) == 3

    def test_transform_date_conversion(self, mock_session, sample_source_data):
        """测试日期转换"""
        job = AdjFactor(session=mock_session)
        result = job.transform(sample_source_data)

        # Check date format YYYY-MM-DD
        assert result["date"].iloc[0] == "2024-12-01"
        # Check datecode format YYYYMMDD
        assert result["datecode"].iloc[0] == "20241201"

    def test_transform_adj_factor_values(self, mock_session, sample_source_data):
        """测试复权因子值保持不变"""
        job = AdjFactor(session=mock_session)
        result = job.transform(sample_source_data)

        assert result["adj_factor"].iloc[0] == 1.234567
        assert result["adj_factor"].iloc[1] == 2.345678
        assert result["adj_factor"].iloc[2] == 3.456789

    def test_transform_empty_data(self, mock_session):
        """测试空数据转换"""
        job = AdjFactor(session=mock_session)
        empty_df = pd.DataFrame()
        result = job.transform(empty_df)

        assert result.empty
        assert "code" in result.columns

    def test_transform_none_data(self, mock_session):
        """测试None数据转换"""
        job = AdjFactor(session=mock_session)
        result = job.transform(None)

        assert result.empty
        assert "code" in result.columns

    def test_transform_invalid_dates(self, mock_session):
        """测试无效日期处理"""
        job = AdjFactor(session=mock_session)
        data = pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "trade_date": ["invalid"],
                "adj_factor": [1.0],
            }
        )
        result = job.transform(data)

        # Should handle invalid dates gracefully
        assert len(result) == 1
        assert pd.isna(result["date"].iloc[0]) or result["date"].iloc[0] == "NaT"

    def test_transform_duplicates_removed(self, mock_session):
        """测试重复数据删除"""
        job = AdjFactor(session=mock_session)
        data = pd.DataFrame(
            {
                "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
                "trade_date": ["20241201", "20241201", "20241201"],
                "adj_factor": [1.0, 1.0, 2.0],
            }
        )
        result = job.transform(data)

        # Duplicates should be removed
        assert len(result) == 2

    def test_transform_sorting(self, mock_session):
        """测试数据排序"""
        job = AdjFactor(session=mock_session)
        data = pd.DataFrame(
            {
                "ts_code": ["600000.SH", "000001.SZ", "000002.SZ"],
                "trade_date": ["20241203", "20241201", "20241202"],
                "adj_factor": [3.0, 1.0, 2.0],
            }
        )
        result = job.transform(data)

        # Should be sorted by code and date
        assert result["code"].iloc[0] == "000001.SZ"
        assert result["code"].iloc[1] == "000002.SZ"
        assert result["code"].iloc[2] == "600000.SH"


# Run Tests


class TestAdjFactorRun:
    def test_run_basic(self, mock_session, sample_source_data):
        """测试基本运行"""
        job = AdjFactor(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) == 3
            assert "code" in result.columns

    def test_run_with_ts_code(self, mock_session, sample_source_data):
        """测试指定股票代码运行"""
        params = {"ts_code": "000001.SZ"}
        job = AdjFactor(session=mock_session, params=params, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) > 0

    def test_run_with_trade_date_string(self, mock_session, sample_source_data):
        """测试交易日期（字符串）运行"""
        params = {"trade_date": "20241201"}
        job = AdjFactor(session=mock_session, params=params, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) > 0

    def test_run_with_trade_date_datetime(self, mock_session, sample_source_data):
        """测试交易日期（datetime）运行"""
        params = {"trade_date": datetime(2024, 12, 1)}
        job = AdjFactor(session=mock_session, params=params, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) > 0

    def test_run_with_trade_date_date(self, mock_session, sample_source_data):
        """测试交易日期（date）运行"""
        params = {"trade_date": date(2024, 12, 1)}
        job = AdjFactor(session=mock_session, params=params, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) > 0

    def test_run_with_date_range_string(self, mock_session, sample_source_data):
        """测试日期区间（字符串）运行"""
        params = {"start_date": "20241101", "end_date": "20241231"}
        job = AdjFactor(session=mock_session, params=params, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) > 0

    def test_run_with_date_range_datetime(self, mock_session, sample_source_data):
        """测试日期区间（datetime）运行"""
        params = {
            "start_date": datetime(2024, 11, 1),
            "end_date": datetime(2024, 12, 31),
        }
        job = AdjFactor(session=mock_session, params=params, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) > 0

    def test_run_with_date_range_date(self, mock_session, sample_source_data):
        """测试日期区间（date）运行"""
        params = {"start_date": date(2024, 11, 1), "end_date": date(2024, 12, 31)}
        job = AdjFactor(session=mock_session, params=params, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) > 0

    def test_run_calls_transform(self, mock_session, sample_source_data):
        """测试运行时调用transform"""
        job = AdjFactor(session=mock_session, cache=False)

        with (
            patch.object(job, "_fetchall", return_value=sample_source_data),
            patch.object(job, "transform", wraps=job.transform) as mock_transform,
        ):
            job.run()
            mock_transform.assert_called_once()


# Cache Tests


class TestAdjFactorCache:
    def test_cache_persistence(self, mock_session, sample_source_data):
        """测试缓存持久性"""
        job = AdjFactor(session=mock_session, cache=True)

        with (
            patch.object(job, "_fetchall", return_value=sample_source_data),
            patch.object(job, "_load_cache", return_value=None),
            patch.object(job, "_save_cache") as mock_save,
        ):
            job.run()
            mock_save.assert_called_once()

    def test_run_without_cache(self, mock_session, sample_source_data):
        """测试不使用缓存运行"""
        job = AdjFactor(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()
            assert len(result) == 3


# Integration Tests


class TestAdjFactorIntegration:
    def test_full_workflow(self, mock_session, sample_source_data):
        """测试完整工作流程"""
        job = AdjFactor(
            session=mock_session,
            params={"ts_code": "000001.SZ"},
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            # Run job
            result = job.run()
            assert not result.empty

    def test_large_dataset_handling(self, mock_session):
        """测试大数据集处理"""
        # Create large dataset
        large_data = pd.DataFrame(
            {
                "ts_code": [f"{i:06d}.SZ" for i in range(1000)],
                "trade_date": ["20241201"] * 1000,
                "adj_factor": [1.0 + i * 0.001 for i in range(1000)],
            }
        )
        job = AdjFactor(session=mock_session, cache=False)
        with patch.object(job, "_fetchall", return_value=large_data):
            result = job.run()
            assert len(result) == 1000

    def test_missing_fields_handling(self, mock_session):
        """测试缺失字段处理"""
        data = pd.DataFrame(
            {
                "ts_code": ["000001.SZ", "000002.SZ"],
                "trade_date": ["20241201", "20241201"],
                "adj_factor": [1.0, None],
            }
        )
        job = AdjFactor(session=mock_session, cache=False)
        with patch.object(job, "_fetchall", return_value=data):
            result = job.run()
            # Should handle None/NaN gracefully
            assert len(result) == 2

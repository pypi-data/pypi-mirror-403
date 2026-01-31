"""
Comprehensive test suite for CompanyDebt class
Tests cover initialization, transformation, execution, and integration scenarios
"""

import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.companydebt import CompanyDebt
from xfintech.data.source.tushare.stock.companydebt.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)

# ============================================================================
# Test Fixtures
# ============================================================================


class FakeConnection:
    """Fake Tushare connection for testing"""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def balancesheet_vip(self, **kwargs):
        """Mock balancesheet_vip API call"""
        return self.frame


class FakeSession:
    """Fake session for testing"""

    def __init__(self, connection: FakeConnection):
        self.connection = connection


@pytest.fixture
def mock_session():
    """Create a mock session with empty data"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    return FakeSession(fake_conn)


@pytest.fixture
def sample_source_data():
    """Sample balance sheet data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "ann_date": ["20200430", "20201031", "20200430"],
            "f_ann_date": ["20200430", "20201031", "20200430"],
            "end_date": ["20200331", "20200930", "20200331"],
            "report_type": ["1", "1", "1"],
            "comp_type": ["2", "2", "1"],
            "end_type": ["Q1", "Q3", "Q1"],
            "total_assets": ["2000000.50", "2100000.75", "500000.25"],
            "total_liab": ["1500000.30", "1550000.40", "300000.15"],
            "total_hldr_eqy_inc_min_int": ["500000.20", "550000.35", "200000.10"],
            "money_cap": ["100000.00", "110000.00", "50000.00"],
            "accounts_receiv": ["80000.50", "85000.75", "30000.25"],
            "inventories": ["60000.25", "65000.50", "25000.10"],
            "fix_assets": ["400000.00", "420000.00", "150000.00"],
            "update_flag": ["0", "0", "0"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_companydebt_init_basic(mock_session):
    """Test basic initialization with required session"""
    debt = CompanyDebt(session=mock_session)
    assert debt.name == NAME
    assert debt.key == KEY
    assert debt.source == SOURCE
    assert debt.target == TARGET
    assert debt.paginate.pagesize == PAGINATE["pagesize"]
    assert debt.paginate.pagelimit == PAGINATE["pagelimit"]


def test_companydebt_init_with_params_dict(mock_session):
    """Test initialization with params as dict"""
    params = {"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"}
    debt = CompanyDebt(session=mock_session, params=params)
    assert debt.params.get("ts_code") == "000001.SZ"
    assert debt.params.get("start_date") == "20200101"
    assert debt.params.get("end_date") == "20201231"


def test_companydebt_init_with_params_object(mock_session):
    """Test initialization with params as Params object"""
    from xfintech.data.common.params import Params

    params = Params(ts_code="000001.SZ", start_date="20200101")
    debt = CompanyDebt(session=mock_session, params=params)
    assert debt.params.get("ts_code") == "000001.SZ"


def test_companydebt_init_with_period_param(mock_session):
    """Test initialization with period parameter"""
    params = {"ts_code": "000001.SZ", "period": "20201231"}
    debt = CompanyDebt(session=mock_session, params=params)
    assert debt.params.get("period") == "20201231"


def test_companydebt_init_with_cache_bool_true(mock_session):
    """Test initialization with cache enabled"""
    debt = CompanyDebt(session=mock_session, cache=True)
    assert debt.cache is not None


def test_companydebt_init_with_cache_bool_false(mock_session):
    """Test initialization with cache disabled"""
    debt = CompanyDebt(session=mock_session, cache=False)
    assert debt.cache is None


def test_companydebt_init_with_cache_dict(mock_session):
    """Test initialization with cache config dict"""
    cache_config = {"path": "/tmp/cache", "key": "test"}
    debt = CompanyDebt(session=mock_session, cache=cache_config)
    assert debt.cache is not None


def test_companydebt_init_default_paginate_limit(mock_session):
    """Test that default pagination limit is set correctly"""
    debt = CompanyDebt(session=mock_session)
    assert debt.paginate.pagesize == 1000
    assert debt.paginate.pagelimit == 1000


def test_companydebt_init_with_all_params(mock_session):
    """Test initialization with all parameters"""
    params = {"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"}
    coolant = {"interval": 0.5}
    retry = {"max_attempts": 3}
    cache = True

    debt = CompanyDebt(session=mock_session, params=params, coolant=coolant, retry=retry, cache=cache)
    assert debt.params.get("ts_code") == "000001.SZ"
    assert debt.cache is not None


def test_companydebt_constants():
    """Test that constants are correctly defined"""
    assert NAME == "companydebt"
    assert KEY == "/tushare/companydebt"
    assert SOURCE.name == "balancesheet_vip"
    assert TARGET.name == "companydebt"
    assert PAGINATE["pagesize"] == 1000


# ============================================================================
# Transform Tests
# ============================================================================


def test_companydebt_transform_basic(sample_source_data):
    """Test basic transformation of balance sheet data"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "datecode" in result.columns


def test_companydebt_transform_code_mapping(sample_source_data):
    """Test that ts_code is correctly mapped to code"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[2]["code"] == "000002.SZ"


def test_companydebt_transform_date_format(sample_source_data):
    """Test that dates are properly formatted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    assert pd.api.types.is_datetime64_any_dtype(result["date"]) is False
    assert result.iloc[0]["date"] == "2020-03-31"


def test_companydebt_transform_datecode_preserved(sample_source_data):
    """Test that datecode is correctly created from end_date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    assert result.iloc[0]["datecode"] == "20200331"
    assert result.iloc[1]["datecode"] == "20200930"


def test_companydebt_transform_numeric_conversions(sample_source_data):
    """Test that numeric fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    assert result.iloc[0]["total_assets"] == 2000000.50
    assert result.iloc[0]["total_liab"] == 1500000.30
    assert pd.api.types.is_numeric_dtype(result["total_assets"])


def test_companydebt_transform_string_fields(sample_source_data):
    """Test that string fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    assert result.iloc[0]["report_type"] == "1"
    assert result.iloc[0]["comp_type"] == "2"
    assert result.iloc[0]["update_flag"] == "0"


def test_companydebt_transform_empty_dataframe():
    """Test transformation with empty dataframe"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(pd.DataFrame())

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_companydebt_transform_none_input():
    """Test transformation with None input"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(None)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_companydebt_transform_handles_invalid_dates():
    """Test that invalid dates are handled gracefully"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["invalid"],
            "f_ann_date": ["20200430"],
            "end_date": ["20200331"],
            "report_type": ["1"],
            "comp_type": ["1"],
            "end_type": ["Q1"],
            "update_flag": ["0"],
        }
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(data)

    assert len(result) == 1
    assert pd.isna(result.iloc[0]["ann_date"])


def test_companydebt_transform_removes_duplicates(sample_source_data):
    """Test that duplicate rows are removed"""
    # Create data with duplicates
    data = pd.concat([sample_source_data, sample_source_data.iloc[[0]]], ignore_index=True)

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(data)

    # Should have 3 unique rows, not 4
    assert len(result) == 3


def test_companydebt_transform_sorts_by_code_and_date(sample_source_data):
    """Test that output is sorted by code and date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    # Check first row is 000001.SZ, 2020-03-31
    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[0]["date"] == "2020-03-31"
    # Check last row is 000002.SZ
    assert result.iloc[2]["code"] == "000002.SZ"


def test_companydebt_transform_resets_index():
    """Test that index is reset after transformation"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "ann_date": ["20200430", "20200430"],
            "f_ann_date": ["20200430", "20200430"],
            "end_date": ["20200331", "20200331"],
            "report_type": ["1", "1"],
            "comp_type": ["1", "1"],
            "end_type": ["Q1", "Q1"],
            "update_flag": ["0", "0"],
        },
        index=[5, 10],
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(data)

    assert result.index.tolist() == [0, 1]


def test_companydebt_transform_only_target_columns(sample_source_data):
    """Test that only target columns are in output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)

    assert actual_cols == expected_cols


# ============================================================================
# Run Method Tests
# ============================================================================


def test_companydebt_run_with_cache_hit(sample_source_data):
    """Test that run() returns cached data when available"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    # First run should fetch and cache
    result1 = debt.run()

    # Second run should return cached data
    result2 = debt.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_companydebt_run_basic_date_range(sample_source_data):
    """Test run() with date range parameters"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(
        session=session,
        params={"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"},
    )

    result = debt.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_companydebt_run_with_datetime_params(sample_source_data):
    """Test run() with datetime objects as parameters"""
    from datetime import datetime

    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2020, 12, 31),
        },
    )

    result = debt.run()

    assert isinstance(result, pd.DataFrame)


def test_companydebt_run_adds_fields_param(sample_source_data):
    """Test that run() adds fields parameter if not provided"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    # Monkey patch _fetchall to capture params
    debt._fetchall
    captured_params = {}

    def mock_fetchall(api, **kwargs):
        captured_params.update(kwargs)
        return sample_source_data

    debt._fetchall = mock_fetchall
    debt.run()

    assert "fields" in captured_params
    assert len(captured_params["fields"]) > 0


def test_companydebt_run_sets_cache(sample_source_data):
    """Test that run() saves result to cache"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    result = debt.run()

    # Cache should be set after run
    cached = debt._load_cache()
    assert cached is not None
    pd.testing.assert_frame_equal(result, cached)


def test_companydebt_run_calls_transform(sample_source_data):
    """Test that run() calls transform method"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    # Monkey patch transform to track if it was called
    original_transform = debt.transform
    transform_called = {"called": False}

    def mock_transform(data):
        transform_called["called"] = True
        return original_transform(data)

    debt.transform = mock_transform
    debt.run()

    assert transform_called["called"] is True


def test_companydebt_run_uses_balancesheet_vip_api(sample_source_data):
    """Test that run() uses balancesheet_vip API"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    # Monkey patch _fetchall to capture API
    captured_api = {"api": None}

    def mock_fetchall(api, **kwargs):
        captured_api["api"] = api
        return sample_source_data

    debt._fetchall = mock_fetchall
    debt.run()

    assert captured_api["api"] == session.connection.balancesheet_vip


# ============================================================================
# Integration Tests
# ============================================================================


def test_companydebt_full_workflow(sample_source_data):
    """Test complete workflow from initialization to output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    debt = CompanyDebt(
        session=session,
        params={"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"},
        cache=True,
    )

    result = debt.run()

    # Verify output structure
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "total_assets" in result.columns
    assert "total_liab" in result.columns

    # Verify data types
    assert pd.api.types.is_numeric_dtype(result["total_assets"])
    assert result.iloc[0]["code"] == "000001.SZ"


def test_companydebt_cache_persistence(sample_source_data):
    """Test that cache persists across multiple runs"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    # Run once to populate cache
    result1 = debt.run()

    # Clear in-memory data to simulate fresh load
    debt2 = CompanyDebt(session=session, params={"ts_code": "000001.SZ"}, cache=True)
    result2 = debt2.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_companydebt_params_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    debt1 = CompanyDebt(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20200101"},
        cache=True,
    )
    debt2 = CompanyDebt(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20210101"},
        cache=True,
    )

    # Test that different params are properly stored
    assert debt1.params.get("start_date") == "20200101"
    assert debt2.params.get("start_date") == "20210101"
    assert debt1.params.get("start_date") != debt2.params.get("start_date")


def test_companydebt_different_stocks(sample_source_data):
    """Test that different stock codes are handled correctly"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    debt1 = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})
    result1 = debt1.run()

    debt2 = CompanyDebt(session=session, params={"ts_code": "000002.SZ"})
    result2 = debt2.run()

    # Both should have data for their respective stocks
    assert "000001.SZ" in result1["code"].values
    assert "000002.SZ" in result2["code"].values


def test_companydebt_empty_result_handling():
    """Test handling of empty API results"""
    empty_data = pd.DataFrame()
    fake_conn = FakeConnection(frame=empty_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.run()

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) > 0


def test_companydebt_large_dataset_handling():
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"] * 1000,
            "ann_date": ["20200430"] * 1000,
            "f_ann_date": ["20200430"] * 1000,
            "end_date": ["20200331"] * 1000,
            "report_type": ["1"] * 1000,
            "comp_type": ["1"] * 1000,
            "end_type": ["Q1"] * 1000,
            "total_assets": ["1000000.00"] * 1000,
            "update_flag": ["0"] * 1000,
        }
    )

    fake_conn = FakeConnection(frame=large_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.run()

    # Should deduplicate to 1 row
    assert len(result) == 1


def test_companydebt_without_cache(sample_source_data):
    """Test that class works correctly without caching"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"}, cache=False)

    result = debt.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert debt.cache is None


def test_companydebt_handles_missing_numeric_fields():
    """Test that missing numeric fields don't break transformation"""
    # Data with only subset of fields
    minimal_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20200430"],
            "f_ann_date": ["20200430"],
            "end_date": ["20200331"],
            "report_type": ["1"],
            "comp_type": ["1"],
            "end_type": ["Q1"],
            "total_assets": ["1000000.00"],
            "update_flag": ["0"],
        }
    )

    fake_conn = FakeConnection(frame=minimal_data)
    session = FakeSession(fake_conn)
    debt = CompanyDebt(session=session, params={"ts_code": "000001.SZ"})

    result = debt.run()

    # Should complete without error
    assert len(result) == 1
    # Missing fields should be NaN
    assert pd.isna(result.iloc[0]["total_liab"])


def test_companydebt_api_doc_reference():
    """Test that class correctly references API documentation"""
    assert "doc_id=36" in CompanyDebt.__doc__

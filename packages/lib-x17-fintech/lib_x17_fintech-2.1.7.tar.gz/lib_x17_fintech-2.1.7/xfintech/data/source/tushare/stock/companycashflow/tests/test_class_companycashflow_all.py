import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.companycashflow import CompanyCashflow
from xfintech.data.source.tushare.stock.companycashflow.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)

# Test Fixtures


class FakeConnection:
    """Fake Tushare connection for testing"""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def cashflow_vip(self, **kwargs):
        """Mock cashflow_vip API call"""
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
    """Sample cash flow data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "ann_date": ["20200430", "20201031", "20200430"],
            "f_ann_date": ["20200430", "20201031", "20200430"],
            "end_date": ["20200331", "20200930", "20200331"],
            "comp_type": ["2", "2", "1"],
            "report_type": ["1", "1", "1"],
            "end_type": ["Q1", "Q3", "Q1"],
            "net_profit": ["100000.50", "120000.75", "50000.25"],
            "n_cashflow_act": ["150000.30", "180000.40", "60000.15"],
            "n_cashflow_inv_act": ["-80000.20", "-90000.35", "-30000.10"],
            "n_cash_flows_fnc_act": ["50000.00", "60000.00", "20000.00"],
            "c_cash_equ_beg_period": ["200000.50", "270000.75", "100000.25"],
            "c_cash_equ_end_period": ["270000.25", "340000.50", "120000.10"],
            "finan_exp": ["15000.00", "18000.00", "8000.00"],
            "update_flag": ["1", "1", "1"],
        }
    )


# Initialization Tests


def test_companycashflow_init_basic(mock_session):
    """Test basic initialization with required session"""
    cashflow = CompanyCashflow(session=mock_session)
    assert cashflow.name == NAME
    assert cashflow.key == KEY
    assert cashflow.source == SOURCE
    assert cashflow.target == TARGET
    assert cashflow.paginate.pagesize == PAGINATE["pagesize"]
    assert cashflow.paginate.pagelimit == PAGINATE["pagelimit"]


def test_companycashflow_init_with_params_dict(mock_session):
    """Test initialization with params as dict"""
    params = {"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"}
    cashflow = CompanyCashflow(session=mock_session, params=params)
    assert cashflow.params.get("ts_code") == "000001.SZ"
    assert cashflow.params.get("start_date") == "20200101"
    assert cashflow.params.get("end_date") == "20201231"


def test_companycashflow_init_with_params_object(mock_session):
    """Test initialization with params as Params object"""
    from xfintech.data.common.params import Params

    params = Params(ts_code="000001.SZ", start_date="20200101")
    cashflow = CompanyCashflow(session=mock_session, params=params)
    assert cashflow.params.get("ts_code") == "000001.SZ"


def test_companycashflow_init_with_period_param(mock_session):
    """Test initialization with period parameter"""
    params = {"ts_code": "000001.SZ", "period": "20201231"}
    cashflow = CompanyCashflow(session=mock_session, params=params)
    assert cashflow.params.get("period") == "20201231"


def test_companycashflow_init_with_cache_bool_true(mock_session):
    """Test initialization with cache enabled"""
    cashflow = CompanyCashflow(session=mock_session, cache=True)
    assert cashflow.cache is not None


def test_companycashflow_init_with_cache_bool_false(mock_session):
    """Test initialization with cache disabled"""
    cashflow = CompanyCashflow(session=mock_session, cache=False)
    assert cashflow.cache is None


def test_companycashflow_init_with_cache_dict(mock_session):
    """Test initialization with cache config dict"""
    cache_config = {"path": "/tmp/cache", "key": "test"}
    cashflow = CompanyCashflow(session=mock_session, cache=cache_config)
    assert cashflow.cache is not None


def test_companycashflow_init_default_paginate_limit(mock_session):
    """Test that default pagination limit is set correctly"""
    cashflow = CompanyCashflow(session=mock_session)
    assert cashflow.paginate.pagesize == 1000
    assert cashflow.paginate.pagelimit == 1000


def test_companycashflow_init_with_all_params(mock_session):
    """Test initialization with all parameters"""
    params = {"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"}
    coolant = {"interval": 0.5}
    retry = {"max_attempts": 3}
    cache = True

    cashflow = CompanyCashflow(session=mock_session, params=params, coolant=coolant, retry=retry, cache=cache)
    assert cashflow.params.get("ts_code") == "000001.SZ"
    assert cashflow.cache is not None


def test_companycashflow_constants():
    """Test that constants are correctly defined"""
    assert NAME == "companycashflow"
    assert KEY == "/tushare/companycashflow"
    assert SOURCE.name == "cashflow_vip"
    assert TARGET.name == "companycashflow"
    assert PAGINATE["pagesize"] == 1000


# Transform Tests


def test_companycashflow_transform_basic(sample_source_data):
    """Test basic transformation of cash flow data"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "datecode" in result.columns


def test_companycashflow_transform_code_mapping(sample_source_data):
    """Test that ts_code is correctly mapped to code"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[2]["code"] == "000002.SZ"


def test_companycashflow_transform_date_format(sample_source_data):
    """Test that dates are properly formatted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    assert pd.api.types.is_datetime64_any_dtype(result["date"]) is False
    assert result.iloc[0]["date"] == "2020-03-31"


def test_companycashflow_transform_datecode_preserved(sample_source_data):
    """Test that datecode is correctly created from end_date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    assert result.iloc[0]["datecode"] == "20200331"
    assert result.iloc[1]["datecode"] == "20200930"


def test_companycashflow_transform_numeric_conversions(sample_source_data):
    """Test that numeric fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    assert result.iloc[0]["net_profit"] == 100000.50
    assert result.iloc[0]["n_cashflow_act"] == 150000.30
    assert pd.api.types.is_numeric_dtype(result["net_profit"])


def test_companycashflow_transform_string_fields(sample_source_data):
    """Test that string fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    assert result.iloc[0]["comp_type"] == "2"
    assert result.iloc[0]["report_type"] == "1"
    assert result.iloc[0]["update_flag"] == "1"


def test_companycashflow_transform_empty_dataframe():
    """Test transformation with empty dataframe"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(pd.DataFrame())

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_companycashflow_transform_none_input():
    """Test transformation with None input"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(None)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_companycashflow_transform_handles_invalid_dates():
    """Test that invalid dates are handled gracefully"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["invalid"],
            "f_ann_date": ["20200430"],
            "end_date": ["20200331"],
            "comp_type": ["1"],
            "report_type": ["1"],
            "end_type": ["Q1"],
            "update_flag": ["1"],
        }
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(data)

    assert len(result) == 1
    assert pd.isna(result.iloc[0]["ann_date"])


def test_companycashflow_transform_removes_duplicates(sample_source_data):
    """Test that duplicate rows are removed"""
    # Create data with duplicates
    data = pd.concat([sample_source_data, sample_source_data.iloc[[0]]], ignore_index=True)

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(data)

    # Should have 3 unique rows, not 4
    assert len(result) == 3


def test_companycashflow_transform_sorts_by_code_and_date(sample_source_data):
    """Test that output is sorted by code and date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    # Check first row is 000001.SZ, 2020-03-31
    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[0]["date"] == "2020-03-31"
    # Check last row is 000002.SZ
    assert result.iloc[2]["code"] == "000002.SZ"


def test_companycashflow_transform_resets_index():
    """Test that index is reset after transformation"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "ann_date": ["20200430", "20200430"],
            "f_ann_date": ["20200430", "20200430"],
            "end_date": ["20200331", "20200331"],
            "comp_type": ["1", "1"],
            "report_type": ["1", "1"],
            "end_type": ["Q1", "Q1"],
            "update_flag": ["1", "1"],
        },
        index=[5, 10],
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(data)

    assert result.index.tolist() == [0, 1]


def test_companycashflow_transform_only_target_columns(sample_source_data):
    """Test that only target columns are in output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)

    assert actual_cols == expected_cols


# Run Method Tests


def test_companycashflow_run_with_cache_hit(sample_source_data):
    """Test that run() returns cached data when available"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    # First run should fetch and cache
    result1 = cashflow.run()

    # Second run should return cached data
    result2 = cashflow.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_companycashflow_run_basic_date_range(sample_source_data):
    """Test run() with date range parameters"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(
        session=session,
        params={"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"},
    )

    result = cashflow.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_companycashflow_run_with_datetime_params(sample_source_data):
    """Test run() with datetime objects as parameters"""
    from datetime import datetime

    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2020, 12, 31),
        },
    )

    result = cashflow.run()

    assert isinstance(result, pd.DataFrame)


def test_companycashflow_run_sets_cache(sample_source_data):
    """Test that run() saves result to cache"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    result = cashflow.run()

    # Cache should be set after run
    cached = cashflow._load_cache()
    assert cached is not None
    pd.testing.assert_frame_equal(result, cached)


def test_companycashflow_run_calls_transform(sample_source_data):
    """Test that run() calls transform method"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    # Monkey patch transform to track if it was called
    original_transform = cashflow.transform
    transform_called = {"called": False}

    def mock_transform(data):
        transform_called["called"] = True
        return original_transform(data)

    cashflow.transform = mock_transform
    cashflow.run()

    assert transform_called["called"] is True


def test_companycashflow_run_uses_cashflow_vip_api(sample_source_data):
    """Test that run() uses cashflow_vip API"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    # Monkey patch _fetchall to capture API
    captured_api = {"api": None}

    def mock_fetchall(api, **kwargs):
        captured_api["api"] = api
        return sample_source_data

    cashflow._fetchall = mock_fetchall
    cashflow.run()

    assert captured_api["api"] == session.connection.cashflow_vip


# Integration Tests


def test_companycashflow_full_workflow(sample_source_data):
    """Test complete workflow from initialization to output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    cashflow = CompanyCashflow(
        session=session,
        params={"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"},
        cache=True,
    )

    result = cashflow.run()

    # Verify output structure
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "net_profit" in result.columns
    assert "n_cashflow_act" in result.columns

    # Verify data types
    assert pd.api.types.is_numeric_dtype(result["net_profit"])
    assert result.iloc[0]["code"] == "000001.SZ"


def test_companycashflow_cache_persistence(sample_source_data):
    """Test that cache persists across multiple runs"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    # Run once to populate cache
    result1 = cashflow.run()

    # Clear in-memory data to simulate fresh load
    cashflow2 = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"}, cache=True)
    result2 = cashflow2.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_companycashflow_params_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    cashflow1 = CompanyCashflow(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20200101"},
        cache=True,
    )
    cashflow2 = CompanyCashflow(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20210101"},
        cache=True,
    )

    # Test that different params are properly stored
    assert cashflow1.params.get("start_date") == "20200101"
    assert cashflow2.params.get("start_date") == "20210101"
    assert cashflow1.params.get("start_date") != cashflow2.params.get("start_date")


def test_companycashflow_different_stocks(sample_source_data):
    """Test that different stock codes are handled correctly"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    cashflow1 = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})
    result1 = cashflow1.run()

    cashflow2 = CompanyCashflow(session=session, params={"ts_code": "000002.SZ"})
    result2 = cashflow2.run()

    # Both should have data for their respective stocks
    assert "000001.SZ" in result1["code"].values
    assert "000002.SZ" in result2["code"].values


def test_companycashflow_empty_result_handling():
    """Test handling of empty API results"""
    empty_data = pd.DataFrame()
    fake_conn = FakeConnection(frame=empty_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.run()

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) > 0


def test_companycashflow_large_dataset_handling():
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"] * 1000,
            "ann_date": ["20200430"] * 1000,
            "f_ann_date": ["20200430"] * 1000,
            "end_date": ["20200331"] * 1000,
            "comp_type": ["1"] * 1000,
            "report_type": ["1"] * 1000,
            "end_type": ["Q1"] * 1000,
            "net_profit": ["100000.00"] * 1000,
            "update_flag": ["1"] * 1000,
        }
    )

    fake_conn = FakeConnection(frame=large_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.run()

    # Should deduplicate to 1 row
    assert len(result) == 1


def test_companycashflow_without_cache(sample_source_data):
    """Test that class works correctly without caching"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"}, cache=False)

    result = cashflow.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert cashflow.cache is None


def test_companycashflow_handles_missing_numeric_fields():
    """Test that missing numeric fields don't break transformation"""
    # Data with only subset of fields
    minimal_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20200430"],
            "f_ann_date": ["20200430"],
            "end_date": ["20200331"],
            "comp_type": ["1"],
            "report_type": ["1"],
            "end_type": ["Q1"],
            "net_profit": ["100000.00"],
            "update_flag": ["1"],
        }
    )

    fake_conn = FakeConnection(frame=minimal_data)
    session = FakeSession(fake_conn)
    cashflow = CompanyCashflow(session=session, params={"ts_code": "000001.SZ"})

    result = cashflow.run()

    # Should complete without error
    assert len(result) == 1
    # Missing fields should be NaN
    assert pd.isna(result.iloc[0]["n_cashflow_act"])


def test_companycashflow_api_doc_reference():
    """Test that class correctly references API documentation"""
    assert "doc_id=44" in CompanyCashflow.__doc__

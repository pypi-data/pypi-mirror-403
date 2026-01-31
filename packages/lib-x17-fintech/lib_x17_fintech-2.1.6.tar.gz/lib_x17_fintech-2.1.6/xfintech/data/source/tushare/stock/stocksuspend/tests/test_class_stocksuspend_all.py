import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.stocksuspend import StockSuspend
from xfintech.data.source.tushare.stock.stocksuspend.constant import (
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

    def suspend_d(self, **kwargs):
        """Mock suspend_d API call"""
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
    """Sample stock suspend/resume data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "000001.SZ"],
            "trade_date": ["20200331", "20200331", "20200630"],
            "suspend_timing": ["全天", "全天", "午后"],
            "suspend_type": ["临时停牌", "重大事项", "临时停牌"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_stocksuspend_init_basic(mock_session):
    """Test basic initialization with required session"""
    suspend = StockSuspend(session=mock_session)
    assert suspend.name == NAME
    assert suspend.key == KEY
    assert suspend.source == SOURCE
    assert suspend.target == TARGET
    assert suspend.paginate.pagesize == PAGINATE["pagesize"]
    assert suspend.paginate.pagelimit == PAGINATE["pagelimit"]


def test_stocksuspend_init_with_params_dict(mock_session):
    """Test initialization with params as dict"""
    params = {"trade_date": "20201231", "ts_code": "000001.SZ"}
    suspend = StockSuspend(session=mock_session, params=params)
    assert suspend.params.get("trade_date") == "20201231"
    assert suspend.params.get("ts_code") == "000001.SZ"


def test_stocksuspend_init_with_params_object(mock_session):
    """Test initialization with params as Params object"""
    from xfintech.data.common.params import Params

    params = Params(trade_date="20201231")
    suspend = StockSuspend(session=mock_session, params=params)
    assert suspend.params.get("trade_date") == "20201231"


def test_stocksuspend_init_with_date_range(mock_session):
    """Test initialization with date range parameters"""
    params = {"start_date": "20200101", "end_date": "20201231"}
    suspend = StockSuspend(session=mock_session, params=params)
    assert suspend.params.get("start_date") == "20200101"
    assert suspend.params.get("end_date") == "20201231"


def test_stocksuspend_init_with_cache_bool_true(mock_session):
    """Test initialization with cache enabled"""
    suspend = StockSuspend(session=mock_session, cache=True)
    assert suspend.cache is not None


def test_stocksuspend_init_with_cache_bool_false(mock_session):
    """Test initialization with cache disabled"""
    suspend = StockSuspend(session=mock_session, cache=False)
    assert suspend.cache is None


def test_stocksuspend_init_with_cache_dict(mock_session):
    """Test initialization with cache config dict"""
    cache_config = {"path": "/tmp/cache", "key": "test"}
    suspend = StockSuspend(session=mock_session, cache=cache_config)
    assert suspend.cache is not None


def test_stocksuspend_init_default_paginate_limit(mock_session):
    """Test that default pagination limit is set correctly"""
    suspend = StockSuspend(session=mock_session)
    assert suspend.paginate.pagesize == 1000
    assert suspend.paginate.pagelimit == 1000


def test_stocksuspend_init_with_all_params(mock_session):
    """Test initialization with all parameters"""
    params = {"trade_date": "20201231"}
    coolant = {"interval": 0.5}
    retry = {"max_attempts": 3}
    cache = True

    suspend = StockSuspend(session=mock_session, params=params, coolant=coolant, retry=retry, cache=cache)
    assert suspend.params.get("trade_date") == "20201231"
    assert suspend.cache is not None


def test_stocksuspend_constants():
    """Test that constants are correctly defined"""
    assert NAME == "stocksuspend"
    assert KEY == "/tushare/stocksuspend"
    assert SOURCE.name == "suspend_d"
    assert TARGET.name == "stocksuspend"
    assert PAGINATE["pagesize"] == 1000
    assert PAGINATE["pagelimit"] == 1000


# ============================================================================
# Transform Tests
# ============================================================================


def test_stocksuspend_transform_basic(sample_source_data):
    """Test basic transformation of suspend/resume data"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "datecode" in result.columns


def test_stocksuspend_transform_code_mapping(sample_source_data):
    """Test that ts_code is correctly mapped to code"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(sample_source_data)

    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[1]["code"] == "000001.SZ"
    assert result.iloc[2]["code"] == "000002.SZ"


def test_stocksuspend_transform_date_format(sample_source_data):
    """Test that dates are properly formatted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(sample_source_data)

    assert pd.api.types.is_datetime64_any_dtype(result["date"]) is False
    assert result.iloc[0]["date"] == "2020-03-31"
    assert result.iloc[1]["date"] == "2020-06-30"


def test_stocksuspend_transform_datecode_preserved(sample_source_data):
    """Test that datecode is correctly created from trade_date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(sample_source_data)

    assert result.iloc[0]["datecode"] == "20200331"
    assert result.iloc[1]["datecode"] == "20200630"


def test_stocksuspend_transform_string_fields(sample_source_data):
    """Test that string fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(sample_source_data)

    # After sorting by code and date: 000001.SZ-20200331, 000001.SZ-20200630, 000002.SZ-20200331
    assert result.iloc[0]["suspend_timing"] == "全天"
    assert result.iloc[0]["suspend_type"] == "临时停牌"
    assert result.iloc[1]["suspend_timing"] == "午后"  # This is 000001.SZ-20200630


def test_stocksuspend_transform_empty_dataframe():
    """Test transformation with empty dataframe"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(pd.DataFrame())

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_stocksuspend_transform_none_input():
    """Test transformation with None input"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(None)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_stocksuspend_transform_handles_invalid_dates():
    """Test that invalid dates are handled gracefully"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "trade_date": ["invalid"],
            "suspend_timing": ["全天"],
            "suspend_type": ["临时停牌"],
        }
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(data)

    assert len(result) == 1
    assert pd.isna(result.iloc[0]["date"])


def test_stocksuspend_transform_removes_duplicates(sample_source_data):
    """Test that duplicate rows are removed"""
    # Create data with duplicates
    data = pd.concat([sample_source_data, sample_source_data.iloc[[0]]], ignore_index=True)

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(data)

    # Should have 3 unique rows, not 4
    assert len(result) == 3


def test_stocksuspend_transform_sorts_by_code_and_date(sample_source_data):
    """Test that output is sorted by code and date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(sample_source_data)

    # Check first rows are sorted correctly
    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[0]["date"] == "2020-03-31"
    assert result.iloc[1]["code"] == "000001.SZ"
    assert result.iloc[1]["date"] == "2020-06-30"
    assert result.iloc[2]["code"] == "000002.SZ"


def test_stocksuspend_transform_resets_index():
    """Test that index is reset after transformation"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "trade_date": ["20200331", "20200331"],
            "suspend_timing": ["全天", "全天"],
            "suspend_type": ["临时停牌", "重大事项"],
        },
        index=[5, 10],
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(data)

    assert result.index.tolist() == [0, 1]


def test_stocksuspend_transform_only_target_columns(sample_source_data):
    """Test that only target columns are in output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session)

    result = suspend.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)

    assert actual_cols == expected_cols


# ============================================================================
# Run Method Tests
# ============================================================================


def test_stocksuspend_run_basic(sample_source_data):
    """Test basic run() execution"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"})

    result = suspend.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_stocksuspend_run_with_cache_hit(sample_source_data):
    """Test that run() returns cached data when available"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"}, cache=True)

    # First run should fetch and cache
    result1 = suspend.run()

    # Second run should return cached data
    result2 = suspend.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_stocksuspend_run_with_date_range(sample_source_data):
    """Test run() with date range parameters"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"start_date": "20200101", "end_date": "20201231"})

    result = suspend.run()

    assert isinstance(result, pd.DataFrame)


def test_stocksuspend_run_with_datetime_params(sample_source_data):
    """Test run() with datetime objects as parameters"""
    from datetime import datetime

    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(
        session=session,
        params={
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2020, 12, 31),
        },
    )

    result = suspend.run()

    assert isinstance(result, pd.DataFrame)


def test_stocksuspend_run_adds_fields_param(sample_source_data):
    """Test that run() adds fields parameter if not provided"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"})

    # Monkey patch _fetchall to capture params
    suspend._fetchall
    captured_params = {}

    def mock_fetchall(api, **kwargs):
        captured_params.update(kwargs)
        return sample_source_data

    suspend._fetchall = mock_fetchall
    suspend.run()

    assert "fields" in captured_params
    assert len(captured_params["fields"]) > 0


def test_stocksuspend_run_sets_cache(sample_source_data):
    """Test that run() saves result to cache"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"}, cache=True)

    result = suspend.run()

    # Cache should be set after run
    cached = suspend._load_cache()
    assert cached is not None
    pd.testing.assert_frame_equal(result, cached)


def test_stocksuspend_run_calls_transform(sample_source_data):
    """Test that run() calls transform method"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"})

    # Monkey patch transform to track if it was called
    original_transform = suspend.transform
    transform_called = {"called": False}

    def mock_transform(data):
        transform_called["called"] = True
        return original_transform(data)

    suspend.transform = mock_transform
    suspend.run()

    assert transform_called["called"] is True


def test_stocksuspend_run_uses_suspend_d_api(sample_source_data):
    """Test that run() uses suspend_d API"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"})

    # Monkey patch _fetchall to capture API
    captured_api = {"api": None}

    def mock_fetchall(api, **kwargs):
        captured_api["api"] = api
        return sample_source_data

    suspend._fetchall = mock_fetchall
    suspend.run()

    assert captured_api["api"] == session.connection.suspend_d


# ============================================================================
# Integration Tests
# ============================================================================


def test_stocksuspend_full_workflow(sample_source_data):
    """Test complete workflow from initialization to output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    suspend = StockSuspend(
        session=session,
        params={"trade_date": "20200331"},
        cache=True,
    )

    result = suspend.run()

    # Verify output structure
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3  # Mock returns all data regardless of params
    assert "code" in result.columns
    assert "date" in result.columns
    assert "suspend_timing" in result.columns
    assert "suspend_type" in result.columns

    # Verify sorting (code, date)
    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[0]["date"] == "2020-03-31"
    assert result.iloc[1]["code"] == "000001.SZ"
    assert result.iloc[1]["date"] == "2020-06-30"
    assert result.iloc[2]["code"] == "000002.SZ"


def test_stocksuspend_cache_persistence(sample_source_data):
    """Test that cache persists across multiple runs"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"}, cache=True)

    # Run once to populate cache
    result1 = suspend.run()

    # Clear in-memory data to simulate fresh load
    suspend2 = StockSuspend(session=session, params={"trade_date": "20200331"}, cache=True)
    result2 = suspend2.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_stocksuspend_params_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    suspend1 = StockSuspend(
        session=mock_session,
        params={"trade_date": "20200331"},
        cache=True,
    )
    suspend2 = StockSuspend(
        session=mock_session,
        params={"trade_date": "20210331"},
        cache=True,
    )

    # Test that different params are properly stored
    assert suspend1.params.get("trade_date") == "20200331"
    assert suspend2.params.get("trade_date") == "20210331"
    assert suspend1.params.get("trade_date") != suspend2.params.get("trade_date")


def test_stocksuspend_empty_result_handling():
    """Test handling of empty API results"""
    empty_data = pd.DataFrame()
    fake_conn = FakeConnection(frame=empty_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"})

    result = suspend.run()

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) > 0


def test_stocksuspend_large_dataset_handling():
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"] * 1000,
            "trade_date": ["20200331"] * 1000,
            "suspend_timing": ["全天"] * 1000,
            "suspend_type": ["临时停牌"] * 1000,
        }
    )

    fake_conn = FakeConnection(frame=large_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"})

    result = suspend.run()

    # Should deduplicate to 1 row
    assert len(result) == 1


def test_stocksuspend_without_cache(sample_source_data):
    """Test that class works correctly without caching"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"}, cache=False)

    result = suspend.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert suspend.cache is None


def test_stocksuspend_handles_missing_fields():
    """Test that missing fields don't break transformation"""
    # Data with only subset of fields
    minimal_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "trade_date": ["20200331"],
            "suspend_timing": ["全天"],
        }
    )

    fake_conn = FakeConnection(frame=minimal_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"trade_date": "20200331"})

    result = suspend.run()

    # Should complete without error
    assert len(result) == 1
    # Missing fields should be NaN
    assert pd.isna(result.iloc[0]["suspend_type"])


def test_stocksuspend_api_doc_reference():
    """Test that class correctly references API documentation"""
    assert "doc_id=397" in StockSuspend.__doc__


def test_stocksuspend_crosssection_scale():
    """Test that module is correctly configured as crosssection scale"""
    assert SOURCE.meta["scale"] == "crosssection"
    assert TARGET.meta["scale"] == "crosssection"


def test_stocksuspend_multiple_dates_handling(sample_source_data):
    """Test handling of data with multiple dates"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    suspend = StockSuspend(session=session, params={"start_date": "20200101", "end_date": "20201231"})

    result = suspend.run()

    # Should have data for both dates
    assert len(result) == 3
    assert "2020-03-31" in result["date"].values
    assert "2020-06-30" in result["date"].values

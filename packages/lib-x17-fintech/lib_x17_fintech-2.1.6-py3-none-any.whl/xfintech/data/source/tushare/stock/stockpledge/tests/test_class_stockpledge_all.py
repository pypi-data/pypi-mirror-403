import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.stockpledge import StockPledge
from xfintech.data.source.tushare.stock.stockpledge.constant import (
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

    def pledge_stat(self, **kwargs):
        """Mock pledge_stat API call"""
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
    """Sample pledge stat data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000014.SZ", "000014.SZ", "600848.SH"],
            "end_date": ["20180928", "20180921", "20180928"],
            "pledge_count": ["23", "24", "15"],
            "unrest_pledge": ["63.16", "63.17", "25.50"],
            "rest_pledge": ["0.0", "0.0", "5.20"],
            "total_share": ["100000.00", "100000.00", "50000.00"],
            "pledge_ratio": ["0.6316", "0.6317", "0.3070"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_stockpledge_init_basic(mock_session):
    """Test basic initialization with required session"""
    pledge = StockPledge(session=mock_session)
    assert pledge.name == NAME
    assert pledge.key == KEY
    assert pledge.source == SOURCE
    assert pledge.target == TARGET
    assert pledge.paginate.pagesize == PAGINATE["pagesize"]
    assert pledge.paginate.pagelimit == PAGINATE["pagelimit"]


def test_stockpledge_init_with_params_dict(mock_session):
    """Test initialization with params as dict"""
    params = {"ts_code": "000014.SZ", "end_date": "20180928"}
    pledge = StockPledge(session=mock_session, params=params)
    assert pledge.params.get("ts_code") == "000014.SZ"
    assert pledge.params.get("end_date") == "20180928"


def test_stockpledge_init_with_params_object(mock_session):
    """Test initialization with params as Params object"""
    from xfintech.data.common.params import Params

    params = Params(ts_code="000014.SZ")
    pledge = StockPledge(session=mock_session, params=params)
    assert pledge.params.get("ts_code") == "000014.SZ"


def test_stockpledge_init_with_end_date(mock_session):
    """Test initialization with end_date parameter"""
    params = {"ts_code": "000014.SZ", "end_date": "20180928"}
    pledge = StockPledge(session=mock_session, params=params)
    assert pledge.params.get("end_date") == "20180928"


def test_stockpledge_init_with_cache_bool_true(mock_session):
    """Test initialization with cache enabled"""
    pledge = StockPledge(session=mock_session, cache=True)
    assert pledge.cache is not None


def test_stockpledge_init_with_cache_bool_false(mock_session):
    """Test initialization with cache disabled"""
    pledge = StockPledge(session=mock_session, cache=False)
    assert pledge.cache is None


def test_stockpledge_init_with_cache_dict(mock_session):
    """Test initialization with cache config dict"""
    cache_config = {"path": "/tmp/cache", "key": "test"}
    pledge = StockPledge(session=mock_session, cache=cache_config)
    assert pledge.cache is not None


def test_stockpledge_init_default_paginate_limit(mock_session):
    """Test that default pagination limit is set correctly"""
    pledge = StockPledge(session=mock_session)
    assert pledge.paginate.pagesize == 1000
    assert pledge.paginate.pagelimit == 1000


def test_stockpledge_init_with_all_params(mock_session):
    """Test initialization with all parameters"""
    params = {"ts_code": "000014.SZ", "end_date": "20180928"}
    coolant = {"interval": 0.5}
    retry = {"max_attempts": 3}
    cache = True

    pledge = StockPledge(session=mock_session, params=params, coolant=coolant, retry=retry, cache=cache)
    assert pledge.params.get("ts_code") == "000014.SZ"
    assert pledge.cache is not None


def test_stockpledge_constants():
    """Test that constants are correctly defined"""
    assert NAME == "stockpledge"
    assert KEY == "/tushare/stockpledge"
    assert SOURCE.name == "pledge_stat"
    assert TARGET.name == "stockpledge"
    assert PAGINATE["pagesize"] == 1000
    assert PAGINATE["pagelimit"] == 1000


# ============================================================================
# Transform Tests
# ============================================================================


def test_stockpledge_transform_basic(sample_source_data):
    """Test basic transformation of pledge stat data"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "datecode" in result.columns


def test_stockpledge_transform_code_mapping(sample_source_data):
    """Test that ts_code is correctly mapped to code"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    assert result.iloc[0]["code"] == "000014.SZ"
    assert result.iloc[2]["code"] == "600848.SH"


def test_stockpledge_transform_date_format(sample_source_data):
    """Test that dates are properly formatted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    assert pd.api.types.is_datetime64_any_dtype(result["date"]) is False
    # After sorting by code and date: 000014.SZ dates first (21st, 28th), then 600848.SH
    assert result.iloc[0]["date"] == "2018-09-21"
    assert result.iloc[1]["date"] == "2018-09-28"


def test_stockpledge_transform_datecode_preserved(sample_source_data):
    """Test that datecode is correctly created from end_date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    # After sorting: 000014.SZ dates first (21st, 28th)
    assert result.iloc[0]["datecode"] == "20180921"
    assert result.iloc[1]["datecode"] == "20180928"


def test_stockpledge_transform_numeric_conversions(sample_source_data):
    """Test that numeric fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    # After sorting: first row is 000014.SZ 20180921
    assert result.iloc[0]["unrest_pledge"] == 63.17
    assert result.iloc[0]["total_share"] == 100000.00
    assert result.iloc[0]["pledge_ratio"] == 0.6317
    assert pd.api.types.is_numeric_dtype(result["unrest_pledge"])


def test_stockpledge_transform_integer_field(sample_source_data):
    """Test that integer field is properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    # After sorting: first row is 000014.SZ 20180921 (count=24)
    assert result.iloc[0]["pledge_count"] == 24
    assert result.iloc[1]["pledge_count"] == 23
    assert pd.api.types.is_integer_dtype(result["pledge_count"])


def test_stockpledge_transform_empty_dataframe():
    """Test transformation with empty dataframe"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(pd.DataFrame())

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_stockpledge_transform_none_input():
    """Test transformation with None input"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(None)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_stockpledge_transform_handles_invalid_dates():
    """Test that invalid dates are handled gracefully"""
    data = pd.DataFrame(
        {
            "ts_code": ["000014.SZ"],
            "end_date": ["invalid"],
            "pledge_count": ["23"],
            "unrest_pledge": ["63.16"],
            "rest_pledge": ["0.0"],
            "total_share": ["100000.00"],
            "pledge_ratio": ["0.6316"],
        }
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(data)

    assert len(result) == 1
    assert pd.isna(result.iloc[0]["date"])


def test_stockpledge_transform_removes_duplicates(sample_source_data):
    """Test that duplicate rows are removed"""
    # Create data with duplicates
    data = pd.concat([sample_source_data, sample_source_data.iloc[[0]]], ignore_index=True)

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(data)

    # Should have 3 unique rows, not 4
    assert len(result) == 3


def test_stockpledge_transform_sorts_by_code_and_date(sample_source_data):
    """Test that output is sorted by code and date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    # Check sorting: 000014.SZ dates first, then 600848.SH
    assert result.iloc[0]["code"] == "000014.SZ"
    assert result.iloc[0]["date"] == "2018-09-21"
    assert result.iloc[1]["code"] == "000014.SZ"
    assert result.iloc[1]["date"] == "2018-09-28"
    assert result.iloc[2]["code"] == "600848.SH"


def test_stockpledge_transform_resets_index():
    """Test that index is reset after transformation"""
    data = pd.DataFrame(
        {
            "ts_code": ["000014.SZ", "600848.SH"],
            "end_date": ["20180928", "20180928"],
            "pledge_count": ["23", "15"],
            "unrest_pledge": ["63.16", "25.50"],
            "rest_pledge": ["0.0", "5.20"],
            "total_share": ["100000.00", "50000.00"],
            "pledge_ratio": ["0.6316", "0.3070"],
        },
        index=[5, 10],
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(data)

    assert result.index.tolist() == [0, 1]


def test_stockpledge_transform_only_target_columns(sample_source_data):
    """Test that only target columns are in output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)

    assert actual_cols == expected_cols


# ============================================================================
# Run Method Tests
# ============================================================================


def test_stockpledge_run_basic(sample_source_data):
    """Test basic run() execution"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"})

    result = pledge.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_stockpledge_run_with_cache_hit(sample_source_data):
    """Test that run() returns cached data when available"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"}, cache=True)

    # First run should fetch and cache
    result1 = pledge.run()

    # Second run should return cached data
    result2 = pledge.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_stockpledge_run_with_end_date(sample_source_data):
    """Test run() with end_date parameter"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"end_date": "20180928"})

    result = pledge.run()

    assert isinstance(result, pd.DataFrame)


def test_stockpledge_run_with_datetime_params(sample_source_data):
    """Test run() with datetime objects as parameters"""
    from datetime import datetime

    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(
        session=session,
        params={
            "ts_code": "000014.SZ",
            "end_date": datetime(2018, 9, 28),
        },
    )

    result = pledge.run()

    assert isinstance(result, pd.DataFrame)


def test_stockpledge_run_adds_fields_param(sample_source_data):
    """Test that run() adds fields parameter if not provided"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"})

    # Monkey patch _fetchall to capture params
    pledge._fetchall
    captured_params = {}

    def mock_fetchall(api, **kwargs):
        captured_params.update(kwargs)
        return sample_source_data

    pledge._fetchall = mock_fetchall
    pledge.run()

    assert "fields" in captured_params
    assert len(captured_params["fields"]) > 0


def test_stockpledge_run_sets_cache(sample_source_data):
    """Test that run() saves result to cache"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"}, cache=True)

    result = pledge.run()

    # Cache should be set after run
    cached = pledge._load_cache()
    assert cached is not None
    pd.testing.assert_frame_equal(result, cached)


def test_stockpledge_run_calls_transform(sample_source_data):
    """Test that run() calls transform method"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"})

    # Monkey patch transform to track if it was called
    original_transform = pledge.transform
    transform_called = {"called": False}

    def mock_transform(data):
        transform_called["called"] = True
        return original_transform(data)

    pledge.transform = mock_transform
    pledge.run()

    assert transform_called["called"] is True


def test_stockpledge_run_uses_pledge_stat_api(sample_source_data):
    """Test that run() uses pledge_stat API"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"})

    # Monkey patch _fetchall to capture API
    captured_api = {"api": None}

    def mock_fetchall(api, **kwargs):
        captured_api["api"] = api
        return sample_source_data

    pledge._fetchall = mock_fetchall
    pledge.run()

    assert captured_api["api"] == session.connection.pledge_stat


# ============================================================================
# Integration Tests
# ============================================================================


def test_stockpledge_full_workflow(sample_source_data):
    """Test complete workflow from initialization to output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    pledge = StockPledge(
        session=session,
        params={"ts_code": "000014.SZ"},
        cache=True,
    )

    result = pledge.run()

    # Verify output structure
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "pledge_count" in result.columns
    assert "pledge_ratio" in result.columns

    # Verify data types
    assert pd.api.types.is_numeric_dtype(result["pledge_ratio"])
    assert pd.api.types.is_integer_dtype(result["pledge_count"])


def test_stockpledge_cache_persistence(sample_source_data):
    """Test that cache persists across multiple runs"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"}, cache=True)

    # Run once to populate cache
    result1 = pledge.run()

    # Clear in-memory data to simulate fresh load
    pledge2 = StockPledge(session=session, params={"ts_code": "000014.SZ"}, cache=True)
    result2 = pledge2.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_stockpledge_params_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    pledge1 = StockPledge(
        session=mock_session,
        params={"ts_code": "000014.SZ"},
        cache=True,
    )
    pledge2 = StockPledge(
        session=mock_session,
        params={"ts_code": "600848.SH"},
        cache=True,
    )

    # Test that different params are properly stored
    assert pledge1.params.get("ts_code") == "000014.SZ"
    assert pledge2.params.get("ts_code") == "600848.SH"
    assert pledge1.params.get("ts_code") != pledge2.params.get("ts_code")


def test_stockpledge_empty_result_handling():
    """Test handling of empty API results"""
    empty_data = pd.DataFrame()
    fake_conn = FakeConnection(frame=empty_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"})

    result = pledge.run()

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) > 0


def test_stockpledge_large_dataset_handling():
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": ["000014.SZ"] * 1000,
            "end_date": ["20180928"] * 1000,
            "pledge_count": ["23"] * 1000,
            "unrest_pledge": ["63.16"] * 1000,
            "rest_pledge": ["0.0"] * 1000,
            "total_share": ["100000.00"] * 1000,
            "pledge_ratio": ["0.6316"] * 1000,
        }
    )

    fake_conn = FakeConnection(frame=large_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"})

    result = pledge.run()

    # Should deduplicate to 1 row
    assert len(result) == 1


def test_stockpledge_without_cache(sample_source_data):
    """Test that class works correctly without caching"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"}, cache=False)

    result = pledge.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert pledge.cache is None


def test_stockpledge_handles_missing_fields():
    """Test that missing fields don't break transformation"""
    # Data with only subset of fields
    minimal_data = pd.DataFrame(
        {
            "ts_code": ["000014.SZ"],
            "end_date": ["20180928"],
            "pledge_count": ["23"],
            "unrest_pledge": ["63.16"],
        }
    )

    fake_conn = FakeConnection(frame=minimal_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"ts_code": "000014.SZ"})

    result = pledge.run()

    # Should complete without error
    assert len(result) == 1
    # Missing fields should be NaN
    assert pd.isna(result.iloc[0]["rest_pledge"])


def test_stockpledge_api_doc_reference():
    """Test that class correctly references API documentation"""
    assert "doc_id=110" in StockPledge.__doc__


def test_stockpledge_crosssection_scale():
    """Test that module is correctly configured as crosssection scale"""
    assert SOURCE.meta["scale"] == "crosssection"
    assert TARGET.meta["scale"] == "crosssection"


def test_stockpledge_multiple_stocks_handling(sample_source_data):
    """Test handling of data with multiple stocks"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session, params={"end_date": "20180928"})

    result = pledge.run()

    # Should have data for both stocks
    assert len(result) == 3
    assert "000014.SZ" in result["code"].values
    assert "600848.SH" in result["code"].values


def test_stockpledge_handles_zero_values(sample_source_data):
    """Test that zero values in numeric fields are handled correctly"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    pledge = StockPledge(session=session)

    result = pledge.transform(sample_source_data)

    # Check that zero values are preserved (not treated as missing)
    zero_rest_rows = result[result["rest_pledge"] == 0.0]
    assert len(zero_rest_rows) == 2

"""
Test suite for Weekline class
Tests cover initialization, data fetching, transformation, date handling, and utility methods
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.weekline.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.tushare.stock.weekline.weekline import Weekline

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session():
    """Create a mock Tushare session"""
    session = MagicMock(spec=Session)
    session._credential = "test_token"
    session.id = "test1234"
    session.mode = "direct"
    session.relay_url = None
    session.relay_secret = None
    session.connected = True

    # Mock the connection object
    mock_connection = MagicMock()
    mock_connection.weekly = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "trade_date": ["20241129", "20241129", "20241122"],
            "open": [10.50, 8.20, 15.30],
            "high": [10.80, 8.45, 15.60],
            "low": [10.30, 8.00, 15.10],
            "close": [10.75, 8.35, 15.45],
            "pre_close": [10.50, 8.20, 15.20],
            "change": [0.25, 0.15, 0.25],
            "pct_chg": [2.38, 1.83, 1.64],
            "vol": [6250000.0, 4900000.0, 10500000.0],
            "amount": [672500.0, 406000.0, 1622500.0],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_weekline_initialization_basic(mock_session):
    """Test basic initialization"""
    job = Weekline(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET
    assert job.paginate.pagesize == 6000


def test_weekline_initialization_with_params(mock_session):
    """Test initialization with params"""
    params = {"ts_code": "000001.SZ", "start_date": "20240101"}
    job = Weekline(session=mock_session, params=params)

    assert job.params.ts_code == "000001.SZ"
    assert job.params.start_date == "20240101"


def test_weekline_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    params = {"ts_code": "000001.SZ"}
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = Weekline(
        session=mock_session,
        params=params,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert job.params.ts_code == "000001.SZ"
    assert job.coolant.interval == 0.2
    assert job.retry.retry == 3
    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_weekline_name_and_key():
    """Test name and key constants"""
    assert NAME == "weekline"
    assert KEY == "/tushare/weekline"


def test_weekline_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert SOURCE.desc == "A股周线行情数据（Tushare格式）"

    column_names = SOURCE.columns
    assert "ts_code" in column_names
    assert "trade_date" in column_names
    assert "open" in column_names
    assert "high" in column_names
    assert "low" in column_names
    assert "close" in column_names
    assert "vol" in column_names
    assert "amount" in column_names


def test_weekline_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert TARGET.desc == "A股周线行情数据（xfintech格式）"

    column_names = TARGET.columns
    assert "code" in column_names
    assert "date" in column_names
    assert "datecode" in column_names
    assert "open" in column_names
    assert "close" in column_names
    assert "percent_change" in column_names
    assert "volume" in column_names
    assert "amount" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_weekline_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = Weekline(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "datecode" in result.columns
    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[0]["datecode"] == "20241129"


def test_weekline_transform_date_conversion(mock_session, sample_source_data):
    """Test date field conversions"""
    job = Weekline(session=mock_session)
    result = job.transform(sample_source_data)

    # Check date format (YYYY-MM-DD)
    assert result.iloc[0]["date"] == "2024-11-29"
    assert result.iloc[1]["date"] == "2024-11-29"
    assert result.iloc[2]["date"] == "2024-11-22"

    # Check datecode format (YYYYMMDD)
    assert result.iloc[0]["datecode"] == "20241129"


def test_weekline_transform_price_fields(mock_session, sample_source_data):
    """Test price field transformations"""
    job = Weekline(session=mock_session)
    result = job.transform(sample_source_data)

    row = result.iloc[0]
    assert row["open"] == 10.50
    assert row["high"] == 10.80
    assert row["low"] == 10.30
    assert row["close"] == 10.75
    assert row["pre_close"] == 10.50
    assert row["change"] == 0.25
    assert row["percent_change"] == 2.38


def test_weekline_transform_volume_fields(mock_session, sample_source_data):
    """Test volume field transformations"""
    job = Weekline(session=mock_session)
    result = job.transform(sample_source_data)

    row = result.iloc[0]
    assert row["volume"] == 6250000.0
    assert row["amount"] == 672500.0


def test_weekline_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = Weekline(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_weekline_transform_invalid_data(mock_session):
    """Test transform with invalid numeric values"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "trade_date": ["20241129", "invalid_date"],
            "open": [10.50, "invalid"],
            "high": [10.80, 8.45],
            "low": [10.30, 8.00],
            "close": [10.75, 8.35],
            "pre_close": [10.50, 8.20],
            "change": [0.25, 0.15],
            "pct_chg": [2.38, 1.83],
            "vol": [6250000.0, 4900000.0],
            "amount": [672500.0, 406000.0],
        }
    )
    job = Weekline(session=mock_session)
    result = job.transform(data)

    # Should handle invalid data gracefully
    assert len(result) == 2
    assert pd.isna(result.iloc[1]["date"])  # Invalid date
    assert pd.isna(result.iloc[1]["open"])  # Invalid numeric


def test_weekline_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "trade_date": ["20241129", "20241129", "20241129"],
            "open": [10.50, 10.50, 8.20],
            "high": [10.80, 10.80, 8.45],
            "low": [10.30, 10.30, 8.00],
            "close": [10.75, 10.75, 8.35],
            "pre_close": [10.50, 10.50, 8.20],
            "change": [0.25, 0.25, 0.15],
            "pct_chg": [2.38, 2.38, 1.83],
            "vol": [6250000.0, 6250000.0, 4900000.0],
            "amount": [672500.0, 672500.0, 406000.0],
        }
    )
    job = Weekline(session=mock_session)
    result = job.transform(data)

    # Duplicates should be removed
    assert len(result) == 2


def test_weekline_transform_sorting(mock_session):
    """Test that result is sorted by code and date"""
    data = pd.DataFrame(
        {
            "ts_code": ["600000.SH", "000001.SZ", "000002.SZ"],
            "trade_date": ["20241115", "20241129", "20241122"],
            "open": [15.30, 10.50, 8.20],
            "high": [15.60, 10.80, 8.45],
            "low": [15.10, 10.30, 8.00],
            "close": [15.45, 10.75, 8.35],
            "pre_close": [15.20, 10.50, 8.20],
            "change": [0.25, 0.25, 0.15],
            "pct_chg": [1.64, 2.38, 1.83],
            "vol": [10500000.0, 6250000.0, 4900000.0],
            "amount": [1622500.0, 672500.0, 406000.0],
        }
    )
    job = Weekline(session=mock_session)
    result = job.transform(data)

    # Should be sorted by code, then date
    expected_order = ["000001.SZ", "000002.SZ", "600000.SH"]
    actual_order = result["code"].tolist()
    assert actual_order == expected_order


# ============================================================================
# Run Tests
# ============================================================================


def test_weekline_run_basic(mock_session, sample_source_data):
    """Test basic run method"""
    job = Weekline(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "code" in result.columns
        assert "date" in result.columns


def test_weekline_run_with_ts_code(mock_session, sample_source_data):
    """Test run with ts_code parameter"""
    filtered_data = sample_source_data[sample_source_data["ts_code"] == "000001.SZ"]

    job = Weekline(session=mock_session, params={"ts_code": "000001.SZ"})

    with patch.object(job, "_fetchall", return_value=filtered_data):
        result = job.run()

        assert len(result) == 1
        assert result["code"].iloc[0] == "000001.SZ"


def test_weekline_run_with_trade_date_string(mock_session, sample_source_data):
    """Test run with trade_date as string"""
    job = Weekline(session=mock_session, params={"trade_date": "20241129"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["trade_date"] == "20241129"


def test_weekline_run_with_date_range_string(mock_session, sample_source_data):
    """Test run with start_date and end_date as strings"""
    job = Weekline(
        session=mock_session,
        params={"start_date": "20241101", "end_date": "20241231"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["start_date"] == "20241101"
        assert call_kwargs["end_date"] == "20241231"


def test_weekline_run_calls_transform(mock_session, sample_source_data):
    """Test that run calls transform"""
    job = Weekline(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "transform", wraps=job.transform) as mock_transform:
            job.run()

            mock_transform.assert_called_once()


# ============================================================================
# Cache Tests
# ============================================================================


def test_weekline_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across runs"""
    job = Weekline(session=mock_session, cache=True)

    with patch.object(job, "_load_cache", return_value=None) as mock_load:
        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            # First run - fetches data and caches it
            result1 = job.run()
            assert mock_fetchall.call_count == 1
            assert mock_load.call_count == 1

            # Second run - _load_cache still returns None, so _fetchall called again
            result2 = job.run()
            assert mock_fetchall.call_count == 2
            assert mock_load.call_count == 2

            pd.testing.assert_frame_equal(result1, result2)


def test_weekline_params_identifier_uniqueness(mock_session):
    """Test that different params create different cache keys"""
    job1 = Weekline(session=mock_session, params={"trade_date": "20241129"}, cache=True)
    job2 = Weekline(session=mock_session, params={"trade_date": "20241122"}, cache=True)

    assert job1.params.identifier != job2.params.identifier


def test_weekline_without_cache(mock_session, sample_source_data):
    """Test that weekline works correctly without cache"""
    job = Weekline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()
        job.run()

        # Should fetch twice (no caching)
        assert mock_fetchall.call_count == 2


# ============================================================================
# List Methods Tests
# ============================================================================


def test_weekline_list_codes(mock_session, sample_source_data):
    """Test list_codes method"""
    job = Weekline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        codes = job.list_codes()

        assert isinstance(codes, list)
        assert len(codes) == 3
        assert "000001.SZ" in codes
        assert "000002.SZ" in codes
        assert "600000.SH" in codes
        assert codes == sorted(codes)  # Should be sorted


def test_weekline_list_dates(mock_session, sample_source_data):
    """Test list_dates method"""
    job = Weekline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        dates = job.list_dates()

        assert isinstance(dates, list)
        assert len(dates) == 2  # Two unique dates
        assert "2024-11-22" in dates
        assert "2024-11-29" in dates
        assert dates == sorted(dates)  # Should be sorted


def test_weekline_list_codes_unique(mock_session):
    """Test that list_codes returns unique codes"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "trade_date": ["20241129", "20241122", "20241129"],
            "open": [10.50, 10.60, 8.20],
            "high": [10.80, 10.90, 8.45],
            "low": [10.30, 10.40, 8.00],
            "close": [10.75, 10.85, 8.35],
            "pre_close": [10.50, 10.60, 8.20],
            "change": [0.25, 0.25, 0.15],
            "pct_chg": [2.38, 2.36, 1.83],
            "vol": [6250000.0, 6500000.0, 4900000.0],
            "amount": [672500.0, 702500.0, 406000.0],
        }
    )

    job = Weekline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=data):
        codes = job.list_codes()

        assert len(codes) == 2  # Should be unique


def test_weekline_list_dates_sorted(mock_session):
    """Test that list_dates returns sorted dates"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "trade_date": ["20241229", "20241108", "20241115"],
            "open": [10.50, 8.20, 15.30],
            "high": [10.80, 8.45, 15.60],
            "low": [10.30, 8.00, 15.10],
            "close": [10.75, 8.35, 15.45],
            "pre_close": [10.50, 8.20, 15.20],
            "change": [0.25, 0.15, 0.25],
            "pct_chg": [2.38, 1.83, 1.64],
            "vol": [6250000.0, 4900000.0, 10500000.0],
            "amount": [672500.0, 406000.0, 1622500.0],
        }
    )

    job = Weekline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=data):
        dates = job.list_dates()

        expected_dates = ["2024-11-08", "2024-11-15", "2024-12-29"]
        assert dates == expected_dates


# ============================================================================
# Integration Tests
# ============================================================================


def test_weekline_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    job = Weekline(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20241101", "end_date": "20241231"},
        cache=False,
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()
        codes = job.list_codes()
        dates = job.list_dates()

        assert len(result) > 0
        assert len(codes) > 0
        assert len(dates) > 0


def test_weekline_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": [f"{str(i).zfill(6)}.SZ" for i in range(1000)],
            "trade_date": ["20241129"] * 1000,
            "open": [10.50] * 1000,
            "high": [10.80] * 1000,
            "low": [10.30] * 1000,
            "close": [10.75] * 1000,
            "pre_close": [10.50] * 1000,
            "change": [0.25] * 1000,
            "pct_chg": [2.38] * 1000,
            "vol": [6250000.0] * 1000,
            "amount": [672500.0] * 1000,
        }
    )

    job = Weekline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=large_data):
        result = job.run()

    assert len(result) == 1000


def test_weekline_handles_missing_fields(mock_session):
    """Test handling of data with some missing fields"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "trade_date": ["20241129"],
            "open": [10.50],
            "high": [10.80],
            "low": [10.30],
            "close": [10.75],
            "pre_close": [10.50],
            "change": [0.25],
            "pct_chg": [2.38],
            "vol": [None],  # Missing volume
            "amount": [None],  # Missing amount
        }
    )

    job = Weekline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        assert len(result) == 1
        assert pd.isna(result.iloc[0]["volume"])
        assert pd.isna(result.iloc[0]["amount"])

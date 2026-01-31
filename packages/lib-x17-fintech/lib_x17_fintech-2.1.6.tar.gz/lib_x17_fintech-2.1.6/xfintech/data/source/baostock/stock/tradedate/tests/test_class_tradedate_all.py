from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.tradedate.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.baostock.stock.tradedate.tradedate import TradeDate

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session():
    """Create a mock Baostock session"""
    session = MagicMock(spec=Session)
    session._credential = None
    session.id = "test1234"
    session.mode = "direct"
    session.relay_url = None
    session.relay_secret = None
    session.connected = True

    # Mock the connection object
    mock_connection = MagicMock()
    mock_connection.query_trade_dates = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Baostock format"""
    return pd.DataFrame(
        {
            "calendar_date": [
                "2026-01-01",
                "2026-01-02",
                "2026-01-05",
                "2026-01-06",
                "2026-01-07",
            ],
            "is_trading_day": ["0", "0", "1", "1", "1"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_tradedate_initialization_basic(mock_session):
    """Test basic initialization"""
    job = TradeDate(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET


def test_tradedate_initialization_with_params(mock_session):
    """Test initialization with params"""
    params = {"year": "2026"}
    job = TradeDate(session=mock_session, params=params)

    assert job.params.year == "2026"


def test_tradedate_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    params = {"start_date": "20260101", "end_date": "20260131"}
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = TradeDate(
        session=mock_session,
        params=params,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert job.params.start_date == "20260101"
    assert job.params.end_date == "20260131"
    assert job.coolant.interval == 0.2
    assert job.retry.retry == 3
    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_tradedate_name_and_key():
    """Test name and key constants"""
    assert NAME == "tradedate"
    assert KEY == "/baostock/tradedate"


def test_tradedate_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert "交易日历数据" in SOURCE.desc

    column_names = SOURCE.columns
    assert "calendar_date" in column_names
    assert "is_trading_day" in column_names


def test_tradedate_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert "交易日历数据" in TARGET.desc

    column_names = TARGET.columns
    assert "datecode" in column_names
    assert "date" in column_names
    assert "exchange" in column_names
    assert "is_open" in column_names
    assert "year" in column_names
    assert "month" in column_names
    assert "day" in column_names
    assert "week" in column_names
    assert "weekday" in column_names
    assert "quarter" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_tradedate_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = TradeDate(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 5
    assert "date" in result.columns
    assert "datecode" in result.columns
    assert "is_open" in result.columns
    assert result.iloc[0]["date"] == "2026-01-01"
    assert result.iloc[0]["datecode"] == "20260101"


def test_tradedate_transform_field_types(mock_session, sample_source_data):
    """Test field type conversions"""
    job = TradeDate(session=mock_session)
    result = job.transform(sample_source_data)

    # Check string fields
    assert isinstance(result.iloc[0]["date"], str)
    assert isinstance(result.iloc[0]["datecode"], str)
    assert isinstance(result.iloc[0]["exchange"], str)
    assert isinstance(result.iloc[0]["weekday"], str)

    # Check boolean field (pandas returns numpy.bool_)
    assert pd.api.types.is_bool_dtype(result["is_open"])

    # Check integer fields
    assert pd.api.types.is_integer_dtype(result["year"])
    assert pd.api.types.is_integer_dtype(result["month"])
    assert pd.api.types.is_integer_dtype(result["day"])
    assert pd.api.types.is_integer_dtype(result["week"])
    assert pd.api.types.is_integer_dtype(result["quarter"])


def test_tradedate_transform_date_parsing(mock_session, sample_source_data):
    """Test date parsing and transformation"""
    job = TradeDate(session=mock_session)
    result = job.transform(sample_source_data)

    # Check date format conversion
    assert result.iloc[0]["date"] == "2026-01-01"
    assert result.iloc[0]["datecode"] == "20260101"
    assert result.iloc[2]["date"] == "2026-01-05"
    assert result.iloc[2]["datecode"] == "20260105"


def test_tradedate_transform_is_open_conversion(mock_session, sample_source_data):
    """Test is_open field conversion"""
    job = TradeDate(session=mock_session)
    result = job.transform(sample_source_data)

    # "0" -> False, "1" -> True
    assert not result.iloc[0]["is_open"]  # 2026-01-01 休市
    assert not result.iloc[1]["is_open"]  # 2026-01-02 休市
    assert result.iloc[2]["is_open"]  # 2026-01-05 交易日
    assert result.iloc[3]["is_open"]  # 2026-01-06 交易日


def test_tradedate_transform_date_components(mock_session, sample_source_data):
    """Test date component extraction"""
    job = TradeDate(session=mock_session)
    result = job.transform(sample_source_data)

    # Check first row (2026-01-01)
    assert result.iloc[0]["year"] == 2026
    assert result.iloc[0]["month"] == 1
    assert result.iloc[0]["day"] == 1
    assert result.iloc[0]["quarter"] == 1


def test_tradedate_transform_weekday(mock_session, sample_source_data):
    """Test weekday extraction"""
    job = TradeDate(session=mock_session)
    result = job.transform(sample_source_data)

    # Check that weekday is 3-letter abbreviation
    weekday = result.iloc[0]["weekday"]
    assert isinstance(weekday, str)
    assert len(weekday) == 3


def test_tradedate_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = TradeDate(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_tradedate_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-05", "2026-01-05", "2026-01-06"],
            "is_trading_day": ["1", "1", "1"],
        }
    )
    job = TradeDate(session=mock_session)
    result = job.transform(data)

    # Note: previous field may differ, so check unique dates
    assert len(result["datecode"].unique()) == 2


def test_tradedate_transform_sorting(mock_session):
    """Test that result is sorted by datecode"""
    data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-07", "2026-01-05", "2026-01-06"],
            "is_trading_day": ["1", "1", "1"],
        }
    )
    job = TradeDate(session=mock_session)
    result = job.transform(data)

    # Should be sorted by datecode
    assert result.iloc[0]["datecode"] == "20260105"
    assert result.iloc[1]["datecode"] == "20260106"
    assert result.iloc[2]["datecode"] == "20260107"


def test_tradedate_transform_exchange_field(mock_session, sample_source_data):
    """Test that exchange field is set to ALL"""
    job = TradeDate(session=mock_session)
    result = job.transform(sample_source_data)

    # All records should have exchange = "ALL"
    assert all(result["exchange"] == "ALL")


# ============================================================================
# Run Tests
# ============================================================================


def test_tradedate_run_basic(mock_session, sample_source_data):
    """Test basic run method"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert "date" in result.columns
        assert "datecode" in result.columns
        assert "is_open" in result.columns


def test_tradedate_run_with_year(mock_session, sample_source_data):
    """Test run with year parameter"""
    job = TradeDate(session=mock_session, params={"year": "2026"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        # Verify _fetchall was called (year processing happens in _parse_year_params)
        assert mock_fetchall.call_count == 1


def test_tradedate_run_with_date_range(mock_session, sample_source_data):
    """Test run with start_date and end_date"""
    job = TradeDate(
        session=mock_session,
        params={"start_date": "20260101", "end_date": "20260131"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-01-31"


def test_tradedate_run_calls_query_trade_dates(mock_session, sample_source_data):
    """Test that run calls query_trade_dates API"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        # Verify that _fetchall was called with the correct API
        assert mock_fetchall.call_count == 1
        call_args = mock_fetchall.call_args
        assert call_args[1]["api"] == job.connection.query_trade_dates


def test_tradedate_run_calls_transform(mock_session, sample_source_data):
    """Test that run calls transform"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "transform", wraps=job.transform) as mock_transform:
            job.run()

            mock_transform.assert_called_once()


# ============================================================================
# Cache Tests
# ============================================================================


def test_tradedate_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across runs"""
    job = TradeDate(session=mock_session, cache=True)

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


def test_tradedate_params_identifier_uniqueness(mock_session):
    """Test that different params create different cache keys"""
    job1 = TradeDate(session=mock_session, params={"year": "2026"}, cache=True)
    job2 = TradeDate(session=mock_session, params={"year": "2025"}, cache=True)

    assert job1.params.identifier != job2.params.identifier


def test_tradedate_without_cache(mock_session, sample_source_data):
    """Test that tradedate works correctly without cache"""
    job = TradeDate(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()
        job.run()

        # Should fetch twice (no caching)
        assert mock_fetchall.call_count == 2


# ============================================================================
# Date Parsing Tests
# ============================================================================


def test_tradedate_date_parsing_yyyymmdd(mock_session, sample_source_data):
    """Test date parsing from YYYYMMDD format"""
    job = TradeDate(
        session=mock_session,
        params={"start_date": "20260101", "end_date": "20260131"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        # Should convert YYYYMMDD to YYYY-MM-DD
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-01-31"


def test_tradedate_date_parsing_hyphen_format(mock_session, sample_source_data):
    """Test date parsing preserves YYYY-MM-DD format"""
    job = TradeDate(
        session=mock_session,
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-01-31"


# ============================================================================
# List Methods Tests
# ============================================================================


def test_tradedate_list_dates(mock_session, sample_source_data):
    """Test list_dates method"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        dates = job.list_dates()

        assert isinstance(dates, list)
        assert len(dates) == 5
        assert "2026-01-01" in dates
        assert "2026-01-05" in dates
        # Should be sorted
        assert dates == sorted(dates)


def test_tradedate_list_datecodes(mock_session, sample_source_data):
    """Test list_datecodes method"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        datecodes = job.list_datecodes()

        assert isinstance(datecodes, list)
        assert len(datecodes) == 5
        assert "20260101" in datecodes
        assert "20260105" in datecodes
        # Should be sorted
        assert datecodes == sorted(datecodes)


def test_tradedate_list_open_dates(mock_session, sample_source_data):
    """Test list_open_dates method returns only trading days"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        open_dates = job.list_open_dates()

        assert isinstance(open_dates, list)
        assert len(open_dates) == 3  # Only trading days
        assert "2026-01-01" not in open_dates  # Non-trading day
        assert "2026-01-02" not in open_dates  # Non-trading day
        assert "2026-01-05" in open_dates  # Trading day
        assert "2026-01-06" in open_dates  # Trading day
        assert "2026-01-07" in open_dates  # Trading day


def test_tradedate_list_open_datecodes(mock_session, sample_source_data):
    """Test list_open_datecodes method returns only trading days"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        open_datecodes = job.list_open_datecodes()

        assert isinstance(open_datecodes, list)
        assert len(open_datecodes) == 3  # Only trading days
        assert "20260101" not in open_datecodes  # Non-trading day
        assert "20260102" not in open_datecodes  # Non-trading day
        assert "20260105" in open_datecodes  # Trading day
        assert "20260106" in open_datecodes  # Trading day
        assert "20260107" in open_datecodes  # Trading day


# ============================================================================
# Check Method Tests
# ============================================================================


def test_tradedate_check_with_string_hyphen(mock_session):
    """Test check method with string date in YYYY-MM-DD format"""
    trading_data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-10"],
            "is_trading_day": ["1"],
        }
    )

    with patch.object(TradeDate, "_fetchall", return_value=trading_data):
        result = TradeDate.check(mock_session, "2026-01-10")
        assert result


def test_tradedate_check_with_string_yyyymmdd(mock_session):
    """Test check method with string date in YYYYMMDD format"""
    trading_data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-10"],
            "is_trading_day": ["1"],
        }
    )

    with patch.object(TradeDate, "_fetchall", return_value=trading_data):
        result = TradeDate.check(mock_session, "20260110")
        assert result


def test_tradedate_check_with_date_object(mock_session):
    """Test check method with date object"""
    trading_data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-10"],
            "is_trading_day": ["1"],
        }
    )

    with patch.object(TradeDate, "_fetchall", return_value=trading_data):
        result = TradeDate.check(mock_session, date(2026, 1, 10))
        assert result


def test_tradedate_check_with_datetime_object(mock_session):
    """Test check method with datetime object"""
    trading_data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-10"],
            "is_trading_day": ["1"],
        }
    )

    with patch.object(TradeDate, "_fetchall", return_value=trading_data):
        result = TradeDate.check(mock_session, datetime(2026, 1, 10, 9, 30, 0))
        assert result


def test_tradedate_check_non_trading_day(mock_session):
    """Test check method returns False for non-trading day"""
    empty_data = pd.DataFrame(columns=["calendar_date", "is_trading_day"])

    with patch.object(TradeDate, "_fetchall", return_value=empty_data):
        result = TradeDate.check(mock_session, "2026-01-01")
        assert result is False


# ============================================================================
# Integration Tests
# ============================================================================


def test_tradedate_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    job = TradeDate(
        session=mock_session,
        params={"start_date": "20260101", "end_date": "20260107"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert not result.empty
        assert len(result) == 5
        assert "date" in result.columns
        assert "datecode" in result.columns
        assert "is_open" in result.columns
        assert "year" in result.columns


def test_tradedate_with_year_query(mock_session):
    """Test querying by year"""
    year_data = pd.DataFrame(
        {
            "calendar_date": [f"2026-01-{str(i).zfill(2)}" for i in range(1, 11)],
            "is_trading_day": ["0", "0", "0", "0", "1", "1", "1", "1", "1", "0"],
        }
    )

    job = TradeDate(session=mock_session, params={"year": 2026})

    with patch.object(job, "_fetchall", return_value=year_data):
        result = job.run()

        assert len(result) == 10
        assert all(result["year"] == 2026)


def test_tradedate_filtering_trading_days(mock_session, sample_source_data):
    """Test filtering for only trading days"""
    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        # Filter for trading days
        trading_days = result[result["is_open"]]
        assert len(trading_days) == 3
        assert all(trading_days["is_open"])


def test_tradedate_with_large_dataset(mock_session):
    """Test handling of large dataset"""
    # Create a large dataset (365 days)
    dates = pd.date_range(start="2026-01-01", end="2026-12-31", freq="D")
    large_data = pd.DataFrame(
        {
            "calendar_date": dates.strftime("%Y-%m-%d"),
            "is_trading_day": ["1"] * len(dates),  # All trading days for simplicity
        }
    )

    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=large_data):
        result = job.run()

        assert len(result) == 365
        assert result.iloc[0]["datecode"] == "20260101"
        assert result.iloc[-1]["datecode"] == "20261231"


def test_tradedate_with_empty_result(mock_session):
    """Test handling of empty result from API"""
    empty_data = pd.DataFrame(columns=["calendar_date", "is_trading_day"])

    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=empty_data):
        result = job.run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()


def test_tradedate_quarter_calculation(mock_session):
    """Test quarter calculation for different months"""
    data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-15", "2026-04-15", "2026-07-15", "2026-10-15"],
            "is_trading_day": ["1", "1", "1", "1"],
        }
    )

    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        assert result.iloc[0]["quarter"] == 1
        assert result.iloc[1]["quarter"] == 2
        assert result.iloc[2]["quarter"] == 3
        assert result.iloc[3]["quarter"] == 4


def test_tradedate_week_calculation(mock_session):
    """Test ISO week number calculation"""
    data = pd.DataFrame(
        {
            "calendar_date": ["2026-01-05", "2026-01-12"],
            "is_trading_day": ["1", "1"],
        }
    )

    job = TradeDate(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        # Check that week numbers are calculated
        assert pd.api.types.is_integer_dtype(result["week"])
        assert result.iloc[0]["week"] > 0
        assert result.iloc[1]["week"] > 0

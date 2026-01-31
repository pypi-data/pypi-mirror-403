from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.minuteline.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.baostock.stock.minuteline.minuteline import Minuteline

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
    mock_connection.query_history_k_data_plus = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Baostock format"""
    return pd.DataFrame(
        {
            "date": ["2026-01-10", "2026-01-10", "2026-01-09"],
            "time": ["093500000", "094000000", "150000000"],
            "code": ["sh.600000", "sh.600000", "sz.000001"],
            "open": ["10.50", "10.60", "8.20"],
            "high": ["10.80", "10.70", "8.45"],
            "low": ["10.30", "10.40", "8.00"],
            "close": ["10.75", "10.65", "8.35"],
            "volume": ["6250000", "5500000", "4900000"],
            "amount": ["672500000", "585500000", "406000000"],
            "adjustflag": ["3", "3", "3"],
            "turn": ["", "", ""],
            "tradestatus": ["1", "1", "1"],
            "pctChg": ["", "", ""],
            "isST": ["0", "0", "0"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_minuteline_initialization_basic(mock_session):
    """Test basic initialization"""
    job = Minuteline(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET


def test_minuteline_initialization_with_params(mock_session):
    """Test initialization with params"""
    params = {"code": "sh.600000", "start_date": "2026-01-01"}
    job = Minuteline(session=mock_session, params=params)

    assert job.params.code == "sh.600000"
    assert job.params.start_date == "2026-01-01"


def test_minuteline_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    params = {"code": "sh.600000", "frequency": "5", "adjustflag": "3"}
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = Minuteline(
        session=mock_session,
        params=params,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert job.params.code == "sh.600000"
    assert job.coolant.interval == 0.2
    assert job.retry.retry == 3
    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_minuteline_name_and_key():
    """Test name and key constants"""
    assert NAME == "minuteline"
    assert KEY == "/baostock/minuteline"


def test_minuteline_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert SOURCE.desc == "A股分钟线行情数据（BaoStock格式）"

    column_names = SOURCE.columns
    assert "date" in column_names
    assert "time" in column_names
    assert "code" in column_names
    assert "open" in column_names
    assert "high" in column_names
    assert "low" in column_names
    assert "close" in column_names
    assert "volume" in column_names
    assert "amount" in column_names
    assert "adjustflag" in column_names


def test_minuteline_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert TARGET.desc == "A股分钟线行情数据（xfintech格式）"

    column_names = TARGET.columns
    assert "code" in column_names
    assert "date" in column_names
    assert "time" in column_names
    assert "open" in column_names
    assert "high" in column_names
    assert "low" in column_names
    assert "close" in column_names
    assert "volume" in column_names
    assert "amount" in column_names
    assert "adjustflag" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_minuteline_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = Minuteline(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "time" in result.columns
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[0]["date"] == "2026-01-10"


def test_minuteline_transform_field_types(mock_session, sample_source_data):
    """Test field type conversions"""
    job = Minuteline(session=mock_session)
    result = job.transform(sample_source_data)

    # Check string fields
    assert isinstance(result.iloc[0]["code"], str)
    assert isinstance(result.iloc[0]["date"], str)
    assert isinstance(result.iloc[0]["time"], str)
    assert isinstance(result.iloc[0]["adjustflag"], str)

    # Check numeric fields (pandas converts to numpy types)
    assert pd.api.types.is_numeric_dtype(result["open"])
    assert pd.api.types.is_numeric_dtype(result["high"])
    assert pd.api.types.is_numeric_dtype(result["low"])
    assert pd.api.types.is_numeric_dtype(result["close"])
    assert pd.api.types.is_numeric_dtype(result["volume"])
    assert pd.api.types.is_numeric_dtype(result["amount"])


def test_minuteline_transform_price_fields(mock_session, sample_source_data):
    """Test price field transformations"""
    job = Minuteline(session=mock_session)
    result = job.transform(sample_source_data)

    row = result.iloc[0]
    assert row["open"] == 10.50
    assert row["high"] == 10.80
    assert row["low"] == 10.30
    assert row["close"] == 10.75


def test_minuteline_transform_volume_fields(mock_session, sample_source_data):
    """Test volume field transformations"""
    job = Minuteline(session=mock_session)
    result = job.transform(sample_source_data)

    row = result.iloc[0]
    assert row["volume"] == 6250000.0
    assert row["amount"] == 672500000.0


def test_minuteline_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = Minuteline(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_minuteline_transform_invalid_data(mock_session):
    """Test transform with invalid numeric values"""
    data = pd.DataFrame(
        {
            "date": ["2026-01-10", "invalid_date"],
            "time": ["093500000", "094000000"],
            "code": ["sh.600000", "sh.600001"],
            "open": ["10.50", "invalid"],
            "high": ["10.80", "10.70"],
            "low": ["10.30", "10.40"],
            "close": ["10.75", "10.65"],
            "volume": ["6250000", "5500000"],
            "amount": ["672500000", "585500000"],
            "adjustflag": ["3", "3"],
        }
    )
    job = Minuteline(session=mock_session)
    result = job.transform(data)

    # Should handle invalid data gracefully
    assert len(result) == 2
    assert pd.isna(result.iloc[1]["open"])  # Invalid numeric


def test_minuteline_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "date": ["2026-01-10", "2026-01-10", "2026-01-10"],
            "time": ["093500000", "093500000", "094000000"],
            "code": ["sh.600000", "sh.600000", "sh.600000"],
            "open": ["10.50", "10.50", "10.60"],
            "high": ["10.80", "10.80", "10.70"],
            "low": ["10.30", "10.30", "10.40"],
            "close": ["10.75", "10.75", "10.65"],
            "volume": ["6250000", "6250000", "5500000"],
            "amount": ["672500000", "672500000", "585500000"],
            "adjustflag": ["3", "3", "3"],
        }
    )
    job = Minuteline(session=mock_session)
    result = job.transform(data)

    # Duplicates should be removed
    assert len(result) == 2


def test_minuteline_transform_sorting(mock_session):
    """Test that result is sorted by code, date, and time"""
    data = pd.DataFrame(
        {
            "date": ["2026-01-10", "2026-01-09", "2026-01-10"],
            "time": ["094000000", "150000000", "093500000"],
            "code": ["sh.600000", "sz.000001", "sh.600000"],
            "open": ["10.60", "8.20", "10.50"],
            "high": ["10.70", "8.45", "10.80"],
            "low": ["10.40", "8.00", "10.30"],
            "close": ["10.65", "8.35", "10.75"],
            "volume": ["5500000", "4900000", "6250000"],
            "amount": ["585500000", "406000000", "672500000"],
            "adjustflag": ["3", "3", "3"],
        }
    )
    job = Minuteline(session=mock_session)
    result = job.transform(data)

    # Should be sorted by code, date, then time
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[0]["time"] == "093500000"
    assert result.iloc[1]["code"] == "sh.600000"
    assert result.iloc[1]["time"] == "094000000"
    assert result.iloc[2]["code"] == "sz.000001"


# ============================================================================
# Run Tests
# ============================================================================


def test_minuteline_run_basic(mock_session, sample_source_data):
    """Test basic run method"""
    job = Minuteline(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "code" in result.columns
        assert "date" in result.columns
        assert "time" in result.columns


def test_minuteline_run_with_code(mock_session, sample_source_data):
    """Test run with code parameter"""
    filtered_data = sample_source_data[sample_source_data["code"] == "sh.600000"]

    job = Minuteline(session=mock_session, params={"code": "sh.600000"})

    with patch.object(job, "_fetchall", return_value=filtered_data):
        result = job.run()

        assert len(result) == 2
        assert result["code"].iloc[0] == "sh.600000"


def test_minuteline_run_with_frequency(mock_session, sample_source_data):
    """Test run with frequency parameter"""
    job = Minuteline(session=mock_session, params={"code": "sh.600000", "frequency": "15"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()
        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["frequency"] == "15"


def test_minuteline_run_with_adjustflag(mock_session, sample_source_data):
    """Test run with adjustflag parameter"""
    job = Minuteline(session=mock_session, params={"code": "sh.600000", "adjustflag": "1"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()
        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["adjustflag"] == "1"


def test_minuteline_run_with_date_range_string(mock_session, sample_source_data):
    """Test run with start_date and end_date as strings"""
    job = Minuteline(
        session=mock_session,
        params={"code": "sh.600000", "start_date": "2026-01-01", "end_date": "2026-01-31"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-01-31"


def test_minuteline_run_fields_parameter(mock_session, sample_source_data):
    """Test that fields parameter is correctly constructed"""
    job = Minuteline(session=mock_session, params={"code": "sh.600000"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert "fields" in call_kwargs
        fields = call_kwargs["fields"].split(",")
        assert "date" in fields
        assert "time" in fields
        assert "code" in fields
        assert "open" in fields
        assert "close" in fields


def test_minuteline_run_calls_transform(mock_session, sample_source_data):
    """Test that run calls transform"""
    job = Minuteline(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "transform", wraps=job.transform) as mock_transform:
            job.run()

            mock_transform.assert_called_once()


# ============================================================================
# Cache Tests
# ============================================================================


def test_minuteline_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across runs"""
    job = Minuteline(session=mock_session, cache=True)

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


def test_minuteline_params_identifier_uniqueness(mock_session):
    """Test that different params create different cache keys"""
    job1 = Minuteline(session=mock_session, params={"code": "sh.600000", "frequency": "5"}, cache=True)
    job2 = Minuteline(session=mock_session, params={"code": "sh.600000", "frequency": "15"}, cache=True)

    assert job1.params.identifier != job2.params.identifier


def test_minuteline_without_cache(mock_session, sample_source_data):
    """Test that minuteline works correctly without cache"""
    job = Minuteline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()
        job.run()

        # Should fetch twice (no caching)
        assert mock_fetchall.call_count == 2


# ============================================================================
# Date Parsing Tests
# ============================================================================


def test_minuteline_date_parsing_yyyymmdd(mock_session, sample_source_data):
    """Test date parsing from YYYYMMDD format"""
    job = Minuteline(
        session=mock_session,
        params={"code": "sh.600000", "start_date": "20260101", "end_date": "20260131"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        # Should convert YYYYMMDD to YYYY-MM-DD
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-01-31"


def test_minuteline_date_parsing_hyphen_format(mock_session, sample_source_data):
    """Test date parsing preserves YYYY-MM-DD format"""
    job = Minuteline(
        session=mock_session,
        params={"code": "sh.600000", "start_date": "2026-01-01", "end_date": "2026-01-31"},
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-01-31"


# ============================================================================
# Integration Tests
# ============================================================================


def test_minuteline_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    job = Minuteline(
        session=mock_session,
        params={
            "code": "sh.600000",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "frequency": "5",
            "adjustflag": "3",
        },
        cache=False,
    )

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert len(result) > 0
        assert "code" in result.columns
        assert "date" in result.columns
        assert "time" in result.columns


def test_minuteline_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "date": ["2026-01-10"] * 1000,
            "time": [f"{str(i).zfill(9)}" for i in range(1000)],
            "code": ["sh.600000"] * 1000,
            "open": ["10.50"] * 1000,
            "high": ["10.80"] * 1000,
            "low": ["10.30"] * 1000,
            "close": ["10.75"] * 1000,
            "volume": ["6250000"] * 1000,
            "amount": ["672500000"] * 1000,
            "adjustflag": ["3"] * 1000,
        }
    )

    job = Minuteline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=large_data):
        result = job.run()

    assert len(result) == 1000


def test_minuteline_handles_missing_fields(mock_session):
    """Test handling of data with some missing fields"""
    data = pd.DataFrame(
        {
            "date": ["2026-01-10"],
            "time": ["093500000"],
            "code": ["sh.600000"],
            "open": ["10.50"],
            "high": ["10.80"],
            "low": ["10.30"],
            "close": ["10.75"],
            "volume": [None],  # Missing volume
            "amount": [None],  # Missing amount
            "adjustflag": ["3"],
        }
    )

    job = Minuteline(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        assert len(result) == 1
        assert pd.isna(result.iloc[0]["volume"])
        assert pd.isna(result.iloc[0]["amount"])


def test_minuteline_different_frequencies(mock_session, sample_source_data):
    """Test different frequency options"""
    frequencies = ["5", "15", "30", "60"]

    for freq in frequencies:
        job = Minuteline(session=mock_session, params={"code": "sh.600000", "frequency": freq})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["frequency"] == freq


def test_minuteline_different_adjustflags(mock_session, sample_source_data):
    """Test different adjustflag options"""
    adjustflags = ["1", "2", "3"]  # 1=后复权, 2=前复权, 3=不复权

    for flag in adjustflags:
        job = Minuteline(session=mock_session, params={"code": "sh.600000", "adjustflag": flag})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["adjustflag"] == flag

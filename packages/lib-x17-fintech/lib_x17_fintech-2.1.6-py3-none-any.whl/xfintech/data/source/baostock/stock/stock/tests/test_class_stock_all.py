from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.stock.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.baostock.stock.stock.stock import Stock

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
    mock_connection.query_all_stock = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Baostock format"""
    return pd.DataFrame(
        {
            "code": ["sh.600000", "sz.000001", "sz.000002"],
            "tradeStatus": ["1", "1", "0"],
            "code_name": ["浦发银行", "平安银行", "万科A"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_stock_initialization_basic(mock_session):
    """Test basic initialization"""
    job = Stock(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET


def test_stock_initialization_with_params(mock_session):
    """Test initialization with params"""
    params = {"day": "2026-01-10"}
    job = Stock(session=mock_session, params=params)

    assert job.params.day == "2026-01-10"


def test_stock_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    params = {"day": "2026-01-10"}
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = Stock(
        session=mock_session,
        params=params,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert job.params.day == "2026-01-10"
    assert job.coolant.interval == 0.2
    assert job.retry.retry == 3
    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_stock_name_and_key():
    """Test name and key constants"""
    assert NAME == "stock"
    assert KEY == "/baostock/stock"


def test_stock_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert SOURCE.desc == "上市股票基本信息（Baostock格式）"

    column_names = SOURCE.columns
    assert "code" in column_names
    assert "tradestatus" in column_names  # lowercase
    assert "code_name" in column_names


def test_stock_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert TARGET.desc == "上市公司基本信息（xfintech格式）"

    column_names = TARGET.columns
    assert "code" in column_names
    assert "trade_status" in column_names
    assert "name" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_stock_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = Stock(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "trade_status" in result.columns
    assert "name" in result.columns
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[0]["name"] == "浦发银行"


def test_stock_transform_field_types(mock_session, sample_source_data):
    """Test field type conversions"""
    job = Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Check string fields
    assert isinstance(result.iloc[0]["code"], str)
    assert isinstance(result.iloc[0]["trade_status"], str)
    assert isinstance(result.iloc[0]["name"], str)


def test_stock_transform_field_mapping(mock_session, sample_source_data):
    """Test field name mappings"""
    job = Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Verify field mappings
    assert result.iloc[0]["trade_status"] == "1"  # from tradeStatus
    assert result.iloc[0]["name"] == "浦发银行"  # from code_name
    assert result.iloc[0]["code"] == "sh.600000"


def test_stock_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = Stock(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_stock_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600000", "sz.000001"],
            "tradeStatus": ["1", "1", "1"],
            "code_name": ["浦发银行", "浦发银行", "平安银行"],
        }
    )
    job = Stock(session=mock_session)
    result = job.transform(data)

    # Duplicates should be removed
    assert len(result) == 2


def test_stock_transform_sorting(mock_session):
    """Test that result is sorted by code"""
    data = pd.DataFrame(
        {
            "code": ["sz.000002", "sh.600000", "sz.000001"],
            "tradeStatus": ["1", "1", "1"],
            "code_name": ["万科A", "浦发银行", "平安银行"],
        }
    )
    job = Stock(session=mock_session)
    result = job.transform(data)

    # Should be sorted by code
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[1]["code"] == "sz.000001"
    assert result.iloc[2]["code"] == "sz.000002"


# ============================================================================
# Run Tests
# ============================================================================


def test_stock_run_basic(mock_session, sample_source_data):
    """Test basic run method"""
    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "code" in result.columns
        assert "trade_status" in result.columns
        assert "name" in result.columns


def test_stock_run_with_day_param(mock_session, sample_source_data):
    """Test run with day parameter"""
    job = Stock(session=mock_session, params={"day": "2026-01-10"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["day"] == "2026-01-10"


def test_stock_run_calls_query_all_stock(mock_session, sample_source_data):
    """Test that run calls query_all_stock API"""
    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        # Verify that _fetchall was called with the correct API
        assert mock_fetchall.call_count == 1
        call_args = mock_fetchall.call_args
        assert call_args[1]["api"] == job.connection.query_all_stock


def test_stock_run_calls_transform(mock_session, sample_source_data):
    """Test that run calls transform"""
    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "transform", wraps=job.transform) as mock_transform:
            job.run()

            mock_transform.assert_called_once()


# ============================================================================
# Cache Tests
# ============================================================================


def test_stock_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across runs"""
    job = Stock(session=mock_session, cache=True)

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


def test_stock_params_identifier_uniqueness(mock_session):
    """Test that different params create different cache keys"""
    job1 = Stock(session=mock_session, params={"day": "2026-01-10"}, cache=True)
    job2 = Stock(session=mock_session, params={"day": "2026-01-11"}, cache=True)

    assert job1.params.identifier != job2.params.identifier


def test_stock_without_cache(mock_session, sample_source_data):
    """Test that stock works correctly without cache"""
    job = Stock(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()
        job.run()

        # Should fetch twice (no caching)
        assert mock_fetchall.call_count == 2


# ============================================================================
# Date Parsing Tests
# ============================================================================


def test_stock_date_parsing_yyyymmdd(mock_session, sample_source_data):
    """Test date parsing from YYYYMMDD format"""
    job = Stock(session=mock_session, params={"day": "20260110"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        # Should convert YYYYMMDD to YYYY-MM-DD
        assert call_kwargs["day"] == "2026-01-10"


def test_stock_date_parsing_hyphen_format(mock_session, sample_source_data):
    """Test date parsing preserves YYYY-MM-DD format"""
    job = Stock(session=mock_session, params={"day": "2026-01-10"})

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["day"] == "2026-01-10"


# ============================================================================
# Integration Tests
# ============================================================================


def test_stock_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    job = Stock(session=mock_session, params={"day": "2026-01-10"})

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert not result.empty
        assert len(result) == 3
        assert list(result.columns) == ["code", "trade_status", "name"]


def test_stock_with_large_dataset(mock_session):
    """Test handling of large dataset"""
    # Create a large dataset
    large_data = pd.DataFrame(
        {
            "code": [f"sh.{600000 + i}" for i in range(1000)],
            "tradeStatus": ["1"] * 1000,
            "code_name": [f"股票{i}" for i in range(1000)],
        }
    )

    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=large_data):
        result = job.run()

        assert len(result) == 1000
        assert result.iloc[0]["code"] == "sh.600000"
        assert result.iloc[-1]["code"] == "sh.600999"


def test_stock_with_various_trade_statuses(mock_session):
    """Test handling stocks with different trade statuses"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sz.000001", "sz.000002"],
            "tradeStatus": ["1", "0", "1"],
            "code_name": ["浦发银行", "平安银行", "万科A"],
        }
    )

    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        assert len(result) == 3
        # Check that all trade statuses are preserved
        assert "1" in result["trade_status"].values
        assert "0" in result["trade_status"].values


def test_stock_with_empty_result_from_api(mock_session):
    """Test handling of empty result from API"""
    empty_data = pd.DataFrame(columns=["code", "tradeStatus", "code_name"])

    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=empty_data):
        result = job.run()

        assert result.empty
        assert list(result.columns) == ["code", "trade_status", "name"]


def test_stock_with_special_characters_in_names(mock_session):
    """Test handling of special characters in stock names"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sz.000001"],
            "tradeStatus": ["1", "1"],
            "code_name": ["*ST浦发", "ST平安"],
        }
    )

    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        assert result.iloc[0]["name"] == "*ST浦发"
        assert result.iloc[1]["name"] == "ST平安"


# ============================================================================
# List Methods Tests
# ============================================================================


def test_stock_list_codes(mock_session, sample_source_data):
    """Test list_codes method"""
    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        codes = job.list_codes()

        assert isinstance(codes, list)
        assert len(codes) == 3
        assert "sh.600000" in codes
        assert "sz.000001" in codes
        assert "sz.000002" in codes
        # Should be sorted
        assert codes == sorted(codes)


def test_stock_list_names(mock_session, sample_source_data):
    """Test list_names method"""
    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        names = job.list_names()

        assert isinstance(names, list)
        assert len(names) == 3
        assert "浦发银行" in names
        assert "平安银行" in names
        assert "万科A" in names
        # Should be sorted
        assert names == sorted(names)


def test_stock_list_codes_with_duplicates(mock_session):
    """Test list_codes removes duplicates"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600000", "sz.000001"],
            "tradeStatus": ["1", "1", "1"],
            "code_name": ["浦发银行", "浦发银行", "平安银行"],
        }
    )

    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        codes = job.list_codes()

        # Should return unique codes only
        assert len(codes) == 2
        assert codes.count("sh.600000") == 1


def test_stock_list_names_with_duplicates(mock_session):
    """Test list_names removes duplicates"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sz.000001", "sz.000002"],
            "tradeStatus": ["1", "1", "1"],
            "code_name": ["浦发银行", "平安银行", "平安银行"],
        }
    )

    job = Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        names = job.list_names()

        # Should return unique names only
        assert len(names) == 2
        assert names.count("平安银行") == 1

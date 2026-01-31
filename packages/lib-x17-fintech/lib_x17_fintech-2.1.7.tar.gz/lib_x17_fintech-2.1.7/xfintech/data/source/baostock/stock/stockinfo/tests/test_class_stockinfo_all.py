from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.stockinfo.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.baostock.stock.stockinfo.stockinfo import StockInfo

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
    mock_connection.query_stock_basic = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Baostock format"""
    return pd.DataFrame(
        {
            "code": ["sh.600000", "sz.000001", "sh.000001"],
            "code_name": ["浦发银行", "平安银行", "上证指数"],
            "ipoDate": ["1999-11-10", "1991-04-03", ""],
            "outDate": ["", "", ""],
            "type": ["1", "1", "2"],
            "status": ["1", "1", "1"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_stockinfo_initialization_basic(mock_session):
    """Test basic initialization"""
    job = StockInfo(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET


def test_stockinfo_initialization_with_params(mock_session):
    """Test initialization with params"""
    params = {"code": "sh.600000"}
    job = StockInfo(session=mock_session, params=params)

    assert job.params.code == "sh.600000"


def test_stockinfo_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    params = {"code": "sh.600000"}
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = StockInfo(
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


def test_stockinfo_name_and_key():
    """Test name and key constants"""
    assert NAME == "stockinfo"
    assert KEY == "/baostock/stockinfo"


def test_stockinfo_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert "证券基本资料" in SOURCE.desc

    column_names = SOURCE.columns
    assert "code" in column_names
    assert "code_name" in column_names
    assert "ipodate" in column_names
    assert "outdate" in column_names
    assert "type" in column_names
    assert "status" in column_names


def test_stockinfo_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert "证券基本资料" in TARGET.desc

    column_names = TARGET.columns
    assert "code" in column_names
    assert "name" in column_names
    assert "ipo_date" in column_names
    assert "delist_date" in column_names
    assert "security_type" in column_names
    assert "list_status" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_stockinfo_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = StockInfo(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "name" in result.columns
    assert "ipo_date" in result.columns
    assert result.iloc[0]["code"] == "sh.000001"
    assert result.iloc[0]["name"] == "上证指数"


def test_stockinfo_transform_field_types(mock_session, sample_source_data):
    """Test field type conversions"""
    job = StockInfo(session=mock_session)
    result = job.transform(sample_source_data)

    # Check string fields
    assert isinstance(result.iloc[0]["code"], str)
    assert isinstance(result.iloc[0]["name"], str)
    assert isinstance(result.iloc[0]["ipo_date"], str)
    assert isinstance(result.iloc[0]["delist_date"], str)

    # Check integer fields
    assert pd.api.types.is_integer_dtype(result["security_type"])
    assert pd.api.types.is_integer_dtype(result["list_status"])


def test_stockinfo_transform_field_mapping(mock_session, sample_source_data):
    """Test field name mappings"""
    job = StockInfo(session=mock_session)
    result = job.transform(sample_source_data)

    # Verify field mappings
    row = result[result["code"] == "sh.600000"].iloc[0]
    assert row["name"] == "浦发银行"  # from code_name
    assert row["ipo_date"] == "1999-11-10"  # from ipoDate
    assert row["delist_date"] == ""  # from outDate
    assert row["security_type"] == 1  # from type
    assert row["list_status"] == 1  # from status


def test_stockinfo_transform_security_types(mock_session):
    """Test security type conversions"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.000001", "sh.000300", "sh.113001", "sh.510050"],
            "code_name": ["股票", "指数", "其它", "可转债", "ETF"],
            "ipoDate": ["2000-01-01"] * 5,
            "outDate": [""] * 5,
            "type": ["1", "2", "3", "4", "5"],
            "status": ["1"] * 5,
        }
    )
    job = StockInfo(session=mock_session)
    result = job.transform(data)

    # Result is sorted by code, so check by code instead of position
    assert result[result["code"] == "sh.600000"].iloc[0]["security_type"] == 1  # 股票
    assert result[result["code"] == "sh.000001"].iloc[0]["security_type"] == 2  # 指数
    assert result[result["code"] == "sh.000300"].iloc[0]["security_type"] == 3  # 其它
    assert result[result["code"] == "sh.113001"].iloc[0]["security_type"] == 4  # 可转债
    assert result[result["code"] == "sh.510050"].iloc[0]["security_type"] == 5  # ETF


def test_stockinfo_transform_list_status(mock_session):
    """Test list status conversions"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600001"],
            "code_name": ["上市股票", "退市股票"],
            "ipoDate": ["2000-01-01", "2000-01-01"],
            "outDate": ["", "2020-01-01"],
            "type": ["1", "1"],
            "status": ["1", "0"],
        }
    )
    job = StockInfo(session=mock_session)
    result = job.transform(data)

    assert result.iloc[0]["list_status"] == 1  # 上市
    assert result.iloc[1]["list_status"] == 0  # 退市


def test_stockinfo_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = StockInfo(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_stockinfo_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600000", "sz.000001"],
            "code_name": ["浦发银行", "浦发银行", "平安银行"],
            "ipoDate": ["1999-11-10", "1999-11-10", "1991-04-03"],
            "outDate": ["", "", ""],
            "type": ["1", "1", "1"],
            "status": ["1", "1", "1"],
        }
    )
    job = StockInfo(session=mock_session)
    result = job.transform(data)

    # Duplicates should be removed
    assert len(result) == 2


def test_stockinfo_transform_sorting(mock_session):
    """Test that result is sorted by code"""
    data = pd.DataFrame(
        {
            "code": ["sz.000002", "sh.600000", "sz.000001"],
            "code_name": ["万科A", "浦发银行", "平安银行"],
            "ipoDate": ["1991-01-29", "1999-11-10", "1991-04-03"],
            "outDate": ["", "", ""],
            "type": ["1", "1", "1"],
            "status": ["1", "1", "1"],
        }
    )
    job = StockInfo(session=mock_session)
    result = job.transform(data)

    # Should be sorted by code
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[1]["code"] == "sz.000001"
    assert result.iloc[2]["code"] == "sz.000002"


def test_stockinfo_transform_invalid_types(mock_session):
    """Test transform with invalid type/status values"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600001"],
            "code_name": ["正常", "异常"],
            "ipoDate": ["2000-01-01", "2000-01-01"],
            "outDate": ["", ""],
            "type": ["1", "invalid"],
            "status": ["1", "invalid"],
        }
    )
    job = StockInfo(session=mock_session)
    result = job.transform(data)

    # Invalid values should be converted to 0
    assert result.iloc[0]["security_type"] == 1
    assert result.iloc[1]["security_type"] == 0  # invalid -> 0
    assert result.iloc[0]["list_status"] == 1
    assert result.iloc[1]["list_status"] == 0  # invalid -> 0


# ============================================================================
# Run Tests
# ============================================================================


def test_stockinfo_run_basic(mock_session, sample_source_data):
    """Test basic run method"""
    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "code" in result.columns
        assert "name" in result.columns
        assert "security_type" in result.columns


def test_stockinfo_run_with_code_param(mock_session, sample_source_data):
    """Test run with code parameter"""
    filtered_data = sample_source_data[sample_source_data["code"] == "sh.600000"]

    job = StockInfo(session=mock_session, params={"code": "sh.600000"})

    with patch.object(job, "_fetchall", return_value=filtered_data) as mock_fetchall:
        result = job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["code"] == "sh.600000"
        assert len(result) == 1
        assert result["code"].iloc[0] == "sh.600000"


def test_stockinfo_run_with_code_name_param(mock_session, sample_source_data):
    """Test run with code_name parameter"""
    filtered_data = sample_source_data[sample_source_data["code_name"].str.contains("浦发")]

    job = StockInfo(session=mock_session, params={"code_name": "浦发"})

    with patch.object(job, "_fetchall", return_value=filtered_data) as mock_fetchall:
        job.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["code_name"] == "浦发"


def test_stockinfo_run_calls_query_stock_basic(mock_session, sample_source_data):
    """Test that run calls query_stock_basic API"""
    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()

        # Verify that _fetchall was called with the correct API
        assert mock_fetchall.call_count == 1
        call_args = mock_fetchall.call_args
        assert call_args[1]["api"] == job.connection.query_stock_basic


def test_stockinfo_run_calls_transform(mock_session, sample_source_data):
    """Test that run calls transform"""
    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "transform", wraps=job.transform) as mock_transform:
            job.run()

            mock_transform.assert_called_once()


# ============================================================================
# Cache Tests
# ============================================================================


def test_stockinfo_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across runs"""
    job = StockInfo(session=mock_session, cache=True)

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


def test_stockinfo_params_identifier_uniqueness(mock_session):
    """Test that different params create different cache keys"""
    job1 = StockInfo(session=mock_session, params={"code": "sh.600000"}, cache=True)
    job2 = StockInfo(session=mock_session, params={"code": "sz.000001"}, cache=True)

    assert job1.params.identifier != job2.params.identifier


def test_stockinfo_without_cache(mock_session, sample_source_data):
    """Test that stockinfo works correctly without cache"""
    job = StockInfo(session=mock_session, cache=False)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        job.run()
        job.run()

        # Should fetch twice (no caching)
        assert mock_fetchall.call_count == 2


# ============================================================================
# Integration Tests
# ============================================================================


def test_stockinfo_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    job = StockInfo(session=mock_session, params={"code": "sh.600000"})

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        result = job.run()

        assert not result.empty
        assert len(result) == 3
        assert list(result.columns) == [
            "code",
            "name",
            "ipo_date",
            "delist_date",
            "security_type",
            "list_status",
        ]


def test_stockinfo_with_large_dataset(mock_session):
    """Test handling of large dataset"""
    # Create a large dataset
    large_data = pd.DataFrame(
        {
            "code": [f"sh.{600000 + i}" for i in range(1000)],
            "code_name": [f"股票{i}" for i in range(1000)],
            "ipoDate": ["2000-01-01"] * 1000,
            "outDate": [""] * 1000,
            "type": ["1"] * 1000,
            "status": ["1"] * 1000,
        }
    )

    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=large_data):
        result = job.run()

        assert len(result) == 1000
        assert result.iloc[0]["code"] == "sh.600000"
        assert result.iloc[-1]["code"] == "sh.600999"


def test_stockinfo_with_mixed_security_types(mock_session):
    """Test handling different security types"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.000001", "sh.113001"],
            "code_name": ["浦发银行", "上证指数", "某转债"],
            "ipoDate": ["1999-11-10", "", "2020-01-01"],
            "outDate": ["", "", ""],
            "type": ["1", "2", "4"],
            "status": ["1", "1", "1"],
        }
    )

    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        assert len(result) == 3
        # Check that all security types are preserved
        assert 1 in result["security_type"].values  # 股票
        assert 2 in result["security_type"].values  # 指数
        assert 4 in result["security_type"].values  # 可转债


def test_stockinfo_with_empty_result_from_api(mock_session):
    """Test handling of empty result from API"""
    empty_data = pd.DataFrame(columns=["code", "code_name", "ipoDate", "outDate", "type", "status"])

    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=empty_data):
        result = job.run()

        assert result.empty
        assert list(result.columns) == [
            "code",
            "name",
            "ipo_date",
            "delist_date",
            "security_type",
            "list_status",
        ]


def test_stockinfo_with_delisted_stocks(mock_session):
    """Test handling of delisted stocks"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600001"],
            "code_name": ["浦发银行", "退市股票"],
            "ipoDate": ["1999-11-10", "2000-01-01"],
            "outDate": ["", "2020-12-31"],
            "type": ["1", "1"],
            "status": ["1", "0"],
        }
    )

    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        result = job.run()

        assert len(result) == 2
        # Check that delisted stock is marked correctly
        delisted = result[result["code"] == "sh.600001"].iloc[0]
        assert delisted["list_status"] == 0
        assert delisted["delist_date"] == "2020-12-31"


# ============================================================================
# List Methods Tests
# ============================================================================


def test_stockinfo_list_codes(mock_session, sample_source_data):
    """Test list_codes method"""
    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        codes = job.list_codes()

        assert isinstance(codes, list)
        assert len(codes) == 3
        assert "sh.600000" in codes
        assert "sz.000001" in codes
        assert "sh.000001" in codes
        # Should be sorted
        assert codes == sorted(codes)


def test_stockinfo_list_names(mock_session, sample_source_data):
    """Test list_names method"""
    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        names = job.list_names()

        assert isinstance(names, list)
        assert len(names) == 3
        assert "浦发银行" in names
        assert "平安银行" in names
        assert "上证指数" in names
        # Should be sorted
        assert names == sorted(names)


def test_stockinfo_list_codes_with_duplicates(mock_session):
    """Test list_codes removes duplicates"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600000", "sz.000001"],
            "code_name": ["浦发银行", "浦发银行", "平安银行"],
            "ipoDate": ["1999-11-10", "1999-11-10", "1991-04-03"],
            "outDate": ["", "", ""],
            "type": ["1", "1", "1"],
            "status": ["1", "1", "1"],
        }
    )

    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        codes = job.list_codes()

        # Should return unique codes only
        assert len(codes) == 2
        assert codes.count("sh.600000") == 1


def test_stockinfo_list_names_with_duplicates(mock_session):
    """Test list_names removes duplicates"""
    data = pd.DataFrame(
        {
            "code": ["sh.600000", "sz.000001", "sz.000002"],
            "code_name": ["浦发银行", "平安银行", "平安银行"],
            "ipoDate": ["1999-11-10", "1991-04-03", "1991-01-29"],
            "outDate": ["", "", ""],
            "type": ["1", "1", "1"],
            "status": ["1", "1", "1"],
        }
    )

    job = StockInfo(session=mock_session)

    with patch.object(job, "_fetchall", return_value=data):
        names = job.list_names()

        # Should return unique names only
        assert len(names) == 2
        assert names.count("平安银行") == 1

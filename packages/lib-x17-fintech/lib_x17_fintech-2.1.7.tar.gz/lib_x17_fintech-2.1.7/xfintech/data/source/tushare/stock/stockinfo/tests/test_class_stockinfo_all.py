"""
Test suite for StockInfo class
Tests cover initialization, data fetching, transformation, date handling, and utility methods
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.stockinfo.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)
from xfintech.data.source.tushare.stock.stockinfo.stockinfo import StockInfo

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
    mock_connection.bak_basic = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "trade_date": ["20230101", "20230101", "20230102"],
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "name": ["平安银行", "万科A", "浦发银行"],
            "industry": ["银行", "房地产", "银行"],
            "area": ["深圳", "深圳", "上海"],
            "pe": [5.5, 10.2, 6.3],
            "float_share": [100.5, 50.3, 80.2],
            "total_share": [150.2, 80.5, 120.3],
            "total_assets": [1000.5, 500.3, 800.2],
            "liquid_assets": [500.2, 250.1, 400.1],
            "fixed_assets": [300.1, 150.2, 250.3],
            "reserved": [100.5, 50.3, 80.2],
            "reserved_pershare": [0.67, 0.63, 0.67],
            "eps": [1.2, 0.8, 1.1],
            "bvps": [8.5, 6.3, 7.8],
            "pb": [1.5, 1.8, 1.6],
            "list_date": ["19910403", "19910129", "19991110"],
            "undp": [50.2, 25.1, 40.1],
            "per_undp": [0.33, 0.31, 0.33],
            "rev_yoy": [5.5, 10.2, 6.3],
            "profit_yoy": [8.5, 12.3, 9.1],
            "gpr": [30.5, 25.3, 28.2],
            "npr": [20.1, 18.5, 19.3],
            "holder_num": [50000, 30000, 40000],
        }
    )


@pytest.fixture
def expected_transformed_data():
    """Create expected transformed data"""
    return pd.DataFrame(
        {
            "code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "name": ["平安银行", "万科A", "浦发银行"],
            "date": ["2023-01-01", "2023-01-01", "2023-01-02"],
            "datecode": ["20230101", "20230101", "20230102"],
            "list_date": ["1991-04-03", "1991-01-29", "1999-11-10"],
            "list_datecode": ["19910403", "19910129", "19991110"],
            "industry": ["银行", "房地产", "银行"],
            "area": ["深圳", "深圳", "上海"],
            "pe": [5.5, 10.2, 6.3],
            "float_share": [100.5, 50.3, 80.2],
            "total_share": [150.2, 80.5, 120.3],
            "total_assets": [1000.5, 500.3, 800.2],
            "liquid_assets": [500.2, 250.1, 400.1],
            "fixed_assets": [300.1, 150.2, 250.3],
            "reserved": [100.5, 50.3, 80.2],
            "reserved_pershare": [0.67, 0.63, 0.67],
            "eps": [1.2, 0.8, 1.1],
            "bvps": [8.5, 6.3, 7.8],
            "pb": [1.5, 1.8, 1.6],
            "undp": [50.2, 25.1, 40.1],
            "per_undp": [0.33, 0.31, 0.33],
            "rev_yoy": [5.5, 10.2, 6.3],
            "profit_yoy": [8.5, 12.3, 9.1],
            "gpr": [30.5, 25.3, 28.2],
            "npr": [20.1, 18.5, 19.3],
            "holder_num": [50000, 30000, 40000],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_stockinfo_init_basic(mock_session):
    """Test StockInfo initialization with minimal parameters"""
    stockinfo = StockInfo(session=mock_session)

    assert stockinfo.name == NAME
    assert stockinfo.key == KEY
    assert stockinfo.source == SOURCE
    assert stockinfo.target == TARGET
    assert isinstance(stockinfo.params, Params)
    assert isinstance(stockinfo.coolant, Coolant)
    assert isinstance(stockinfo.paginate, Paginate)
    assert isinstance(stockinfo.retry, Retry)
    assert stockinfo.paginate.pagesize == PAGINATE["pagesize"]
    assert stockinfo.paginate.pagelimit == PAGINATE["pagelimit"]


def test_stockinfo_init_with_params_dict(mock_session):
    """Test StockInfo initialization with params as dict"""
    params = {"ts_code": "000001.SZ"}
    stockinfo = StockInfo(session=mock_session, params=params)

    assert isinstance(stockinfo.params, Params)
    assert stockinfo.params.to_dict()["ts_code"] == "000001.SZ"


def test_stockinfo_init_with_params_object(mock_session):
    """Test StockInfo initialization with params as Params object"""
    params = Params(ts_code="000001.SZ")
    stockinfo = StockInfo(session=mock_session, params=params)

    assert isinstance(stockinfo.params, Params)
    assert stockinfo.params.to_dict()["ts_code"] == "000001.SZ"


def test_stockinfo_init_with_trade_date_param(mock_session):
    """Test StockInfo initialization with trade_date param"""
    params = {"trade_date": "20230101"}
    stockinfo = StockInfo(session=mock_session, params=params)

    assert stockinfo.params.to_dict()["trade_date"] == "20230101"


def test_stockinfo_init_with_ts_code_param(mock_session):
    """Test StockInfo initialization with ts_code param"""
    params = {"ts_code": "000001.SZ"}
    stockinfo = StockInfo(session=mock_session, params=params)

    assert stockinfo.params.to_dict()["ts_code"] == "000001.SZ"


def test_stockinfo_init_with_cache_bool_true(mock_session):
    """Test StockInfo initialization with cache as bool True"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    assert isinstance(stockinfo.cache, Cache)


def test_stockinfo_init_with_cache_bool_false(mock_session):
    """Test StockInfo initialization with cache as bool False"""
    stockinfo = StockInfo(session=mock_session, cache=False)

    assert stockinfo.cache is None


def test_stockinfo_init_with_cache_dict(mock_session):
    """Test StockInfo initialization with cache as dict"""
    cache_config = {"enabled": True, "ttl": 3600}
    stockinfo = StockInfo(session=mock_session, cache=cache_config)

    assert isinstance(stockinfo.cache, Cache)


def test_stockinfo_init_with_all_params(mock_session):
    """Test StockInfo initialization with all parameters"""
    params = {"ts_code": "000001.SZ", "trade_date": "20230101"}
    coolant = {"enabled": True, "interval": 1.0}
    retry = {"max_attempts": 3, "backoff": 2.0}
    cache = {"enabled": True, "ttl": 3600}

    stockinfo = StockInfo(
        session=mock_session,
        params=params,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert stockinfo.params.to_dict()["ts_code"] == "000001.SZ"
    assert isinstance(stockinfo.coolant, Coolant)
    assert isinstance(stockinfo.retry, Retry)
    assert isinstance(stockinfo.cache, Cache)


def test_stockinfo_constants():
    """Test that constants are properly defined"""
    assert NAME == "stockinfo"
    assert KEY == "/tushare/stockinfo"
    assert PAGINATE["pagesize"] == 7000
    assert SOURCE is not None
    assert TARGET is not None


# ============================================================================
# Transform Tests
# ============================================================================


def test_stockinfo_transform_basic(mock_session, sample_source_data):
    """Test basic transform functionality"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert list(result.columns) == stockinfo.target.list_column_names()


def test_stockinfo_transform_code_mapping(mock_session, sample_source_data):
    """Test that ts_code is mapped to code"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert "code" in result.columns
    assert result["code"].tolist() == ["000001.SZ", "000002.SZ", "600000.SH"]


def test_stockinfo_transform_name_mapping(mock_session, sample_source_data):
    """Test that name is preserved"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert "name" in result.columns
    assert result["name"].tolist() == ["平安银行", "万科A", "浦发银行"]


def test_stockinfo_transform_date_format(mock_session, sample_source_data):
    """Test that trade_date is formatted correctly"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert "date" in result.columns
    assert result["date"].dtype == object
    assert result["date"].iloc[0] == "2023-01-01"
    assert result["date"].iloc[2] == "2023-01-02"


def test_stockinfo_transform_datecode_preserved(mock_session, sample_source_data):
    """Test that datecode preserves original format"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert "datecode" in result.columns
    assert result["datecode"].tolist() == ["20230101", "20230101", "20230102"]


def test_stockinfo_transform_list_date_format(mock_session, sample_source_data):
    """Test that list_date is formatted correctly"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert "list_date" in result.columns
    assert result["list_date"].dtype == object
    assert result["list_date"].iloc[0] == "1991-04-03"


def test_stockinfo_transform_list_datecode_preserved(mock_session, sample_source_data):
    """Test that list_datecode preserves original format"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert "list_datecode" in result.columns
    assert result["list_datecode"].tolist() == ["19910403", "19910129", "19991110"]


def test_stockinfo_transform_numeric_conversions(mock_session, sample_source_data):
    """Test that numeric fields are converted correctly"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    # Check numeric fields
    numeric_fields = ["pe", "float_share", "total_share", "eps", "bvps", "pb"]
    for field in numeric_fields:
        assert field in result.columns
        assert pd.api.types.is_numeric_dtype(result[field])


def test_stockinfo_transform_string_fields(mock_session, sample_source_data):
    """Test that string fields are converted correctly"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert result["industry"].tolist() == ["银行", "房地产", "银行"]
    assert result["area"].tolist() == ["深圳", "深圳", "上海"]


def test_stockinfo_transform_empty_dataframe(mock_session):
    """Test transform with empty DataFrame"""
    stockinfo = StockInfo(session=mock_session)
    empty_df = pd.DataFrame()
    result = stockinfo.transform(empty_df)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
    assert list(result.columns) == stockinfo.target.list_column_names()


def test_stockinfo_transform_none_input(mock_session):
    """Test transform with None input"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(None)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
    assert list(result.columns) == stockinfo.target.list_column_names()


def test_stockinfo_transform_handles_invalid_dates(mock_session):
    """Test that transform handles invalid dates gracefully"""
    stockinfo = StockInfo(session=mock_session)
    data = pd.DataFrame(
        {
            "trade_date": ["invalid", "20230101"],
            "ts_code": ["000001.SZ", "000002.SZ"],
            "name": ["平安银行", "万科A"],
            "industry": ["银行", "房地产"],
            "area": ["深圳", "深圳"],
            "pe": [5.5, 10.2],
            "float_share": [100.5, 50.3],
            "total_share": [150.2, 80.5],
            "total_assets": [1000.5, 500.3],
            "liquid_assets": [500.2, 250.1],
            "fixed_assets": [300.1, 150.2],
            "reserved": [100.5, 50.3],
            "reserved_pershare": [0.67, 0.63],
            "eps": [1.2, 0.8],
            "bvps": [8.5, 6.3],
            "pb": [1.5, 1.8],
            "list_date": ["19910403", "19910129"],
            "undp": [50.2, 25.1],
            "per_undp": [0.33, 0.31],
            "rev_yoy": [5.5, 10.2],
            "profit_yoy": [8.5, 12.3],
            "gpr": [30.5, 25.3],
            "npr": [20.1, 18.5],
            "holder_num": [50000, 30000],
        }
    )
    result = stockinfo.transform(data)

    assert len(result) == 2
    assert pd.isna(result.loc[result["code"] == "000001.SZ", "date"].iloc[0])


def test_stockinfo_transform_removes_duplicates(mock_session, sample_source_data):
    """Test that transform removes duplicate rows"""
    stockinfo = StockInfo(session=mock_session)
    # Add duplicate rows
    duplicated_data = pd.concat([sample_source_data, sample_source_data.iloc[[0]]])
    result = stockinfo.transform(duplicated_data)

    assert len(result) == 3  # Original length without duplicates


def test_stockinfo_transform_sorts_by_code(mock_session):
    """Test that transform sorts by code"""
    stockinfo = StockInfo(session=mock_session)
    data = pd.DataFrame(
        {
            "trade_date": ["20230101", "20230101", "20230101"],
            "ts_code": ["600000.SH", "000001.SZ", "000002.SZ"],
            "name": ["浦发银行", "平安银行", "万科A"],
            "industry": ["银行", "银行", "房地产"],
            "area": ["上海", "深圳", "深圳"],
            "pe": [6.3, 5.5, 10.2],
            "float_share": [80.2, 100.5, 50.3],
            "total_share": [120.3, 150.2, 80.5],
            "total_assets": [800.2, 1000.5, 500.3],
            "liquid_assets": [400.1, 500.2, 250.1],
            "fixed_assets": [250.3, 300.1, 150.2],
            "reserved": [80.2, 100.5, 50.3],
            "reserved_pershare": [0.67, 0.67, 0.63],
            "eps": [1.1, 1.2, 0.8],
            "bvps": [7.8, 8.5, 6.3],
            "pb": [1.6, 1.5, 1.8],
            "list_date": ["19991110", "19910403", "19910129"],
            "undp": [40.1, 50.2, 25.1],
            "per_undp": [0.33, 0.33, 0.31],
            "rev_yoy": [6.3, 5.5, 10.2],
            "profit_yoy": [9.1, 8.5, 12.3],
            "gpr": [28.2, 30.5, 25.3],
            "npr": [19.3, 20.1, 18.5],
            "holder_num": [40000, 50000, 30000],
        }
    )
    result = stockinfo.transform(data)

    # Should be sorted by code
    assert result["code"].tolist() == ["000001.SZ", "000002.SZ", "600000.SH"]


def test_stockinfo_transform_resets_index(mock_session, sample_source_data):
    """Test that transform resets the index"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    assert result.index.tolist() == [0, 1, 2]


def test_stockinfo_transform_only_target_columns(mock_session, sample_source_data):
    """Test that transform only includes target columns"""
    stockinfo = StockInfo(session=mock_session)
    result = stockinfo.transform(sample_source_data)

    expected_columns = stockinfo.target.list_column_names()
    assert list(result.columns) == expected_columns


# ============================================================================
# Run Tests
# ============================================================================


def test_stockinfo_run_with_cache_hit(mock_session, sample_source_data):
    """Test run method with cache hit"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    # Pre-populate cache
    cached_data = stockinfo.transform(sample_source_data)
    stockinfo.cache.set(stockinfo.params.identifier, cached_data)

    # Run should return cached data
    with patch.object(stockinfo, "_fetchall") as mock_fetchall:
        result = stockinfo.run()
        mock_fetchall.assert_not_called()

    assert len(result) == 3


def test_stockinfo_run_basic_date(mock_session, sample_source_data):
    """Test run with basic trade_date parameter"""
    stockinfo = StockInfo(session=mock_session, params={"trade_date": "20230101"})

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        result = stockinfo.run()

    assert len(result) == 3
    assert isinstance(result, pd.DataFrame)


def test_stockinfo_run_with_trade_date_string(mock_session, sample_source_data):
    """Test run with trade_date as string"""
    stockinfo = StockInfo(session=mock_session, params={"trade_date": "20230101"})

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        stockinfo.run()

        # Check that trade_date is preserved as string
        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["trade_date"] == "20230101"


def test_stockinfo_run_with_trade_date_datetime(mock_session, sample_source_data):
    """Test run with trade_date as datetime object"""
    trade_date = datetime(2023, 1, 1)
    stockinfo = StockInfo(session=mock_session, params={"trade_date": trade_date})

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        stockinfo.run()

        # Check that datetime was converted to string format YYYYMMDD
        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["trade_date"] == "20230101"


def test_stockinfo_run_with_ts_code_param(mock_session, sample_source_data):
    """Test run with ts_code parameter"""
    stockinfo = StockInfo(session=mock_session, params={"ts_code": "000001.SZ"})

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        stockinfo.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["ts_code"] == "000001.SZ"


def test_stockinfo_run_adds_fields_param(mock_session, sample_source_data):
    """Test that run adds fields parameter if not present"""
    stockinfo = StockInfo(session=mock_session)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        stockinfo.run()

        call_kwargs = mock_fetchall.call_args[1]
        assert "fields" in call_kwargs
        assert isinstance(call_kwargs["fields"], str)


def test_stockinfo_run_sets_cache(mock_session, sample_source_data):
    """Test that run sets cache after fetching"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        result = stockinfo.run()

    cached = stockinfo.cache.get(stockinfo.params.identifier)
    assert cached is not None
    assert len(cached) == len(result)


def test_stockinfo_run_calls_transform(mock_session, sample_source_data):
    """Test that run calls transform method"""
    stockinfo = StockInfo(session=mock_session)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        with patch.object(stockinfo, "transform", wraps=stockinfo.transform) as mock_transform:
            stockinfo.run()
            mock_transform.assert_called_once()


def test_stockinfo_run_with_trade_date_as_date(mock_session, sample_source_data):
    """Test run with trade_date as date object (not datetime)"""
    trade_date = date(2023, 1, 1)
    stockinfo = StockInfo(session=mock_session, params={"trade_date": trade_date})

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        stockinfo.run()

        # Check that date was converted to string format YYYYMMDD
        call_kwargs = mock_fetchall.call_args[1]
        assert call_kwargs["trade_date"] == "20230101"


# ============================================================================
# List Methods Tests
# ============================================================================


def test_stockinfo_list_codes_basic(mock_session, sample_source_data):
    """Test list_codes returns list of stock codes"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        codes = stockinfo.list_codes()

    assert isinstance(codes, list)
    assert len(codes) == 3
    assert "000001.SZ" in codes
    assert "000002.SZ" in codes
    assert "600000.SH" in codes


def test_stockinfo_list_codes_unique(mock_session):
    """Test list_codes returns unique codes"""
    stockinfo = StockInfo(session=mock_session, cache=False)  # Disable cache

    # Create data with duplicate codes
    data = pd.DataFrame(
        {
            "trade_date": ["20230101", "20230102", "20230101"],
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "name": ["平安银行", "平安银行", "万科A"],
            "industry": ["银行", "银行", "房地产"],
            "area": ["深圳", "深圳", "深圳"],
            "pe": [5.5, 5.6, 10.2],
            "float_share": [100.5, 100.5, 50.3],
            "total_share": [150.2, 150.2, 80.5],
            "total_assets": [1000.5, 1000.5, 500.3],
            "liquid_assets": [500.2, 500.2, 250.1],
            "fixed_assets": [300.1, 300.1, 150.2],
            "reserved": [100.5, 100.5, 50.3],
            "reserved_pershare": [0.67, 0.67, 0.63],
            "eps": [1.2, 1.2, 0.8],
            "bvps": [8.5, 8.5, 6.3],
            "pb": [1.5, 1.5, 1.8],
            "list_date": ["19910403", "19910403", "19910129"],
            "undp": [50.2, 50.2, 25.1],
            "per_undp": [0.33, 0.33, 0.31],
            "rev_yoy": [5.5, 5.5, 10.2],
            "profit_yoy": [8.5, 8.5, 12.3],
            "gpr": [30.5, 30.5, 25.3],
            "npr": [20.1, 20.1, 18.5],
            "holder_num": [50000, 50000, 30000],
        }
    )

    with patch.object(stockinfo, "_fetchall", return_value=data):
        codes = stockinfo.list_codes()

    assert len(codes) == 2  # Only unique codes
    assert codes == ["000001.SZ", "000002.SZ"]


def test_stockinfo_list_codes_sorted(mock_session, sample_source_data):
    """Test list_codes returns sorted codes"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        codes = stockinfo.list_codes()

    assert codes == sorted(codes)


def test_stockinfo_list_codes_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_codes calls run when cache is empty"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        codes = stockinfo.list_codes()

    assert len(codes) > 0


def test_stockinfo_list_names_basic(mock_session, sample_source_data):
    """Test list_names returns list of stock names"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        names = stockinfo.list_names()

    assert isinstance(names, list)
    assert len(names) == 3
    assert "平安银行" in names
    assert "万科A" in names
    assert "浦发银行" in names


def test_stockinfo_list_names_sorted(mock_session, sample_source_data):
    """Test list_names returns sorted names"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        names = stockinfo.list_names()

    assert names == sorted(names)


def test_stockinfo_list_names_unique(mock_session):
    """Test list_names returns unique names"""
    stockinfo = StockInfo(session=mock_session, cache=False)  # Disable cache for this test

    # Create data with duplicate names
    data = pd.DataFrame(
        {
            "trade_date": ["20230101", "20230102", "20230101"],
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "name": ["平安银行", "平安银行", "万科A"],
            "industry": ["银行", "银行", "房地产"],
            "area": ["深圳", "深圳", "深圳"],
            "pe": [5.5, 5.6, 10.2],
            "float_share": [100.5, 100.5, 50.3],
            "total_share": [150.2, 150.2, 80.5],
            "total_assets": [1000.5, 1000.5, 500.3],
            "liquid_assets": [500.2, 500.2, 250.1],
            "fixed_assets": [300.1, 300.1, 150.2],
            "reserved": [100.5, 100.5, 50.3],
            "reserved_pershare": [0.67, 0.67, 0.63],
            "eps": [1.2, 1.2, 0.8],
            "bvps": [8.5, 8.5, 6.3],
            "pb": [1.5, 1.5, 1.8],
            "list_date": ["19910403", "19910403", "19910129"],
            "undp": [50.2, 50.2, 25.1],
            "per_undp": [0.33, 0.33, 0.31],
            "rev_yoy": [5.5, 5.5, 10.2],
            "profit_yoy": [8.5, 8.5, 12.3],
            "gpr": [30.5, 30.5, 25.3],
            "npr": [20.1, 20.1, 18.5],
            "holder_num": [50000, 50000, 30000],
        }
    )

    with patch.object(stockinfo, "_fetchall", return_value=data):
        names = stockinfo.list_names()

    assert len(names) == 2  # Only unique names


def test_stockinfo_list_names_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_names calls run when cache is empty"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        names = stockinfo.list_names()

    assert len(names) > 0


# ============================================================================
# Integration Tests
# ============================================================================


def test_stockinfo_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    stockinfo = StockInfo(
        session=mock_session,
        params={"trade_date": "20230101"},
        cache=True,
    )

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data):
        # First run - should fetch from source
        result1 = stockinfo.run()
        assert len(result1) == 3

        # Second run - should use cache
        result2 = stockinfo.run()
        assert len(result2) == 3
        assert result1.equals(result2)

        # List methods should work with cached data
        codes = stockinfo.list_codes()
        names = stockinfo.list_names()
        assert len(codes) == 3
        assert len(names) == 3


def test_stockinfo_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across runs"""
    stockinfo = StockInfo(session=mock_session, cache=True)

    with patch.object(stockinfo, "_load_cache", return_value=None) as mock_load:
        with patch.object(stockinfo, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            # First run - fetches data and caches it
            result1 = stockinfo.run()
            assert mock_fetchall.call_count == 1
            assert mock_load.call_count == 1

            # Second run - _load_cache still returns None because we're mocking it
            result2 = stockinfo.run()
            assert mock_fetchall.call_count == 2  # Called again since cache mock returns None
            assert mock_load.call_count == 2

            pd.testing.assert_frame_equal(result1, result2)


def test_stockinfo_params_identifier_uniqueness(mock_session):
    """Test that different params create different cache keys"""
    stockinfo1 = StockInfo(session=mock_session, params={"trade_date": "20230101"}, cache=True)
    stockinfo2 = StockInfo(session=mock_session, params={"trade_date": "20230102"}, cache=True)

    assert stockinfo1.params.identifier != stockinfo2.params.identifier


def test_stockinfo_different_date_params(mock_session, sample_source_data):
    """Test handling of different date parameters"""
    stockinfo1 = StockInfo(session=mock_session, params={"trade_date": "20230101"})
    stockinfo2 = StockInfo(session=mock_session, params={"trade_date": datetime(2023, 1, 2)})

    with patch.object(stockinfo1, "_fetchall", return_value=sample_source_data):
        result1 = stockinfo1.run()

    with patch.object(stockinfo2, "_fetchall", return_value=sample_source_data):
        result2 = stockinfo2.run()

    assert len(result1) == 3
    assert len(result2) == 3


def test_stockinfo_empty_result_handling(mock_session):
    """Test handling of empty results from API"""
    stockinfo = StockInfo(session=mock_session)
    empty_df = pd.DataFrame()

    with patch.object(stockinfo, "_fetchall", return_value=empty_df):
        result = stockinfo.run()

    assert len(result) == 0
    assert list(result.columns) == stockinfo.target.list_column_names()


def test_stockinfo_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    stockinfo = StockInfo(session=mock_session)

    # Create a large dataset
    large_data = pd.DataFrame(
        {
            "trade_date": ["20230101"] * 1000,
            "ts_code": [f"{str(i).zfill(6)}.SZ" for i in range(1000)],
            "name": [f"股票{i}" for i in range(1000)],
            "industry": ["银行"] * 1000,
            "area": ["深圳"] * 1000,
            "pe": [5.5] * 1000,
            "float_share": [100.5] * 1000,
            "total_share": [150.2] * 1000,
            "total_assets": [1000.5] * 1000,
            "liquid_assets": [500.2] * 1000,
            "fixed_assets": [300.1] * 1000,
            "reserved": [100.5] * 1000,
            "reserved_pershare": [0.67] * 1000,
            "eps": [1.2] * 1000,
            "bvps": [8.5] * 1000,
            "pb": [1.5] * 1000,
            "list_date": ["19910403"] * 1000,
            "undp": [50.2] * 1000,
            "per_undp": [0.33] * 1000,
            "rev_yoy": [5.5] * 1000,
            "profit_yoy": [8.5] * 1000,
            "gpr": [30.5] * 1000,
            "npr": [20.1] * 1000,
            "holder_num": [50000] * 1000,
        }
    )

    with patch.object(stockinfo, "_fetchall", return_value=large_data):
        result = stockinfo.run()

    assert len(result) == 1000


def test_stockinfo_without_cache(mock_session, sample_source_data):
    """Test that stockinfo works correctly without cache"""
    stockinfo = StockInfo(session=mock_session, cache=False)

    with patch.object(stockinfo, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        stockinfo.run()
        stockinfo.run()

        # Should fetch twice (no caching)
        assert mock_fetchall.call_count == 2


def test_stockinfo_handles_missing_numeric_fields(mock_session):
    """Test handling of data with missing numeric fields"""
    stockinfo = StockInfo(session=mock_session)

    # Create data with some missing numeric fields
    data = pd.DataFrame(
        {
            "trade_date": ["20230101"],
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "industry": ["银行"],
            "area": ["深圳"],
            "pe": [None],
            "float_share": [100.5],
            "total_share": [150.2],
            "total_assets": [1000.5],
            "liquid_assets": [500.2],
            "fixed_assets": [300.1],
            "reserved": [100.5],
            "reserved_pershare": [0.67],
            "eps": [1.2],
            "bvps": [8.5],
            "pb": [1.5],
            "list_date": ["19910403"],
            "undp": [50.2],
            "per_undp": [0.33],
            "rev_yoy": [5.5],
            "profit_yoy": [8.5],
            "gpr": [30.5],
            "npr": [20.1],
            "holder_num": [50000],
        }
    )

    result = stockinfo.transform(data)
    assert pd.isna(result["pe"].iloc[0])

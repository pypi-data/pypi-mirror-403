"""
Test suite for Stock class
Tests cover initialization, data fetching, transformation, and utility methods
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.stock.constant import (
    EXCHANGES,
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    STATUSES,
    TARGET,
)
from xfintech.data.source.tushare.stock.stock.stock import Stock

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

    # Mock the connection object (which is returned by ts.pro_api())
    mock_connection = MagicMock()
    mock_connection.stock_basic = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "symbol": ["000001", "000002", "600000"],
            "name": ["平安银行", "万科A", "浦发银行"],
            "area": ["深圳", "深圳", "上海"],
            "industry": ["银行", "房地产", "银行"],
            "fullname": ["平安银行股份有限公司", "万科企业股份有限公司", "上海浦东发展银行股份有限公司"],
            "enname": ["Ping An Bank", "China Vanke", "Shanghai Pudong Development Bank"],
            "cnspell": ["PAYH", "WKA", "PFFH"],
            "market": ["主板", "主板", "主板"],
            "exchange": ["SZSE", "SZSE", "SSE"],
            "curr_type": ["CNY", "CNY", "CNY"],
            "list_status": ["L", "L", "L"],
            "list_date": ["19910403", "19910129", "19991110"],
            "delist_date": ["", "", ""],
            "is_hs": ["S", "S", "S"],
            "act_name": ["平安集团", "华润", "上海国资"],
            "act_ent_type": ["央企", "央企", "地方国资"],
        }
    )


@pytest.fixture
def expected_transformed_data():
    """Create expected transformed data"""
    return pd.DataFrame(
        {
            "code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "symbol": ["000001", "000002", "600000"],
            "name": ["平安银行", "万科A", "浦发银行"],
            "area": ["深圳", "深圳", "上海"],
            "industry": ["银行", "房地产", "银行"],
            "fullname": ["平安银行股份有限公司", "万科企业股份有限公司", "上海浦东发展银行股份有限公司"],
            "enname": ["Ping An Bank", "China Vanke", "Shanghai Pudong Development Bank"],
            "cnspell": ["PAYH", "WKA", "PFFH"],
            "market": ["主板", "主板", "主板"],
            "exchange": ["SZSE", "SZSE", "SSE"],
            "currency": ["CNY", "CNY", "CNY"],
            "list_status": ["L", "L", "L"],
            "list_date": ["1991-04-03", "1991-01-29", "1999-11-10"],
            "delist_date": ["NaT", "NaT", "NaT"],
            "is_hs": ["S", "S", "S"],
            "ace_name": ["平安集团", "华润", "上海国资"],
            "ace_type": ["央企", "央企", "地方国资"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_stock_init_basic(mock_session):
    """Test Stock initialization with minimal parameters"""
    stock = Stock(session=mock_session)

    assert stock.name == NAME
    assert stock.key == KEY
    assert stock.source == SOURCE
    assert stock.target == TARGET
    assert isinstance(stock.params, Params)
    assert isinstance(stock.coolant, Coolant)
    assert isinstance(stock.paginate, Paginate)
    assert isinstance(stock.retry, Retry)
    assert stock.paginate.pagesize == PAGINATE["pagesize"]
    assert stock.paginate.pagelimit == PAGINATE["pagelimit"]


def test_stock_init_with_params_dict(mock_session):
    """Test Stock initialization with params as dict"""
    params = {"list_status": "L", "ts_code": "600000.SH"}
    stock = Stock(session=mock_session, params=params)

    assert stock.params.list_status == "L"
    assert stock.params.ts_code == "600000.SH"


def test_stock_init_with_params_object(mock_session):
    """Test Stock initialization with Params object"""
    params = Params(list_status="D", ts_code="000001.SZ")
    stock = Stock(session=mock_session, params=params)

    assert stock.params.list_status == "D"
    assert stock.params.ts_code == "000001.SZ"


def test_stock_init_with_cache_bool_true(mock_session):
    """Test Stock initialization with cache=True"""
    stock = Stock(session=mock_session, cache=True)

    assert stock.cache is not None
    assert isinstance(stock.cache, Cache)


def test_stock_init_with_cache_bool_false(mock_session):
    """Test Stock initialization with cache=False"""
    stock = Stock(session=mock_session, cache=False)

    assert stock.cache is None


def test_stock_init_with_cache_dict(mock_session):
    """Test Stock initialization with cache as dict"""
    cache_config = {"directory": "/tmp/cache"}
    stock = Stock(session=mock_session, cache=cache_config)

    assert stock.cache is not None
    assert isinstance(stock.cache, Cache)


def test_stock_init_with_all_params(mock_session):
    """Test Stock initialization with all parameters"""
    stock = Stock(
        session=mock_session,
        params={"list_status": "L"},
        coolant={"interval": 1.0},
        retry={"max_retries": 3},
        cache=True,
    )

    assert stock.name == NAME
    assert stock.params.list_status == "L"
    assert stock.cache is not None
    assert stock.paginate.pagesize == PAGINATE["pagesize"]
    assert stock.paginate.pagelimit == PAGINATE["pagelimit"]


def test_stock_constants():
    """Test that constants are properly defined"""
    assert NAME == "stock"
    assert KEY == "/tushare/stock"
    assert EXCHANGES == ["SSE", "SZSE", "BSE"]
    assert STATUSES == ["L", "D", "P"]
    assert SOURCE is not None
    assert TARGET is not None


# ============================================================================
# Transform Method Tests
# ============================================================================


def test_stock_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    assert not result.empty
    assert len(result) == 3
    assert "code" in result.columns
    assert "name" in result.columns
    assert "list_date" in result.columns


def test_stock_transform_code_mapping(mock_session, sample_source_data):
    """Test that ts_code is mapped to code"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    assert result["code"].tolist() == ["000001.SZ", "000002.SZ", "600000.SH"]


def test_stock_transform_name_mapping(mock_session, sample_source_data):
    """Test that name is preserved"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    assert "平安银行" in result["name"].values


def test_stock_transform_date_format(mock_session, sample_source_data):
    """Test that list_date is converted from YYYYMMDD to YYYY-MM-DD"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    assert result["list_date"].tolist() == ["1991-04-03", "1991-01-29", "1999-11-10"]


def test_stock_transform_currency_mapping(mock_session, sample_source_data):
    """Test that curr_type is mapped to currency"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    assert "currency" in result.columns
    assert all(result["currency"] == "CNY")


def test_stock_transform_ace_name_mapping(mock_session, sample_source_data):
    """Test that act_name is mapped to ace_name"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    assert "ace_name" in result.columns
    assert "平安集团" in result["ace_name"].values


def test_stock_transform_empty_dataframe(mock_session):
    """Test transform with empty DataFrame"""
    stock = Stock(session=mock_session)
    empty_df = pd.DataFrame()
    result = stock.transform(empty_df)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_stock_transform_none_input(mock_session):
    """Test transform with None input"""
    stock = Stock(session=mock_session)
    result = stock.transform(None)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_stock_transform_handles_invalid_dates(mock_session):
    """Test transform handles invalid date formats"""
    stock = Stock(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "symbol": ["000001"],
            "name": ["Test Stock"],
            "area": ["Test"],
            "industry": ["Test"],
            "fullname": ["Test Company"],
            "enname": ["Test"],
            "cnspell": ["TS"],
            "market": ["主板"],
            "exchange": ["SZSE"],
            "curr_type": ["CNY"],
            "list_status": ["L"],
            "list_date": ["invalid"],  # Invalid date
            "delist_date": [""],
            "is_hs": ["N"],
            "act_name": ["Test"],
            "act_ent_type": ["Test"],
        }
    )

    result = stock.transform(data)
    # Should handle error with coerce
    assert pd.isna(result["list_date"].iloc[0]) or result["list_date"].iloc[0] == "NaT"


def test_stock_transform_removes_duplicates(mock_session):
    """Test that transform removes duplicate rows"""
    stock = Stock(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ"],  # Duplicate
            "symbol": ["000001", "000001"],
            "name": ["Test", "Test"],
            "area": ["Test", "Test"],
            "industry": ["Test", "Test"],
            "fullname": ["Test", "Test"],
            "enname": ["Test", "Test"],
            "cnspell": ["TS", "TS"],
            "market": ["主板", "主板"],
            "exchange": ["SZSE", "SZSE"],
            "curr_type": ["CNY", "CNY"],
            "list_status": ["L", "L"],
            "list_date": ["20200101", "20200101"],
            "delist_date": ["", ""],
            "is_hs": ["N", "N"],
            "act_name": ["Test", "Test"],
            "act_ent_type": ["Test", "Test"],
        }
    )

    result = stock.transform(data)
    assert len(result) == 1


def test_stock_transform_sorts_by_code(mock_session, sample_source_data):
    """Test that result is sorted by code"""
    stock = Stock(session=mock_session)
    # Shuffle the data
    shuffled = sample_source_data.sample(frac=1).reset_index(drop=True)
    result = stock.transform(shuffled)

    # Should be sorted
    assert result["code"].tolist() == sorted(result["code"].tolist())


def test_stock_transform_resets_index(mock_session, sample_source_data):
    """Test that result has reset index"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    assert result.index.tolist() == list(range(len(result)))


def test_stock_transform_only_target_columns(mock_session, sample_source_data):
    """Test that only target columns are in result"""
    stock = Stock(session=mock_session)
    result = stock.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)
    assert actual_cols == expected_cols


# ============================================================================
# _run Method Tests
# ============================================================================


def test_stock_run_with_cache_hit(mock_session):
    """Test _run returns cached data when available"""
    stock = Stock(session=mock_session, cache=True)

    # Set up cached data
    cached_df = pd.DataFrame({"code": ["000001.SZ"]})
    stock.cache.set(stock.params.identifier, cached_df)

    result = stock._run()

    # Should return cached data without calling API
    assert result.equals(cached_df)


def test_stock_run_without_list_status_param(mock_session, sample_source_data):
    """Test _run queries all statuses when list_status not specified"""
    stock = Stock(session=mock_session)

    # Mock _fetchall to return sample data
    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        with patch.object(stock, "transform", return_value=sample_source_data):
            stock._run()

            # Should call _fetchall for each status
            assert stock._fetchall.call_count == len(STATUSES)


def test_stock_run_with_list_status_param(mock_session, sample_source_data):
    """Test _run queries specific status when provided"""
    stock = Stock(session=mock_session, params={"list_status": "L"})

    # Mock _fetchall
    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        with patch.object(stock, "transform", return_value=sample_source_data):
            stock._run()

            # Should call _fetchall only once
            assert stock._fetchall.call_count == 1


def test_stock_run_adds_fields_param(mock_session, sample_source_data):
    """Test _run adds fields parameter if not provided"""
    stock = Stock(session=mock_session)

    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        with patch.object(stock, "transform", return_value=sample_source_data):
            stock._run()

            # Check that fields were added to params
            call_args = stock._fetchall.call_args
            assert "fields" in call_args[1]


def test_stock_run_preserves_fields_param(mock_session, sample_source_data):
    """Test _run preserves existing fields parameter"""
    custom_fields = "ts_code,name,symbol"
    stock = Stock(session=mock_session, params={"fields": custom_fields})

    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        with patch.object(stock, "transform", return_value=sample_source_data):
            stock._run()

            # Should use provided fields
            assert stock.params.fields == custom_fields


def test_stock_run_sets_cache(mock_session, sample_source_data):
    """Test _run saves result to cache"""
    stock = Stock(session=mock_session, cache=True)

    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        with patch.object(stock, "transform", return_value=sample_source_data):
            stock._run()

            # Check cache was set
            cached = stock.cache.get(stock.params.identifier)
            assert cached is not None


def test_stock_run_calls_transform(mock_session, sample_source_data):
    """Test _run calls transform method"""
    stock = Stock(session=mock_session)

    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        with patch.object(stock, "transform", return_value=sample_source_data) as mock_transform:
            stock._run()

            # Transform should be called
            assert mock_transform.called


def test_stock_run_concatenates_multiple_statuses(mock_session, sample_source_data):
    """Test _run concatenates data from multiple statuses"""
    stock = Stock(session=mock_session)

    # Create different data for each status
    listed_data = sample_source_data[sample_source_data["list_status"] == "L"]
    delisted_data = sample_source_data.copy()
    delisted_data["list_status"] = "D"

    call_count = [0]

    def mock_fetchall(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return listed_data
        elif call_count[0] == 2:
            return delisted_data
        else:
            return pd.DataFrame()

    with patch.object(stock, "_fetchall", side_effect=mock_fetchall):
        with patch.object(stock, "transform", side_effect=lambda x: x):
            result = stock._run()

            # Should have data from multiple statuses
            assert len(result) >= 1


# ============================================================================
# list_codes Method Tests
# ============================================================================


def test_stock_list_codes_basic(mock_session, sample_source_data):
    """Test list_codes returns list of stock codes"""
    stock = Stock(session=mock_session, cache=True)

    # Mock the run to return sample data
    transformed = stock.transform(sample_source_data)
    stock.cache.set(stock.params.identifier, transformed)

    codes = stock.list_codes()

    assert isinstance(codes, list)
    assert len(codes) == 3
    assert "000001.SZ" in codes


def test_stock_list_codes_unique(mock_session):
    """Test list_codes returns unique codes"""
    stock = Stock(session=mock_session, cache=True)

    # Create data with duplicates
    df = pd.DataFrame(
        {
            "code": ["000001.SZ", "000001.SZ", "000002.SZ"],
        }
    )
    stock.cache.set(stock.params.identifier, df)

    codes = stock.list_codes()

    assert len(codes) == 2  # Only unique codes


def test_stock_list_codes_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_codes calls run() when data not in cache"""
    stock = Stock(session=mock_session)

    with patch.object(stock, "run", return_value=stock.transform(sample_source_data)):
        codes = stock.list_codes()

        # run should have been called
        stock.run.assert_called_once()
        assert len(codes) == 3


def test_stock_list_codes_uses_cache(mock_session, sample_source_data):
    """Test list_codes uses cached data when available"""
    stock = Stock(session=mock_session, cache=True)

    transformed = stock.transform(sample_source_data)
    stock.cache.set(stock.params.identifier, transformed)

    # Mock _fetchall to verify it's not called when cache exists
    with patch.object(stock, "_fetchall") as mock_fetch:
        codes = stock.list_codes()

        # _fetchall should NOT be called when cache exists
        mock_fetch.assert_not_called()
        assert len(codes) == 3


# ============================================================================
# list_names Method Tests
# ============================================================================


def test_stock_list_names_basic(mock_session, sample_source_data):
    """Test list_names returns list of stock names"""
    stock = Stock(session=mock_session, cache=True)

    transformed = stock.transform(sample_source_data)
    stock.cache.set(stock.params.identifier, transformed)

    names = stock.list_names()

    assert isinstance(names, list)
    assert len(names) == 3
    assert "平安银行" in names


def test_stock_list_names_sorted(mock_session, sample_source_data):
    """Test list_names returns sorted list"""
    stock = Stock(session=mock_session, cache=True)

    transformed = stock.transform(sample_source_data)
    stock.cache.set(stock.params.identifier, transformed)

    names = stock.list_names()

    assert names == sorted(names)


def test_stock_list_names_unique(mock_session):
    """Test list_names returns unique names"""
    stock = Stock(session=mock_session, cache=True)

    df = pd.DataFrame(
        {
            "name": ["平安银行", "平安银行", "万科A"],
        }
    )
    stock.cache.set(stock.params.identifier, df)

    names = stock.list_names()

    assert len(names) == 2  # Only unique names


def test_stock_list_names_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_names calls run() when data not in cache"""
    stock = Stock(session=mock_session)

    with patch.object(stock, "run", return_value=stock.transform(sample_source_data)):
        names = stock.list_names()

        stock.run.assert_called_once()
        assert len(names) == 3


def test_stock_list_names_uses_cache(mock_session, sample_source_data):
    """Test list_names uses cached data when available"""
    stock = Stock(session=mock_session, cache=True)

    transformed = stock.transform(sample_source_data)
    stock.cache.set(stock.params.identifier, transformed)

    # Mock _fetchall to verify it's not called when cache exists
    with patch.object(stock, "_fetchall") as mock_fetch:
        names = stock.list_names()

        # _fetchall should NOT be called when cache exists
        mock_fetch.assert_not_called()
        assert len(names) == 3


# ============================================================================
# Integration Tests
# ============================================================================


def test_stock_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    stock = Stock(
        session=mock_session,
        params={"list_status": "L"},
        cache=True,
    )

    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        # Run the job
        result = stock.run()

        assert not result.empty
        assert "code" in result.columns

        # Get codes and names
        codes = stock.list_codes()
        names = stock.list_names()

        assert len(codes) > 0
        assert len(names) > 0


def test_stock_multiple_statuses_integration(mock_session, sample_source_data):
    """Test fetching data from multiple statuses"""
    stock = Stock(session=mock_session, cache=True)

    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        result = stock.run()

        # Should have data from multiple statuses
        unique_statuses = result["list_status"].unique()
        assert len(unique_statuses) >= 1


def test_stock_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across method calls"""
    stock = Stock(session=mock_session, cache=True)

    with patch.object(stock, "_load_cache", return_value=None) as mock_load:
        with patch.object(stock, "_fetchall", return_value=sample_source_data) as mock_fetch:
            # First call - fetches data and caches it
            result1 = stock.run()
            assert mock_fetch.call_count == len(STATUSES)  # Once per status
            assert mock_load.call_count == 1

            # Second call - _load_cache still returns None, so _fetchall called again
            result2 = stock.run()
            assert mock_fetch.call_count == len(STATUSES) * 2  # Called again for each status
            assert mock_load.call_count == 2

            pd.testing.assert_frame_equal(result1, result2)


def test_stock_params_identifier_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    stock1 = Stock(session=mock_session, params={"list_status": "L"}, cache=True)
    stock2 = Stock(session=mock_session, params={"list_status": "D"}, cache=True)

    assert stock1.params.identifier != stock2.params.identifier


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_stock_empty_result_handling(mock_session):
    """Test handling of empty API results"""
    stock = Stock(session=mock_session)

    empty_df = pd.DataFrame()
    with patch.object(stock, "_fetchall", return_value=empty_df):
        result = stock._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()


def test_stock_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    stock = Stock(session=mock_session)

    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": [f"{i:06d}.SZ" for i in range(5000)],
            "symbol": [f"{i:06d}" for i in range(5000)],
            "name": [f"Stock {i}" for i in range(5000)],
            "area": ["Test"] * 5000,
            "industry": ["Test"] * 5000,
            "fullname": [f"Company {i}" for i in range(5000)],
            "enname": ["Test"] * 5000,
            "cnspell": ["TS"] * 5000,
            "market": ["主板"] * 5000,
            "exchange": ["SZSE"] * 5000,
            "curr_type": ["CNY"] * 5000,
            "list_status": ["L"] * 5000,
            "list_date": ["20200101"] * 5000,
            "delist_date": [""] * 5000,
            "is_hs": ["N"] * 5000,
            "act_name": ["Test"] * 5000,
            "act_ent_type": ["Test"] * 5000,
        }
    )

    result = stock.transform(large_data)

    assert len(result) == 5000
    assert not result.empty


def test_stock_special_characters_in_data(mock_session):
    """Test handling of special characters in stock data"""
    stock = Stock(session=mock_session)

    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "symbol": ["000001"],
            "name": ["股票名称（中文）& Special <Chars>"],
            "area": ["深圳"],
            "industry": ["Test & Industry"],
            "fullname": ["公司全称 & info"],
            "enname": ["Company Name <Special>"],
            "cnspell": ["GPMZ"],
            "market": ["主板"],
            "exchange": ["SZSE"],
            "curr_type": ["CNY"],
            "list_status": ["L"],
            "list_date": ["20200101"],
            "delist_date": [""],
            "is_hs": ["N"],
            "act_name": ["实控人@公司"],
            "act_ent_type": ["央企"],
        }
    )

    result = stock.transform(data)

    assert len(result) == 1
    assert "特" in result["name"].values[0] or "股" in result["name"].values[0]


def test_stock_without_cache(mock_session, sample_source_data):
    """Test Stock works correctly without cache"""
    stock = Stock(session=mock_session, cache=False)

    assert stock.cache is None

    with patch.object(stock, "_fetchall", return_value=sample_source_data):
        result = stock.run()

        assert not result.empty

        # list_codes and list_names should still work
        codes = stock.list_codes()
        names = stock.list_names()

        assert len(codes) > 0
        assert len(names) > 0

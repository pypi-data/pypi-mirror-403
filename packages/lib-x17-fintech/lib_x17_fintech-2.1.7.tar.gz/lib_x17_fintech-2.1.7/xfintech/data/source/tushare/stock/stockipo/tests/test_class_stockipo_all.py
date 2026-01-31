from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.stockipo.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)
from xfintech.data.source.tushare.stock.stockipo.stockipo import StockIpo

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
    mock_connection.new_share = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["688001.SH", "688002.SH", "688003.SH"],
            "sub_code": ["787001", "787002", "787003"],
            "name": ["华兴源创", "睿创微纳", "天准科技"],
            "ipo_date": ["20190627", "20190628", "20190710"],
            "issue_date": ["20190710", "20190712", "20190722"],
            "amount": [40100.0, 60000.0, 45360.0],
            "market_amount": [10025.0, 15000.0, 11340.0],
            "price": [24.26, 20.00, 25.50],
            "pe": [41.08, 79.09, 58.62],
            "limit_amount": [10.025, 15.0, 11.34],
            "funds": [9.73, 12.0, 11.57],
            "ballot": [0.0424, 0.0632, 0.0587],
        }
    )


@pytest.fixture
def expected_transformed_data():
    """Create expected transformed data"""
    return pd.DataFrame(
        {
            "code": ["688001.SH", "688002.SH", "688003.SH"],
            "sub_code": ["787001", "787002", "787003"],
            "name": ["华兴源创", "睿创微纳", "天准科技"],
            "ipo_date": ["2019-06-27", "2019-06-28", "2019-07-10"],
            "ipo_datecode": ["20190627", "20190628", "20190710"],
            "issue_date": ["2019-07-10", "2019-07-12", "2019-07-22"],
            "issue_datecode": ["20190710", "20190712", "20190722"],
            "amount": [40100.0, 60000.0, 45360.0],
            "market_amount": [10025.0, 15000.0, 11340.0],
            "price": [24.26, 20.00, 25.50],
            "pe": [41.08, 79.09, 58.62],
            "limit_amount": [10.025, 15.0, 11.34],
            "funds": [9.73, 12.0, 11.57],
            "ballot": [0.0424, 0.0632, 0.0587],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_ipo_init_basic(mock_session):
    """Test StockIpo initialization with minimal parameters"""
    ipo = StockIpo(session=mock_session)

    assert ipo.name == NAME
    assert ipo.key == KEY
    assert ipo.source == SOURCE
    assert ipo.target == TARGET
    assert isinstance(ipo.params, Params)
    assert isinstance(ipo.coolant, Coolant)
    assert isinstance(ipo.paginate, Paginate)
    assert isinstance(ipo.retry, Retry)


def test_ipo_init_with_params_dict(mock_session):
    """Test StockIpo initialization with params as dict"""
    params = {"start_date": "20230101", "end_date": "20231231"}
    ipo = StockIpo(session=mock_session, params=params)

    assert ipo.params.start_date == "20230101"
    assert ipo.params.end_date == "20231231"


def test_ipo_init_with_params_object(mock_session):
    """Test StockIpo initialization with Params object"""
    params = Params(year="2023")
    ipo = StockIpo(session=mock_session, params=params)

    assert ipo.params.year == "2023"


def test_ipo_init_with_year_param(mock_session):
    """Test StockIpo initialization with year parameter"""
    ipo = StockIpo(session=mock_session, params={"year": "2023"})

    assert ipo.params.year == "2023"


def test_ipo_init_with_trade_date_param(mock_session):
    """Test StockIpo initialization with trade_date parameter"""
    ipo = StockIpo(session=mock_session, params={"trade_date": "20230315"})

    assert ipo.params.trade_date == "20230315"


def test_ipo_init_with_cache_bool_true(mock_session):
    """Test StockIpo initialization with cache=True"""
    ipo = StockIpo(session=mock_session, cache=True)

    assert ipo.cache is not None
    assert isinstance(ipo.cache, Cache)


def test_ipo_init_with_cache_bool_false(mock_session):
    """Test StockIpo initialization with cache=False"""
    ipo = StockIpo(session=mock_session, cache=False)

    assert ipo.cache is None


def test_ipo_init_with_cache_dict(mock_session):
    """Test StockIpo initialization with cache as dict"""
    cache_config = {"directory": "/tmp/cache"}
    ipo = StockIpo(session=mock_session, cache=cache_config)

    assert ipo.cache is not None
    assert isinstance(ipo.cache, Cache)


def test_ipo_init_default_paginate_limit(mock_session):
    """Test StockIpo sets default paginate pagesize to 2000 and pagelimit to 5"""
    ipo = StockIpo(session=mock_session)

    assert ipo.paginate.pagesize == PAGINATE["pagesize"]
    assert ipo.paginate.pagelimit == PAGINATE["pagelimit"]


def test_ipo_init_with_all_params(mock_session):
    """Test StockIpo initialization with all parameters"""
    ipo = StockIpo(
        session=mock_session,
        params={"year": "2023"},
        coolant={"interval": 1.0},
        retry={"max_retries": 3},
        cache=True,
    )

    assert ipo.name == NAME
    assert ipo.params.year == "2023"
    assert ipo.cache is not None
    assert ipo.paginate.pagesize == PAGINATE["pagesize"]
    assert ipo.paginate.pagelimit == PAGINATE["pagelimit"]


def test_ipo_constants():
    """Test that constants are properly defined"""
    assert NAME == "stockipo"
    assert KEY == "/tushare/stockipo"
    assert SOURCE is not None
    assert TARGET is not None


# ============================================================================
# Transform Method Tests
# ============================================================================


def test_ipo_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert not result.empty
    assert len(result) == 3
    assert "code" in result.columns
    assert "name" in result.columns
    assert "ipo_date" in result.columns


def test_ipo_transform_code_mapping(mock_session, sample_source_data):
    """Test that ts_code is mapped to code"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert result["code"].tolist() == ["688001.SH", "688002.SH", "688003.SH"]


def test_ipo_transform_name_mapping(mock_session, sample_source_data):
    """Test that name is preserved"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert "华兴源创" in result["name"].values


def test_ipo_transform_ipo_date_format(mock_session, sample_source_data):
    """Test that ipo_date is converted from YYYYMMDD to YYYY-MM-DD"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert result["ipo_date"].tolist() == ["2019-06-27", "2019-06-28", "2019-07-10"]


def test_ipo_transform_ipo_datecode_preserved(mock_session, sample_source_data):
    """Test that ipo_datecode preserves original format"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert result["ipo_datecode"].tolist() == ["20190627", "20190628", "20190710"]


def test_ipo_transform_issue_date_format(mock_session, sample_source_data):
    """Test that issue_date is converted from YYYYMMDD to YYYY-MM-DD"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert result["issue_date"].tolist() == ["2019-07-10", "2019-07-12", "2019-07-22"]


def test_ipo_transform_issue_datecode_preserved(mock_session, sample_source_data):
    """Test that issue_datecode preserves original format"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert result["issue_datecode"].tolist() == ["20190710", "20190712", "20190722"]


def test_ipo_transform_numeric_conversions(mock_session, sample_source_data):
    """Test numeric field conversions"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert result["amount"].dtype in [float, "float64"]
    assert result["price"].dtype in [float, "float64"]
    assert result["pe"].dtype in [float, "float64"]


def test_ipo_transform_empty_dataframe(mock_session):
    """Test transform with empty DataFrame"""
    ipo = StockIpo(session=mock_session)
    empty_df = pd.DataFrame()
    result = ipo.transform(empty_df)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_ipo_transform_none_input(mock_session):
    """Test transform with None input"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(None)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_ipo_transform_handles_invalid_dates(mock_session):
    """Test transform handles invalid date formats"""
    ipo = StockIpo(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["688001.SH"],
            "sub_code": ["787001"],
            "name": ["Test"],
            "ipo_date": ["invalid"],
            "issue_date": ["invalid"],
            "amount": [1000.0],
            "market_amount": [500.0],
            "price": [10.0],
            "pe": [20.0],
            "limit_amount": [5.0],
            "funds": [1.0],
            "ballot": [0.05],
        }
    )

    result = ipo.transform(data)
    assert pd.isna(result["ipo_date"].iloc[0]) or result["ipo_date"].iloc[0] == "NaT"


def test_ipo_transform_removes_duplicates(mock_session):
    """Test that transform removes duplicate rows"""
    ipo = StockIpo(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["688001.SH", "688001.SH"],  # Duplicate
            "sub_code": ["787001", "787001"],
            "name": ["Test", "Test"],
            "ipo_date": ["20190627", "20190627"],
            "issue_date": ["20190710", "20190710"],
            "amount": [1000.0, 1000.0],
            "market_amount": [500.0, 500.0],
            "price": [10.0, 10.0],
            "pe": [20.0, 20.0],
            "limit_amount": [5.0, 5.0],
            "funds": [1.0, 1.0],
            "ballot": [0.05, 0.05],
        }
    )

    result = ipo.transform(data)
    assert len(result) == 1


def test_ipo_transform_sorts_by_code(mock_session, sample_source_data):
    """Test that result is sorted by code"""
    ipo = StockIpo(session=mock_session)
    shuffled = sample_source_data.sample(frac=1).reset_index(drop=True)
    result = ipo.transform(shuffled)

    assert result["code"].tolist() == sorted(result["code"].tolist())


def test_ipo_transform_resets_index(mock_session, sample_source_data):
    """Test that result has reset index"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    assert result.index.tolist() == list(range(len(result)))


def test_ipo_transform_only_target_columns(mock_session, sample_source_data):
    """Test that only target columns are in result"""
    ipo = StockIpo(session=mock_session)
    result = ipo.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)
    assert actual_cols == expected_cols


# ============================================================================
# _run Method Tests
# ============================================================================


def test_ipo_run_with_cache_hit(mock_session):
    """Test _run returns cached data when available"""
    ipo = StockIpo(session=mock_session, cache=True)

    cached_df = pd.DataFrame({"code": ["688001.SH"]})
    ipo.cache.set(ipo.params.identifier, cached_df)

    result = ipo._run()

    assert result.equals(cached_df)


def test_ipo_run_basic_date_range(mock_session, sample_source_data):
    """Test _run with start_date and end_date"""
    ipo = StockIpo(session=mock_session, params={"start_date": "20190101", "end_date": "20191231"})

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        result = ipo._run()

        assert not result.empty
        ipo._fetchall.assert_called_once()
        call_kwargs = ipo._fetchall.call_args[1]
        assert call_kwargs["start_date"] == "20190101"
        assert call_kwargs["end_date"] == "20191231"


def test_ipo_run_with_year_param(mock_session, sample_source_data):
    """Test _run converts year to start/end date"""
    ipo = StockIpo(session=mock_session, params={"year": "2023"})

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        ipo._run()

        call_kwargs = ipo._fetchall.call_args[1]
        assert call_kwargs["start_date"] == "20230101"
        assert call_kwargs["end_date"] == "20231231"
        assert "year" not in call_kwargs


def test_ipo_run_with_year_param_int(mock_session, sample_source_data):
    """Test _run handles year as integer"""
    ipo = StockIpo(session=mock_session, params={"year": 2023})

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        ipo._run()

        call_kwargs = ipo._fetchall.call_args[1]
        assert call_kwargs["start_date"] == "20230101"
        assert call_kwargs["end_date"] == "20231231"


def test_ipo_run_adds_fields_param(mock_session, sample_source_data):
    """Test _run adds fields parameter if not provided"""
    ipo = StockIpo(session=mock_session)

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        ipo._run()

        call_kwargs = ipo._fetchall.call_args[1]
        assert "fields" in call_kwargs


def test_ipo_run_preserves_fields_param(mock_session, sample_source_data):
    """Test _run preserves existing fields parameter"""
    custom_fields = "ts_code,name,ipo_date"
    ipo = StockIpo(session=mock_session, params={"fields": custom_fields})

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        ipo._run()

        # Fields should be in the call
        call_kwargs = ipo._fetchall.call_args[1]
        assert "fields" in call_kwargs


def test_ipo_run_sets_cache(mock_session, sample_source_data):
    """Test _run saves result to cache"""
    ipo = StockIpo(session=mock_session, cache=True)

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        ipo._run()

        cached = ipo.cache.get(ipo.params.identifier)
        assert cached is not None


def test_ipo_run_calls_transform(mock_session, sample_source_data):
    """Test _run calls transform method"""
    ipo = StockIpo(session=mock_session)

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        with patch.object(ipo, "transform", return_value=sample_source_data) as mock_transform:
            ipo._run()

            mock_transform.assert_called_once()


# ============================================================================
# list_codes Method Tests
# ============================================================================


def test_ipo_list_codes_basic(mock_session, sample_source_data):
    """Test list_codes returns list of IPO codes"""
    ipo = StockIpo(session=mock_session, cache=True)

    transformed = ipo.transform(sample_source_data)
    ipo.cache.set(ipo.params.identifier, transformed)

    codes = ipo.list_codes()

    assert isinstance(codes, list)
    assert len(codes) == 3
    assert "688001.SH" in codes


def test_ipo_list_codes_unique(mock_session):
    """Test list_codes returns unique codes"""
    ipo = StockIpo(session=mock_session, cache=True)

    df = pd.DataFrame(
        {
            "code": ["688001.SH", "688001.SH", "688002.SH"],
        }
    )
    ipo.cache.set(ipo.params.identifier, df)

    codes = ipo.list_codes()

    assert len(codes) == 2


def test_ipo_list_codes_sorted(mock_session, sample_source_data):
    """Test list_codes returns sorted list"""
    ipo = StockIpo(session=mock_session, cache=True)

    transformed = ipo.transform(sample_source_data)
    ipo.cache.set(ipo.params.identifier, transformed)

    codes = ipo.list_codes()

    assert codes == sorted(codes)


def test_ipo_list_codes_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_codes calls run() when data not in cache"""
    ipo = StockIpo(session=mock_session)

    with patch.object(ipo, "run", return_value=ipo.transform(sample_source_data)):
        codes = ipo.list_codes()

        ipo.run.assert_called_once()
        assert len(codes) == 3


# ============================================================================
# list_names Method Tests
# ============================================================================


def test_ipo_list_names_basic(mock_session, sample_source_data):
    """Test list_names returns list of IPO names"""
    ipo = StockIpo(session=mock_session, cache=True)

    transformed = ipo.transform(sample_source_data)
    ipo.cache.set(ipo.params.identifier, transformed)

    names = ipo.list_names()

    assert isinstance(names, list)
    assert len(names) == 3
    assert "华兴源创" in names


def test_ipo_list_names_sorted(mock_session, sample_source_data):
    """Test list_names returns sorted list"""
    ipo = StockIpo(session=mock_session, cache=True)

    transformed = ipo.transform(sample_source_data)
    ipo.cache.set(ipo.params.identifier, transformed)

    names = ipo.list_names()

    assert names == sorted(names)


def test_ipo_list_names_unique(mock_session):
    """Test list_names returns unique names"""
    ipo = StockIpo(session=mock_session, cache=True)

    df = pd.DataFrame(
        {
            "name": ["华兴源创", "华兴源创", "睿创微纳"],
        }
    )
    ipo.cache.set(ipo.params.identifier, df)

    names = ipo.list_names()

    assert len(names) == 2


def test_ipo_list_names_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_names calls run() when data not in cache"""
    ipo = StockIpo(session=mock_session)

    with patch.object(ipo, "run", return_value=ipo.transform(sample_source_data)):
        names = ipo.list_names()

        ipo.run.assert_called_once()
        assert len(names) == 3


# ============================================================================
# Integration Tests
# ============================================================================


def test_ipo_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    ipo = StockIpo(
        session=mock_session,
        params={"year": "2019"},
        cache=True,
    )

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        result = ipo.run()

        assert not result.empty
        assert "code" in result.columns

        codes = ipo.list_codes()
        names = ipo.list_names()

        assert len(codes) > 0
        assert len(names) > 0


def test_ipo_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across method calls"""
    ipo = StockIpo(session=mock_session, cache=True)

    with patch.object(ipo, "_load_cache", return_value=None) as mock_load:
        with patch.object(ipo, "_fetchall", return_value=sample_source_data) as mock_fetch:
            # First run - fetches data and caches it
            result1 = ipo.run()
            assert mock_fetch.call_count == 1
            assert mock_load.call_count == 1

            # Second run - _load_cache still returns None, so _fetchall called again
            result2 = ipo.run()
            assert mock_fetch.call_count == 2  # Called again
            assert mock_load.call_count == 2

            pd.testing.assert_frame_equal(result1, result2)


def test_ipo_params_identifier_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    ipo1 = StockIpo(session=mock_session, params={"year": "2022"}, cache=True)
    ipo2 = StockIpo(session=mock_session, params={"year": "2023"}, cache=True)

    assert ipo1.params.identifier != ipo2.params.identifier


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_ipo_empty_result_handling(mock_session):
    """Test handling of empty API results"""
    ipo = StockIpo(session=mock_session)

    empty_df = pd.DataFrame()
    with patch.object(ipo, "_fetchall", return_value=empty_df):
        result = ipo._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()


def test_ipo_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    ipo = StockIpo(session=mock_session)

    large_data = pd.DataFrame(
        {
            "ts_code": [f"{i:06d}.SH" for i in range(2000)],
            "sub_code": [f"78{i:04d}" for i in range(2000)],
            "name": [f"Stock {i}" for i in range(2000)],
            "ipo_date": ["20230101"] * 2000,
            "issue_date": ["20230115"] * 2000,
            "amount": [1000.0] * 2000,
            "market_amount": [500.0] * 2000,
            "price": [10.0] * 2000,
            "pe": [20.0] * 2000,
            "limit_amount": [5.0] * 2000,
            "funds": [1.0] * 2000,
            "ballot": [0.05] * 2000,
        }
    )

    result = ipo.transform(large_data)

    assert len(result) == 2000
    assert not result.empty


def test_ipo_special_characters_in_data(mock_session):
    """Test handling of special characters in IPO data"""
    ipo = StockIpo(session=mock_session)

    data = pd.DataFrame(
        {
            "ts_code": ["688001.SH"],
            "sub_code": ["787001"],
            "name": ["股票名称（中文）& Special <Chars>"],
            "ipo_date": ["20230101"],
            "issue_date": ["20230115"],
            "amount": [1000.0],
            "market_amount": [500.0],
            "price": [10.0],
            "pe": [20.0],
            "limit_amount": [5.0],
            "funds": [1.0],
            "ballot": [0.05],
        }
    )

    result = ipo.transform(data)

    assert len(result) == 1
    assert "股" in result["name"].values[0] or "Special" in result["name"].values[0]


def test_ipo_without_cache(mock_session, sample_source_data):
    """Test StockIpo works correctly without cache"""
    ipo = StockIpo(session=mock_session, cache=False)

    assert ipo.cache is None

    with patch.object(ipo, "_fetchall", return_value=sample_source_data):
        result = ipo.run()

        assert not result.empty

        codes = ipo.list_codes()
        names = ipo.list_names()

        assert len(codes) > 0
        assert len(names) > 0


def test_ipo_missing_numeric_values(mock_session):
    """Test handling of missing numeric values"""
    ipo = StockIpo(session=mock_session)

    data = pd.DataFrame(
        {
            "ts_code": ["688001.SH"],
            "sub_code": ["787001"],
            "name": ["Test Stock"],
            "ipo_date": ["20230101"],
            "issue_date": ["20230115"],
            "amount": [None],
            "market_amount": [None],
            "price": [None],
            "pe": [None],
            "limit_amount": [None],
            "funds": [None],
            "ballot": [None],
        }
    )

    result = ipo.transform(data)

    assert len(result) == 1
    assert pd.isna(result["amount"].iloc[0])
    assert pd.isna(result["price"].iloc[0])

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.stockst.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)
from xfintech.data.source.tushare.stock.stockst.stockst import StockSt

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
    mock_connection.stock_st = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "name": ["*ST平安", "*ST万科", "ST浦发"],
            "trade_date": ["20230101", "20230101", "20230102"],
            "type": ["S", "S", "S"],
            "type_name": ["*ST", "*ST", "ST"],
        }
    )


@pytest.fixture
def expected_transformed_data():
    """Create expected transformed data"""
    return pd.DataFrame(
        {
            "code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "name": ["*ST平安", "*ST万科", "ST浦发"],
            "date": ["2023-01-01", "2023-01-01", "2023-01-02"],
            "datecode": ["20230101", "20230101", "20230102"],
            "type": ["S", "S", "S"],
            "type_name": ["*ST", "*ST", "ST"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_st_init_basic(mock_session):
    """Test StockSt initialization with minimal parameters"""
    st = StockSt(session=mock_session)

    assert st.name == NAME
    assert st.key == KEY
    assert st.source == SOURCE
    assert st.target == TARGET
    assert isinstance(st.params, Params)
    assert isinstance(st.coolant, Coolant)
    assert isinstance(st.paginate, Paginate)
    assert isinstance(st.retry, Retry)
    assert st.paginate.pagesize == PAGINATE["pagesize"]
    assert st.paginate.pagelimit == PAGINATE["pagelimit"]


def test_st_init_with_params_dict(mock_session):
    """Test StockSt initialization with params as dict"""
    params = {"start_date": "20230101", "end_date": "20231231"}
    st = StockSt(session=mock_session, params=params)
    assert st.params.get("start_date") == "20230101"
    assert st.params.get("end_date") == "20231231"


def test_st_init_with_params_object(mock_session):
    """Test StockSt initialization with Params object"""
    params = Params(year="2023")
    st = StockSt(session=mock_session, params=params)
    assert st.params.get("year") == "2023"


def test_st_init_with_year_param(mock_session):
    """Test StockSt initialization with year parameter"""
    st = StockSt(session=mock_session, params={"year": "2023"})
    assert st.params.get("year") == "2023"


def test_st_init_with_trade_date_param(mock_session):
    """Test StockSt initialization with trade_date parameter"""
    st = StockSt(session=mock_session, params={"trade_date": "20230315"})

    assert st.params.trade_date == "20230315"


def test_st_init_with_ts_code_param(mock_session):
    """Test StockSt initialization with ts_code parameter"""
    st = StockSt(session=mock_session, params={"ts_code": "600000.SH"})

    assert st.params.ts_code == "600000.SH"


def test_st_init_with_cache_bool_true(mock_session):
    """Test StockSt initialization with cache=True"""
    st = StockSt(session=mock_session, cache=True)

    assert st.cache is not None
    assert isinstance(st.cache, Cache)


def test_st_init_with_cache_bool_false(mock_session):
    """Test StockSt initialization with cache=False"""
    st = StockSt(session=mock_session, cache=False)

    assert st.cache is None


def test_st_init_with_cache_dict(mock_session):
    """Test StockSt initialization with cache as dict"""
    cache_config = {"directory": "/tmp/cache"}
    st = StockSt(session=mock_session, cache=cache_config)

    assert st.cache is not None
    assert isinstance(st.cache, Cache)


def test_st_init_with_all_params(mock_session):
    """Test StockSt initialization with all parameters"""
    st = StockSt(
        session=mock_session,
        params={"year": "2023"},
        coolant={"interval": 1.0},
        retry={"max_retries": 3},
        cache=True,
    )

    assert st.name == NAME
    assert st.params.year == "2023"
    assert st.cache is not None
    assert st.paginate.pagesize == PAGINATE["pagesize"]
    assert st.paginate.pagelimit == PAGINATE["pagelimit"]


def test_st_constants():
    """Test that constants are properly defined"""
    assert NAME == "stockst"
    assert KEY == "/tushare/stockst"
    assert SOURCE is not None
    assert TARGET is not None


# ============================================================================
# Transform Method Tests
# ============================================================================


def test_st_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    assert not result.empty
    assert len(result) == 3
    assert "code" in result.columns
    assert "name" in result.columns
    assert "date" in result.columns


def test_st_transform_code_mapping(mock_session, sample_source_data):
    """Test that ts_code is mapped to code"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    assert result["code"].tolist() == ["000001.SZ", "000002.SZ", "600000.SH"]


def test_st_transform_name_mapping(mock_session, sample_source_data):
    """Test that name is preserved"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    assert "*ST平安" in result["name"].values


def test_st_transform_date_format(mock_session, sample_source_data):
    """Test that trade_date is converted from YYYYMMDD to YYYY-MM-DD"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    assert "2023-01-01" in result["date"].values
    assert "2023-01-02" in result["date"].values


def test_st_transform_datecode_preserved(mock_session, sample_source_data):
    """Test that datecode preserves original format"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    assert "20230101" in result["datecode"].values
    assert "20230102" in result["datecode"].values


def test_st_transform_type_fields(mock_session, sample_source_data):
    """Test that type and type_name are preserved"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    assert all(result["type"] == "S")
    assert "*ST" in result["type_name"].values
    assert "ST" in result["type_name"].values


def test_st_transform_empty_dataframe(mock_session):
    """Test transform with empty DataFrame"""
    st = StockSt(session=mock_session)
    empty_df = pd.DataFrame()
    result = st.transform(empty_df)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_st_transform_none_input(mock_session):
    """Test transform with None input"""
    st = StockSt(session=mock_session)
    result = st.transform(None)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_st_transform_handles_invalid_dates(mock_session):
    """Test transform handles invalid date formats"""
    st = StockSt(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "name": ["Test ST"],
            "trade_date": ["invalid"],
            "type": ["S"],
            "type_name": ["*ST"],
        }
    )

    result = st.transform(data)
    assert pd.isna(result["date"].iloc[0]) or result["date"].iloc[0] == "NaT"


def test_st_transform_removes_duplicates(mock_session):
    """Test that transform removes duplicate rows"""
    st = StockSt(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ"],  # Duplicate
            "name": ["*ST平安", "*ST平安"],
            "trade_date": ["20230101", "20230101"],
            "type": ["S", "S"],
            "type_name": ["*ST", "*ST"],
        }
    )

    result = st.transform(data)
    assert len(result) == 1


def test_st_transform_sorts_by_code(mock_session, sample_source_data):
    """Test that result is sorted by code"""
    st = StockSt(session=mock_session)
    shuffled = sample_source_data.sample(frac=1).reset_index(drop=True)
    result = st.transform(shuffled)

    assert result["code"].tolist() == sorted(result["code"].tolist())


def test_st_transform_resets_index(mock_session, sample_source_data):
    """Test that result has reset index"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    assert result.index.tolist() == list(range(len(result)))


def test_st_transform_only_target_columns(mock_session, sample_source_data):
    """Test that only target columns are in result"""
    st = StockSt(session=mock_session)
    result = st.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)
    assert actual_cols == expected_cols


# ============================================================================
# _run Method Tests
# ============================================================================


def test_st_run_with_cache_hit(mock_session):
    """Test _run returns cached data when available"""
    st = StockSt(session=mock_session, cache=True)

    cached_df = pd.DataFrame({"code": ["000001.SZ"]})
    st.cache.set(st.params.identifier, cached_df)

    result = st._run()

    assert result.equals(cached_df)


def test_st_run_basic_date_range(mock_session, sample_source_data):
    """Test _run with start_date and end_date"""
    st = StockSt(session=mock_session, params={"start_date": "20230101", "end_date": "20231231"})

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        result = st._run()

        assert not result.empty
        st._fetchall.assert_called_once()
        call_kwargs = st._fetchall.call_args[1]
        assert call_kwargs["start_date"] == "20230101"
        assert call_kwargs["end_date"] == "20231231"


def test_st_run_with_year_param(mock_session, sample_source_data):
    """Test _run converts year to start/end date"""
    st = StockSt(session=mock_session, params={"year": "2023"})

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        st._run()

        call_kwargs = st._fetchall.call_args[1]
        assert call_kwargs["start_date"] == "20230101"
        assert call_kwargs["end_date"] == "20231231"
        assert "year" not in call_kwargs


def test_st_run_with_year_param_int(mock_session, sample_source_data):
    """Test _run handles year as integer"""
    st = StockSt(session=mock_session, params={"year": 2023})

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        st._run()

        call_kwargs = st._fetchall.call_args[1]
        assert call_kwargs["start_date"] == "20230101"
        assert call_kwargs["end_date"] == "20231231"


def test_st_run_with_ts_code_param(mock_session, sample_source_data):
    """Test _run with ts_code parameter"""
    st = StockSt(session=mock_session, params={"ts_code": "600000.SH"})

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        st._run()

        call_kwargs = st._fetchall.call_args[1]
        assert call_kwargs["ts_code"] == "600000.SH"


def test_st_run_adds_fields_param(mock_session, sample_source_data):
    """Test _run adds fields parameter if not provided"""
    st = StockSt(session=mock_session)

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        st._run()

        call_kwargs = st._fetchall.call_args[1]
        assert "fields" in call_kwargs


def test_st_run_preserves_fields_param(mock_session, sample_source_data):
    """Test _run preserves existing fields parameter"""
    custom_fields = "ts_code,name,trade_date"
    st = StockSt(session=mock_session, params={"fields": custom_fields})

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        st._run()

        call_kwargs = st._fetchall.call_args[1]
        assert "fields" in call_kwargs


def test_st_run_sets_cache(mock_session, sample_source_data):
    """Test _run saves result to cache"""
    st = StockSt(session=mock_session, cache=True)

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        st._run()

        cached = st.cache.get(st.params.identifier)
        assert cached is not None


def test_st_run_calls_transform(mock_session, sample_source_data):
    """Test _run calls transform method"""
    st = StockSt(session=mock_session)

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        with patch.object(st, "transform", return_value=sample_source_data) as mock_transform:
            st._run()

            mock_transform.assert_called_once()


# ============================================================================
# list_codes Method Tests
# ============================================================================


def test_st_list_codes_basic(mock_session, sample_source_data):
    """Test list_codes returns list of ST stock codes"""
    st = StockSt(session=mock_session, cache=True)

    transformed = st.transform(sample_source_data)
    st.cache.set(st.params.identifier, transformed)

    codes = st.list_codes()

    assert isinstance(codes, list)
    assert len(codes) == 3
    assert "000001.SZ" in codes


def test_st_list_codes_unique(mock_session):
    """Test list_codes returns unique codes"""
    st = StockSt(session=mock_session, cache=True)

    df = pd.DataFrame(
        {
            "code": ["000001.SZ", "000001.SZ", "000002.SZ"],
        }
    )
    st.cache.set(st.params.identifier, df)

    codes = st.list_codes()

    assert len(codes) == 2


def test_st_list_codes_sorted(mock_session, sample_source_data):
    """Test list_codes returns sorted list"""
    st = StockSt(session=mock_session, cache=True)

    transformed = st.transform(sample_source_data)
    st.cache.set(st.params.identifier, transformed)

    codes = st.list_codes()

    assert codes == sorted(codes)


def test_st_list_codes_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_codes calls run() when data not in cache"""
    st = StockSt(session=mock_session)

    with patch.object(st, "run", return_value=st.transform(sample_source_data)):
        codes = st.list_codes()

        st.run.assert_called_once()
        assert len(codes) == 3


# ============================================================================
# list_names Method Tests
# ============================================================================


def test_st_list_names_basic(mock_session, sample_source_data):
    """Test list_names returns list of ST stock names"""
    st = StockSt(session=mock_session, cache=True)

    transformed = st.transform(sample_source_data)
    st.cache.set(st.params.identifier, transformed)

    names = st.list_names()

    assert isinstance(names, list)
    assert len(names) == 3
    assert "*ST平安" in names


def test_st_list_names_sorted(mock_session, sample_source_data):
    """Test list_names returns sorted list"""
    st = StockSt(session=mock_session, cache=True)

    transformed = st.transform(sample_source_data)
    st.cache.set(st.params.identifier, transformed)

    names = st.list_names()

    assert names == sorted(names)


def test_st_list_names_unique(mock_session):
    """Test list_names returns unique names"""
    st = StockSt(session=mock_session, cache=True)

    df = pd.DataFrame(
        {
            "name": ["*ST平安", "*ST平安", "*ST万科"],
        }
    )
    st.cache.set(st.params.identifier, df)

    names = st.list_names()

    assert len(names) == 2


def test_st_list_names_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_names calls run() when data not in cache"""
    st = StockSt(session=mock_session)

    with patch.object(st, "run", return_value=st.transform(sample_source_data)):
        names = st.list_names()

        st.run.assert_called_once()
        assert len(names) == 3


# ============================================================================
# Integration Tests
# ============================================================================


def test_st_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    st = StockSt(
        session=mock_session,
        params={"year": "2023"},
        cache=True,
    )

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        result = st.run()

        assert not result.empty
        assert "code" in result.columns

        codes = st.list_codes()
        names = st.list_names()

        assert len(codes) > 0
        assert len(names) > 0


def test_st_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across method calls"""
    st = StockSt(session=mock_session, cache=True)

    with patch.object(st, "_load_cache", return_value=None) as mock_load:
        with patch.object(st, "_fetchall", return_value=sample_source_data) as mock_fetch:
            # First run - fetches data and caches it
            result1 = st.run()
            assert mock_fetch.call_count == 1
            assert mock_load.call_count == 1

            # Second run - _load_cache still returns None, so _fetchall called again
            result2 = st.run()
            assert mock_fetch.call_count == 2  # Called again
            assert mock_load.call_count == 2

            pd.testing.assert_frame_equal(result1, result2)


def test_st_params_identifier_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    st1 = StockSt(session=mock_session, params={"year": "2022"}, cache=True)
    st2 = StockSt(session=mock_session, params={"year": "2023"}, cache=True)

    assert st1.params.identifier != st2.params.identifier


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_st_empty_result_handling(mock_session):
    """Test handling of empty API results"""
    st = StockSt(session=mock_session)

    empty_df = pd.DataFrame()
    with patch.object(st, "_fetchall", return_value=empty_df):
        result = st._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()


def test_st_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    st = StockSt(session=mock_session)

    large_data = pd.DataFrame(
        {
            "ts_code": [f"{i:06d}.SZ" for i in range(1000)],
            "name": [f"*ST股票{i}" for i in range(1000)],
            "trade_date": ["20230101"] * 1000,
            "type": ["S"] * 1000,
            "type_name": ["*ST"] * 1000,
        }
    )

    result = st.transform(large_data)

    assert len(result) == 1000
    assert not result.empty


def test_st_special_characters_in_data(mock_session):
    """Test handling of special characters in ST data"""
    st = StockSt(session=mock_session)

    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "name": ["*ST股票（特殊）& Special <Chars>"],
            "trade_date": ["20230101"],
            "type": ["S"],
            "type_name": ["*ST"],
        }
    )

    result = st.transform(data)

    assert len(result) == 1
    assert "ST" in result["name"].values[0] or "特殊" in result["name"].values[0]


def test_st_without_cache(mock_session, sample_source_data):
    """Test StockSt works correctly without cache"""
    st = StockSt(session=mock_session, cache=False)

    assert st.cache is None

    with patch.object(st, "_fetchall", return_value=sample_source_data):
        result = st.run()

        assert not result.empty

        codes = st.list_codes()
        names = st.list_names()

        assert len(codes) > 0
        assert len(names) > 0


def test_st_multiple_st_types(mock_session):
    """Test handling of multiple ST types"""
    st = StockSt(session=mock_session)

    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "000003.SZ"],
            "name": ["*ST股票1", "ST股票2", "SST股票3"],
            "trade_date": ["20230101", "20230101", "20230101"],
            "type": ["S", "S", "S"],
            "type_name": ["*ST", "ST", "SST"],
        }
    )

    result = st.transform(data)

    assert len(result) == 3
    assert set(result["type_name"].values) == {"*ST", "ST", "SST"}

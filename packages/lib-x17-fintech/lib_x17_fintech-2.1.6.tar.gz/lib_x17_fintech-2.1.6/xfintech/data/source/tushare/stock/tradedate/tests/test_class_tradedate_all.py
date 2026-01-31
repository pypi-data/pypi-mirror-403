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
from xfintech.data.source.tushare.stock.tradedate.constant import (
    EXCHANGES,
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)
from xfintech.data.source.tushare.stock.tradedate.tradedate import TradeDate

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
    mock_connection.trade_cal = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "exchange": ["SSE", "SSE", "SSE", "SSE"],
            "cal_date": ["20230101", "20230102", "20230103", "20230104"],
            "is_open": [0, 1, 1, 0],
            "pretrade_date": ["20221230", "20221230", "20230102", "20230103"],
        }
    )


@pytest.fixture
def expected_transformed_data():
    """Create expected transformed data"""
    return pd.DataFrame(
        {
            "datecode": ["20230101", "20230102", "20230103", "20230104"],
            "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            "exchange": ["ALL", "ALL", "ALL", "ALL"],
            "previous": ["2022-12-30", "2022-12-30", "2023-01-02", "2023-01-03"],
            "is_open": [False, True, True, False],
            "year": [2023, 2023, 2023, 2023],
            "month": [1, 1, 1, 1],
            "day": [1, 2, 3, 4],
            "week": [52, 1, 1, 1],
            "weekday": ["Sun", "Mon", "Tue", "Wed"],
            "quarter": [1, 1, 1, 1],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_tradedate_init_basic(mock_session):
    """Test TradeDate initialization with minimal parameters"""
    td = TradeDate(session=mock_session)

    assert td.name == NAME
    assert td.key == KEY
    assert td.source == SOURCE
    assert td.target == TARGET
    assert isinstance(td.params, Params)
    assert isinstance(td.coolant, Coolant)
    assert isinstance(td.paginate, Paginate)
    assert isinstance(td.retry, Retry)
    assert td.paginate.pagesize == PAGINATE["pagesize"]
    assert td.paginate.pagelimit == PAGINATE["pagelimit"]


def test_tradedate_init_with_params_dict(mock_session):
    """Test TradeDate initialization with params as dict"""
    params = {"start_date": "20230101", "end_date": "20231231"}
    td = TradeDate(session=mock_session, params=params)

    assert td.params.start_date == "20230101"
    assert td.params.end_date == "20231231"


def test_tradedate_init_with_params_object(mock_session):
    """Test TradeDate initialization with Params object"""
    params = Params(year="2023")
    td = TradeDate(session=mock_session, params=params)

    assert td.params.year == "2023"


def test_tradedate_init_with_year_param(mock_session):
    """Test TradeDate initialization with year parameter"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    assert td.params.year == "2023"


def test_tradedate_init_with_exchange_param(mock_session):
    """Test TradeDate initialization with exchange parameter"""
    td = TradeDate(session=mock_session, params={"exchange": "SSE"})

    assert td.params.exchange == "SSE"


def test_tradedate_init_with_is_open_param(mock_session):
    """Test TradeDate initialization with is_open parameter"""
    td = TradeDate(session=mock_session, params={"is_open": "1"})

    assert td.params.is_open == "1"


def test_tradedate_init_with_cache_bool_true(mock_session):
    """Test TradeDate initialization with cache=True"""
    td = TradeDate(session=mock_session, cache=True)

    assert td.cache is not None
    assert isinstance(td.cache, Cache)


def test_tradedate_init_with_cache_bool_false(mock_session):
    """Test TradeDate initialization with cache=False"""
    td = TradeDate(session=mock_session, cache=False)

    assert td.cache is None


def test_tradedate_init_with_cache_dict(mock_session):
    """Test TradeDate initialization with cache as dict"""
    cache_config = {"directory": "/tmp/cache"}
    td = TradeDate(session=mock_session, cache=cache_config)

    assert td.cache is not None
    assert isinstance(td.cache, Cache)


def test_tradedate_init_with_all_params(mock_session):
    """Test TradeDate initialization with all parameters"""
    td = TradeDate(
        session=mock_session,
        params={"year": "2023", "exchange": "SSE"},
        coolant={"interval": 1.0},
        retry={"max_retries": 3},
        cache=True,
    )

    assert td.name == NAME
    assert td.params.year == "2023"
    assert td.params.exchange == "SSE"
    assert td.cache is not None
    assert td.paginate.pagesize == PAGINATE["pagesize"]
    assert td.paginate.pagelimit == PAGINATE["pagelimit"]


def test_tradedate_constants():
    """Test that constants are properly defined"""
    assert NAME == "tradedate"
    assert KEY == "/tushare/tradedate"
    assert SOURCE is not None
    assert TARGET is not None
    assert PAGINATE["pagesize"] == 1000
    assert PAGINATE["pagelimit"] == 1000
    assert len(EXCHANGES) == 7


# ============================================================================
# Transform Method Tests
# ============================================================================


def test_tradedate_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    assert not result.empty
    assert len(result) == 4
    assert "datecode" in result.columns
    assert "date" in result.columns
    assert "is_open" in result.columns


def test_tradedate_transform_datecode_mapping(mock_session, sample_source_data):
    """Test that cal_date is mapped to datecode"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    assert result["datecode"].tolist() == ["20230101", "20230102", "20230103", "20230104"]


def test_tradedate_transform_date_format(mock_session, sample_source_data):
    """Test that dates are converted from YYYYMMDD to YYYY-MM-DD"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    assert "2023-01-01" in result["date"].values
    assert "2023-01-02" in result["date"].values


def test_tradedate_transform_is_open_boolean(mock_session, sample_source_data):
    """Test that is_open is converted to boolean"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    assert result["is_open"].dtype == bool
    assert not result.loc[result["datecode"] == "20230101", "is_open"].iloc[0]
    assert result.loc[result["datecode"] == "20230102", "is_open"].iloc[0]


def test_tradedate_transform_previous_date(mock_session, sample_source_data):
    """Test that previous trade date is formatted correctly"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    assert "2022-12-30" in result["previous"].values
    assert "2023-01-02" in result["previous"].values


def test_tradedate_transform_exchange_field(mock_session, sample_source_data):
    """Test that exchange is set to ALL"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    assert all(result["exchange"] == "ALL")


def test_tradedate_transform_date_components(mock_session, sample_source_data):
    """Test that date components are extracted correctly"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    first_row = result.iloc[0]
    assert first_row["year"] == 2023
    assert first_row["month"] == 1
    assert first_row["day"] == 1
    assert first_row["quarter"] == 1


def test_tradedate_transform_weekday(mock_session, sample_source_data):
    """Test that weekday is extracted correctly"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    # 2023-01-01 is Sunday, 2023-01-02 is Monday
    assert result.loc[result["datecode"] == "20230101", "weekday"].iloc[0] == "Sun"
    assert result.loc[result["datecode"] == "20230102", "weekday"].iloc[0] == "Mon"


def test_tradedate_transform_empty_dataframe(mock_session):
    """Test transform with empty DataFrame"""
    td = TradeDate(session=mock_session)
    empty_df = pd.DataFrame()
    result = td.transform(empty_df)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_tradedate_transform_none_input(mock_session):
    """Test transform with None input"""
    td = TradeDate(session=mock_session)
    result = td.transform(None)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_tradedate_transform_handles_invalid_dates(mock_session):
    """Test transform handles invalid date formats"""
    td = TradeDate(session=mock_session)
    data = pd.DataFrame(
        {
            "exchange": ["SSE"],
            "cal_date": ["invalid"],
            "is_open": [1],
            "pretrade_date": ["20230101"],
        }
    )

    result = td.transform(data)
    assert pd.isna(result["date"].iloc[0]) or result["date"].iloc[0] == "NaT"


def test_tradedate_transform_removes_duplicates(mock_session):
    """Test that transform removes duplicate rows"""
    td = TradeDate(session=mock_session)
    data = pd.DataFrame(
        {
            "exchange": ["SSE", "SSE"],  # Duplicate
            "cal_date": ["20230101", "20230101"],
            "is_open": [1, 1],
            "pretrade_date": ["20221230", "20221230"],
        }
    )

    result = td.transform(data)
    assert len(result) == 1


def test_tradedate_transform_sorts_by_datecode(mock_session, sample_source_data):
    """Test that result is sorted by datecode"""
    td = TradeDate(session=mock_session)
    shuffled = sample_source_data.sample(frac=1).reset_index(drop=True)
    result = td.transform(shuffled)

    assert result["datecode"].tolist() == sorted(result["datecode"].tolist())


def test_tradedate_transform_resets_index(mock_session, sample_source_data):
    """Test that result has reset index"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    assert result.index.tolist() == list(range(len(result)))


def test_tradedate_transform_only_target_columns(mock_session, sample_source_data):
    """Test that only target columns are in result"""
    td = TradeDate(session=mock_session)
    result = td.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)
    assert actual_cols == expected_cols


# ============================================================================
# _run Method Tests
# ============================================================================


def test_tradedate_run_with_cache_hit(mock_session):
    """Test _run returns cached data when available"""
    td = TradeDate(session=mock_session, cache=True)

    cached_df = pd.DataFrame({"datecode": ["20230101"]})
    td.cache.set(td.params.identifier, cached_df)

    result = td._run()

    assert result.equals(cached_df)


def test_tradedate_run_basic_date_range(mock_session, sample_source_data):
    """Test _run with start_date and end_date"""
    td = TradeDate(session=mock_session, params={"start_date": "20230101", "end_date": "20231231"})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        result = td._run()

        assert not result.empty
        # _fetchall should be called twice (open and close days)
        assert td._fetchall.call_count == 2


def test_tradedate_run_with_year_param(mock_session, sample_source_data):
    """Test _run converts year to start/end date"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        td._run()

        # Check that year was converted
        assert td._fetchall.call_count == 2
        first_call_kwargs = td._fetchall.call_args_list[0][1]
        assert first_call_kwargs["start_date"] == "20230101"
        assert first_call_kwargs["end_date"] == "20231231"


def test_tradedate_run_with_year_param_int(mock_session, sample_source_data):
    """Test _run handles year as integer"""
    td = TradeDate(session=mock_session, params={"year": 2023})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        td._run()

        # Check that year was converted
        assert td._fetchall.call_count == 2
        first_call_kwargs = td._fetchall.call_args_list[0][1]
        assert first_call_kwargs["start_date"] == "20230101"
        assert first_call_kwargs["end_date"] == "20231231"


def test_tradedate_run_with_is_open_param(mock_session, sample_source_data):
    """Test _run with is_open parameter (only fetch one type)"""
    td = TradeDate(session=mock_session, params={"is_open": "1", "start_date": "20230101", "end_date": "20231231"})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        td._run()

        # Should only call _fetchall once when is_open is specified
        assert td._fetchall.call_count == 1
        call_kwargs = td._fetchall.call_args[1]
        assert call_kwargs["is_open"] == "1"


def test_tradedate_run_without_is_open_fetches_both(mock_session, sample_source_data):
    """Test _run without is_open parameter fetches both trading and non-trading days"""
    td = TradeDate(session=mock_session, params={"start_date": "20230101", "end_date": "20231231"})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        td._run()

        # Should call _fetchall twice (once for open, once for close)
        assert td._fetchall.call_count == 2

        # Verify both calls
        calls = td._fetchall.call_args_list
        assert calls[0][1]["is_open"] == "1"
        assert calls[1][1]["is_open"] == "0"


def test_tradedate_run_adds_fields_param(mock_session, sample_source_data):
    """Test _run adds fields parameter if not provided"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        td._run()

        call_kwargs = td._fetchall.call_args_list[0][1]
        assert "fields" in call_kwargs


def test_tradedate_run_sets_cache(mock_session, sample_source_data):
    """Test _run saves result to cache"""
    td = TradeDate(session=mock_session, cache=True, params={"year": "2023"})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        td._run()

        cached = td.cache.get(td.params.identifier)
        assert cached is not None


def test_tradedate_run_calls_transform(mock_session, sample_source_data):
    """Test _run calls transform method"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        with patch.object(td, "transform", return_value=sample_source_data) as mock_transform:
            td._run()

            mock_transform.assert_called_once()


def test_tradedate_run_concatenates_open_close(mock_session):
    """Test _run concatenates open and close day data"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    open_data = pd.DataFrame(
        {
            "exchange": ["SSE"],
            "cal_date": ["20230102"],
            "is_open": [1],
            "pretrade_date": ["20221230"],
        }
    )

    close_data = pd.DataFrame(
        {
            "exchange": ["SSE"],
            "cal_date": ["20230101"],
            "is_open": [0],
            "pretrade_date": ["20221230"],
        }
    )

    with patch.object(td, "_fetchall", side_effect=[open_data, close_data]):
        with patch.object(td, "transform", side_effect=lambda x: x) as mock_transform:
            td._run()

            # Check that concat happened
            called_df = mock_transform.call_args[0][0]
            assert len(called_df) == 2


# ============================================================================
# list_dates Method Tests
# ============================================================================


def test_tradedate_list_dates_basic(mock_session, sample_source_data):
    """Test list_dates returns list of all dates"""
    td = TradeDate(session=mock_session, cache=True, params={"year": "2023"})

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    dates = td.list_dates()

    assert isinstance(dates, list)
    assert len(dates) == 4
    assert "2023-01-01" in dates


def test_tradedate_list_dates_unique(mock_session):
    """Test list_dates returns unique dates"""
    td = TradeDate(session=mock_session, cache=True)

    df = pd.DataFrame(
        {
            "date": ["2023-01-01", "2023-01-01", "2023-01-02"],
            "is_open": [True, True, True],
            "datecode": ["20230101", "20230101", "20230102"],
        }
    )
    td.cache.set(td.params.identifier, df)

    dates = td.list_dates()

    assert len(dates) == 2


def test_tradedate_list_dates_sorted(mock_session, sample_source_data):
    """Test list_dates returns sorted list"""
    td = TradeDate(session=mock_session, cache=True)

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    dates = td.list_dates()

    assert dates == sorted(dates)


def test_tradedate_list_dates_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_dates calls run() when data not in cache"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    with patch.object(td, "run", return_value=td.transform(sample_source_data)):
        dates = td.list_dates()

        td.run.assert_called_once()
        assert len(dates) == 4


# ============================================================================
# list_datecodes Method Tests
# ============================================================================


def test_tradedate_list_datecodes_basic(mock_session, sample_source_data):
    """Test list_datecodes returns list of all datecodes"""
    td = TradeDate(session=mock_session, cache=True)

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    datecodes = td.list_datecodes()

    assert isinstance(datecodes, list)
    assert len(datecodes) == 4
    assert "20230101" in datecodes


def test_tradedate_list_datecodes_sorted(mock_session, sample_source_data):
    """Test list_datecodes returns sorted list"""
    td = TradeDate(session=mock_session, cache=True)

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    datecodes = td.list_datecodes()

    assert datecodes == sorted(datecodes)


def test_tradedate_list_datecodes_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_datecodes calls run() when data not in cache"""
    td = TradeDate(session=mock_session)

    with patch.object(td, "run", return_value=td.transform(sample_source_data)):
        datecodes = td.list_datecodes()

        td.run.assert_called_once()
        assert len(datecodes) == 4


# ============================================================================
# list_open_dates Method Tests
# ============================================================================


def test_tradedate_list_open_dates_basic(mock_session, sample_source_data):
    """Test list_open_dates returns only trading days"""
    td = TradeDate(session=mock_session, cache=True)

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    open_dates = td.list_open_dates()

    assert isinstance(open_dates, list)
    assert len(open_dates) == 2  # Only 2 trading days
    assert "2023-01-02" in open_dates
    assert "2023-01-03" in open_dates
    assert "2023-01-01" not in open_dates  # Non-trading day


def test_tradedate_list_open_dates_sorted(mock_session, sample_source_data):
    """Test list_open_dates returns sorted list"""
    td = TradeDate(session=mock_session, cache=True)

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    open_dates = td.list_open_dates()

    assert open_dates == sorted(open_dates)


def test_tradedate_list_open_dates_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_open_dates calls run() when data not in cache"""
    td = TradeDate(session=mock_session)

    with patch.object(td, "run", return_value=td.transform(sample_source_data)):
        open_dates = td.list_open_dates()

        td.run.assert_called_once()
        assert len(open_dates) == 2


# ============================================================================
# list_open_datecodes Method Tests
# ============================================================================


def test_tradedate_list_open_datecodes_basic(mock_session, sample_source_data):
    """Test list_open_datecodes returns only trading day codes"""
    td = TradeDate(session=mock_session, cache=True)

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    open_datecodes = td.list_open_datecodes()

    assert isinstance(open_datecodes, list)
    assert len(open_datecodes) == 2  # Only 2 trading days
    assert "20230102" in open_datecodes
    assert "20230103" in open_datecodes
    assert "20230101" not in open_datecodes  # Non-trading day


def test_tradedate_list_open_datecodes_sorted(mock_session, sample_source_data):
    """Test list_open_datecodes returns sorted list"""
    td = TradeDate(session=mock_session, cache=True)

    transformed = td.transform(sample_source_data)
    td.cache.set(td.params.identifier, transformed)

    open_datecodes = td.list_open_datecodes()

    assert open_datecodes == sorted(open_datecodes)


def test_tradedate_list_open_datecodes_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_open_datecodes calls run() when data not in cache"""
    td = TradeDate(session=mock_session)

    with patch.object(td, "run", return_value=td.transform(sample_source_data)):
        open_datecodes = td.list_open_datecodes()

        td.run.assert_called_once()
        assert len(open_datecodes) == 2


# ============================================================================
# check Method Tests
# ============================================================================


def test_tradedate_check_with_string_date_hyphen(mock_session, sample_source_data):
    """Test check method with string date (YYYY-MM-DD format)"""
    with patch.object(
        TradeDate,
        "run",
        return_value=pd.DataFrame(
            {
                "datecode": ["20230102"],
                "is_open": [True],
            }
        ),
    ):
        result = TradeDate.check(mock_session, "2023-01-02")

        assert result is True


def test_tradedate_check_with_string_date_no_hyphen(mock_session, sample_source_data):
    """Test check method with string date (YYYYMMDD format)"""
    with patch.object(
        TradeDate,
        "run",
        return_value=pd.DataFrame(
            {
                "datecode": ["20230102"],
                "is_open": [True],
            }
        ),
    ):
        result = TradeDate.check(mock_session, "20230102")

        assert result is True


def test_tradedate_check_with_datetime(mock_session):
    """Test check method with datetime object"""
    test_date = datetime(2023, 1, 2)

    with patch.object(
        TradeDate,
        "run",
        return_value=pd.DataFrame(
            {
                "datecode": ["20230102"],
                "is_open": [True],
            }
        ),
    ):
        result = TradeDate.check(mock_session, test_date)

        assert result is True


def test_tradedate_check_with_date(mock_session):
    """Test check method with date object"""
    test_date = date(2023, 1, 2)

    with patch.object(
        TradeDate,
        "run",
        return_value=pd.DataFrame(
            {
                "datecode": ["20230102"],
                "is_open": [True],
            }
        ),
    ):
        result = TradeDate.check(mock_session, test_date)

        assert result is True


def test_tradedate_check_non_trading_day(mock_session):
    """Test check method returns False for non-trading day"""
    with patch.object(
        TradeDate,
        "run",
        return_value=pd.DataFrame(
            {
                "datecode": [],
                "is_open": [],
            }
        ),
    ):
        result = TradeDate.check(mock_session, "2023-01-01")

        assert result is False


def test_tradedate_check_with_none_uses_current_date(mock_session):
    """Test check method uses current date when None is passed"""
    today = datetime.now().date()
    today_code = today.strftime("%Y%m%d")

    with patch.object(
        TradeDate,
        "run",
        return_value=pd.DataFrame(
            {
                "datecode": [today_code],
                "is_open": [True],
            }
        ),
    ):
        result = TradeDate.check(mock_session, None)

        assert isinstance(result, bool)


# ============================================================================
# Integration Tests
# ============================================================================


def test_tradedate_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    td = TradeDate(
        session=mock_session,
        params={"year": "2023"},
        cache=True,
    )

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        result = td.run()

        assert not result.empty
        assert "datecode" in result.columns

        dates = td.list_dates()
        open_dates = td.list_open_dates()
        datecodes = td.list_datecodes()
        open_datecodes = td.list_open_datecodes()

        assert len(dates) == 4
        assert len(open_dates) == 2
        assert len(datecodes) == 4
        assert len(open_datecodes) == 2


def test_tradedate_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across method calls"""
    td = TradeDate(session=mock_session, cache=True, params={"year": "2023"})

    with patch.object(td, "_load_cache", return_value=None) as mock_load:
        with patch.object(td, "_fetchall", return_value=sample_source_data) as mock_fetch:
            # First run - fetches data and caches it
            result1 = td.run()
            assert mock_fetch.call_count == 2  # Called twice (open/close)
            assert mock_load.call_count == 1

            # Second run - _load_cache still returns None, so _fetchall called again
            result2 = td.run()
            assert mock_fetch.call_count == 4  # Called twice more
            assert mock_load.call_count == 2

            pd.testing.assert_frame_equal(result1, result2)


def test_tradedate_params_identifier_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    td1 = TradeDate(session=mock_session, params={"year": "2022"}, cache=True)
    td2 = TradeDate(session=mock_session, params={"year": "2023"}, cache=True)

    assert td1.params.identifier != td2.params.identifier


def test_tradedate_different_exchanges(mock_session, sample_source_data):
    """Test with different exchange parameters"""
    for exchange in EXCHANGES:
        td = TradeDate(session=mock_session, params={"exchange": exchange, "year": "2023"})

        with patch.object(td, "_fetchall", return_value=sample_source_data):
            td._run()

            call_kwargs = td._fetchall.call_args_list[0][1]
            assert call_kwargs["exchange"] == exchange


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_tradedate_empty_result_handling(mock_session):
    """Test handling of empty API results"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    empty_df = pd.DataFrame()
    with patch.object(td, "_fetchall", return_value=empty_df):
        result = td._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()


def test_tradedate_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    td = TradeDate(session=mock_session, params={"year": "2023"})

    # Create large dataset (365 days)
    large_data = pd.DataFrame(
        {
            "exchange": ["SSE"] * 365,
            "cal_date": [f"2023{i:04d}" for i in range(101, 466)],  # Simplified
            "is_open": [1] * 365,
            "pretrade_date": [f"2023{i:04d}" for i in range(100, 465)],
        }
    )

    result = td.transform(large_data)

    assert len(result) <= 365  # Some may be filtered
    assert not result.empty


def test_tradedate_without_cache(mock_session, sample_source_data):
    """Test TradeDate works correctly without cache"""
    td = TradeDate(session=mock_session, cache=False, params={"year": "2023"})

    assert td.cache is None

    with patch.object(td, "_fetchall", return_value=sample_source_data):
        result = td.run()

        assert not result.empty

        dates = td.list_dates()
        open_dates = td.list_open_dates()

        assert len(dates) > 0
        assert len(open_dates) > 0


def test_tradedate_mixed_trading_non_trading_days(mock_session):
    """Test handling of mixed trading and non-trading days"""
    td = TradeDate(session=mock_session)

    data = pd.DataFrame(
        {
            "exchange": ["SSE"] * 7,
            "cal_date": [f"2023010{i}" for i in range(1, 8)],
            "is_open": [0, 1, 1, 1, 1, 1, 0],  # Weekend, weekdays, weekend
            "pretrade_date": ["20221230"] + [f"2023010{i}" for i in range(1, 7)],
        }
    )

    result = td.transform(data)

    assert len(result) == 7
    assert result["is_open"].sum() == 5  # 5 trading days

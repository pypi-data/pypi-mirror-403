from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.params import Params
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.companyprofit.companyprofit import CompanyProfit
from xfintech.data.source.tushare.stock.companyprofit.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)

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
    mock_connection.income_vip = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ", "000001.SZ"],
            "ann_date": ["20200425", "20200826", "20201030"],
            "f_ann_date": ["20200425", "20200826", "20201030"],
            "end_date": ["20200331", "20200630", "20200930"],
            "report_type": ["1", "1", "1"],
            "comp_type": ["1", "1", "1"],
            "end_type": ["12", "12", "12"],
            "update_flag": ["0", "0", "0"],
            "basic_eps": [0.5, 1.2, 1.8],
            "diluted_eps": [0.5, 1.2, 1.8],
            "total_revenue": [100000000.0, 250000000.0, 380000000.0],
            "revenue": [98000000.0, 245000000.0, 372000000.0],
            "n_income": [12000000.0, 32000000.0, 48000000.0],
            "n_income_attr_p": [11500000.0, 31000000.0, 46000000.0],
            "total_profit": [15000000.0, 39000000.0, 58000000.0],
            "income_tax": [3000000.0, 7000000.0, 10000000.0],
        }
    )


@pytest.fixture
def expected_transformed_data():
    """Create expected transformed data"""
    return pd.DataFrame(
        {
            "code": ["000001.SZ", "000001.SZ", "000001.SZ"],
            "date": ["2020-03-31", "2020-06-30", "2020-09-30"],
            "datecode": ["20200331", "20200630", "20200930"],
            "ann_date": ["2020-04-25", "2020-08-26", "2020-10-30"],
            "f_ann_date": ["2020-04-25", "2020-08-26", "2020-10-30"],
            "end_date": ["2020-03-31", "2020-06-30", "2020-09-30"],
            "report_type": ["1", "1", "1"],
            "comp_type": ["1", "1", "1"],
            "end_type": ["12", "12", "12"],
            "update_flag": ["0", "0", "0"],
            "basic_eps": [0.5, 1.2, 1.8],
            "diluted_eps": [0.5, 1.2, 1.8],
            "total_revenue": [100000000.0, 250000000.0, 380000000.0],
            "revenue": [98000000.0, 245000000.0, 372000000.0],
            "n_income": [12000000.0, 32000000.0, 48000000.0],
            "n_income_attr_p": [11500000.0, 31000000.0, 46000000.0],
            "total_profit": [15000000.0, 39000000.0, 58000000.0],
            "income_tax": [3000000.0, 7000000.0, 10000000.0],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_companyprofit_init_basic(mock_session):
    """Test basic initialization with required session"""
    profit = CompanyProfit(session=mock_session)
    assert profit.name == NAME
    assert profit.key == KEY
    assert profit.source == SOURCE
    assert profit.target == TARGET
    assert profit.paginate.pagesize == PAGINATE["pagesize"]
    assert profit.paginate.pagelimit == PAGINATE["pagelimit"]


def test_companyprofit_init_with_params_dict(mock_session):
    """Test initialization with params as dict"""
    params = {"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"}
    profit = CompanyProfit(session=mock_session, params=params)
    assert profit.params.get("ts_code") == "000001.SZ"
    assert profit.params.get("start_date") == "20200101"
    assert profit.params.get("end_date") == "20201231"


def test_companyprofit_init_with_params_object(mock_session):
    """Test initialization with params as Params object"""
    params = Params(ts_code="000001.SZ", start_date="20200101")
    profit = CompanyProfit(session=mock_session, params=params)
    assert profit.params.get("ts_code") == "000001.SZ"


def test_companyprofit_init_with_year_param(mock_session):
    """Test initialization with year parameter"""
    params = {"ts_code": "000001.SZ", "year": "2020"}
    profit = CompanyProfit(session=mock_session, params=params)
    assert profit.params.get("year") == "2020"


def test_companyprofit_init_with_cache_bool_true(mock_session):
    """Test initialization with cache as boolean True"""
    profit = CompanyProfit(session=mock_session, cache=True)
    assert profit.cache is not None
    assert isinstance(profit.cache, Cache)


def test_companyprofit_init_with_cache_bool_false(mock_session):
    """Test initialization with cache as boolean False"""
    profit = CompanyProfit(session=mock_session, cache=False)
    assert profit.cache is None


def test_companyprofit_init_with_cache_dict(mock_session):
    """Test initialization with cache as dict"""
    cache_config = {"dir": "/tmp/test_cache", "ttl": 3600}
    profit = CompanyProfit(session=mock_session, cache=cache_config)
    assert profit.cache is not None
    assert isinstance(profit.cache, Cache)


def test_companyprofit_init_default_paginate_limit(mock_session):
    """Test that default paginate settings are correctly set"""
    profit = CompanyProfit(session=mock_session)
    assert profit.paginate.pagesize == 1000
    assert profit.paginate.pagelimit == 1000


def test_companyprofit_init_with_all_params(mock_session):
    """Test initialization with all parameters"""
    params = {"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"}
    coolant = {"interval": 0.5}
    retry = {"max_attempts": 3}
    cache = True

    profit = CompanyProfit(session=mock_session, params=params, coolant=coolant, retry=retry, cache=cache)
    assert profit.params.get("ts_code") == "000001.SZ"
    assert profit.cache is not None


# ============================================================================
# Transform Tests
# ============================================================================


def test_companyprofit_transform_basic(mock_session, sample_source_data):
    """Test basic transformation of source data"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(sample_source_data)

    assert not result.empty
    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "datecode" in result.columns


def test_companyprofit_transform_code_mapping(mock_session, sample_source_data):
    """Test that ts_code is correctly mapped to code"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(sample_source_data)

    assert all(result["code"] == ["000001.SZ", "000001.SZ", "000001.SZ"])


def test_companyprofit_transform_date_format(mock_session, sample_source_data):
    """Test that dates are formatted correctly (YYYY-MM-DD)"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(sample_source_data)

    # Check date format
    assert result["date"].iloc[0] == "2020-03-31"
    assert result["ann_date"].iloc[0] == "2020-04-25"
    assert result["f_ann_date"].iloc[0] == "2020-04-25"
    assert result["end_date"].iloc[0] == "2020-03-31"


def test_companyprofit_transform_datecode_preserved(mock_session, sample_source_data):
    """Test that datecode is preserved in YYYYMMDD format"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(sample_source_data)

    assert result["datecode"].iloc[0] == "20200331"
    assert result["datecode"].iloc[1] == "20200630"
    assert result["datecode"].iloc[2] == "20200930"


def test_companyprofit_transform_numeric_conversions(mock_session, sample_source_data):
    """Test that numeric fields are properly converted"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(sample_source_data)

    # Check numeric fields
    assert result["basic_eps"].dtype == "float64"
    assert result["diluted_eps"].dtype == "float64"
    assert result["total_revenue"].dtype == "float64"
    assert result["n_income"].dtype == "float64"


def test_companyprofit_transform_string_fields(mock_session, sample_source_data):
    """Test that string fields are properly converted"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(sample_source_data)

    assert result["report_type"].dtype == "object"
    assert result["comp_type"].dtype == "object"
    assert result["end_type"].dtype == "object"
    assert result["update_flag"].dtype == "object"


def test_companyprofit_transform_empty_dataframe(mock_session):
    """Test transform with empty DataFrame"""
    profit = CompanyProfit(session=mock_session)
    empty_df = pd.DataFrame()
    result = profit.transform(empty_df)

    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_companyprofit_transform_none_input(mock_session):
    """Test transform with None input"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(None)

    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_companyprofit_transform_handles_invalid_dates(mock_session):
    """Test transform handles invalid dates gracefully"""
    profit = CompanyProfit(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["invalid"],
            "ann_date": ["20200101"],
            "f_ann_date": ["20200101"],
            "report_type": ["1"],
            "comp_type": ["1"],
            "end_type": ["12"],
            "update_flag": ["0"],
        }
    )
    result = profit.transform(data)

    assert not result.empty
    assert pd.isna(result["date"].iloc[0]) or result["date"].iloc[0] == "NaT"


def test_companyprofit_transform_removes_duplicates(mock_session):
    """Test that duplicates are removed"""
    profit = CompanyProfit(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ"],
            "end_date": ["20200331", "20200331"],
            "ann_date": ["20200425", "20200425"],
            "f_ann_date": ["20200425", "20200425"],
            "report_type": ["1", "1"],
            "comp_type": ["1", "1"],
            "end_type": ["12", "12"],
            "update_flag": ["0", "0"],
            "basic_eps": [0.5, 0.5],
        }
    )
    result = profit.transform(data)

    assert len(result) == 1


def test_companyprofit_transform_sorts_by_code_and_date(mock_session):
    """Test that output is sorted by code and date"""
    profit = CompanyProfit(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000002.SZ", "000001.SZ", "000001.SZ"],
            "end_date": ["20200331", "20200630", "20200331"],
            "ann_date": ["20200425", "20200826", "20200425"],
            "f_ann_date": ["20200425", "20200826", "20200425"],
            "report_type": ["1", "1", "1"],
            "comp_type": ["1", "1", "1"],
            "end_type": ["12", "12", "12"],
            "update_flag": ["0", "0", "0"],
        }
    )
    result = profit.transform(data)

    assert result["code"].iloc[0] == "000001.SZ"
    assert result["code"].iloc[1] == "000001.SZ"
    assert result["code"].iloc[2] == "000002.SZ"
    assert result["date"].iloc[0] == "2020-03-31"
    assert result["date"].iloc[1] == "2020-06-30"


def test_companyprofit_transform_resets_index(mock_session, sample_source_data):
    """Test that index is reset after transformation"""
    profit = CompanyProfit(session=mock_session)
    result = profit.transform(sample_source_data)

    assert list(result.index) == [0, 1, 2]


def test_companyprofit_transform_only_target_columns(mock_session, sample_source_data):
    """Test that only target columns are returned"""
    profit = CompanyProfit(session=mock_session)

    # Add extra column to source data
    data_with_extra = sample_source_data.copy()
    data_with_extra["extra_column"] = "test"

    result = profit.transform(data_with_extra)

    assert "extra_column" not in result.columns
    assert "ts_code" not in result.columns  # Should be renamed to "code"
    assert "code" in result.columns


# ============================================================================
# Run Tests
# ============================================================================


def test_companyprofit_run_with_cache_hit(mock_session, sample_source_data):
    """Test run with cache hit (no API call)"""
    profit = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ"},
        cache=True,
    )

    # Mock cache load to return data
    with patch.object(profit, "_load_cache", return_value=sample_source_data):
        result = profit.run()

        assert not result.empty
        mock_session.connection.income_vip.assert_not_called()


def test_companyprofit_run_basic_date_range(mock_session, sample_source_data):
    """Test run with start_date and end_date"""
    profit = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"},
    )

    with patch.object(profit, "_fetchall", return_value=sample_source_data):
        with patch.object(profit, "_save_cache"):
            result = profit.run()

            assert not result.empty
            assert "code" in result.columns


def test_companyprofit_run_with_year_param(mock_session, sample_source_data):
    """Test that year parameter is converted to start_date and end_date"""
    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ", "year": "2020"})

    with patch.object(profit, "_fetchall", return_value=sample_source_data) as mock_fetch:
        with patch.object(profit, "_save_cache"):
            profit.run()

            # Verify that year was converted to date range
            call_kwargs = mock_fetch.call_args[1]
            assert call_kwargs["start_date"] == "20200101"
            assert call_kwargs["end_date"] == "20201231"


def test_companyprofit_run_with_year_param_int(mock_session, sample_source_data):
    """Test year parameter as integer"""
    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ", "year": 2020})

    with patch.object(profit, "_fetchall", return_value=sample_source_data) as mock_fetch:
        with patch.object(profit, "_save_cache"):
            profit.run()

            call_kwargs = mock_fetch.call_args[1]
            assert call_kwargs["start_date"] == "20200101"
            assert call_kwargs["end_date"] == "20201231"


def test_companyprofit_run_with_datetime_params(mock_session, sample_source_data):
    """Test run with datetime objects as parameters"""
    profit = CompanyProfit(
        session=mock_session,
        params={
            "ts_code": "000001.SZ",
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2020, 12, 31),
        },
    )

    with patch.object(profit, "_fetchall", return_value=sample_source_data) as mock_fetch:
        with patch.object(profit, "_save_cache"):
            profit.run()

            call_kwargs = mock_fetch.call_args[1]
            assert call_kwargs["start_date"] == "20200101"
            assert call_kwargs["end_date"] == "20201231"


def test_companyprofit_run_adds_fields_param(mock_session, sample_source_data):
    """Test that fields parameter is automatically added"""
    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ"})

    with patch.object(profit, "_fetchall", return_value=sample_source_data) as mock_fetch:
        with patch.object(profit, "_save_cache"):
            profit.run()

            call_kwargs = mock_fetch.call_args[1]
            assert "fields" in call_kwargs
            assert isinstance(call_kwargs["fields"], str)
            assert "ts_code" in call_kwargs["fields"]


def test_companyprofit_run_sets_cache(mock_session, sample_source_data):
    """Test that result is saved to cache"""
    profit = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ"},
        cache=True,
    )

    with patch.object(profit, "_fetchall", return_value=sample_source_data):
        with patch.object(profit, "_save_cache") as mock_save:
            profit.run()

            mock_save.assert_called_once()


def test_companyprofit_run_calls_transform(mock_session, sample_source_data):
    """Test that run calls transform method"""
    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ"})

    with patch.object(profit, "_fetchall", return_value=sample_source_data):
        with patch.object(profit, "transform", return_value=pd.DataFrame()) as mock_transform:
            with patch.object(profit, "_save_cache"):
                profit.run()

                mock_transform.assert_called_once()


def test_companyprofit_run_uses_income_vip_api(mock_session, sample_source_data):
    """Test that run method uses the correct API endpoint"""
    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ"})

    with patch.object(profit, "_fetchall", return_value=sample_source_data) as mock_fetch:
        with patch.object(profit, "_save_cache"):
            profit.run()

            # Verify the correct API method is used
            assert mock_fetch.call_args[1]["api"] == mock_session.connection.income_vip


# ============================================================================
# Integration Tests
# ============================================================================


def test_companyprofit_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to result"""
    profit = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"},
        cache=True,
    )

    with patch.object(profit, "_fetchall", return_value=sample_source_data):
        with patch.object(profit, "_save_cache"):
            result = profit.run()

            assert not result.empty
            assert "code" in result.columns
            assert "date" in result.columns
            assert "datecode" in result.columns
            assert all(result["code"] == "000001.SZ")


def test_companyprofit_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across runs"""
    profit = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ"},
        cache=True,
    )

    # First run - should fetch data
    with patch.object(profit, "_fetchall", return_value=sample_source_data) as mock_fetch:
        with patch.object(profit, "_load_cache", return_value=None):
            with patch.object(profit, "_save_cache"):
                first_result = profit.run()
                assert mock_fetch.called

    # Second run - should use cache
    with patch.object(profit, "_fetchall", return_value=sample_source_data) as mock_fetch:
        with patch.object(profit, "_load_cache", return_value=first_result):
            profit.run()
            assert not mock_fetch.called


def test_companyprofit_params_identifier_uniqueness(mock_session):
    """Test that different params create different cache identifiers"""
    profit1 = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20200101"},
        cache=True,
    )
    profit2 = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ", "start_date": "20210101"},
        cache=True,
    )

    # Test that different params are properly stored
    assert profit1.params.get("start_date") == "20200101"
    assert profit2.params.get("start_date") == "20210101"
    assert profit1.params.get("start_date") != profit2.params.get("start_date")


def test_companyprofit_different_stocks(mock_session, sample_source_data):
    """Test that different stock codes are handled correctly"""
    profit1 = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ"})
    profit2 = CompanyProfit(session=mock_session, params={"ts_code": "000002.SZ"})

    assert profit1.params.get("ts_code") != profit2.params.get("ts_code")


def test_companyprofit_empty_result_handling(mock_session):
    """Test handling of empty result from API"""
    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ"})

    with patch.object(profit, "_fetchall", return_value=pd.DataFrame()):
        with patch.object(profit, "_save_cache"):
            result = profit.run()

            assert result.empty
            assert len(result.columns) == len(TARGET.list_column_names())


def test_companyprofit_large_dataset_handling(mock_session):
    """Test handling of large dataset"""
    large_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"] * 1000,
            "end_date": ["20200331"] * 1000,
            "ann_date": ["20200425"] * 1000,
            "f_ann_date": ["20200425"] * 1000,
            "report_type": ["1"] * 1000,
            "comp_type": ["1"] * 1000,
            "end_type": ["12"] * 1000,
            "update_flag": ["0"] * 1000,
            "basic_eps": [0.5] * 1000,
        }
    )

    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ"})

    with patch.object(profit, "_fetchall", return_value=large_data):
        with patch.object(profit, "_save_cache"):
            result = profit.run()

            # After deduplication, should have only 1 row
            assert len(result) == 1


def test_companyprofit_without_cache(mock_session, sample_source_data):
    """Test that data fetching works without cache"""
    profit = CompanyProfit(
        session=mock_session,
        params={"ts_code": "000001.SZ"},
        cache=False,
    )

    with patch.object(profit, "_fetchall", return_value=sample_source_data):
        result = profit.run()

        assert not result.empty
        assert profit.cache is None


def test_companyprofit_handles_missing_numeric_fields(mock_session):
    """Test handling of missing numeric values"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["20200331"],
            "ann_date": ["20200425"],
            "f_ann_date": ["20200425"],
            "report_type": ["1"],
            "comp_type": ["1"],
            "end_type": ["12"],
            "update_flag": ["0"],
            "basic_eps": [None],
            "n_income": [None],
        }
    )

    profit = CompanyProfit(session=mock_session, params={"ts_code": "000001.SZ"})
    result = profit.transform(data)

    assert not result.empty
    assert pd.isna(result["basic_eps"].iloc[0])
    assert pd.isna(result["n_income"].iloc[0])

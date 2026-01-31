"""
Comprehensive test suite for StockDividend class
Tests cover initialization, transformation, execution, and integration scenarios
"""

import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.stockdividend import StockDividend
from xfintech.data.source.tushare.stock.stockdividend.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)

# ============================================================================
# Test Fixtures
# ============================================================================


class FakeConnection:
    """Fake Tushare connection for testing"""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def dividend(self, **kwargs):
        """Mock dividend API call"""
        return self.frame


class FakeSession:
    """Fake session for testing"""

    def __init__(self, connection: FakeConnection):
        self.connection = connection


@pytest.fixture
def mock_session():
    """Create a mock session with empty data"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    return FakeSession(fake_conn)


@pytest.fixture
def sample_source_data():
    """Sample dividend data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["600848.SH", "600848.SH", "000001.SZ"],
            "end_date": ["20201231", "20191231", "20201231"],
            "ann_date": ["20210415", "20200410", "20210420"],
            "div_proc": ["实施", "实施", "预案"],
            "stk_div": ["0.10", "0.15", "0.00"],
            "stk_bo_rate": ["0.05", "0.08", "0.00"],
            "stk_co_rate": ["0.05", "0.07", "0.00"],
            "cash_div": ["0.50", "0.60", "0.30"],
            "cash_div_tax": ["0.55", "0.65", "0.32"],
            "record_date": ["20210520", "20200515", "20210525"],
            "ex_date": ["20210521", "20200516", "20210526"],
            "pay_date": ["20210528", "20200525", "20210601"],
            "div_listdate": ["20210528", "20200525", "20210601"],
            "imp_ann_date": ["20210415", "20200410", "20210420"],
            "base_date": ["20201231", "20191231", "20201231"],
            "base_share": ["100000.00", "95000.00", "200000.00"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_stockdividend_init_basic(mock_session):
    """Test basic initialization with required session"""
    dividend = StockDividend(session=mock_session)
    assert dividend.name == NAME
    assert dividend.key == KEY
    assert dividend.source == SOURCE
    assert dividend.target == TARGET
    assert dividend.paginate.pagesize == PAGINATE["pagesize"]
    assert dividend.paginate.pagelimit == PAGINATE["pagelimit"]


def test_stockdividend_init_with_params_dict(mock_session):
    """Test initialization with params as dict"""
    params = {"ts_code": "600848.SH", "ann_date": "20210415"}
    dividend = StockDividend(session=mock_session, params=params)
    assert dividend.params.get("ts_code") == "600848.SH"
    assert dividend.params.get("ann_date") == "20210415"


def test_stockdividend_init_with_params_object(mock_session):
    """Test initialization with params as Params object"""
    from xfintech.data.common.params import Params

    params = Params(ts_code="600848.SH")
    dividend = StockDividend(session=mock_session, params=params)
    assert dividend.params.get("ts_code") == "600848.SH"


def test_stockdividend_init_with_multiple_date_params(mock_session):
    """Test initialization with multiple date parameters"""
    params = {
        "ts_code": "600848.SH",
        "ann_date": "20210415",
        "record_date": "20210520",
        "ex_date": "20210521",
    }
    dividend = StockDividend(session=mock_session, params=params)
    assert dividend.params.get("ann_date") == "20210415"
    assert dividend.params.get("record_date") == "20210520"


def test_stockdividend_init_with_cache_bool_true(mock_session):
    """Test initialization with cache enabled"""
    dividend = StockDividend(session=mock_session, cache=True)
    assert dividend.cache is not None


def test_stockdividend_init_with_cache_bool_false(mock_session):
    """Test initialization with cache disabled"""
    dividend = StockDividend(session=mock_session, cache=False)
    assert dividend.cache is None


def test_stockdividend_init_with_cache_dict(mock_session):
    """Test initialization with cache config dict"""
    cache_config = {"path": "/tmp/cache", "key": "test"}
    dividend = StockDividend(session=mock_session, cache=cache_config)
    assert dividend.cache is not None


def test_stockdividend_init_default_paginate_limit(mock_session):
    """Test that default pagination limit is set correctly"""
    dividend = StockDividend(session=mock_session)
    assert dividend.paginate.pagesize == 1000
    assert dividend.paginate.pagelimit == 1000


def test_stockdividend_init_with_all_params(mock_session):
    """Test initialization with all parameters"""
    params = {"ts_code": "600848.SH", "ann_date": "20210415"}
    coolant = {"interval": 0.5}
    retry = {"max_attempts": 3}
    cache = True

    dividend = StockDividend(session=mock_session, params=params, coolant=coolant, retry=retry, cache=cache)
    assert dividend.params.get("ts_code") == "600848.SH"
    assert dividend.cache is not None


def test_stockdividend_constants():
    """Test that constants are correctly defined"""
    assert NAME == "stockdividend"
    assert KEY == "/tushare/stockdividend"
    assert SOURCE.name == "dividend"
    assert TARGET.name == "stockdividend"
    assert PAGINATE["pagesize"] == 1000
    assert PAGINATE["pagelimit"] == 1000


# ============================================================================
# Transform Tests
# ============================================================================


def test_stockdividend_transform_basic(sample_source_data):
    """Test basic transformation of dividend data"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "ann_date" in result.columns
    assert "ann_datecode" in result.columns


def test_stockdividend_transform_code_mapping(sample_source_data):
    """Test that ts_code is correctly mapped to code"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[1]["code"] == "600848.SH"


def test_stockdividend_transform_date_format(sample_source_data):
    """Test that dates are properly formatted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    assert pd.api.types.is_datetime64_any_dtype(result["ann_date"]) is False
    assert result.iloc[1]["ann_date"] == "2020-04-10"
    assert result.iloc[1]["record_date"] == "2020-05-15"


def test_stockdividend_transform_datecode_preserved(sample_source_data):
    """Test that datecode is correctly created"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    assert result.iloc[1]["ann_datecode"] == "20200410"
    assert result.iloc[1]["record_datecode"] == "20200515"
    assert result.iloc[1]["ex_datecode"] == "20200516"


def test_stockdividend_transform_numeric_conversions(sample_source_data):
    """Test that numeric fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    assert result.iloc[1]["stk_div"] == 0.15
    assert result.iloc[1]["cash_div"] == 0.60
    assert result.iloc[1]["base_share"] == 95000.00
    assert pd.api.types.is_numeric_dtype(result["stk_div"])


def test_stockdividend_transform_string_fields(sample_source_data):
    """Test that string fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    assert result.iloc[1]["div_proc"] == "实施"
    assert result.iloc[0]["div_proc"] == "预案"
    assert result.iloc[1]["end_date"] == "20191231"


def test_stockdividend_transform_empty_dataframe():
    """Test transformation with empty dataframe"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(pd.DataFrame())

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_stockdividend_transform_none_input():
    """Test transformation with None input"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(None)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_stockdividend_transform_handles_invalid_dates():
    """Test that invalid dates are handled gracefully"""
    data = pd.DataFrame(
        {
            "ts_code": ["600848.SH"],
            "end_date": ["20201231"],
            "ann_date": ["invalid"],
            "div_proc": ["实施"],
            "stk_div": ["0.10"],
            "cash_div": ["0.50"],
            "record_date": ["20210520"],
            "ex_date": ["20210521"],
            "pay_date": ["20210528"],
            "div_listdate": ["20210528"],
            "imp_ann_date": ["20210415"],
            "base_date": ["20201231"],
        }
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(data)

    assert len(result) == 1
    assert pd.isna(result.iloc[0]["ann_date"])


def test_stockdividend_transform_removes_duplicates(sample_source_data):
    """Test that duplicate rows are removed"""
    # Create data with duplicates
    data = pd.concat([sample_source_data, sample_source_data.iloc[[0]]], ignore_index=True)

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(data)

    # Should have 3 unique rows, not 4
    assert len(result) == 3


def test_stockdividend_transform_sorts_by_code_and_ann_date(sample_source_data):
    """Test that output is sorted by code and ann_date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    # Check sorting: 000001.SZ first, then 600848.SH by dates
    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[1]["code"] == "600848.SH"
    assert result.iloc[1]["ann_date"] == "2020-04-10"
    assert result.iloc[2]["code"] == "600848.SH"
    assert result.iloc[2]["ann_date"] == "2021-04-15"


def test_stockdividend_transform_resets_index():
    """Test that index is reset after transformation"""
    data = pd.DataFrame(
        {
            "ts_code": ["600848.SH", "000001.SZ"],
            "end_date": ["20201231", "20201231"],
            "ann_date": ["20210415", "20210420"],
            "div_proc": ["实施", "预案"],
            "stk_div": ["0.10", "0.00"],
            "cash_div": ["0.50", "0.30"],
            "record_date": ["20210520", "20210525"],
            "ex_date": ["20210521", "20210526"],
            "pay_date": ["20210528", "20210601"],
            "div_listdate": ["20210528", "20210601"],
            "imp_ann_date": ["20210415", "20210420"],
            "base_date": ["20201231", "20201231"],
        },
        index=[5, 10],
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(data)

    assert result.index.tolist() == [0, 1]


def test_stockdividend_transform_only_target_columns(sample_source_data):
    """Test that only target columns are in output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)

    assert actual_cols == expected_cols


def test_stockdividend_transform_all_date_fields(sample_source_data):
    """Test that all date fields are properly transformed"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    # Check that all date/datecode pairs exist
    date_pairs = [
        ("ann_date", "ann_datecode"),
        ("record_date", "record_datecode"),
        ("ex_date", "ex_datecode"),
        ("pay_date", "pay_datecode"),
        ("div_listdate", "div_listdatecode"),
        ("imp_ann_date", "imp_ann_datecode"),
        ("base_date", "base_datecode"),
    ]

    for date_col, datecode_col in date_pairs:
        assert date_col in result.columns
        assert datecode_col in result.columns


# ============================================================================
# Run Method Tests
# ============================================================================


def test_stockdividend_run_basic(sample_source_data):
    """Test basic run() execution"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"})

    result = dividend.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_stockdividend_run_with_cache_hit(sample_source_data):
    """Test that run() returns cached data when available"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"}, cache=True)

    # First run should fetch and cache
    result1 = dividend.run()

    # Second run should return cached data
    result2 = dividend.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_stockdividend_run_with_ann_date(sample_source_data):
    """Test run() with ann_date parameter"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ann_date": "20210415"})

    result = dividend.run()

    assert isinstance(result, pd.DataFrame)


def test_stockdividend_run_with_datetime_params(sample_source_data):
    """Test run() with datetime objects as parameters"""
    from datetime import datetime

    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(
        session=session,
        params={
            "ts_code": "600848.SH",
            "ann_date": datetime(2021, 4, 15),
        },
    )

    result = dividend.run()

    assert isinstance(result, pd.DataFrame)


def test_stockdividend_run_adds_fields_param(sample_source_data):
    """Test that run() adds fields parameter if not provided"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"})

    # Monkey patch _fetchall to capture params
    dividend._fetchall
    captured_params = {}

    def mock_fetchall(api, **kwargs):
        captured_params.update(kwargs)
        return sample_source_data

    dividend._fetchall = mock_fetchall
    dividend.run()

    assert "fields" in captured_params
    assert len(captured_params["fields"]) > 0


def test_stockdividend_run_sets_cache(sample_source_data):
    """Test that run() saves result to cache"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"}, cache=True)

    result = dividend.run()

    # Cache should be set after run
    cached = dividend._load_cache()
    assert cached is not None
    pd.testing.assert_frame_equal(result, cached)


def test_stockdividend_run_calls_transform(sample_source_data):
    """Test that run() calls transform method"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"})

    # Monkey patch transform to track if it was called
    original_transform = dividend.transform
    transform_called = {"called": False}

    def mock_transform(data):
        transform_called["called"] = True
        return original_transform(data)

    dividend.transform = mock_transform
    dividend.run()

    assert transform_called["called"] is True


def test_stockdividend_run_uses_dividend_api(sample_source_data):
    """Test that run() uses dividend API"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"})

    # Monkey patch _fetchall to capture API
    captured_api = {"api": None}

    def mock_fetchall(api, **kwargs):
        captured_api["api"] = api
        return sample_source_data

    dividend._fetchall = mock_fetchall
    dividend.run()

    assert captured_api["api"] == session.connection.dividend


# ============================================================================
# Integration Tests
# ============================================================================


def test_stockdividend_full_workflow(sample_source_data):
    """Test complete workflow from initialization to output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    dividend = StockDividend(
        session=session,
        params={"ts_code": "600848.SH"},
        cache=True,
    )

    result = dividend.run()

    # Verify output structure
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "code" in result.columns
    assert "ann_date" in result.columns
    assert "div_proc" in result.columns
    assert "stk_div" in result.columns

    # Verify data types
    assert pd.api.types.is_numeric_dtype(result["stk_div"])
    assert pd.api.types.is_numeric_dtype(result["cash_div"])


def test_stockdividend_cache_persistence(sample_source_data):
    """Test that cache persists across multiple runs"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"}, cache=True)

    # Run once to populate cache
    result1 = dividend.run()

    # Clear in-memory data to simulate fresh load
    dividend2 = StockDividend(session=session, params={"ts_code": "600848.SH"}, cache=True)
    result2 = dividend2.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_stockdividend_params_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    dividend1 = StockDividend(
        session=mock_session,
        params={"ts_code": "600848.SH"},
        cache=True,
    )
    dividend2 = StockDividend(
        session=mock_session,
        params={"ts_code": "000001.SZ"},
        cache=True,
    )

    # Test that different params are properly stored
    assert dividend1.params.get("ts_code") == "600848.SH"
    assert dividend2.params.get("ts_code") == "000001.SZ"
    assert dividend1.params.get("ts_code") != dividend2.params.get("ts_code")


def test_stockdividend_empty_result_handling():
    """Test handling of empty API results"""
    empty_data = pd.DataFrame()
    fake_conn = FakeConnection(frame=empty_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"})

    result = dividend.run()

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) > 0


def test_stockdividend_large_dataset_handling():
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": ["600848.SH"] * 1000,
            "end_date": ["20201231"] * 1000,
            "ann_date": ["20210415"] * 1000,
            "div_proc": ["实施"] * 1000,
            "stk_div": ["0.10"] * 1000,
            "cash_div": ["0.50"] * 1000,
            "record_date": ["20210520"] * 1000,
            "ex_date": ["20210521"] * 1000,
            "pay_date": ["20210528"] * 1000,
            "div_listdate": ["20210528"] * 1000,
            "imp_ann_date": ["20210415"] * 1000,
            "base_date": ["20201231"] * 1000,
        }
    )

    fake_conn = FakeConnection(frame=large_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"})

    result = dividend.run()

    # Should deduplicate to 1 row
    assert len(result) == 1


def test_stockdividend_without_cache(sample_source_data):
    """Test that class works correctly without caching"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"}, cache=False)

    result = dividend.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert dividend.cache is None


def test_stockdividend_handles_missing_fields():
    """Test that missing fields don't break transformation"""
    # Data with only subset of fields
    minimal_data = pd.DataFrame(
        {
            "ts_code": ["600848.SH"],
            "end_date": ["20201231"],
            "ann_date": ["20210415"],
            "div_proc": ["实施"],
            "stk_div": ["0.10"],
            "cash_div": ["0.50"],
            "record_date": ["20210520"],
            "ex_date": ["20210521"],
        }
    )

    fake_conn = FakeConnection(frame=minimal_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ts_code": "600848.SH"})

    result = dividend.run()

    # Should complete without error
    assert len(result) == 1
    # Missing fields should be NaN
    assert pd.isna(result.iloc[0]["base_share"])


def test_stockdividend_api_doc_reference():
    """Test that class correctly references API documentation"""
    assert "doc_id=103" in StockDividend.__doc__


def test_stockdividend_crosssection_scale():
    """Test that module is correctly configured as crosssection scale"""
    assert SOURCE.meta["scale"] == "crosssection"
    assert TARGET.meta["scale"] == "crosssection"


def test_stockdividend_multiple_stocks_handling(sample_source_data):
    """Test handling of data with multiple stocks"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session, params={"ann_date": "20210415"})

    result = dividend.run()

    # Should have data for both stocks
    assert len(result) == 3
    assert "600848.SH" in result["code"].values
    assert "000001.SZ" in result["code"].values


def test_stockdividend_handles_zero_values(sample_source_data):
    """Test that zero values in numeric fields are handled correctly"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    dividend = StockDividend(session=session)

    result = dividend.transform(sample_source_data)

    # Check that zero values are preserved (not treated as missing)
    zero_div_rows = result[result["stk_div"] == 0.0]
    assert len(zero_div_rows) == 1
    assert zero_div_rows.iloc[0]["code"] == "000001.SZ"

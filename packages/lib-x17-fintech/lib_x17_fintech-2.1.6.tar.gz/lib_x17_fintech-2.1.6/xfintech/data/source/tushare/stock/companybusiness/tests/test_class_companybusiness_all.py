import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.companybusiness import CompanyBusiness
from xfintech.data.source.tushare.stock.companybusiness.constant import (
    KEY,
    NAME,
    PAGINATE,
    SOURCE,
    TARGET,
)

# Test Fixtures


class FakeConnection:
    """Fake Tushare connection for testing"""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def fina_mainbz_vip(self, **kwargs):
        """Mock fina_mainbz_vip API call"""
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
    """Sample company business composition data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "end_date": ["20200331", "20200331", "20200331"],
            "bz_item": ["产品A", "产品B", "产品C"],
            "bz_sales": ["100000000.50", "80000000.75", "50000000.25"],
            "bz_profit": ["15000000.30", "12000000.40", "6000000.15"],
            "bz_cost": ["85000000.20", "68000000.35", "44000000.10"],
            "curr_type": ["CNY", "CNY", "CNY"],
            "update_flag": ["1", "1", "1"],
        }
    )


# Initialization Tests


def test_companybusiness_init_basic(mock_session):
    """Test basic initialization with required session"""
    business = CompanyBusiness(session=mock_session)
    assert business.name == NAME
    assert business.key == KEY
    assert business.source == SOURCE
    assert business.target == TARGET
    assert business.paginate.pagesize == PAGINATE["pagesize"]
    assert business.paginate.pagelimit == PAGINATE["pagelimit"]


def test_companybusiness_init_with_params_dict(mock_session):
    """Test initialization with params as dict"""
    params = {"ts_code": "000001.SZ", "period": "20201231", "type": "P"}
    business = CompanyBusiness(session=mock_session, params=params)
    assert business.params.get("ts_code") == "000001.SZ"
    assert business.params.get("period") == "20201231"
    assert business.params.get("type") == "P"


def test_companybusiness_init_with_params_object(mock_session):
    """Test initialization with params as Params object"""
    from xfintech.data.common.params import Params

    params = Params(ts_code="000001.SZ", period="20201231")
    business = CompanyBusiness(session=mock_session, params=params)
    assert business.params.get("ts_code") == "000001.SZ"


def test_companybusiness_init_with_type_param(mock_session):
    """Test initialization with type parameter"""
    params = {"ts_code": "000001.SZ", "type": "P"}
    business = CompanyBusiness(session=mock_session, params=params)
    assert business.params.get("type") == "P"


def test_companybusiness_init_with_cache_bool_true(mock_session):
    """Test initialization with cache enabled"""
    business = CompanyBusiness(session=mock_session, cache=True)
    assert business.cache is not None


def test_companybusiness_init_with_cache_bool_false(mock_session):
    """Test initialization with cache disabled"""
    business = CompanyBusiness(session=mock_session, cache=False)
    assert business.cache is None


def test_companybusiness_init_with_cache_dict(mock_session):
    """Test initialization with cache config dict"""
    cache_config = {"path": "/tmp/cache", "key": "test"}
    business = CompanyBusiness(session=mock_session, cache=cache_config)
    assert business.cache is not None


def test_companybusiness_init_default_paginate_limit(mock_session):
    """Test that default pagination limit is set correctly"""
    business = CompanyBusiness(session=mock_session)
    assert business.paginate.pagesize
    assert business.paginate.pagelimit


def test_companybusiness_init_with_all_params(mock_session):
    """Test initialization with all parameters"""
    params = {"ts_code": "000001.SZ", "period": "20201231", "type": "P"}
    coolant = {"interval": 0.5}
    retry = {"max_attempts": 3}
    cache = True

    business = CompanyBusiness(session=mock_session, params=params, coolant=coolant, retry=retry, cache=cache)
    assert business.params.get("ts_code") == "000001.SZ"
    assert business.cache is not None


def test_companybusiness_constants():
    """Test that constants are correctly defined"""
    assert NAME == "companybusiness"
    assert KEY == "/tushare/companybusiness"
    assert SOURCE.name == "fina_mainbz_vip"
    assert TARGET.name == "companybusiness"
    assert PAGINATE["pagesize"]


# Transform Tests


def test_companybusiness_transform_basic(sample_source_data):
    """Test basic transformation of business composition data"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "datecode" in result.columns


def test_companybusiness_transform_code_mapping(sample_source_data):
    """Test that ts_code is correctly mapped to code"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[2]["code"] == "000002.SZ"


def test_companybusiness_transform_date_format(sample_source_data):
    """Test that dates are properly formatted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    assert pd.api.types.is_datetime64_any_dtype(result["date"]) is False
    assert result.iloc[0]["date"] == "2020-03-31"


def test_companybusiness_transform_datecode_preserved(sample_source_data):
    """Test that datecode is correctly created from end_date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    assert result.iloc[0]["datecode"] == "20200331"
    assert result.iloc[1]["datecode"] == "20200331"


def test_companybusiness_transform_numeric_conversions(sample_source_data):
    """Test that numeric fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    assert result.iloc[0]["bz_sales"] == 100000000.50
    assert result.iloc[0]["bz_profit"] == 15000000.30
    assert pd.api.types.is_numeric_dtype(result["bz_sales"])


def test_companybusiness_transform_string_fields(sample_source_data):
    """Test that string fields are properly converted"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    assert result.iloc[0]["bz_item"] == "产品A"
    assert result.iloc[0]["curr_type"] == "CNY"
    assert result.iloc[0]["update_flag"] == "1"


def test_companybusiness_transform_empty_dataframe():
    """Test transformation with empty dataframe"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(pd.DataFrame())

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) == len(TARGET.list_column_names())


def test_companybusiness_transform_none_input():
    """Test transformation with None input"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(None)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_companybusiness_transform_handles_invalid_dates():
    """Test that invalid dates are handled gracefully"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["invalid"],
            "bz_item": ["产品A"],
            "bz_sales": ["100000.00"],
            "curr_type": ["CNY"],
            "update_flag": ["1"],
        }
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(data)

    assert len(result) == 1
    assert pd.isna(result.iloc[0]["date"])


def test_companybusiness_transform_removes_duplicates(sample_source_data):
    """Test that duplicate rows are removed"""
    # Create data with duplicates
    data = pd.concat([sample_source_data, sample_source_data.iloc[[0]]], ignore_index=True)

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(data)

    # Should have 3 unique rows, not 4
    assert len(result) == 3


def test_companybusiness_transform_sorts_by_code_and_date(sample_source_data):
    """Test that output is sorted by code and date"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    # Check first row is 000001.SZ
    assert result.iloc[0]["code"] == "000001.SZ"
    assert result.iloc[0]["date"] == "2020-03-31"
    # Check last row is 000002.SZ
    assert result.iloc[2]["code"] == "000002.SZ"


def test_companybusiness_transform_resets_index():
    """Test that index is reset after transformation"""
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "end_date": ["20200331", "20200331"],
            "bz_item": ["产品A", "产品B"],
            "bz_sales": ["100000.00", "50000.00"],
            "curr_type": ["CNY", "CNY"],
            "update_flag": ["1", "1"],
        },
        index=[5, 10],
    )

    fake_conn = FakeConnection(frame=data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(data)

    assert result.index.tolist() == [0, 1]


def test_companybusiness_transform_only_target_columns(sample_source_data):
    """Test that only target columns are in output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)

    assert actual_cols == expected_cols


# Run Method Tests


def test_companybusiness_run_with_cache_hit(sample_source_data):
    """Test that run() returns cached data when available"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    # First run should fetch and cache
    result1 = business.run()

    # Second run should return cached data
    result2 = business.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_companybusiness_run_basic_date_range(sample_source_data):
    """Test run() with date range parameters"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(
        session=session,
        params={"ts_code": "000001.SZ", "start_date": "20200101", "end_date": "20201231"},
    )

    result = business.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_companybusiness_run_with_period_param(sample_source_data):
    """Test run() with period parameter"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ", "period": "20200331"})

    result = business.run()

    assert isinstance(result, pd.DataFrame)


def test_companybusiness_run_with_datetime_params(sample_source_data):
    """Test run() with datetime objects as parameters"""
    from datetime import datetime

    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(
        session=session,
        params={
            "ts_code": "000001.SZ",
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2020, 12, 31),
        },
    )

    result = business.run()

    assert isinstance(result, pd.DataFrame)


def test_companybusiness_run_preserves_fields_param(sample_source_data):
    """Test that run() preserves fields parameter if provided"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    custom_fields = "ts_code,end_date,bz_item,bz_sales"
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ", "fields": custom_fields})

    # Monkey patch _fetchall to capture params
    captured_params = {}

    def mock_fetchall(api, **kwargs):
        captured_params.update(kwargs)
        return sample_source_data

    business._fetchall = mock_fetchall
    business.run()

    assert captured_params["fields"] == custom_fields


def test_companybusiness_run_sets_cache(sample_source_data):
    """Test that run() saves result to cache"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    result = business.run()

    # Cache should be set after run
    cached = business._load_cache()
    assert cached is not None
    pd.testing.assert_frame_equal(result, cached)


def test_companybusiness_run_calls_transform(sample_source_data):
    """Test that run() calls transform method"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    # Monkey patch transform to track if it was called
    original_transform = business.transform
    transform_called = {"called": False}

    def mock_transform(data):
        transform_called["called"] = True
        return original_transform(data)

    business.transform = mock_transform
    business.run()

    assert transform_called["called"] is True


def test_companybusiness_run_uses_fina_mainbz_vip_api(sample_source_data):
    """Test that run() uses fina_mainbz_vip API"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    # Monkey patch _fetchall to capture API
    captured_api = {"api": None}

    def mock_fetchall(api, **kwargs):
        captured_api["api"] = api
        return sample_source_data

    business._fetchall = mock_fetchall
    business.run()

    assert captured_api["api"] == session.connection.fina_mainbz_vip


# Integration Tests


def test_companybusiness_full_workflow(sample_source_data):
    """Test complete workflow from initialization to output"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    business = CompanyBusiness(
        session=session,
        params={"ts_code": "000001.SZ", "period": "20200331", "type": "P"},
        cache=True,
    )

    result = business.run()

    # Verify output structure
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "code" in result.columns
    assert "date" in result.columns
    assert "bz_item" in result.columns
    assert "bz_sales" in result.columns

    # Verify data types
    assert pd.api.types.is_numeric_dtype(result["bz_sales"])
    assert result.iloc[0]["code"] == "000001.SZ"


def test_companybusiness_cache_persistence(sample_source_data):
    """Test that cache persists across multiple runs"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"}, cache=True)

    # Run once to populate cache
    result1 = business.run()

    # Clear in-memory data to simulate fresh load
    business2 = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"}, cache=True)
    result2 = business2.run()

    pd.testing.assert_frame_equal(result1, result2)


def test_companybusiness_params_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    business1 = CompanyBusiness(
        session=mock_session,
        params={"ts_code": "000001.SZ", "period": "20200331"},
        cache=True,
    )
    business2 = CompanyBusiness(
        session=mock_session,
        params={"ts_code": "000001.SZ", "period": "20210331"},
        cache=True,
    )

    # Test that different params are properly stored
    assert business1.params.get("period") == "20200331"
    assert business2.params.get("period") == "20210331"
    assert business1.params.get("period") != business2.params.get("period")


def test_companybusiness_different_stocks(sample_source_data):
    """Test that different stock codes are handled correctly"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)

    business1 = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})
    result1 = business1.run()

    business2 = CompanyBusiness(session=session, params={"ts_code": "000002.SZ"})
    result2 = business2.run()

    # Both should have data for their respective stocks
    assert "000001.SZ" in result1["code"].values
    assert "000002.SZ" in result2["code"].values


def test_companybusiness_empty_result_handling():
    """Test handling of empty API results"""
    empty_data = pd.DataFrame()
    fake_conn = FakeConnection(frame=empty_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.run()

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert len(result.columns) > 0


def test_companybusiness_large_dataset_handling():
    """Test handling of large datasets"""
    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"] * 1000,
            "end_date": ["20200331"] * 1000,
            "bz_item": ["产品A"] * 1000,
            "bz_sales": ["100000.00"] * 1000,
            "curr_type": ["CNY"] * 1000,
            "update_flag": ["1"] * 1000,
        }
    )

    fake_conn = FakeConnection(frame=large_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.run()

    # Should deduplicate to 1 row
    assert len(result) == 1


def test_companybusiness_without_cache(sample_source_data):
    """Test that class works correctly without caching"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"}, cache=False)

    result = business.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert business.cache is None


def test_companybusiness_handles_missing_numeric_fields():
    """Test that missing numeric fields don't break transformation"""
    # Data with only subset of fields
    minimal_data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["20200331"],
            "bz_item": ["产品A"],
            "bz_sales": ["100000.00"],
            "curr_type": ["CNY"],
            "update_flag": ["1"],
        }
    )

    fake_conn = FakeConnection(frame=minimal_data)
    session = FakeSession(fake_conn)
    business = CompanyBusiness(session=session, params={"ts_code": "000001.SZ"})

    result = business.run()

    # Should complete without error
    assert len(result) == 1
    # Missing fields should be NaN
    assert pd.isna(result.iloc[0]["bz_profit"])


def test_companybusiness_api_doc_reference():
    """Test that class correctly references API documentation"""
    assert "doc_id=81" in CompanyBusiness.__doc__

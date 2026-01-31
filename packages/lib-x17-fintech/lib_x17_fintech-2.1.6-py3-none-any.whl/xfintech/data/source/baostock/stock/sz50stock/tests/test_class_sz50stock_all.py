from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.sz50stock.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.baostock.stock.sz50stock.sz50stock import SZ50Stock

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
    mock_connection.query_sz50_stocks = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Baostock format"""
    return pd.DataFrame(
        {
            "updateDate": ["2018-11-26"] * 10,
            "code": [
                "sh.600000",
                "sh.600016",
                "sh.600019",
                "sh.600028",
                "sh.600030",
                "sh.600036",
                "sh.600048",
                "sh.600050",
                "sh.600104",
                "sh.600109",
            ],
            "code_name": [
                "浦发银行",
                "民生银行",
                "宝钢股份",
                "中国石化",
                "中信证券",
                "招商银行",
                "保利地产",
                "中国联通",
                "上汽集团",
                "国金证券",
            ],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_sz50stock_initialization_basic(mock_session):
    """Test basic initialization"""
    job = SZ50Stock(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET


def test_sz50stock_initialization_with_params(mock_session):
    """Test initialization with params (not used for this API)"""
    params = {}
    job = SZ50Stock(session=mock_session, params=params)

    # No specific params needed for SZ50 API
    assert job.params is not None


def test_sz50stock_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = SZ50Stock(
        session=mock_session,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert job.coolant.interval == 0.2
    assert job.retry.retry == 3
    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_sz50stock_name_and_key():
    """Test name and key constants"""
    assert NAME == "sz50stock"
    assert KEY == "/baostock/sz50stock"


def test_sz50stock_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert "上证50成分股" in SOURCE.desc

    column_names = SOURCE.columns
    assert "updatedate" in column_names
    assert "code" in column_names
    assert "code_name" in column_names


def test_sz50stock_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert "上证50成分股" in TARGET.desc

    column_names = TARGET.columns
    assert "update_date" in column_names
    assert "code" in column_names
    assert "name" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_sz50stock_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = SZ50Stock(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 10
    assert "update_date" in result.columns
    assert "code" in result.columns
    assert "name" in result.columns
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[0]["name"] == "浦发银行"


def test_sz50stock_transform_field_types(mock_session, sample_source_data):
    """Test field type conversions"""
    job = SZ50Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Check string fields
    assert isinstance(result.iloc[0]["update_date"], str)
    assert isinstance(result.iloc[0]["code"], str)
    assert isinstance(result.iloc[0]["name"], str)


def test_sz50stock_transform_field_mapping(mock_session, sample_source_data):
    """Test field name mappings"""
    job = SZ50Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Verify field mappings
    row = result[result["code"] == "sh.600000"].iloc[0]
    assert row["update_date"] == "2018-11-26"  # from updateDate
    assert row["name"] == "浦发银行"  # from code_name
    assert row["code"] == "sh.600000"


def test_sz50stock_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = SZ50Stock(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_sz50stock_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sh.600000", "sh.600000", "sh.600016"],
            "code_name": ["浦发银行", "浦发银行", "民生银行"],
        }
    )
    job = SZ50Stock(session=mock_session)
    result = job.transform(data)

    assert len(result) == 2  # Duplicates removed


def test_sz50stock_transform_sorting(mock_session):
    """Test that results are sorted by code"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sh.600050", "sh.600000", "sh.600030"],
            "code_name": ["中国联通", "浦发银行", "中信证券"],
        }
    )
    job = SZ50Stock(session=mock_session)
    result = job.transform(data)

    # Should be sorted by code
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[1]["code"] == "sh.600030"
    assert result.iloc[2]["code"] == "sh.600050"


# ============================================================================
# Run Tests
# ============================================================================


def test_sz50stock_run_basic(mock_session, sample_source_data):
    """Test basic run functionality"""
    job = SZ50Stock(session=mock_session)

    # Mock _fetchall to return sample data
    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "_load_cache", return_value=None):
            with patch.object(job, "_save_cache"):
                result = job._run()

                assert isinstance(result, pd.DataFrame)
                assert len(result) == 10
                assert "update_date" in result.columns
                assert "code" in result.columns
                assert "name" in result.columns


def test_sz50stock_run_calls_api(mock_session, sample_source_data):
    """Test that run calls the correct API"""
    job = SZ50Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        with patch.object(job, "_load_cache", return_value=None):
            with patch.object(job, "_save_cache"):
                job._run()

                # Verify API was called
                mock_fetchall.assert_called_once()
                call_kwargs = mock_fetchall.call_args[1]
                assert call_kwargs["api"] == job.connection.query_sz50_stocks


def test_sz50stock_run_with_cache(mock_session, sample_source_data):
    """Test that cache is used when available"""
    job = SZ50Stock(session=mock_session)
    cached_data = sample_source_data.copy()

    with patch.object(job, "_load_cache", return_value=cached_data):
        with patch.object(job, "_fetchall") as mock_fetchall:
            result = job._run()

            # Should return cached data without calling API
            mock_fetchall.assert_not_called()
            assert len(result) == 10


# ============================================================================
# List Methods Tests
# ============================================================================


def test_sz50stock_list_codes(mock_session, sample_source_data):
    """Test list_codes method"""
    job = SZ50Stock(session=mock_session)

    with patch.object(job, "run", return_value=job.transform(sample_source_data)):
        codes = job.list_codes()

        assert isinstance(codes, list)
        assert len(codes) == 10
        assert "sh.600000" in codes
        assert "sh.600109" in codes
        # Should be sorted
        assert codes == sorted(codes)


def test_sz50stock_list_names(mock_session, sample_source_data):
    """Test list_names method"""
    job = SZ50Stock(session=mock_session)

    with patch.object(job, "run", return_value=job.transform(sample_source_data)):
        names = job.list_names()

        assert isinstance(names, list)
        assert len(names) == 10
        assert "浦发银行" in names
        assert "国金证券" in names
        # Should be sorted
        assert names == sorted(names)


def test_sz50stock_list_codes_with_duplicates(mock_session):
    """Test list_codes with duplicate codes"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sh.600000", "sh.600000", "sh.600016"],
            "code_name": ["浦发银行", "浦发银行", "民生银行"],
        }
    )
    job = SZ50Stock(session=mock_session)
    transformed = job.transform(data)

    with patch.object(job, "run", return_value=transformed):
        codes = job.list_codes()

        # Should return unique codes only
        assert len(codes) == 2
        assert "sh.600000" in codes
        assert "sh.600016" in codes


# ============================================================================
# Integration Tests
# ============================================================================


def test_sz50stock_full_workflow(mock_session, sample_source_data):
    """Test full workflow from initialization to result"""
    job = SZ50Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "_load_cache", return_value=None):
            with patch.object(job, "_save_cache"):
                result = job._run()

                # Verify result structure
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 10
                assert "update_date" in result.columns
                assert "code" in result.columns
                assert "name" in result.columns

                # Verify data types
                assert isinstance(result.iloc[0]["update_date"], str)
                assert isinstance(result.iloc[0]["code"], str)
                assert isinstance(result.iloc[0]["name"], str)

                # Verify sorting
                codes = result["code"].tolist()
                assert codes == sorted(codes)


def test_sz50stock_same_update_date(mock_session, sample_source_data):
    """Test that all stocks have the same update date"""
    job = SZ50Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # All stocks should have the same update date
    unique_dates = result["update_date"].unique()
    assert len(unique_dates) == 1
    assert unique_dates[0] == "2018-11-26"


def test_sz50stock_code_format(mock_session, sample_source_data):
    """Test that codes follow sh.XXXXXX format"""
    job = SZ50Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # All codes should start with "sh."
    for code in result["code"]:
        assert code.startswith("sh.")
        assert len(code) == 9  # sh. + 6 digits


# ============================================================================

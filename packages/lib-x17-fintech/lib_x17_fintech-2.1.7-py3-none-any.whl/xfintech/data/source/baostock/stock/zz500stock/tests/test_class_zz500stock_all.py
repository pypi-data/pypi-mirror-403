"""
Comprehensive tests for ZZ500Stock class.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.zz500stock.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.baostock.stock.zz500stock.zz500stock import ZZ500Stock

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
    mock_connection.query_zz500_stocks = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Baostock format"""
    return pd.DataFrame(
        {
            "updateDate": ["2018-11-26"] * 15,
            "code": [
                "sh.600004",
                "sh.600006",
                "sh.600007",
                "sh.600011",
                "sh.600012",
                "sh.600017",
                "sh.600020",
                "sh.600021",
                "sh.600022",
                "sh.600026",
                "sz.000004",
                "sz.000005",
                "sz.000006",
                "sz.000007",
                "sz.000008",
            ],
            "code_name": [
                "白云机场",
                "东风汽车",
                "中国国贸",
                "华能国际",
                "皖通高速",
                "日照港",
                "中原高速",
                "上海电力",
                "山东钢铁",
                "中远海能",
                "国华网安",
                "ST星源",
                "深振业A",
                "全新好",
                "神州高铁",
            ],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_zz500stock_initialization_basic(mock_session):
    """Test basic initialization"""
    job = ZZ500Stock(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET


def test_zz500stock_initialization_with_params(mock_session):
    """Test initialization with params (not used for this API)"""
    params = {}
    job = ZZ500Stock(session=mock_session, params=params)

    # No specific params needed for ZZ500 API
    assert job.params is not None


def test_zz500stock_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = ZZ500Stock(
        session=mock_session,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert job.coolant.interval == 0.2
    assert job.retry.retry == 3
    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_zz500stock_name_and_key():
    """Test name and key constants"""
    assert NAME == "zz500stock"
    assert KEY == "/baostock/zz500stock"


def test_zz500stock_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert "中证500成分股" in SOURCE.desc

    column_names = SOURCE.columns
    assert "updatedate" in column_names
    assert "code" in column_names
    assert "code_name" in column_names


def test_zz500stock_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert "中证500成分股" in TARGET.desc

    column_names = TARGET.columns
    assert "update_date" in column_names
    assert "code" in column_names
    assert "name" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_zz500stock_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = ZZ500Stock(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 15
    assert "update_date" in result.columns
    assert "code" in result.columns
    assert "name" in result.columns
    assert result.iloc[0]["code"] == "sh.600004"
    assert result.iloc[0]["name"] == "白云机场"


def test_zz500stock_transform_field_types(mock_session, sample_source_data):
    """Test field type conversions"""
    job = ZZ500Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Check string fields
    assert isinstance(result.iloc[0]["update_date"], str)
    assert isinstance(result.iloc[0]["code"], str)
    assert isinstance(result.iloc[0]["name"], str)


def test_zz500stock_transform_field_mapping(mock_session, sample_source_data):
    """Test field name mappings"""
    job = ZZ500Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Verify field mappings
    row = result[result["code"] == "sh.600004"].iloc[0]
    assert row["update_date"] == "2018-11-26"  # from updateDate
    assert row["name"] == "白云机场"  # from code_name
    assert row["code"] == "sh.600004"


def test_zz500stock_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = ZZ500Stock(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_zz500stock_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sh.600004", "sh.600004", "sh.600006"],
            "code_name": ["白云机场", "白云机场", "东风汽车"],
        }
    )
    job = ZZ500Stock(session=mock_session)
    result = job.transform(data)

    assert len(result) == 2  # Duplicates removed


def test_zz500stock_transform_sorting(mock_session):
    """Test that results are sorted by code"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sz.000004", "sh.600004", "sh.600006"],
            "code_name": ["国华网安", "白云机场", "东风汽车"],
        }
    )
    job = ZZ500Stock(session=mock_session)
    result = job.transform(data)

    # Should be sorted by code
    assert result.iloc[0]["code"] == "sh.600004"
    assert result.iloc[1]["code"] == "sh.600006"
    assert result.iloc[2]["code"] == "sz.000004"


def test_zz500stock_transform_mixed_exchanges(mock_session, sample_source_data):
    """Test transform with stocks from both Shanghai and Shenzhen exchanges"""
    job = ZZ500Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Should have both sh. and sz. codes
    sh_codes = [code for code in result["code"] if code.startswith("sh.")]
    sz_codes = [code for code in result["code"] if code.startswith("sz.")]

    assert len(sh_codes) > 0
    assert len(sz_codes) > 0


# ============================================================================
# Run Tests
# ============================================================================


def test_zz500stock_run_basic(mock_session, sample_source_data):
    """Test basic run functionality"""
    job = ZZ500Stock(session=mock_session)

    # Mock _fetchall to return sample data
    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "_load_cache", return_value=None):
            with patch.object(job, "_save_cache"):
                result = job._run()

                assert isinstance(result, pd.DataFrame)
                assert len(result) == 15
                assert "update_date" in result.columns
                assert "code" in result.columns
                assert "name" in result.columns


def test_zz500stock_run_calls_api(mock_session, sample_source_data):
    """Test that run calls the correct API"""
    job = ZZ500Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        with patch.object(job, "_load_cache", return_value=None):
            with patch.object(job, "_save_cache"):
                job._run()

                # Verify API was called
                mock_fetchall.assert_called_once()
                call_kwargs = mock_fetchall.call_args[1]
                assert call_kwargs["api"] == job.connection.query_zz500_stocks


def test_zz500stock_run_with_cache(mock_session, sample_source_data):
    """Test that cache is used when available"""
    job = ZZ500Stock(session=mock_session)
    cached_data = sample_source_data.copy()

    with patch.object(job, "_load_cache", return_value=cached_data):
        with patch.object(job, "_fetchall") as mock_fetchall:
            result = job._run()

            # Should return cached data without calling API
            mock_fetchall.assert_not_called()
            assert len(result) == 15


# ============================================================================
# List Methods Tests
# ============================================================================


def test_zz500stock_list_codes(mock_session, sample_source_data):
    """Test list_codes method"""
    job = ZZ500Stock(session=mock_session)

    with patch.object(job, "run", return_value=job.transform(sample_source_data)):
        codes = job.list_codes()

        assert isinstance(codes, list)
        assert len(codes) == 15
        assert "sh.600004" in codes
        assert "sz.000008" in codes
        # Should be sorted
        assert codes == sorted(codes)


def test_zz500stock_list_names(mock_session, sample_source_data):
    """Test list_names method"""
    job = ZZ500Stock(session=mock_session)

    with patch.object(job, "run", return_value=job.transform(sample_source_data)):
        names = job.list_names()

        assert isinstance(names, list)
        assert len(names) == 15
        assert "白云机场" in names
        assert "神州高铁" in names
        # Should be sorted
        assert names == sorted(names)


def test_zz500stock_list_codes_with_duplicates(mock_session):
    """Test list_codes with duplicate codes"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sh.600004", "sh.600004", "sh.600006"],
            "code_name": ["白云机场", "白云机场", "东风汽车"],
        }
    )
    job = ZZ500Stock(session=mock_session)
    transformed = job.transform(data)

    with patch.object(job, "run", return_value=transformed):
        codes = job.list_codes()

        # Should return unique codes only
        assert len(codes) == 2
        assert "sh.600004" in codes
        assert "sh.600006" in codes


# ============================================================================
# Integration Tests
# ============================================================================


def test_zz500stock_full_workflow(mock_session, sample_source_data):
    """Test full workflow from initialization to result"""
    job = ZZ500Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data):
        with patch.object(job, "_load_cache", return_value=None):
            with patch.object(job, "_save_cache"):
                result = job._run()

                # Verify result structure
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 15
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


def test_zz500stock_same_update_date(mock_session, sample_source_data):
    """Test that all stocks have the same update date"""
    job = ZZ500Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # All stocks should have the same update date
    unique_dates = result["update_date"].unique()
    assert len(unique_dates) == 1
    assert unique_dates[0] == "2018-11-26"


def test_zz500stock_code_format(mock_session, sample_source_data):
    """Test that codes follow sh./sz.XXXXXX format"""
    job = ZZ500Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # All codes should start with "sh." or "sz."
    for code in result["code"]:
        assert code.startswith("sh.") or code.startswith("sz.")
        assert len(code) == 9  # sh./sz. + 6 digits

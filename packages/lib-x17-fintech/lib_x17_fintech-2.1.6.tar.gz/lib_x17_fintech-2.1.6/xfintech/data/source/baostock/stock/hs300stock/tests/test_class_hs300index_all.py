from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.session.session import Session
from xfintech.data.source.baostock.stock.hs300stock.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)
from xfintech.data.source.baostock.stock.hs300stock.hs300stock import HS300Stock


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
    mock_connection.query_hs300_stocks = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Baostock format"""
    return pd.DataFrame(
        {
            "updateDate": ["2018-11-26"] * 15,
            "code": [
                "sh.600000",
                "sh.600008",
                "sh.600009",
                "sh.600010",
                "sh.600015",
                "sh.600016",
                "sh.600018",
                "sh.600019",
                "sh.600028",
                "sh.600029",
                "sz.000001",
                "sz.000002",
                "sz.000063",
                "sz.000069",
                "sz.000100",
            ],
            "code_name": [
                "浦发银行",
                "首创股份",
                "上海机场",
                "包钢股份",
                "华夏银行",
                "民生银行",
                "上港集团",
                "宝钢股份",
                "中国石化",
                "南方航空",
                "平安银行",
                "万科A",
                "中兴通讯",
                "华侨城A",
                "TCL科技",
            ],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_hs300stock_initialization_basic(mock_session):
    """Test basic initialization"""
    job = HS300Stock(session=mock_session)

    assert job.name == NAME
    assert job.key == KEY
    assert job.source == SOURCE
    assert job.target == TARGET


def test_hs300stock_initialization_with_params(mock_session):
    """Test initialization with params (not used for this API)"""
    params = {}
    job = HS300Stock(session=mock_session, params=params)

    # No specific params needed for HS300 API
    assert job.params is not None


def test_hs300stock_initialization_with_all_components(mock_session):
    """Test initialization with all components"""
    coolant = Coolant(interval=0.2)
    retry = Retry(retry=3)
    cache = Cache(path="/tmp/test_cache")

    job = HS300Stock(
        session=mock_session,
        coolant=coolant,
        retry=retry,
        cache=cache,
    )

    assert job.coolant.interval == 0.2
    assert job.retry.retry == 3
    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_hs300stock_name_and_key():
    """Test name and key constants"""
    assert NAME == "hs300stock"
    assert KEY == "/baostock/hs300stock"


def test_hs300stock_source_schema():
    """Test source schema has all required columns"""
    assert SOURCE is not None
    assert "沪深300成分股" in SOURCE.desc

    column_names = SOURCE.columns
    assert "updatedate" in column_names
    assert "code" in column_names
    assert "code_name" in column_names


def test_hs300stock_target_schema():
    """Test target schema has all required columns"""
    assert TARGET is not None
    assert "沪深300成分股" in TARGET.desc

    column_names = TARGET.columns
    assert "update_date" in column_names
    assert "code" in column_names
    assert "name" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


def test_hs300stock_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    job = HS300Stock(session=mock_session)
    result = job.transform(sample_source_data)

    assert len(result) == 15
    assert "update_date" in result.columns
    assert "code" in result.columns
    assert "name" in result.columns
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[0]["name"] == "浦发银行"


def test_hs300stock_transform_field_types(mock_session, sample_source_data):
    """Test field type conversions"""
    job = HS300Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Check string fields
    assert isinstance(result.iloc[0]["update_date"], str)
    assert isinstance(result.iloc[0]["code"], str)
    assert isinstance(result.iloc[0]["name"], str)


def test_hs300stock_transform_field_mapping(mock_session, sample_source_data):
    """Test field name mappings"""
    job = HS300Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Verify field mappings
    row = result[result["code"] == "sh.600000"].iloc[0]
    assert row["update_date"] == "2018-11-26"  # from updateDate
    assert row["name"] == "浦发银行"  # from code_name
    assert row["code"] == "sh.600000"


def test_hs300stock_transform_empty_data(mock_session):
    """Test transform with empty data"""
    job = HS300Stock(session=mock_session)

    # Test with None
    result = job.transform(None)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = job.transform(empty_df)
    assert result.empty
    assert len(result.columns) == len(TARGET.columns)


def test_hs300stock_transform_duplicate_removal(mock_session):
    """Test that duplicates are removed"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sh.600000", "sh.600000", "sh.600008"],
            "code_name": ["浦发银行", "浦发银行", "首创股份"],
        }
    )
    job = HS300Stock(session=mock_session)
    result = job.transform(data)

    assert len(result) == 2  # Duplicates removed


def test_hs300stock_transform_sorting(mock_session):
    """Test that results are sorted by code"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sz.000001", "sh.600000", "sh.600008"],
            "code_name": ["平安银行", "浦发银行", "首创股份"],
        }
    )
    job = HS300Stock(session=mock_session)
    result = job.transform(data)

    # Should be sorted by code
    assert result.iloc[0]["code"] == "sh.600000"
    assert result.iloc[1]["code"] == "sh.600008"
    assert result.iloc[2]["code"] == "sz.000001"


def test_hs300stock_transform_mixed_exchanges(mock_session, sample_source_data):
    """Test transform with stocks from both Shanghai and Shenzhen exchanges"""
    job = HS300Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # Should have both sh. and sz. codes
    sh_codes = [code for code in result["code"] if code.startswith("sh.")]
    sz_codes = [code for code in result["code"] if code.startswith("sz.")]

    assert len(sh_codes) > 0
    assert len(sz_codes) > 0


# ============================================================================
# Run Tests
# ============================================================================


def test_hs300stock_run_basic(mock_session, sample_source_data):
    """Test basic run functionality"""
    job = HS300Stock(session=mock_session)

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


def test_hs300stock_run_calls_api(mock_session, sample_source_data):
    """Test that run calls the correct API"""
    job = HS300Stock(session=mock_session)

    with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
        with patch.object(job, "_load_cache", return_value=None):
            with patch.object(job, "_save_cache"):
                job._run()

                # Verify API was called
                mock_fetchall.assert_called_once()
                call_kwargs = mock_fetchall.call_args[1]
                assert call_kwargs["api"] == job.connection.query_hs300_stocks


def test_hs300stock_run_with_cache(mock_session, sample_source_data):
    """Test that cache is used when available"""
    job = HS300Stock(session=mock_session)
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


def test_hs300stock_list_codes(mock_session, sample_source_data):
    """Test list_codes method"""
    job = HS300Stock(session=mock_session)

    with patch.object(job, "run", return_value=job.transform(sample_source_data)):
        codes = job.list_codes()

        assert isinstance(codes, list)
        assert len(codes) == 15
        assert "sh.600000" in codes
        assert "sz.000100" in codes
        # Should be sorted
        assert codes == sorted(codes)


def test_hs300stock_list_names(mock_session, sample_source_data):
    """Test list_names method"""
    job = HS300Stock(session=mock_session)

    with patch.object(job, "run", return_value=job.transform(sample_source_data)):
        names = job.list_names()

        assert isinstance(names, list)
        assert len(names) == 15
        assert "浦发银行" in names
        assert "TCL科技" in names
        # Should be sorted
        assert names == sorted(names)


def test_hs300stock_list_codes_with_duplicates(mock_session):
    """Test list_codes with duplicate codes"""
    data = pd.DataFrame(
        {
            "updateDate": ["2018-11-26", "2018-11-26", "2018-11-26"],
            "code": ["sh.600000", "sh.600000", "sh.600008"],
            "code_name": ["浦发银行", "浦发银行", "首创股份"],
        }
    )
    job = HS300Stock(session=mock_session)
    transformed = job.transform(data)

    with patch.object(job, "run", return_value=transformed):
        codes = job.list_codes()

        # Should return unique codes only
        assert len(codes) == 2
        assert "sh.600000" in codes
        assert "sh.600008" in codes


# ============================================================================
# Integration Tests
# ============================================================================


def test_hs300stock_full_workflow(mock_session, sample_source_data):
    """Test full workflow from initialization to result"""
    job = HS300Stock(session=mock_session)

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


def test_hs300stock_same_update_date(mock_session, sample_source_data):
    """Test that all stocks have the same update date"""
    job = HS300Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # All stocks should have the same update date
    unique_dates = result["update_date"].unique()
    assert len(unique_dates) == 1
    assert unique_dates[0] == "2018-11-26"


def test_hs300stock_code_format(mock_session, sample_source_data):
    """Test that codes follow sh./sz.XXXXXX format"""
    job = HS300Stock(session=mock_session)
    result = job.transform(sample_source_data)

    # All codes should start with "sh." or "sz."
    for code in result["code"]:
        assert code.startswith("sh.") or code.startswith("sz.")
        assert len(code) == 9  # sh./sz. + 6 digits

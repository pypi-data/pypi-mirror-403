"""
Test suite for Company class
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
from xfintech.data.source.tushare.stock.company.company import Company
from xfintech.data.source.tushare.stock.company.constant import (
    EXCHANGES,
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

    # Mock the connection object (which is returned by ts.pro_api())
    mock_connection = MagicMock()
    mock_connection.stock_company = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "com_name": ["平安银行股份有限公司", "万科企业股份有限公司", "浦发银行"],
            "com_id": ["91440300192448726P", "91440300192452569K", "9131000010000093XR"],
            "exchange": ["SZSE", "SZSE", "SSE"],
            "short_name": ["平安银行", "万科A", "浦发银行"],
            "chairman": ["谢永林", "郁亮", "郑杨"],
            "manager": ["谢永林", "祝九胜", "潘卫东"],
            "secretary": ["周强", "朱旭", "谢伟"],
            "reg_capital": [19405918.198, 1118226.3929, 29352374.0519],
            "setup_date": ["19871212", "19840530", "19920928"],
            "province": ["广东", "广东", "上海"],
            "city": ["深圳", "深圳", "上海"],
            "introduction": ["商业银行", "房地产开发", "商业银行"],
            "website": ["http://bank.pingan.com", "http://www.vanke.com", "http://www.spdb.com.cn"],
            "email": ["ir@pingan.com", "ir@vanke.com", "spdb@spdb.com.cn"],
            "office": ["深圳市", "深圳市", "上海市"],
            "employees": [35000, 50000, 45000],
            "main_business": ["银行业务", "房地产业务", "银行业务"],
            "business_scope": ["吸收存款", "房地产开发", "吸收存款"],
        }
    )


@pytest.fixture
def expected_transformed_data():
    """Create expected transformed data"""
    return pd.DataFrame(
        {
            "stockcode": ["000001.SZ", "000002.SZ", "600000.SH"],
            "company_name": ["平安银行股份有限公司", "万科企业股份有限公司", "浦发银行"],
            "company_id": ["91440300192448726P", "91440300192452569K", "9131000010000093XR"],
            "exchange": ["SZSE", "SZSE", "SSE"],
            "chairman": ["谢永林", "郁亮", "郑杨"],
            "manager": ["谢永林", "祝九胜", "潘卫东"],
            "secretary": ["周强", "朱旭", "谢伟"],
            "reg_capital": [19405918.198, 1118226.3929, 29352374.0519],
            "setup_date": ["1987-12-12", "1984-05-30", "1992-09-28"],
            "province": ["广东", "广东", "上海"],
            "city": ["深圳", "深圳", "上海"],
            "introduction": ["商业银行", "房地产开发", "商业银行"],
            "website": ["http://bank.pingan.com", "http://www.vanke.com", "http://www.spdb.com.cn"],
            "email": ["ir@pingan.com", "ir@vanke.com", "spdb@spdb.com.cn"],
            "office": ["深圳市", "深圳市", "上海市"],
            "employees": [35000, 50000, 45000],
            "main_business": ["银行业务", "房地产业务", "银行业务"],
            "business_scope": ["吸收存款", "房地产开发", "吸收存款"],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_company_init_basic(mock_session):
    """Test Company initialization with minimal parameters"""
    company = Company(session=mock_session)

    assert company.name == NAME
    assert company.key == KEY
    assert company.source == SOURCE
    assert company.target == TARGET
    assert isinstance(company.params, Params)
    assert isinstance(company.coolant, Coolant)
    assert isinstance(company.paginate, Paginate)
    assert isinstance(company.retry, Retry)
    assert company.paginate.pagesize == PAGINATE["pagesize"]
    assert company.paginate.pagelimit == PAGINATE["pagelimit"]


def test_company_init_with_params_dict(mock_session):
    """Test Company initialization with params as dict"""
    params = {"exchange": "SSE", "ts_code": "600000.SH"}
    company = Company(session=mock_session, params=params)

    assert company.params.exchange == "SSE"
    assert company.params.ts_code == "600000.SH"


def test_company_init_with_params_object(mock_session):
    """Test Company initialization with Params object"""
    params = Params(exchange="SZSE", ts_code="000001.SZ")
    company = Company(session=mock_session, params=params)

    assert company.params.exchange == "SZSE"
    assert company.params.ts_code == "000001.SZ"


def test_company_init_with_cache_bool_true(mock_session):
    """Test Company initialization with cache=True"""
    company = Company(session=mock_session, cache=True)

    assert company.cache is not None
    assert isinstance(company.cache, Cache)


def test_company_init_with_cache_bool_false(mock_session):
    """Test Company initialization with cache=False"""
    company = Company(session=mock_session, cache=False)

    assert company.cache is None


def test_company_init_with_cache_dict(mock_session):
    """Test Company initialization with cache as dict"""
    cache_config = {"directory": "/tmp/cache"}
    company = Company(session=mock_session, cache=cache_config)

    assert company.cache is not None
    assert isinstance(company.cache, Cache)


def test_company_init_with_all_params(mock_session):
    """Test Company initialization with all parameters"""
    company = Company(
        session=mock_session,
        params={"exchange": "SSE"},
        coolant={"interval": 1.0},
        retry={"max_retries": 3},
        cache=True,
    )

    assert company.name == NAME
    assert company.params.exchange == "SSE"
    assert company.cache is not None
    assert company.paginate.pagesize == PAGINATE["pagesize"]
    assert company.paginate.pagelimit == PAGINATE["pagelimit"]


def test_company_constants():
    """Test that constants are properly defined"""
    assert NAME == "company"
    assert KEY == "/tushare/stockcompany"
    assert EXCHANGES == ["SSE", "SZSE", "BSE"]
    assert SOURCE is not None
    assert TARGET is not None


# ============================================================================
# Transform Method Tests
# ============================================================================


def test_company_transform_basic(mock_session, sample_source_data):
    """Test basic data transformation"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    assert not result.empty
    assert len(result) == 3
    assert "stockcode" in result.columns
    assert "company_name" in result.columns
    assert "setup_date" in result.columns


def test_company_transform_stockcode_mapping(mock_session, sample_source_data):
    """Test that ts_code is mapped to stockcode"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    assert result["stockcode"].tolist() == ["000001.SZ", "000002.SZ", "600000.SH"]


def test_company_transform_company_name_mapping(mock_session, sample_source_data):
    """Test that com_name is mapped to company_name"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    assert "平安银行股份有限公司" in result["company_name"].values


def test_company_transform_date_format(mock_session, sample_source_data):
    """Test that setup_date is converted from YYYYMMDD to YYYY-MM-DD"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    assert result["setup_date"].tolist() == ["1987-12-12", "1984-05-30", "1992-09-28"]


def test_company_transform_numeric_conversion(mock_session, sample_source_data):
    """Test that reg_capital is converted to numeric"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    assert result["reg_capital"].dtype in [float, "float64"]
    assert result["reg_capital"].iloc[0] == 19405918.198


def test_company_transform_employees_integer(mock_session, sample_source_data):
    """Test that employees is converted to Int64"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    assert result["employees"].dtype == "Int64"
    assert result["employees"].iloc[0] == 35000


def test_company_transform_empty_dataframe(mock_session):
    """Test transform with empty DataFrame"""
    company = Company(session=mock_session)
    empty_df = pd.DataFrame()
    result = company.transform(empty_df)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_company_transform_none_input(mock_session):
    """Test transform with None input"""
    company = Company(session=mock_session)
    result = company.transform(None)

    assert result.empty
    assert list(result.columns) == TARGET.list_column_names()


def test_company_transform_handles_invalid_dates(mock_session):
    """Test transform handles invalid date formats"""
    company = Company(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "com_name": ["Test Company"],
            "com_id": ["12345"],
            "exchange": ["SZSE"],
            "short_name": ["Test"],
            "chairman": ["John"],
            "manager": ["Jane"],
            "secretary": ["Bob"],
            "reg_capital": [1000],
            "setup_date": ["invalid"],  # Invalid date
            "province": ["Test"],
            "city": ["Test"],
            "introduction": ["Test"],
            "website": ["http://test.com"],
            "email": ["test@test.com"],
            "office": ["Test"],
            "employees": [100],
            "main_business": ["Test"],
            "business_scope": ["Test"],
        }
    )

    result = company.transform(data)
    # Should handle error with coerce
    assert pd.isna(result["setup_date"].iloc[0]) or result["setup_date"].iloc[0] == "NaT"


def test_company_transform_handles_invalid_numeric(mock_session):
    """Test transform handles invalid numeric values"""
    company = Company(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "com_name": ["Test Company"],
            "com_id": ["12345"],
            "exchange": ["SZSE"],
            "short_name": ["Test"],
            "chairman": ["John"],
            "manager": ["Jane"],
            "secretary": ["Bob"],
            "reg_capital": ["invalid"],  # Invalid number
            "setup_date": ["20200101"],
            "province": ["Test"],
            "city": ["Test"],
            "introduction": ["Test"],
            "website": ["http://test.com"],
            "email": ["test@test.com"],
            "office": ["Test"],
            "employees": ["invalid"],  # Invalid number
            "main_business": ["Test"],
            "business_scope": ["Test"],
        }
    )

    result = company.transform(data)
    # Should handle error with coerce
    assert pd.isna(result["reg_capital"].iloc[0])
    assert pd.isna(result["employees"].iloc[0])


def test_company_transform_removes_duplicates(mock_session):
    """Test that transform removes duplicate rows"""
    company = Company(session=mock_session)
    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ"],  # Duplicate
            "com_name": ["Test", "Test"],
            "com_id": ["123", "123"],
            "exchange": ["SZSE", "SZSE"],
            "short_name": ["Test", "Test"],
            "chairman": ["A", "A"],
            "manager": ["B", "B"],
            "secretary": ["C", "C"],
            "reg_capital": [1000, 1000],
            "setup_date": ["20200101", "20200101"],
            "province": ["Test", "Test"],
            "city": ["Test", "Test"],
            "introduction": ["Test", "Test"],
            "website": ["http://test.com", "http://test.com"],
            "email": ["test@test.com", "test@test.com"],
            "office": ["Test", "Test"],
            "employees": [100, 100],
            "main_business": ["Test", "Test"],
            "business_scope": ["Test", "Test"],
        }
    )

    result = company.transform(data)
    assert len(result) == 1


def test_company_transform_sorts_by_stockcode(mock_session, sample_source_data):
    """Test that result is sorted by stockcode"""
    company = Company(session=mock_session)
    # Shuffle the data
    shuffled = sample_source_data.sample(frac=1).reset_index(drop=True)
    result = company.transform(shuffled)

    # Should be sorted
    assert result["stockcode"].tolist() == sorted(result["stockcode"].tolist())


def test_company_transform_resets_index(mock_session, sample_source_data):
    """Test that result has reset index"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    assert result.index.tolist() == list(range(len(result)))


def test_company_transform_only_target_columns(mock_session, sample_source_data):
    """Test that only target columns are in result"""
    company = Company(session=mock_session)
    result = company.transform(sample_source_data)

    expected_cols = set(TARGET.list_column_names())
    actual_cols = set(result.columns)
    assert actual_cols == expected_cols


# ============================================================================
# _run Method Tests
# ============================================================================


def test_company_run_with_cache_hit(mock_session):
    """Test _run returns cached data when available"""
    company = Company(session=mock_session, cache=True)

    # Set up cached data
    cached_df = pd.DataFrame({"stockcode": ["000001.SZ"]})
    company.cache.set(company.params.identifier, cached_df)

    result = company._run()

    # Should return cached data without calling API
    assert result.equals(cached_df)


def test_company_run_without_exchange_param(mock_session, sample_source_data):
    """Test _run queries all exchanges when exchange not specified"""
    company = Company(session=mock_session)

    # Mock _fetchall to return sample data
    with patch.object(company, "_fetchall", return_value=sample_source_data):
        with patch.object(company, "transform", return_value=sample_source_data):
            company._run()

            # Should call _fetchall for each exchange
            assert company._fetchall.call_count == len(EXCHANGES)


def test_company_run_with_exchange_param(mock_session, sample_source_data):
    """Test _run queries specific exchange when provided"""
    company = Company(session=mock_session, params={"exchange": "SSE"})

    # Mock _fetchall
    with patch.object(company, "_fetchall", return_value=sample_source_data):
        with patch.object(company, "transform", return_value=sample_source_data):
            company._run()

            # Should call _fetchall only once
            assert company._fetchall.call_count == 1


def test_company_run_adds_fields_param(mock_session, sample_source_data):
    """Test _run adds fields parameter if not provided"""
    company = Company(session=mock_session)

    with patch.object(company, "_fetchall", return_value=sample_source_data):
        with patch.object(company, "transform", return_value=sample_source_data):
            company._run()

            # Check that fields were added to params
            call_args = company._fetchall.call_args
            assert "fields" in call_args[1]


def test_company_run_preserves_fields_param(mock_session, sample_source_data):
    """Test _run preserves existing fields parameter"""
    custom_fields = "ts_code,com_name,exchange"
    company = Company(session=mock_session, params={"fields": custom_fields})

    with patch.object(company, "_fetchall", return_value=sample_source_data):
        with patch.object(company, "transform", return_value=sample_source_data):
            company._run()

            # Should use provided fields
            assert company.params.fields == custom_fields


def test_company_run_sets_cache(mock_session, sample_source_data):
    """Test _run saves result to cache"""
    company = Company(session=mock_session, cache=True)

    with patch.object(company, "_fetchall", return_value=sample_source_data):
        with patch.object(company, "transform", return_value=sample_source_data):
            company._run()

            # Check cache was set
            cached = company.cache.get(company.params.identifier)
            assert cached is not None


def test_company_run_calls_transform(mock_session, sample_source_data):
    """Test _run calls transform method"""
    company = Company(session=mock_session)

    with patch.object(company, "_fetchall", return_value=sample_source_data):
        with patch.object(company, "transform", return_value=sample_source_data) as mock_transform:
            company._run()

            # Transform should be called
            assert mock_transform.called


def test_company_run_concatenates_multiple_exchanges(mock_session, sample_source_data):
    """Test _run concatenates data from multiple exchanges"""
    company = Company(session=mock_session)

    # Create different data for each exchange
    sse_data = sample_source_data[sample_source_data["exchange"] == "SSE"]
    szse_data = sample_source_data[sample_source_data["exchange"] == "SZSE"]

    call_count = [0]

    def mock_fetchall(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return sse_data
        elif call_count[0] == 2:
            return szse_data
        else:
            return pd.DataFrame()

    with patch.object(company, "_fetchall", side_effect=mock_fetchall):
        with patch.object(company, "transform", side_effect=lambda x: x):
            result = company._run()

            # Should have data from multiple exchanges
            assert len(result) >= 1


# ============================================================================
# list_codes Method Tests
# ============================================================================


def test_company_list_codes_basic(mock_session, sample_source_data):
    """Test list_codes returns list of stock codes"""
    company = Company(session=mock_session, cache=True)

    # Mock the run to return sample data
    transformed = company.transform(sample_source_data)
    company.cache.set(company.params.identifier, transformed)

    codes = company.list_codes()

    assert isinstance(codes, list)
    assert len(codes) == 3
    assert "000001.SZ" in codes


def test_company_list_codes_unique(mock_session):
    """Test list_codes returns unique codes"""
    company = Company(session=mock_session, cache=True)

    # Create data with duplicates
    df = pd.DataFrame(
        {
            "stockcode": ["000001.SZ", "000001.SZ", "000002.SZ"],
        }
    )
    company.cache.set(company.params.identifier, df)

    codes = company.list_codes()

    assert len(codes) == 2  # Only unique codes


def test_company_list_codes_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_codes calls run() when data not in cache"""
    company = Company(session=mock_session)

    with patch.object(company, "run", return_value=company.transform(sample_source_data)):
        codes = company.list_codes()

        # run should have been called
        company.run.assert_called_once()
        assert len(codes) == 3


def test_company_list_codes_uses_cache(mock_session, sample_source_data):
    """Test list_codes uses cached data when available"""
    company = Company(session=mock_session, cache=True)

    transformed = company.transform(sample_source_data)
    company.cache.set(company.params.identifier, transformed)

    # Mock _fetchall to verify it's not called when cache exists
    with patch.object(company, "_fetchall") as mock_fetch:
        codes = company.list_codes()

        # _fetchall should NOT be called when cache exists
        mock_fetch.assert_not_called()
        assert len(codes) == 3


# ============================================================================
# list_names Method Tests
# ============================================================================


def test_company_list_names_basic(mock_session, sample_source_data):
    """Test list_names returns list of company names"""
    company = Company(session=mock_session, cache=True)

    transformed = company.transform(sample_source_data)
    company.cache.set(company.params.identifier, transformed)

    names = company.list_names()

    assert isinstance(names, list)
    assert len(names) == 3
    assert "平安银行股份有限公司" in names


def test_company_list_names_sorted(mock_session, sample_source_data):
    """Test list_names returns sorted list"""
    company = Company(session=mock_session, cache=True)

    transformed = company.transform(sample_source_data)
    company.cache.set(company.params.identifier, transformed)

    names = company.list_names()

    assert names == sorted(names)


def test_company_list_names_unique(mock_session):
    """Test list_names returns unique names"""
    company = Company(session=mock_session, cache=True)

    df = pd.DataFrame(
        {
            "company_name": ["平安银行", "平安银行", "万科A"],
        }
    )
    company.cache.set(company.params.identifier, df)

    names = company.list_names()

    assert len(names) == 2  # Only unique names


def test_company_list_names_calls_run_when_not_cached(mock_session, sample_source_data):
    """Test list_names calls run() when data not in cache"""
    company = Company(session=mock_session)

    with patch.object(company, "run", return_value=company.transform(sample_source_data)):
        names = company.list_names()

        company.run.assert_called_once()
        assert len(names) == 3


def test_company_list_names_uses_cache(mock_session, sample_source_data):
    """Test list_names uses cached data when available"""
    company = Company(session=mock_session, cache=True)

    transformed = company.transform(sample_source_data)
    company.cache.set(company.params.identifier, transformed)

    # Mock _fetchall to verify it's not called when cache exists
    with patch.object(company, "_fetchall") as mock_fetch:
        names = company.list_names()

        # _fetchall should NOT be called when cache exists
        mock_fetch.assert_not_called()
        assert len(names) == 3


# ============================================================================
# Integration Tests
# ============================================================================


def test_company_full_workflow(mock_session, sample_source_data):
    """Test complete workflow from initialization to data retrieval"""
    company = Company(
        session=mock_session,
        params={"exchange": "SZSE"},
        cache=True,
    )

    with patch.object(company, "_fetchall", return_value=sample_source_data):
        # Run the job
        result = company.run()

        assert not result.empty
        assert "stockcode" in result.columns

        # Get codes and names
        codes = company.list_codes()
        names = company.list_names()

        assert len(codes) > 0
        assert len(names) > 0


def test_company_multiple_exchanges_integration(mock_session, sample_source_data):
    """Test fetching data from multiple exchanges"""
    company = Company(session=mock_session, cache=True)

    with patch.object(company, "_fetchall", return_value=sample_source_data):
        result = company.run()

        # Should have data from multiple exchanges
        unique_exchanges = result["exchange"].unique()
        assert len(unique_exchanges) > 1


def test_company_cache_persistence(mock_session, sample_source_data):
    """Test that cache persists across method calls"""
    company = Company(session=mock_session, cache=True)

    with patch.object(company, "_load_cache", return_value=None) as mock_load:
        with patch.object(company, "_fetchall", return_value=sample_source_data) as mock_fetch:
            # First call - fetches data and caches it
            result1 = company.run()
            assert mock_fetch.call_count == len(EXCHANGES)  # Once per exchange
            assert mock_load.call_count == 1

            # Second call - _load_cache still returns None, so _fetchall called again
            result2 = company.run()
            assert mock_fetch.call_count == len(EXCHANGES) * 2  # Called again for each exchange
            assert mock_load.call_count == 2

            pd.testing.assert_frame_equal(result1, result2)


def test_company_params_identifier_uniqueness(mock_session):
    """Test that different params produce different cache keys"""
    company1 = Company(session=mock_session, params={"exchange": "SSE"}, cache=True)
    company2 = Company(session=mock_session, params={"exchange": "SZSE"}, cache=True)

    assert company1.params.identifier != company2.params.identifier


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_company_empty_result_handling(mock_session):
    """Test handling of empty API results"""
    company = Company(session=mock_session)

    empty_df = pd.DataFrame()
    with patch.object(company, "_fetchall", return_value=empty_df):
        result = company._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()


def test_company_large_dataset_handling(mock_session):
    """Test handling of large datasets"""
    company = Company(session=mock_session)

    # Create large dataset
    large_data = pd.DataFrame(
        {
            "ts_code": [f"{i:06d}.SZ" for i in range(5000)],
            "com_name": [f"Company {i}" for i in range(5000)],
            "com_id": [f"ID{i}" for i in range(5000)],
            "exchange": ["SZSE"] * 5000,
            "short_name": [f"C{i}" for i in range(5000)],
            "chairman": ["A"] * 5000,
            "manager": ["B"] * 5000,
            "secretary": ["C"] * 5000,
            "reg_capital": [1000.0] * 5000,
            "setup_date": ["20200101"] * 5000,
            "province": ["Test"] * 5000,
            "city": ["Test"] * 5000,
            "introduction": ["Test"] * 5000,
            "website": ["http://test.com"] * 5000,
            "email": ["test@test.com"] * 5000,
            "office": ["Test"] * 5000,
            "employees": [100] * 5000,
            "main_business": ["Test"] * 5000,
            "business_scope": ["Test"] * 5000,
        }
    )

    result = company.transform(large_data)

    assert len(result) == 5000
    assert not result.empty


def test_company_special_characters_in_data(mock_session):
    """Test handling of special characters in company data"""
    company = Company(session=mock_session)

    data = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "com_name": ["公司名称（中文）& Special <Chars>"],
            "com_id": ["123-456"],
            "exchange": ["SZSE"],
            "short_name": ["特殊@字符"],
            "chairman": ["董事长"],
            "manager": ["总经理"],
            "secretary": ["董秘"],
            "reg_capital": [1000.0],
            "setup_date": ["20200101"],
            "province": ["广东"],
            "city": ["深圳"],
            "introduction": ["公司介绍 & info"],
            "website": ["http://www.测试.com"],
            "email": ["test@test.com"],
            "office": ["办公室地址"],
            "employees": [100],
            "main_business": ["主要业务"],
            "business_scope": ["经营范围"],
        }
    )

    result = company.transform(data)

    assert len(result) == 1
    assert "特殊@字符" in result["chairman"].values[0] or "董事长" in result["chairman"].values[0]


def test_company_without_cache(mock_session, sample_source_data):
    """Test Company works correctly without cache"""
    company = Company(session=mock_session, cache=False)

    assert company.cache is None

    with patch.object(company, "_fetchall", return_value=sample_source_data):
        result = company.run()

        assert not result.empty

        # list_codes and list_names should still work
        codes = company.list_codes()
        names = company.list_names()

        assert len(codes) > 0
        assert len(names) > 0

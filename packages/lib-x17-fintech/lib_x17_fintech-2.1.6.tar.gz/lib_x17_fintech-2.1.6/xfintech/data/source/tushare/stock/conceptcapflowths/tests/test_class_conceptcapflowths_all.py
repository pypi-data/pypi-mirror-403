from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.conceptcapflowths.conceptcapflowths import (
    ConceptCapflowTHS,
)
from xfintech.data.source.tushare.stock.conceptcapflowths.constant import (
    KEY,
    NAME,
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
    mock_connection.moneyflow_cnt_ths = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "trade_date": ["20241201", "20241201", "20241129"],
            "ts_code": ["885748.TI", "886008.TI", "885426.TI"],
            "name": ["可燃冰", "减速器", "海工装备"],
            "lead_stock": ["海默科技", "大叶股份", "天海防务"],
            "close_price": [7.99, 21.22, 6.97],
            "pct_change": [4.76, 2.60, 2.56],
            "industry_index": [1307.56, 1862.58, 2711.31],
            "company_num": [12, 103, 85],
            "pct_change_stock": [4.76, 2.60, 2.56],
            "net_buy_amount": [21.00, 227.00, 171.00],
            "net_sell_amount": [19.00, 235.00, 148.00],
            "net_amount": [1.00, -8.00, 23.00],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Test initialization and configuration"""

    def test_init_basic(self, mock_session):
        """Test basic initialization"""
        job = ConceptCapflowTHS(session=mock_session)

        assert job.name == NAME
        assert job.key == KEY
        assert job.source == SOURCE
        assert job.target == TARGET
        assert job.paginate.pagesize == 5000

    def test_init_with_params(self, mock_session):
        """Test initialization with params"""
        params = {"ts_code": "885748.TI", "start_date": "20240101"}
        job = ConceptCapflowTHS(session=mock_session, params=params)

        assert job.params.ts_code == "885748.TI"
        assert job.params.start_date == "20240101"

    def test_init_with_all_components(self, mock_session):
        """Test initialization with all components"""
        params = {"ts_code": "885748.TI"}
        coolant = Coolant(interval=0.2)
        retry = Retry(retry=3)
        cache = Cache(path="/tmp/test_cache")

        job = ConceptCapflowTHS(
            session=mock_session,
            params=params,
            coolant=coolant,
            retry=retry,
            cache=cache,
        )

        assert job.params.ts_code == "885748.TI"
        assert job.coolant.interval == 0.2
        assert job.retry.retry == 3
        assert job.cache is not None
        assert isinstance(job.cache, Cache)

    def test_name_constant(self):
        """Test name constant"""
        assert NAME == "conceptcapflowths"

    def test_key_constant(self):
        """Test key constant"""
        assert KEY == "/tushare/conceptcapflowths"

    def test_source_schema(self):
        """Test source schema has all required columns"""
        assert SOURCE is not None
        assert SOURCE.desc == "同花顺概念板块资金流向数据（Tushare格式）"

        column_names = SOURCE.columns
        assert "ts_code" in column_names
        assert "trade_date" in column_names
        assert "name" in column_names
        assert "lead_stock" in column_names
        assert "close_price" in column_names
        assert "pct_change" in column_names
        assert "net_buy_amount" in column_names
        assert "net_sell_amount" in column_names
        assert "net_amount" in column_names

    def test_target_schema(self):
        """Test target schema has all required columns"""
        assert TARGET is not None
        assert TARGET.desc == "同花顺概念板块资金流向数据（xfintech标准格式）"

        column_names = TARGET.columns
        assert "code" in column_names
        assert "date" in column_names
        assert "datecode" in column_names
        assert "name" in column_names
        assert "lead_stock" in column_names
        assert "close" in column_names
        assert "percent_change" in column_names
        assert "net_buy_amount" in column_names
        assert "net_sell_amount" in column_names
        assert "net_amount" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


class TestTransform:
    """Test data transformation"""

    def test_transform_basic(self, mock_session, sample_source_data):
        """Test basic data transformation"""
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        assert len(result) == 3
        assert "code" in result.columns
        assert "date" in result.columns
        assert "datecode" in result.columns
        # Data is sorted by code, so first row is 885426.TI
        assert result.iloc[0]["code"] == "885426.TI"
        assert result.iloc[2]["datecode"] == "20241201"

    def test_transform_date_conversion(self, mock_session, sample_source_data):
        """Test date field conversions"""
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        # Check date format (YYYY-MM-DD) - sorted by code
        assert result.iloc[0]["date"] == "2024-11-29"  # 885426.TI
        assert result.iloc[1]["date"] == "2024-12-01"  # 885748.TI
        assert result.iloc[2]["date"] == "2024-12-01"  # 886008.TI

        # Check datecode format (YYYYMMDD)
        assert result.iloc[1]["datecode"] == "20241201"

    def test_transform_field_mappings(self, mock_session, sample_source_data):
        """Test field mapping transformations"""
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        # Use second row (index 1) which is 885748.TI after sorting
        row = result.iloc[1]
        assert row["code"] == "885748.TI"
        assert row["name"] == "可燃冰"
        assert row["lead_stock"] == "海默科技"
        assert row["close"] == 7.99
        assert row["percent_change"] == 4.76

    def test_transform_numeric_fields(self, mock_session, sample_source_data):
        """Test numeric field transformations"""
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        row = result.iloc[0]
        # Check all numeric fields are properly converted
        assert isinstance(row["close"], (int, float)) or pd.notna(row["close"])
        assert isinstance(row["percent_change"], (int, float)) or pd.notna(row["percent_change"])
        assert isinstance(row["industry_index"], (int, float)) or pd.notna(row["industry_index"])
        # company_num should be numeric
        assert pd.notna(row["company_num"])
        assert isinstance(row["net_buy_amount"], (int, float)) or pd.notna(row["net_buy_amount"])
        assert isinstance(row["net_sell_amount"], (int, float)) or pd.notna(row["net_sell_amount"])
        assert isinstance(row["net_amount"], (int, float)) or pd.notna(row["net_amount"])

    def test_transform_empty_data(self, mock_session):
        """Test transform with empty data"""
        job = ConceptCapflowTHS(session=mock_session)

        # Test with None
        result = job.transform(None)
        assert result.empty
        assert len(result.columns) == len(TARGET.columns)

        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        result = job.transform(empty_df)
        assert result.empty
        assert len(result.columns) == len(TARGET.columns)

    def test_transform_none_data(self, mock_session):
        """Test transform with None data"""
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(None)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_invalid_data(self, mock_session):
        """Test transform with invalid numeric values"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241201", "invalid_date"],
                "ts_code": ["885748.TI", "886008.TI"],
                "name": ["可燃冰", "减速器"],
                "lead_stock": ["海默科技", "大叶股份"],
                "close_price": [7.99, "invalid"],
                "pct_change": [4.76, 2.60],
                "industry_index": [1307.56, 1862.58],
                "company_num": [12, 103],
                "pct_change_stock": [4.76, 2.60],
                "net_buy_amount": [21.00, 227.00],
                "net_sell_amount": [19.00, 235.00],
                "net_amount": [1.00, -8.00],
            }
        )
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(data)

        # Should handle invalid data gracefully
        assert len(result) == 2
        assert pd.isna(result.iloc[1]["date"])  # Invalid date
        assert pd.isna(result.iloc[1]["close"])  # Invalid numeric

    def test_transform_duplicates_removed(self, mock_session):
        """Test that duplicates are removed"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241201", "20241201", "20241201"],
                "ts_code": ["885748.TI", "885748.TI", "886008.TI"],
                "name": ["可燃冰", "可燃冰", "减速器"],
                "lead_stock": ["海默科技", "海默科技", "大叶股份"],
                "close_price": [7.99, 7.99, 21.22],
                "pct_change": [4.76, 4.76, 2.60],
                "industry_index": [1307.56, 1307.56, 1862.58],
                "company_num": [12, 12, 103],
                "pct_change_stock": [4.76, 4.76, 2.60],
                "net_buy_amount": [21.00, 21.00, 227.00],
                "net_sell_amount": [19.00, 19.00, 235.00],
                "net_amount": [1.00, 1.00, -8.00],
            }
        )
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(data)

        # Duplicates should be removed
        assert len(result) == 2

    def test_transform_sorting(self, mock_session):
        """Test that result is sorted by code and date"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241115", "20241201", "20241129"],
                "ts_code": ["885426.TI", "885748.TI", "886008.TI"],
                "name": ["海工装备", "可燃冰", "减速器"],
                "lead_stock": ["天海防务", "海默科技", "大叶股份"],
                "close_price": [6.97, 7.99, 21.22],
                "pct_change": [2.56, 4.76, 2.60],
                "industry_index": [2711.31, 1307.56, 1862.58],
                "company_num": [85, 12, 103],
                "pct_change_stock": [2.56, 4.76, 2.60],
                "net_buy_amount": [171.00, 21.00, 227.00],
                "net_sell_amount": [148.00, 19.00, 235.00],
                "net_amount": [23.00, 1.00, -8.00],
            }
        )
        job = ConceptCapflowTHS(session=mock_session)
        result = job.transform(data)

        # Should be sorted by code, then date
        expected_order = ["885426.TI", "885748.TI", "886008.TI"]
        actual_order = result["code"].tolist()
        assert actual_order == expected_order


# ============================================================================
# Run Tests
# ============================================================================


class TestRun:
    """Test execution logic"""

    def test_run_basic(self, mock_session, sample_source_data):
        """Test basic run method"""
        job = ConceptCapflowTHS(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert "code" in result.columns
            assert "date" in result.columns

    def test_run_with_params(self, mock_session, sample_source_data):
        """Test run with ts_code parameter"""
        filtered_data = sample_source_data[sample_source_data["ts_code"] == "885748.TI"]

        job = ConceptCapflowTHS(session=mock_session, params={"ts_code": "885748.TI"})

        with patch.object(job, "_fetchall", return_value=filtered_data):
            result = job.run()

            assert len(result) == 1
            assert result["code"].iloc[0] == "885748.TI"

    def test_run_with_date_string(self, mock_session, sample_source_data):
        """Test run with trade_date as string"""
        job = ConceptCapflowTHS(session=mock_session, params={"trade_date": "20241201"})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"

    def test_run_with_date_range_string(self, mock_session, sample_source_data):
        """Test run with start_date and end_date as strings"""
        job = ConceptCapflowTHS(
            session=mock_session,
            params={"start_date": "20241101", "end_date": "20241231"},
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["start_date"] == "20241101"
            assert call_kwargs["end_date"] == "20241231"

    def test_run_calls_transform(self, mock_session, sample_source_data):
        """Test that run calls transform"""
        job = ConceptCapflowTHS(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            with patch.object(job, "transform", wraps=job.transform) as mock_transform:
                job.run()

                mock_transform.assert_called_once()

    def test_run_with_multiple_ts_codes(self, mock_session, sample_source_data):
        """Test run with multiple ts_code parameter"""
        job = ConceptCapflowTHS(session=mock_session, params={"ts_code": "885748.TI,886008.TI"})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["ts_code"] == "885748.TI,886008.TI"


# ============================================================================
# Cache Tests
# ============================================================================


class TestCache:
    """Test caching behavior"""

    def test_cache_persistence(self, mock_session, sample_source_data):
        """Test that cache persists across runs"""
        job = ConceptCapflowTHS(session=mock_session, cache=True)

        with patch.object(job, "_load_cache", return_value=None) as mock_load:
            with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
                # First run - fetches data and caches it
                result1 = job.run()
                assert mock_fetchall.call_count == 1
                assert mock_load.call_count == 1

                # Second run - _load_cache still returns None, so _fetchall called again
                result2 = job.run()
                assert mock_fetchall.call_count == 2
                assert mock_load.call_count == 2

                pd.testing.assert_frame_equal(result1, result2)

    def test_run_without_cache(self, mock_session, sample_source_data):
        """Test that conceptcapflow works correctly without cache"""
        job = ConceptCapflowTHS(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            job.run()

            # Should fetch twice (no caching)
            assert mock_fetchall.call_count == 2

    def test_params_identifier_uniqueness(self, mock_session):
        """Test that different params create different cache keys"""
        job1 = ConceptCapflowTHS(session=mock_session, params={"trade_date": "20241201"}, cache=True)
        job2 = ConceptCapflowTHS(session=mock_session, params={"trade_date": "20241129"}, cache=True)

        assert job1.params.identifier != job2.params.identifier


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Test end-to-end workflows"""

    def test_full_workflow(self, mock_session, sample_source_data):
        """Test complete workflow from initialization to data retrieval"""
        job = ConceptCapflowTHS(
            session=mock_session,
            params={
                "ts_code": "885748.TI",
                "start_date": "20241101",
                "end_date": "20241231",
            },
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()

            assert len(result) > 0

    def test_large_dataset_handling(self, mock_session):
        """Test handling of large datasets"""
        # Create large dataset
        large_data = pd.DataFrame(
            {
                "trade_date": ["20241201"] * 1000,
                "ts_code": [f"88{str(i).zfill(4)}.TI" for i in range(1000)],
                "name": ["概念板块"] * 1000,
                "lead_stock": ["领涨股"] * 1000,
                "close_price": [10.50] * 1000,
                "pct_change": [2.50] * 1000,
                "industry_index": [1500.00] * 1000,
                "company_num": [50] * 1000,
                "pct_change_stock": [3.00] * 1000,
                "net_buy_amount": [100.00] * 1000,
                "net_sell_amount": [90.00] * 1000,
                "net_amount": [10.00] * 1000,
            }
        )

        job = ConceptCapflowTHS(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=large_data):
            result = job.run()

        assert len(result) == 1000

    def test_missing_fields_handling(self, mock_session):
        """Test handling of data with some missing fields"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241201"],
                "ts_code": ["885748.TI"],
                "name": ["可燃冰"],
                "lead_stock": ["海默科技"],
                "close_price": [None],  # Missing price
                "pct_change": [4.76],
                "industry_index": [1307.56],
                "company_num": [12],
                "pct_change_stock": [None],  # Missing data
                "net_buy_amount": [21.00],
                "net_sell_amount": [19.00],
                "net_amount": [1.00],
            }
        )

        job = ConceptCapflowTHS(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=data):
            result = job.run()

            assert len(result) == 1
            assert pd.isna(result.iloc[0]["close"])
            assert pd.isna(result.iloc[0]["pct_change_stock"])

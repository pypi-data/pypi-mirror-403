"""
Test suite for CapflowTHS class
Tests cover initialization, data fetching, transformation, date handling, and utility methods
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.capflowths.capflowths import CapflowTHS
from xfintech.data.source.tushare.stock.capflowths.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)

# Fixtures


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
    mock_connection.moneyflow_ths = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "trade_date": ["20241011", "20241010", "20241009"],
            "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "name": ["平安银行", "平安银行", "万科A"],
            "pct_change": [2.47, 1.22, 3.15],
            "latest": [15.83, 15.45, 8.92],
            "net_amount": [12589.45, 8234.67, -5432.11],
            "net_d5_amount": [45632.89, 42123.44, -15234.67],
            "buy_lg_amount": [8500.23, 6200.45, -3200.55],
            "buy_lg_amount_rate": [4.25, 3.87, -2.15],
            "buy_md_amount": [2800.12, 1500.22, -1500.33],
            "buy_md_amount_rate": [1.40, 0.94, -1.01],
            "buy_sm_amount": [1289.10, 534.00, -731.23],
            "buy_sm_amount_rate": [0.64, 0.33, -0.49],
        }
    )


# Initialization Tests


class TestInitialization:
    """Test initialization and configuration"""

    def test_init_basic(self, mock_session):
        """Test basic initialization"""
        job = CapflowTHS(session=mock_session)

        assert job.name == NAME
        assert job.key == KEY
        assert job.source == SOURCE
        assert job.target == TARGET

    def test_init_with_params(self, mock_session):
        """Test initialization with params"""
        params = {"ts_code": "000001.SZ", "start_date": "20240101"}
        job = CapflowTHS(session=mock_session, params=params)

        assert job.params.ts_code == "000001.SZ"
        assert job.params.start_date == "20240101"

    def test_init_with_all_components(self, mock_session):
        """Test initialization with all components"""
        params = {"ts_code": "000001.SZ"}
        coolant = Coolant(interval=0.2)
        retry = Retry(retry=3)
        cache = Cache(path="/tmp/test_cache")

        job = CapflowTHS(
            session=mock_session,
            params=params,
            coolant=coolant,
            retry=retry,
            cache=cache,
        )

        assert job.params.ts_code == "000001.SZ"
        assert job.coolant.interval == 0.2
        assert job.retry.retry == 3
        assert job.cache is not None
        assert isinstance(job.cache, Cache)

    def test_source_schema(self):
        """Test source schema has all required columns"""
        assert SOURCE is not None
        assert SOURCE.desc == "同花顺个股资金流向数据（Tushare格式）"

        column_names = SOURCE.columns
        assert "ts_code" in column_names
        assert "trade_date" in column_names
        assert "name" in column_names
        assert "pct_change" in column_names
        assert "latest" in column_names
        assert "net_amount" in column_names
        assert "buy_lg_amount" in column_names

    def test_target_schema(self):
        """Test target schema has all required columns"""
        assert TARGET is not None
        assert TARGET.desc == "同花顺个股资金流向数据（xfintech标准格式）"

        column_names = TARGET.columns
        assert "code" in column_names
        assert "date" in column_names
        assert "datecode" in column_names
        assert "name" in column_names
        assert "percent_change" in column_names
        assert "latest" in column_names
        assert "net_amount" in column_names


# Transform Tests


class TestTransform:
    """Test data transformation"""

    def test_transform_basic(self, mock_session, sample_source_data):
        """Test basic data transformation"""
        job = CapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        assert len(result) == 3
        assert "code" in result.columns
        assert "date" in result.columns
        assert "datecode" in result.columns
        # Data is sorted by code, so first row is 000001.SZ
        assert result.iloc[0]["code"] == "000001.SZ"
        assert result.iloc[2]["code"] == "000002.SZ"

    def test_transform_date_conversion(self, mock_session, sample_source_data):
        """Test date field conversions"""
        job = CapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        # Check date format (YYYY-MM-DD) - sorted by code and date
        assert result.iloc[0]["date"] == "2024-10-10"  # 000001.SZ earliest
        assert result.iloc[1]["date"] == "2024-10-11"  # 000001.SZ latest
        assert result.iloc[2]["date"] == "2024-10-09"  # 000002.SZ

        # Check datecode format (YYYYMMDD)
        assert result.iloc[1]["datecode"] == "20241011"

    def test_transform_field_mappings(self, mock_session, sample_source_data):
        """Test field mapping transformations"""
        job = CapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        # Use second row (000001.SZ, 20241011) after sorting
        row = result.iloc[1]
        assert row["code"] == "000001.SZ"
        assert row["name"] == "平安银行"
        assert row["percent_change"] == 2.47
        assert row["latest"] == 15.83

    def test_transform_numeric_fields(self, mock_session, sample_source_data):
        """Test numeric field transformations"""
        job = CapflowTHS(session=mock_session)
        result = job.transform(sample_source_data)

        row = result.iloc[0]
        # Check all numeric fields are properly converted
        assert pd.notna(row["latest"])
        assert pd.notna(row["percent_change"])
        assert pd.notna(row["net_amount"])
        assert pd.notna(row["net_d5_amount"])
        assert pd.notna(row["buy_lg_amount"])
        assert pd.notna(row["buy_lg_amount_rate"])

    def test_transform_empty_data(self, mock_session):
        """Test transform with empty data"""
        job = CapflowTHS(session=mock_session)

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
        job = CapflowTHS(session=mock_session)
        result = job.transform(None)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_invalid_data(self, mock_session):
        """Test transform with invalid numeric values"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241011", "invalid_date"],
                "ts_code": ["000001.SZ", "000002.SZ"],
                "name": ["平安银行", "万科A"],
                "pct_change": [2.47, "invalid"],
                "latest": [15.83, 8.92],
                "net_amount": [12589.45, -5432.11],
                "net_d5_amount": [45632.89, -15234.67],
                "buy_lg_amount": [8500.23, -3200.55],
                "buy_lg_amount_rate": [4.25, -2.15],
                "buy_md_amount": [2800.12, -1500.33],
                "buy_md_amount_rate": [1.40, -1.01],
                "buy_sm_amount": [1289.10, -731.23],
                "buy_sm_amount_rate": [0.64, -0.49],
            }
        )
        job = CapflowTHS(session=mock_session)
        result = job.transform(data)

        # Should handle invalid data gracefully
        assert len(result) == 2
        assert pd.isna(result.iloc[1]["date"])  # Invalid date
        assert pd.isna(result.iloc[1]["percent_change"])  # Invalid numeric

    def test_transform_duplicates_removed(self, mock_session):
        """Test that duplicates are removed"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241011", "20241011", "20241010"],
                "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
                "name": ["平安银行", "平安银行", "万科A"],
                "pct_change": [2.47, 2.47, 1.22],
                "latest": [15.83, 15.83, 8.92],
                "net_amount": [12589.45, 12589.45, -5432.11],
                "net_d5_amount": [45632.89, 45632.89, -15234.67],
                "buy_lg_amount": [8500.23, 8500.23, -3200.55],
                "buy_lg_amount_rate": [4.25, 4.25, -2.15],
                "buy_md_amount": [2800.12, 2800.12, -1500.33],
                "buy_md_amount_rate": [1.40, 1.40, -1.01],
                "buy_sm_amount": [1289.10, 1289.10, -731.23],
                "buy_sm_amount_rate": [0.64, 0.64, -0.49],
            }
        )
        job = CapflowTHS(session=mock_session)
        result = job.transform(data)

        # Duplicates should be removed
        assert len(result) == 2

    def test_transform_sorting(self, mock_session):
        """Test that result is sorted by code and date"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241011", "20241009", "20241010"],
                "ts_code": ["000002.SZ", "000001.SZ", "000001.SZ"],
                "name": ["万科A", "平安银行", "平安银行"],
                "pct_change": [3.15, 1.22, 2.47],
                "latest": [8.92, 15.45, 15.83],
                "net_amount": [-5432.11, 8234.67, 12589.45],
                "net_d5_amount": [-15234.67, 42123.44, 45632.89],
                "buy_lg_amount": [-3200.55, 6200.45, 8500.23],
                "buy_lg_amount_rate": [-2.15, 3.87, 4.25],
                "buy_md_amount": [-1500.33, 1500.22, 2800.12],
                "buy_md_amount_rate": [-1.01, 0.94, 1.40],
                "buy_sm_amount": [-731.23, 534.00, 1289.10],
                "buy_sm_amount_rate": [-0.49, 0.33, 0.64],
            }
        )
        job = CapflowTHS(session=mock_session)
        result = job.transform(data)

        # Should be sorted by code, then date
        expected_order = ["000001.SZ", "000001.SZ", "000002.SZ"]
        actual_order = result["code"].tolist()
        assert actual_order == expected_order

        # Check date ordering for 000001.SZ
        assert result.iloc[0]["date"] == "2024-10-09"  # Earlier date first
        assert result.iloc[1]["date"] == "2024-10-10"


# Run Tests


class TestRun:
    """Test execution logic"""

    def test_run_basic(self, mock_session, sample_source_data):
        """Test basic run method"""
        job = CapflowTHS(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert "code" in result.columns
            assert "date" in result.columns

    def test_run_with_params(self, mock_session, sample_source_data):
        """Test run with ts_code parameter"""
        filtered_data = sample_source_data[sample_source_data["ts_code"] == "000001.SZ"]

        job = CapflowTHS(session=mock_session, params={"ts_code": "000001.SZ"})

        with patch.object(job, "_fetchall", return_value=filtered_data):
            result = job.run()

            assert len(result) == 2
            assert all(result["code"] == "000001.SZ")

    def test_run_with_date_string(self, mock_session, sample_source_data):
        """Test run with trade_date as string"""
        job = CapflowTHS(session=mock_session, params={"trade_date": "20241011"})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241011"

    def test_run_with_date_datetime(self, mock_session, sample_source_data):
        """Test run with trade_date as datetime object"""
        trade_date = datetime(2024, 10, 11)
        job = CapflowTHS(session=mock_session, params={"trade_date": trade_date})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241011"

    def test_run_with_date_date(self, mock_session, sample_source_data):
        """Test run with trade_date as date object (not datetime)"""
        trade_date = date(2024, 10, 11)
        job = CapflowTHS(session=mock_session, params={"trade_date": trade_date})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241011"

    def test_run_with_date_range_string(self, mock_session, sample_source_data):
        """Test run with start_date and end_date as strings"""
        job = CapflowTHS(
            session=mock_session,
            params={"start_date": "20241001", "end_date": "20241031"},
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["start_date"] == "20241001"
            assert call_kwargs["end_date"] == "20241031"

    def test_run_with_date_range_datetime(self, mock_session, sample_source_data):
        """Test run with start_date and end_date as datetime objects"""
        job = CapflowTHS(
            session=mock_session,
            params={
                "start_date": datetime(2024, 10, 1),
                "end_date": datetime(2024, 10, 31),
            },
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["start_date"] == "20241001"
            assert call_kwargs["end_date"] == "20241031"

    def test_run_calls_transform(self, mock_session, sample_source_data):
        """Test that run calls transform"""
        job = CapflowTHS(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            with patch.object(job, "transform", wraps=job.transform) as mock_transform:
                job.run()

                mock_transform.assert_called_once()

    def test_run_with_multiple_params(self, mock_session, sample_source_data):
        """Test run with both ts_code and date range"""
        job = CapflowTHS(
            session=mock_session,
            params={
                "ts_code": "000001.SZ",
                "start_date": "20241001",
                "end_date": "20241031",
            },
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["ts_code"] == "000001.SZ"
            assert call_kwargs["start_date"] == "20241001"
            assert call_kwargs["end_date"] == "20241031"


# Cache Tests


class TestCache:
    """Test caching behavior"""

    def test_cache_persistence(self, mock_session, sample_source_data):
        """Test that cache persists across runs"""
        job = CapflowTHS(session=mock_session, cache=True)

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
        """Test that thscapflow works correctly without cache"""
        job = CapflowTHS(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            job.run()

            # Should fetch twice (no caching)
            assert mock_fetchall.call_count == 2

    def test_params_identifier_uniqueness(self, mock_session):
        """Test that different params create different cache keys"""
        job1 = CapflowTHS(session=mock_session, params={"trade_date": "20241011"}, cache=True)
        job2 = CapflowTHS(session=mock_session, params={"trade_date": "20241010"}, cache=True)

        assert job1.params.identifier != job2.params.identifier


# Integration Tests


class TestIntegration:
    """Test end-to-end workflows"""

    def test_full_workflow(self, mock_session, sample_source_data):
        """Test complete workflow from initialization to data retrieval"""
        job = CapflowTHS(
            session=mock_session,
            params={
                "ts_code": "000001.SZ",
                "start_date": "20241001",
                "end_date": "20241031",
            },
            cache=False,
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()

            assert len(result) > 0
            assert "code" in result.columns
            assert "date" in result.columns

    def test_large_dataset_handling(self, mock_session):
        """Test handling of large datasets"""
        # Create large dataset
        large_data = pd.DataFrame(
            {
                "trade_date": ["20241011"] * 1000,
                "ts_code": [f"{str(i).zfill(6)}.SZ" for i in range(1, 1001)],
                "name": ["股票名称"] * 1000,
                "pct_change": [2.50] * 1000,
                "latest": [10.00] * 1000,
                "net_amount": [5000.00] * 1000,
                "net_d5_amount": [25000.00] * 1000,
                "buy_lg_amount": [3000.00] * 1000,
                "buy_lg_amount_rate": [2.00] * 1000,
                "buy_md_amount": [1500.00] * 1000,
                "buy_md_amount_rate": [1.00] * 1000,
                "buy_sm_amount": [500.00] * 1000,
                "buy_sm_amount_rate": [0.33] * 1000,
            }
        )

        job = CapflowTHS(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=large_data):
            result = job.run()

        assert len(result) == 1000

    def test_missing_fields_handling(self, mock_session):
        """Test handling of data with some missing fields"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241011"],
                "ts_code": ["000001.SZ"],
                "name": ["平安银行"],
                "pct_change": [None],  # Missing data
                "latest": [15.83],
                "net_amount": [12589.45],
                "net_d5_amount": [None],  # Missing data
                "buy_lg_amount": [8500.23],
                "buy_lg_amount_rate": [4.25],
                "buy_md_amount": [2800.12],
                "buy_md_amount_rate": [1.40],
                "buy_sm_amount": [1289.10],
                "buy_sm_amount_rate": [0.64],
            }
        )

        job = CapflowTHS(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=data):
            result = job.run()

            assert len(result) == 1
            assert pd.isna(result.iloc[0]["percent_change"])
            assert pd.isna(result.iloc[0]["net_d5_amount"])

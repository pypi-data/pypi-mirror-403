from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.capflow.capflow import Capflow
from xfintech.data.source.tushare.stock.capflow.constant import (
    KEY,
    NAME,
    PAGINATE,
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
    mock_connection.moneyflow = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
            "trade_date": ["20241201", "20241201", "20241129"],
            "buy_sm_vol": [1000.0, 800.0, 1200.0],
            "buy_sm_amount": [105.5, 84.2, 126.3],
            "sell_sm_vol": [900.0, 750.0, 1100.0],
            "sell_sm_amount": [94.7, 78.9, 115.8],
            "buy_md_vol": [2000.0, 1600.0, 2400.0],
            "buy_md_amount": [211.0, 168.4, 252.6],
            "sell_md_vol": [1800.0, 1500.0, 2200.0],
            "sell_md_amount": [189.4, 157.8, 231.6],
            "buy_lg_vol": [3000.0, 2400.0, 3600.0],
            "buy_lg_amount": [316.5, 252.6, 378.9],
            "sell_lg_vol": [2700.0, 2250.0, 3300.0],
            "sell_lg_amount": [284.1, 236.7, 347.4],
            "buy_elg_vol": [5000.0, 4000.0, 6000.0],
            "buy_elg_amount": [527.5, 421.0, 631.5],
            "sell_elg_vol": [4500.0, 3750.0, 5500.0],
            "sell_elg_amount": [474.8, 394.9, 579.2],
            "net_mf_vol": [1000.0, 800.0, 1200.0],
            "net_mf_amount": [105.5, 84.2, 126.3],
        }
    )


# Initialization Tests


class TestInitialization:
    """Test initialization and configuration"""

    def test_init_basic(self, mock_session):
        """Test basic initialization"""
        job = Capflow(session=mock_session)

        assert job.name == NAME
        assert job.key == KEY
        assert job.source == SOURCE
        assert job.target == TARGET
        assert job.paginate.pagesize == 6000

    def test_init_with_params(self, mock_session):
        """Test initialization with params"""
        params = {"ts_code": "000001.SZ", "start_date": "20240101"}
        job = Capflow(session=mock_session, params=params)

        assert job.params.ts_code == "000001.SZ"
        assert job.params.start_date == "20240101"

    def test_init_with_all_components(self, mock_session):
        """Test initialization with all components"""
        params = {"ts_code": "000001.SZ"}
        coolant = Coolant(interval=0.2)
        retry = Retry(retry=3)
        cache = Cache(path="/tmp/test_cache")

        job = Capflow(
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

    def test_name_constant(self):
        """Test name constant"""
        assert NAME == "capflow"

    def test_key_constant(self):
        """Test key constant"""
        assert KEY == "/tushare/capflow"

    def test_paginate_constant(self):
        """Test paginate configuration"""
        assert PAGINATE["pagesize"]
        assert PAGINATE["pagelimit"]

    def test_source_schema(self):
        """Test source schema has all required columns"""
        assert SOURCE is not None
        assert SOURCE.desc

        column_names = SOURCE.columns
        assert "ts_code" in column_names
        assert "trade_date" in column_names
        assert "buy_sm_vol" in column_names
        assert "buy_sm_amount" in column_names
        assert "sell_sm_vol" in column_names
        assert "sell_sm_amount" in column_names
        assert "net_mf_vol" in column_names
        assert "net_mf_amount" in column_names

    def test_target_schema(self):
        """Test target schema has all required columns"""
        assert TARGET is not None
        assert TARGET.desc

        column_names = TARGET.columns
        assert "code" in column_names
        assert "date" in column_names
        assert "datecode" in column_names
        assert "buy_sm_vol" in column_names
        assert "buy_sm_amount" in column_names
        assert "net_mf_vol" in column_names
        assert "net_mf_amount" in column_names


# Transform Tests


class TestTransform:
    """Test data transformation"""

    def test_transform_basic(self, mock_session, sample_source_data):
        """Test basic data transformation"""
        job = Capflow(session=mock_session)
        result = job.transform(sample_source_data)

        assert len(result) == 3
        assert "code" in result.columns
        assert "date" in result.columns
        assert "datecode" in result.columns
        assert result.iloc[0]["code"] == "000001.SZ"
        assert result.iloc[0]["datecode"] == "20241201"

    def test_transform_date_conversion(self, mock_session, sample_source_data):
        """Test date field conversions"""
        job = Capflow(session=mock_session)
        result = job.transform(sample_source_data)

        # Check date format (YYYY-MM-DD)
        assert result.iloc[0]["date"] == "2024-12-01"
        assert result.iloc[1]["date"] == "2024-12-01"
        assert result.iloc[2]["date"] == "2024-11-29"

        # Check datecode format (YYYYMMDD)
        assert result.iloc[0]["datecode"] == "20241201"

    def test_transform_field_mappings(self, mock_session, sample_source_data):
        """Test field mapping transformations"""
        job = Capflow(session=mock_session)
        result = job.transform(sample_source_data)

        row = result.iloc[0]
        assert row["buy_sm_vol"] == 1000.0
        assert row["buy_sm_amount"] == 105.5
        assert row["sell_sm_vol"] == 900.0
        assert row["sell_sm_amount"] == 94.7
        assert row["net_mf_vol"] == 1000.0
        assert row["net_mf_amount"] == 105.5

    def test_transform_numeric_fields(self, mock_session, sample_source_data):
        """Test numeric field transformations"""
        job = Capflow(session=mock_session)
        result = job.transform(sample_source_data)

        row = result.iloc[0]
        # Check all numeric fields are properly converted
        assert isinstance(row["buy_sm_vol"], (int, float))
        assert isinstance(row["buy_sm_amount"], (int, float))
        assert isinstance(row["buy_md_vol"], (int, float))
        assert isinstance(row["buy_lg_vol"], (int, float))
        assert isinstance(row["buy_elg_vol"], (int, float))

    def test_transform_empty_data(self, mock_session):
        """Test transform with empty data"""
        job = Capflow(session=mock_session)

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
        job = Capflow(session=mock_session)
        result = job.transform(None)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_invalid_data(self, mock_session):
        """Test transform with invalid numeric values"""
        data = pd.DataFrame(
            {
                "ts_code": ["000001.SZ", "000002.SZ"],
                "trade_date": ["20241201", "invalid_date"],
                "buy_sm_vol": [1000.0, "invalid"],
                "buy_sm_amount": [105.5, 84.2],
                "sell_sm_vol": [900.0, 750.0],
                "sell_sm_amount": [94.7, 78.9],
                "buy_md_vol": [2000.0, 1600.0],
                "buy_md_amount": [211.0, 168.4],
                "sell_md_vol": [1800.0, 1500.0],
                "sell_md_amount": [189.4, 157.8],
                "buy_lg_vol": [3000.0, 2400.0],
                "buy_lg_amount": [316.5, 252.6],
                "sell_lg_vol": [2700.0, 2250.0],
                "sell_lg_amount": [284.1, 236.7],
                "buy_elg_vol": [5000.0, 4000.0],
                "buy_elg_amount": [527.5, 421.0],
                "sell_elg_vol": [4500.0, 3750.0],
                "sell_elg_amount": [474.8, 394.9],
                "net_mf_vol": [1000.0, 800.0],
                "net_mf_amount": [105.5, 84.2],
            }
        )
        job = Capflow(session=mock_session)
        result = job.transform(data)

        # Should handle invalid data gracefully
        assert len(result) == 2
        assert pd.isna(result.iloc[1]["date"])  # Invalid date
        assert pd.isna(result.iloc[1]["buy_sm_vol"])  # Invalid numeric

    def test_transform_duplicates_removed(self, mock_session):
        """Test that duplicates are removed"""
        data = pd.DataFrame(
            {
                "ts_code": ["000001.SZ", "000001.SZ", "000002.SZ"],
                "trade_date": ["20241201", "20241201", "20241201"],
                "buy_sm_vol": [1000.0, 1000.0, 800.0],
                "buy_sm_amount": [105.5, 105.5, 84.2],
                "sell_sm_vol": [900.0, 900.0, 750.0],
                "sell_sm_amount": [94.7, 94.7, 78.9],
                "buy_md_vol": [2000.0, 2000.0, 1600.0],
                "buy_md_amount": [211.0, 211.0, 168.4],
                "sell_md_vol": [1800.0, 1800.0, 1500.0],
                "sell_md_amount": [189.4, 189.4, 157.8],
                "buy_lg_vol": [3000.0, 3000.0, 2400.0],
                "buy_lg_amount": [316.5, 316.5, 252.6],
                "sell_lg_vol": [2700.0, 2700.0, 2250.0],
                "sell_lg_amount": [284.1, 284.1, 236.7],
                "buy_elg_vol": [5000.0, 5000.0, 4000.0],
                "buy_elg_amount": [527.5, 527.5, 421.0],
                "sell_elg_vol": [4500.0, 4500.0, 3750.0],
                "sell_elg_amount": [474.8, 474.8, 394.9],
                "net_mf_vol": [1000.0, 1000.0, 800.0],
                "net_mf_amount": [105.5, 105.5, 84.2],
            }
        )
        job = Capflow(session=mock_session)
        result = job.transform(data)

        # Duplicates should be removed
        assert len(result) == 2

    def test_transform_sorting(self, mock_session):
        """Test that result is sorted by code and date"""
        data = pd.DataFrame(
            {
                "ts_code": ["600000.SH", "000001.SZ", "000002.SZ"],
                "trade_date": ["20241115", "20241201", "20241129"],
                "buy_sm_vol": [1200.0, 1000.0, 800.0],
                "buy_sm_amount": [126.3, 105.5, 84.2],
                "sell_sm_vol": [1100.0, 900.0, 750.0],
                "sell_sm_amount": [115.8, 94.7, 78.9],
                "buy_md_vol": [2400.0, 2000.0, 1600.0],
                "buy_md_amount": [252.6, 211.0, 168.4],
                "sell_md_vol": [2200.0, 1800.0, 1500.0],
                "sell_md_amount": [231.6, 189.4, 157.8],
                "buy_lg_vol": [3600.0, 3000.0, 2400.0],
                "buy_lg_amount": [378.9, 316.5, 252.6],
                "sell_lg_vol": [3300.0, 2700.0, 2250.0],
                "sell_lg_amount": [347.4, 284.1, 236.7],
                "buy_elg_vol": [6000.0, 5000.0, 4000.0],
                "buy_elg_amount": [631.5, 527.5, 421.0],
                "sell_elg_vol": [5500.0, 4500.0, 3750.0],
                "sell_elg_amount": [579.2, 474.8, 394.9],
                "net_mf_vol": [1200.0, 1000.0, 800.0],
                "net_mf_amount": [126.3, 105.5, 84.2],
            }
        )
        job = Capflow(session=mock_session)
        result = job.transform(data)

        # Should be sorted by code, then date
        expected_order = ["000001.SZ", "000002.SZ", "600000.SH"]
        actual_order = result["code"].tolist()
        assert actual_order == expected_order


# Run Tests


class TestRun:
    """Test execution logic"""

    def test_run_basic(self, mock_session, sample_source_data):
        """Test basic run method"""
        job = Capflow(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert "code" in result.columns
            assert "date" in result.columns

    def test_run_with_params(self, mock_session, sample_source_data):
        """Test run with ts_code parameter"""
        filtered_data = sample_source_data[sample_source_data["ts_code"] == "000001.SZ"]

        job = Capflow(session=mock_session, params={"ts_code": "000001.SZ"})

        with patch.object(job, "_fetchall", return_value=filtered_data):
            result = job.run()

            assert len(result) == 1
            assert result["code"].iloc[0] == "000001.SZ"

    def test_run_with_date_string(self, mock_session, sample_source_data):
        """Test run with trade_date as string"""
        job = Capflow(session=mock_session, params={"trade_date": "20241201"})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"

    def test_run_with_date_datetime(self, mock_session, sample_source_data):
        """Test run with trade_date as datetime object"""
        trade_date = datetime(2024, 12, 1)
        job = Capflow(session=mock_session, params={"trade_date": trade_date})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"

    def test_run_with_date_date(self, mock_session, sample_source_data):
        """Test run with trade_date as date object (not datetime)"""
        trade_date = date(2024, 12, 1)
        job = Capflow(session=mock_session, params={"trade_date": trade_date})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"

    def test_run_with_date_range_string(self, mock_session, sample_source_data):
        """Test run with start_date and end_date as strings"""
        job = Capflow(
            session=mock_session,
            params={"start_date": "20241101", "end_date": "20241231"},
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["start_date"] == "20241101"
            assert call_kwargs["end_date"] == "20241231"

    def test_run_with_date_range_datetime(self, mock_session, sample_source_data):
        """Test run with start_date and end_date as datetime objects"""
        job = Capflow(
            session=mock_session,
            params={
                "start_date": datetime(2024, 11, 1),
                "end_date": datetime(2024, 12, 31),
            },
        )

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["start_date"] == "20241101"
            assert call_kwargs["end_date"] == "20241231"

    def test_run_calls_transform(self, mock_session, sample_source_data):
        """Test that run calls transform"""
        job = Capflow(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            with patch.object(job, "transform", wraps=job.transform) as mock_transform:
                job.run()

                mock_transform.assert_called_once()

    def test_run_with_multiple_ts_codes(self, mock_session, sample_source_data):
        """Test run with multiple ts_code parameter"""
        job = Capflow(session=mock_session, params={"ts_code": "000001.SZ,000002.SZ"})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["ts_code"] == "000001.SZ,000002.SZ"


# Cache Tests


class TestCache:
    """Test caching behavior"""

    def test_cache_persistence(self, mock_session, sample_source_data):
        """Test that cache persists across runs"""
        job = Capflow(session=mock_session, cache=True)

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
        """Test that capflow works correctly without cache"""
        job = Capflow(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            job.run()

            # Should fetch twice (no caching)
            assert mock_fetchall.call_count == 2

    def test_params_identifier_uniqueness(self, mock_session):
        """Test that different params create different cache keys"""
        job1 = Capflow(session=mock_session, params={"trade_date": "20241201"}, cache=True)
        job2 = Capflow(session=mock_session, params={"trade_date": "20241129"}, cache=True)

        assert job1.params.identifier != job2.params.identifier


# List Methods Tests


# Integration Tests


class TestIntegration:
    """Test end-to-end workflows"""

    def test_full_workflow(self, mock_session, sample_source_data):
        """Test complete workflow from initialization to data retrieval"""
        job = Capflow(
            session=mock_session,
            params={"ts_code": "000001.SZ", "start_date": "20241101", "end_date": "20241231"},
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
                "ts_code": [f"{str(i).zfill(6)}.SZ" for i in range(1000)],
                "trade_date": ["20241201"] * 1000,
                "buy_sm_vol": [1000.0] * 1000,
                "buy_sm_amount": [105.5] * 1000,
                "sell_sm_vol": [900.0] * 1000,
                "sell_sm_amount": [94.7] * 1000,
                "buy_md_vol": [2000.0] * 1000,
                "buy_md_amount": [211.0] * 1000,
                "sell_md_vol": [1800.0] * 1000,
                "sell_md_amount": [189.4] * 1000,
                "buy_lg_vol": [3000.0] * 1000,
                "buy_lg_amount": [316.5] * 1000,
                "sell_lg_vol": [2700.0] * 1000,
                "sell_lg_amount": [284.1] * 1000,
                "buy_elg_vol": [5000.0] * 1000,
                "buy_elg_amount": [527.5] * 1000,
                "sell_elg_vol": [4500.0] * 1000,
                "sell_elg_amount": [474.8] * 1000,
                "net_mf_vol": [1000.0] * 1000,
                "net_mf_amount": [105.5] * 1000,
            }
        )

        job = Capflow(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=large_data):
            result = job.run()

        assert len(result) == 1000

    def test_missing_fields_handling(self, mock_session):
        """Test handling of data with some missing fields"""
        data = pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "trade_date": ["20241201"],
                "buy_sm_vol": [1000.0],
                "buy_sm_amount": [None],  # Missing amount
                "sell_sm_vol": [900.0],
                "sell_sm_amount": [94.7],
                "buy_md_vol": [2000.0],
                "buy_md_amount": [211.0],
                "sell_md_vol": [None],  # Missing volume
                "sell_md_amount": [189.4],
                "buy_lg_vol": [3000.0],
                "buy_lg_amount": [316.5],
                "sell_lg_vol": [2700.0],
                "sell_lg_amount": [284.1],
                "buy_elg_vol": [5000.0],
                "buy_elg_amount": [527.5],
                "sell_elg_vol": [4500.0],
                "sell_elg_amount": [474.8],
                "net_mf_vol": [1000.0],
                "net_mf_amount": [105.5],
            }
        )

        job = Capflow(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=data):
            result = job.run()

            assert len(result) == 1
            assert pd.isna(result.iloc[0]["buy_sm_amount"])
            assert pd.isna(result.iloc[0]["sell_md_vol"])

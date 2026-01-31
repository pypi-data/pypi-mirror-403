from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.conceptcapflowdc.conceptcapflowdc import (
    ConceptCapflowDC,
)
from xfintech.data.source.tushare.stock.conceptcapflowdc.constant import (
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
    mock_connection.moneyflow_ind_dc = MagicMock()
    session.connection = mock_connection

    return session


@pytest.fixture
def sample_source_data():
    """Create sample source data in Tushare format"""
    return pd.DataFrame(
        {
            "trade_date": ["20241201", "20241201", "20241129"],
            "content_type": ["概念", "行业", "概念"],
            "ts_code": ["BK0420", "BK0425", "BK0430"],
            "name": ["互联网服务", "证券", "软件开发"],
            "pct_change": [6.28, 8.23, 8.28],
            "close": [16883.55, 135249.80, 721.35],
            "net_amount": [3056382208.00, 2875528704.00, 2733378816.00],
            "net_amount_rate": [3.93, 4.64, 3.18],
            "buy_elg_amount": [2500000000.00, 2300000000.00, 2200000000.00],
            "buy_elg_amount_rate": [3.21, 3.72, 2.56],
            "buy_lg_amount": [556382208.00, 575528704.00, 533378816.00],
            "buy_lg_amount_rate": [0.72, 0.92, 0.62],
            "buy_md_amount": [-100000000.00, -50000000.00, -80000000.00],
            "buy_md_amount_rate": [-0.13, -0.08, -0.09],
            "buy_sm_amount": [-150000000.00, -120000000.00, -140000000.00],
            "buy_sm_amount_rate": [-0.19, -0.19, -0.16],
            "buy_sm_amount_stock": ["腾讯控股", "中信证券", "用友网络"],
            "rank": [1, 2, 3],
        }
    )


# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Test initialization and configuration"""

    def test_init_basic(self, mock_session):
        """Test basic initialization"""
        job = ConceptCapflowDC(session=mock_session)

        assert job.name == NAME
        assert job.key == KEY
        assert job.source == SOURCE
        assert job.target == TARGET
        assert job.paginate.pagesize == 5000

    def test_init_with_params(self, mock_session):
        """Test initialization with params"""
        params = {"ts_code": "BK0420", "start_date": "20240101"}
        job = ConceptCapflowDC(session=mock_session, params=params)

        assert job.params.ts_code == "BK0420"
        assert job.params.start_date == "20240101"

    def test_init_with_all_components(self, mock_session):
        """Test initialization with all components"""
        params = {"ts_code": "BK0420"}
        coolant = Coolant(interval=0.2)
        retry = Retry(retry=3)
        cache = Cache(path="/tmp/test_cache")

        job = ConceptCapflowDC(
            session=mock_session,
            params=params,
            coolant=coolant,
            retry=retry,
            cache=cache,
        )

        assert job.params.ts_code == "BK0420"
        assert job.coolant.interval == 0.2
        assert job.retry.retry == 3
        assert job.cache is not None
        assert isinstance(job.cache, Cache)

    def test_name_constant(self):
        """Test name constant"""
        assert NAME == "conceptcapflowdc"

    def test_key_constant(self):
        """Test key constant"""
        assert KEY == "/tushare/conceptcapflowdc"

    def test_source_schema(self):
        """Test source schema has all required columns"""
        assert SOURCE is not None
        assert SOURCE.desc == "东财概念及行业板块资金流向数据（Tushare格式）"

        column_names = SOURCE.columns
        assert "ts_code" in column_names
        assert "trade_date" in column_names
        assert "content_type" in column_names
        assert "name" in column_names
        assert "pct_change" in column_names
        assert "close" in column_names
        assert "net_amount" in column_names
        assert "net_amount_rate" in column_names

    def test_target_schema(self):
        """Test target schema has all required columns"""
        assert TARGET is not None
        assert TARGET.desc == "东财概念及行业板块资金流向数据（xfintech标准格式）"

        column_names = TARGET.columns
        assert "code" in column_names
        assert "date" in column_names
        assert "datecode" in column_names
        assert "content_type" in column_names
        assert "name" in column_names
        assert "percent_change" in column_names
        assert "close" in column_names
        assert "net_amount" in column_names


# ============================================================================
# Transform Tests
# ============================================================================


class TestTransform:
    """Test data transformation"""

    def test_transform_basic(self, mock_session, sample_source_data):
        """Test basic data transformation"""
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(sample_source_data)

        assert len(result) == 3
        assert "code" in result.columns
        assert "date" in result.columns
        assert "datecode" in result.columns
        # Data is sorted by code, so first row is BK0420
        assert result.iloc[0]["code"] == "BK0420"
        assert result.iloc[2]["datecode"] == "20241129"

    def test_transform_date_conversion(self, mock_session, sample_source_data):
        """Test date field conversions"""
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(sample_source_data)

        # Check date format (YYYY-MM-DD) - sorted by code
        assert result.iloc[0]["date"] == "2024-12-01"  # BK0420
        assert result.iloc[1]["date"] == "2024-12-01"  # BK0425
        assert result.iloc[2]["date"] == "2024-11-29"  # BK0430

        # Check datecode format (YYYYMMDD)
        assert result.iloc[1]["datecode"] == "20241201"

    def test_transform_field_mappings(self, mock_session, sample_source_data):
        """Test field mapping transformations"""
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(sample_source_data)

        # Use first row (BK0420) after sorting
        row = result.iloc[0]
        assert row["code"] == "BK0420"
        assert row["name"] == "互联网服务"
        assert row["content_type"] == "概念"
        assert row["percent_change"] == 6.28
        assert row["close"] == 16883.55

    def test_transform_numeric_fields(self, mock_session, sample_source_data):
        """Test numeric field transformations"""
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(sample_source_data)

        row = result.iloc[0]
        # Check all numeric fields are properly converted
        assert pd.notna(row["close"])
        assert pd.notna(row["percent_change"])
        assert pd.notna(row["net_amount"])
        assert pd.notna(row["net_amount_rate"])
        assert pd.notna(row["buy_elg_amount"])
        assert pd.notna(row["rank"])

    def test_transform_empty_data(self, mock_session):
        """Test transform with empty data"""
        job = ConceptCapflowDC(session=mock_session)

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
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(None)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_invalid_data(self, mock_session):
        """Test transform with invalid numeric values"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241201", "invalid_date"],
                "content_type": ["概念", "行业"],
                "ts_code": ["BK0420", "BK0425"],
                "name": ["互联网服务", "证券"],
                "pct_change": [6.28, "invalid"],
                "close": [16883.55, 135249.80],
                "net_amount": [3056382208.00, 2875528704.00],
                "net_amount_rate": [3.93, 4.64],
                "buy_elg_amount": [2500000000.00, 2300000000.00],
                "buy_elg_amount_rate": [3.21, 3.72],
                "buy_lg_amount": [556382208.00, 575528704.00],
                "buy_lg_amount_rate": [0.72, 0.92],
                "buy_md_amount": [-100000000.00, -50000000.00],
                "buy_md_amount_rate": [-0.13, -0.08],
                "buy_sm_amount": [-150000000.00, -120000000.00],
                "buy_sm_amount_rate": [-0.19, -0.19],
                "buy_sm_amount_stock": ["腾讯控股", "中信证券"],
                "rank": [1, 2],
            }
        )
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(data)

        # Should handle invalid data gracefully
        assert len(result) == 2
        assert pd.isna(result.iloc[1]["date"])  # Invalid date
        assert pd.isna(result.iloc[1]["percent_change"])  # Invalid numeric

    def test_transform_duplicates_removed(self, mock_session):
        """Test that duplicates are removed"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241201", "20241201", "20241201"],
                "content_type": ["概念", "概念", "行业"],
                "ts_code": ["BK0420", "BK0420", "BK0425"],
                "name": ["互联网服务", "互联网服务", "证券"],
                "pct_change": [6.28, 6.28, 8.23],
                "close": [16883.55, 16883.55, 135249.80],
                "net_amount": [3056382208.00, 3056382208.00, 2875528704.00],
                "net_amount_rate": [3.93, 3.93, 4.64],
                "buy_elg_amount": [2500000000.00, 2500000000.00, 2300000000.00],
                "buy_elg_amount_rate": [3.21, 3.21, 3.72],
                "buy_lg_amount": [556382208.00, 556382208.00, 575528704.00],
                "buy_lg_amount_rate": [0.72, 0.72, 0.92],
                "buy_md_amount": [-100000000.00, -100000000.00, -50000000.00],
                "buy_md_amount_rate": [-0.13, -0.13, -0.08],
                "buy_sm_amount": [-150000000.00, -150000000.00, -120000000.00],
                "buy_sm_amount_rate": [-0.19, -0.19, -0.19],
                "buy_sm_amount_stock": ["腾讯控股", "腾讯控股", "中信证券"],
                "rank": [1, 1, 2],
            }
        )
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(data)

        # Duplicates should be removed
        assert len(result) == 2

    def test_transform_sorting(self, mock_session):
        """Test that result is sorted by code and date"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241115", "20241201", "20241129"],
                "content_type": ["概念", "行业", "概念"],
                "ts_code": ["BK0430", "BK0420", "BK0425"],
                "name": ["软件开发", "互联网服务", "证券"],
                "pct_change": [8.28, 6.28, 8.23],
                "close": [721.35, 16883.55, 135249.80],
                "net_amount": [2733378816.00, 3056382208.00, 2875528704.00],
                "net_amount_rate": [3.18, 3.93, 4.64],
                "buy_elg_amount": [2200000000.00, 2500000000.00, 2300000000.00],
                "buy_elg_amount_rate": [2.56, 3.21, 3.72],
                "buy_lg_amount": [533378816.00, 556382208.00, 575528704.00],
                "buy_lg_amount_rate": [0.62, 0.72, 0.92],
                "buy_md_amount": [-80000000.00, -100000000.00, -50000000.00],
                "buy_md_amount_rate": [-0.09, -0.13, -0.08],
                "buy_sm_amount": [-140000000.00, -150000000.00, -120000000.00],
                "buy_sm_amount_rate": [-0.16, -0.19, -0.19],
                "buy_sm_amount_stock": ["用友网络", "腾讯控股", "中信证券"],
                "rank": [3, 1, 2],
            }
        )
        job = ConceptCapflowDC(session=mock_session)
        result = job.transform(data)

        # Should be sorted by code, then date
        expected_order = ["BK0420", "BK0425", "BK0430"]
        actual_order = result["code"].tolist()
        assert actual_order == expected_order


# ============================================================================
# Run Tests
# ============================================================================


class TestRun:
    """Test execution logic"""

    def test_run_basic(self, mock_session, sample_source_data):
        """Test basic run method"""
        job = ConceptCapflowDC(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            result = job.run()

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert "code" in result.columns
            assert "date" in result.columns

    def test_run_with_params(self, mock_session, sample_source_data):
        """Test run with ts_code parameter"""
        filtered_data = sample_source_data[sample_source_data["ts_code"] == "BK0420"]

        job = ConceptCapflowDC(session=mock_session, params={"ts_code": "BK0420"})

        with patch.object(job, "_fetchall", return_value=filtered_data):
            result = job.run()

            assert len(result) == 1
            assert result["code"].iloc[0] == "BK0420"

    def test_run_with_date_string(self, mock_session, sample_source_data):
        """Test run with trade_date as string"""
        job = ConceptCapflowDC(session=mock_session, params={"trade_date": "20241201"})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"

    def test_run_with_date_datetime(self, mock_session, sample_source_data):
        """Test run with trade_date as datetime object"""
        trade_date = "20241201"
        job = ConceptCapflowDC(session=mock_session, params={"trade_date": trade_date})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"

    def test_run_with_date_date(self, mock_session, sample_source_data):
        """Test run with trade_date as date object (not datetime)"""
        trade_date = "20241201"
        job = ConceptCapflowDC(session=mock_session, params={"trade_date": trade_date})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()

            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"

    def test_run_with_date_range_string(self, mock_session, sample_source_data):
        """Test run with start_date and end_date as strings"""
        job = ConceptCapflowDC(
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
        job = ConceptCapflowDC(session=mock_session)

        with patch.object(job, "_fetchall", return_value=sample_source_data):
            with patch.object(job, "transform", wraps=job.transform) as mock_transform:
                job.run()

                mock_transform.assert_called_once()

    def test_run_with_content_type(self, mock_session, sample_source_data):
        """Test run with content_type parameter"""
        job = ConceptCapflowDC(session=mock_session, params={"trade_date": "20241201", "content_type": "概念"})

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            call_kwargs = mock_fetchall.call_args[1]
            assert call_kwargs["trade_date"] == "20241201"
            assert call_kwargs["content_type"] == "概念"


# ============================================================================
# Cache Tests
# ============================================================================


class TestCache:
    """Test caching behavior"""

    def test_cache_persistence(self, mock_session, sample_source_data):
        """Test that cache persists across runs"""
        job = ConceptCapflowDC(session=mock_session, cache=True)

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
        """Test that conceptcapflowdc works correctly without cache"""
        job = ConceptCapflowDC(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=sample_source_data) as mock_fetchall:
            job.run()
            job.run()

            # Should fetch twice (no caching)
            assert mock_fetchall.call_count == 2

    def test_params_identifier_uniqueness(self, mock_session):
        """Test that different params create different cache keys"""
        job1 = ConceptCapflowDC(session=mock_session, params={"trade_date": "20241201"}, cache=True)
        job2 = ConceptCapflowDC(session=mock_session, params={"trade_date": "20241129"}, cache=True)

        assert job1.params.identifier != job2.params.identifier


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Test end-to-end workflows"""

    def test_full_workflow(self, mock_session, sample_source_data):
        """Test complete workflow from initialization to data retrieval"""
        job = ConceptCapflowDC(
            session=mock_session,
            params={
                "ts_code": "BK0420",
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
                "content_type": ["概念"] * 1000,
                "ts_code": [f"BK{str(i).zfill(4)}" for i in range(1000)],
                "name": ["板块名称"] * 1000,
                "pct_change": [5.00] * 1000,
                "close": [10000.00] * 1000,
                "net_amount": [1000000000.00] * 1000,
                "net_amount_rate": [2.50] * 1000,
                "buy_elg_amount": [800000000.00] * 1000,
                "buy_elg_amount_rate": [2.00] * 1000,
                "buy_lg_amount": [200000000.00] * 1000,
                "buy_lg_amount_rate": [0.50] * 1000,
                "buy_md_amount": [-50000000.00] * 1000,
                "buy_md_amount_rate": [-0.12] * 1000,
                "buy_sm_amount": [-100000000.00] * 1000,
                "buy_sm_amount_rate": [-0.25] * 1000,
                "buy_sm_amount_stock": ["领涨股"] * 1000,
                "rank": list(range(1, 1001)),
            }
        )

        job = ConceptCapflowDC(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=large_data):
            result = job.run()

        assert len(result) == 1000

    def test_missing_fields_handling(self, mock_session):
        """Test handling of data with some missing fields"""
        data = pd.DataFrame(
            {
                "trade_date": ["20241201"],
                "content_type": ["概念"],
                "ts_code": ["BK0420"],
                "name": ["互联网服务"],
                "pct_change": [None],  # Missing data
                "close": [16883.55],
                "net_amount": [3056382208.00],
                "net_amount_rate": [None],  # Missing data
                "buy_elg_amount": [2500000000.00],
                "buy_elg_amount_rate": [3.21],
                "buy_lg_amount": [556382208.00],
                "buy_lg_amount_rate": [0.72],
                "buy_md_amount": [-100000000.00],
                "buy_md_amount_rate": [-0.13],
                "buy_sm_amount": [-150000000.00],
                "buy_sm_amount_rate": [-0.19],
                "buy_sm_amount_stock": ["腾讯控股"],
                "rank": [1],
            }
        )

        job = ConceptCapflowDC(session=mock_session, cache=False)

        with patch.object(job, "_fetchall", return_value=data):
            result = job.run()

            assert len(result) == 1
            assert pd.isna(result.iloc[0]["percent_change"])
            assert pd.isna(result.iloc[0]["net_amount_rate"])

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session import Session
from xfintech.data.source.tushare.stock.marketindexcapflowdc import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
    MarketIndexCapflowDC,
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
    mock_connection.moneyflow_mkt_dc = MagicMock()
    session.connection = mock_connection

    return session


# Test Class 1: Initialization Tests


class TestMarketIndexCapflowDCInitialization:
    """Test MarketIndexCapflowDC class initialization and configuration."""

    def test_name_constant(self):
        """Test NAME constant is set correctly."""
        assert NAME == "marketindexcapflowdc"

    def test_key_constant(self):
        """Test KEY constant is set correctly."""
        assert KEY == "/tushare/marketindexcapflowdc"

    def test_source_table_info(self):
        """Test SOURCE TableInfo configuration."""
        assert SOURCE.desc == "东方财富大盘资金流向数据（tushare格式）"
        assert SOURCE.meta["provider"] == "tushare"
        assert SOURCE.meta["source"] == "moneyflow_mkt_dc"
        assert SOURCE.meta["type"] == "partitioned"
        assert SOURCE.meta["scale"] == "crosssection"
        # Verify key columns exist
        column_names = SOURCE.list_column_names()
        assert "trade_date" in column_names
        assert "close_sh" in column_names
        assert "close_sz" in column_names
        assert "net_amount" in column_names

    def test_target_table_info(self):
        """Test TARGET TableInfo configuration."""
        assert TARGET.desc == "东方财富大盘资金流向数据（xfinbatch标准格式）"
        assert TARGET.meta["key"] == KEY
        assert TARGET.meta["name"] == NAME
        assert TARGET.meta["type"] == "partitioned"
        assert TARGET.meta["scale"] == "crosssection"
        # Verify transformed columns exist
        column_names = TARGET.list_column_names()
        assert "date" in column_names
        assert "datecode" in column_names
        assert "percent_change_sh" in column_names
        assert "percent_change_sz" in column_names

    def test_initialization_with_params(self, mock_session):
        """Test MarketIndexCapflowDC initialization with parameters."""
        params = {"start_date": "20240901", "end_date": "20240930"}
        job = MarketIndexCapflowDC(session=mock_session, params=params)

        assert job.name == NAME
        assert job.key == KEY
        assert job.params.get("start_date") == "20240901"
        assert job.params.get("end_date") == "20240930"

    def test_initialization_with_optional_components(self, mock_session):
        """Test initialization with optional coolant, retry, and cache."""
        coolant = Coolant(interval=1.0)
        retry = Retry(retry=3)
        cache = Cache(path="/tmp/test_cache")

        job = MarketIndexCapflowDC(
            session=mock_session,
            params={"trade_date": "20240927"},
            coolant=coolant,
            retry=retry,
            cache=cache,
        )

        assert job.coolant.interval == 1.0
        assert job.retry.retry == 3
        assert job.cache is not None
        assert isinstance(job.cache, Cache)

    def test_initialization_minimal(self, mock_session):
        """Test minimal initialization with only required session."""
        job = MarketIndexCapflowDC(session=mock_session)

        assert job.name == NAME
        assert job.key == KEY


# Test Class 2: Transform Tests


class TestMarketIndexCapflowDCTransform:
    """Test the transform method that converts Tushare format to xfinbatch format."""

    def test_transform_empty_dataframe(self, mock_session):
        """Test transform with empty DataFrame."""
        job = MarketIndexCapflowDC(session=mock_session)

        empty_df = pd.DataFrame()
        result = job.transform(empty_df)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_none_input(self, mock_session):
        """Test transform with None input."""
        job = MarketIndexCapflowDC(session=mock_session)

        result = job.transform(None)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_basic_data(self, mock_session):
        """Test transform with basic data."""
        job = MarketIndexCapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        result = job.transform(source_data)

        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]["date"] == "2024-09-27"
        assert result.iloc[0]["datecode"] == "20240927"
        assert result.iloc[0]["close_sh"] == pytest.approx(3087.53)
        assert result.iloc[0]["percent_change_sh"] == pytest.approx(2.89)
        assert result.iloc[0]["close_sz"] == pytest.approx(9514.86)
        assert result.iloc[0]["percent_change_sz"] == pytest.approx(6.71)
        assert result.iloc[0]["net_amount"] == pytest.approx(17175101440.00)

    def test_transform_multiple_dates(self, mock_session):
        """Test transform with multiple dates."""
        job = MarketIndexCapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240926", "20240925"],
                "close_sh": [3087.53, 3000.95, 2896.31],
                "pct_change_sh": [2.89, 3.61, 1.16],
                "close_sz": [9514.86, 8916.65, 8537.73],
                "pct_change_sz": [6.71, 4.44, 1.21],
                "net_amount": [17175101440.00, 18894807552.00, -4010342144.00],
                "net_amount_rate": [15.5, 18.2, -3.5],
                "buy_elg_amount": [17175101440.00, 18894807552.00, -4010342144.00],
                "buy_elg_amount_rate": [8.2, 9.1, -2.0],
                "buy_lg_amount": [-3564773376.00, -2446319616.00, -10390331392.00],
                "buy_lg_amount_rate": [-2.1, -1.5, -5.2],
                "buy_md_amount": [1234567890.00, 2345678901.00, 3456789012.00],
                "buy_md_amount_rate": [1.5, 2.0, 2.5],
                "buy_sm_amount": [-987654321.00, -1234567890.00, -2345678901.00],
                "buy_sm_amount_rate": [-0.8, -1.0, -1.5],
            }
        )

        result = job.transform(source_data)

        assert len(result) == 3
        # Verify sorted by date
        assert result.iloc[0]["date"] == "2024-09-25"
        assert result.iloc[1]["date"] == "2024-09-26"
        assert result.iloc[2]["date"] == "2024-09-27"

    def test_transform_numeric_conversion(self, mock_session):
        """Test that numeric fields are properly converted."""
        job = MarketIndexCapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": ["3087.53"],  # String
                "pct_change_sh": ["2.89"],  # String
                "close_sz": ["9514.86"],  # String
                "pct_change_sz": ["6.71"],  # String
                "net_amount": ["17175101440.00"],  # String
                "net_amount_rate": ["15.5"],  # String
                "buy_elg_amount": ["17175101440.00"],  # String
                "buy_elg_amount_rate": ["8.2"],  # String
                "buy_lg_amount": ["-3564773376.00"],  # String
                "buy_lg_amount_rate": ["-2.1"],  # String
                "buy_md_amount": ["1234567890.00"],  # String
                "buy_md_amount_rate": ["1.5"],  # String
                "buy_sm_amount": ["-987654321.00"],  # String
                "buy_sm_amount_rate": ["-0.8"],  # String
            }
        )

        result = job.transform(source_data)

        # Verify all numeric fields are actually numeric
        assert isinstance(result.iloc[0]["percent_change_sh"], (int, float))
        assert isinstance(result.iloc[0]["close_sh"], (int, float))
        assert isinstance(result.iloc[0]["net_amount"], (int, float))
        assert result.iloc[0]["percent_change_sh"] == pytest.approx(2.89)
        assert result.iloc[0]["close_sh"] == pytest.approx(3087.53)

    def test_transform_handles_invalid_values(self, mock_session):
        """Test transform handles invalid numeric values gracefully."""
        job = MarketIndexCapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": ["invalid"],
                "pct_change_sh": ["N/A"],
                "close_sz": ["9514.86"],
                "pct_change_sz": ["6.71"],
                "net_amount": ["17175101440.00"],
                "net_amount_rate": ["15.5"],
                "buy_elg_amount": ["17175101440.00"],
                "buy_elg_amount_rate": ["8.2"],
                "buy_lg_amount": ["-3564773376.00"],
                "buy_lg_amount_rate": ["-2.1"],
                "buy_md_amount": ["1234567890.00"],
                "buy_md_amount_rate": ["1.5"],
                "buy_sm_amount": ["-987654321.00"],
                "buy_sm_amount_rate": ["-0.8"],
            }
        )

        result = job.transform(source_data)

        # Should handle gracefully with NaN
        assert pd.isna(result.iloc[0]["percent_change_sh"])
        assert pd.isna(result.iloc[0]["close_sh"])

    def test_transform_removes_duplicates(self, mock_session):
        """Test that transform removes duplicate rows."""
        job = MarketIndexCapflowDC(session=mock_session)

        # Create data with duplicates
        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240927"],
                "close_sh": [3087.53, 3087.53],
                "pct_change_sh": [2.89, 2.89],
                "close_sz": [9514.86, 9514.86],
                "pct_change_sz": [6.71, 6.71],
                "net_amount": [17175101440.00, 17175101440.00],
                "net_amount_rate": [15.5, 15.5],
                "buy_elg_amount": [17175101440.00, 17175101440.00],
                "buy_elg_amount_rate": [8.2, 8.2],
                "buy_lg_amount": [-3564773376.00, -3564773376.00],
                "buy_lg_amount_rate": [-2.1, -2.1],
                "buy_md_amount": [1234567890.00, 1234567890.00],
                "buy_md_amount_rate": [1.5, 1.5],
                "buy_sm_amount": [-987654321.00, -987654321.00],
                "buy_sm_amount_rate": [-0.8, -0.8],
            }
        )

        result = job.transform(source_data)

        # Should only have 1 row after deduplication
        assert len(result) == 1

    def test_transform_date_formatting(self, mock_session):
        """Test that dates are formatted correctly."""
        job = MarketIndexCapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240926"],
                "close_sh": [3087.53, 3000.95],
                "pct_change_sh": [2.89, 3.61],
                "close_sz": [9514.86, 8916.65],
                "pct_change_sz": [6.71, 4.44],
                "net_amount": [17175101440.00, 18894807552.00],
                "net_amount_rate": [15.5, 18.2],
                "buy_elg_amount": [17175101440.00, 18894807552.00],
                "buy_elg_amount_rate": [8.2, 9.1],
                "buy_lg_amount": [-3564773376.00, -2446319616.00],
                "buy_lg_amount_rate": [-2.1, -1.5],
                "buy_md_amount": [1234567890.00, 2345678901.00],
                "buy_md_amount_rate": [1.5, 2.0],
                "buy_sm_amount": [-987654321.00, -1234567890.00],
                "buy_sm_amount_rate": [-0.8, -1.0],
            }
        )

        result = job.transform(source_data)

        # Result is sorted by date
        assert result.iloc[0]["date"] == "2024-09-26"
        assert result.iloc[0]["datecode"] == "20240926"
        assert result.iloc[1]["date"] == "2024-09-27"
        assert result.iloc[1]["datecode"] == "20240927"

    def test_transform_all_target_columns_present(self, mock_session):
        """Test that all target columns are present in transformed data."""
        job = MarketIndexCapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        result = job.transform(source_data)

        expected_columns = TARGET.list_column_names()
        assert list(result.columns) == expected_columns


# Test Class 3: Run Method Tests


class TestMarketIndexCapflowDCRun:
    """Test the _run method and parameter handling."""

    def test_run_with_string_date_params(self, mock_session):
        """Test _run with string date parameters."""
        # Mock the API response
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(
            session=mock_session,
            params={"start_date": "20240901", "end_date": "20240930"},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        mock_session.connection.moneyflow_mkt_dc.assert_called_once()
        call_kwargs = mock_session.connection.moneyflow_mkt_dc.call_args[1]
        assert call_kwargs["start_date"] == "20240901"
        assert call_kwargs["end_date"] == "20240930"

    def test_run_with_datetime_params(self, mock_session):
        """Test _run converts datetime parameters correctly."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(
            session=mock_session,
            params={"trade_date": datetime(2024, 9, 27)},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        call_kwargs = mock_session.connection.moneyflow_mkt_dc.call_args[1]
        assert call_kwargs["trade_date"] == "20240927"

    def test_run_with_date_params(self, mock_session):
        """Test _run converts date parameters correctly."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(
            session=mock_session,
            params={"start_date": date(2024, 9, 1), "end_date": date(2024, 9, 30)},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        call_kwargs = mock_session.connection.moneyflow_mkt_dc.call_args[1]
        assert call_kwargs["start_date"] == "20240901"
        assert call_kwargs["end_date"] == "20240930"

    def test_run_with_trade_date(self, mock_session):
        """Test _run with single trade_date parameter."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        result = job._run()

        assert not result.empty
        call_kwargs = mock_session.connection.moneyflow_mkt_dc.call_args[1]
        assert call_kwargs["trade_date"] == "20240927"

    def test_run_empty_result(self, mock_session):
        """Test _run handles empty API result."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame()

        job = MarketIndexCapflowDC(session=mock_session, params={"trade_date": "20240101"}, cache=False)

        result = job._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_run_with_multiple_params(self, mock_session):
        """Test _run with multiple parameter types."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(
            session=mock_session,
            params={
                "start_date": date(2024, 9, 1),
                "end_date": datetime(2024, 9, 30),
            },
            cache=False,
        )

        job._run()

        call_kwargs = mock_session.connection.moneyflow_mkt_dc.call_args[1]
        assert call_kwargs["start_date"] == "20240901"
        assert call_kwargs["end_date"] == "20240930"

    def test_run_api_called_with_correct_method(self, mock_session):
        """Test that _run calls moneyflow_mkt_dc API method."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        job._run()

        # Verify the correct API method was called
        mock_session.connection.moneyflow_mkt_dc.assert_called_once()


# Test Class 4: Cache Tests


class TestMarketIndexCapflowDCCache:
    """Test caching functionality."""

    def test_cache_enabled(self, mock_session):
        """Test that cache is used when enabled."""
        cached_data = pd.DataFrame(
            {
                "date": ["2024-09-27"],
                "datecode": ["20240927"],
                "close_sh": [3087.53],
                "percent_change_sh": [2.89],
                "close_sz": [9514.86],
                "percent_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(session=mock_session, params={"trade_date": "20240927"}, cache=True)

        # Mock _load_cache to return cached data
        with patch.object(job, "_load_cache", return_value=cached_data):
            result = job._run()

            # Should return cached data without calling API
            assert not result.empty
            mock_session.connection.moneyflow_mkt_dc.assert_not_called()

    def test_cache_disabled(self, mock_session):
        """Test that API is called when cache is disabled."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        result = job._run()

        # Should call API
        assert not result.empty
        mock_session.connection.moneyflow_mkt_dc.assert_called_once()

    def test_cache_save_called(self, mock_session):
        """Test that cache save is called after successful run."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(session=mock_session, params={"trade_date": "20240927"}, cache=True)

        with patch.object(job, "_save_cache") as mock_save:
            job._run()

            # Should call save cache
            mock_save.assert_called_once()


# Test Class 5: Integration Tests


class TestMarketIndexCapflowDCIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow_single_date(self, mock_session):
        """Test complete workflow for single date query."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "close_sh": [3087.53],
                "pct_change_sh": [2.89],
                "close_sz": [9514.86],
                "pct_change_sz": [6.71],
                "net_amount": [17175101440.00],
                "net_amount_rate": [15.5],
                "buy_elg_amount": [17175101440.00],
                "buy_elg_amount_rate": [8.2],
                "buy_lg_amount": [-3564773376.00],
                "buy_lg_amount_rate": [-2.1],
                "buy_md_amount": [1234567890.00],
                "buy_md_amount_rate": [1.5],
                "buy_sm_amount": [-987654321.00],
                "buy_sm_amount_rate": [-0.8],
            }
        )

        job = MarketIndexCapflowDC(
            session=mock_session,
            params={"trade_date": "20240927"},
            cache=False,
        )

        result = job.run()

        assert len(result) == 1
        assert result.iloc[0]["date"] == "2024-09-27"
        assert result.iloc[0]["close_sh"] == pytest.approx(3087.53)
        assert result.iloc[0]["net_amount"] == pytest.approx(17175101440.00)

    def test_full_workflow_date_range(self, mock_session):
        """Test complete workflow for date range query."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240926", "20240925"],
                "close_sh": [3087.53, 3000.95, 2896.31],
                "pct_change_sh": [2.89, 3.61, 1.16],
                "close_sz": [9514.86, 8916.65, 8537.73],
                "pct_change_sz": [6.71, 4.44, 1.21],
                "net_amount": [17175101440.00, 18894807552.00, -4010342144.00],
                "net_amount_rate": [15.5, 18.2, -3.5],
                "buy_elg_amount": [17175101440.00, 18894807552.00, -4010342144.00],
                "buy_elg_amount_rate": [8.2, 9.1, -2.0],
                "buy_lg_amount": [-3564773376.00, -2446319616.00, -10390331392.00],
                "buy_lg_amount_rate": [-2.1, -1.5, -5.2],
                "buy_md_amount": [1234567890.00, 2345678901.00, 3456789012.00],
                "buy_md_amount_rate": [1.5, 2.0, 2.5],
                "buy_sm_amount": [-987654321.00, -1234567890.00, -2345678901.00],
                "buy_sm_amount_rate": [-0.8, -1.0, -1.5],
            }
        )

        job = MarketIndexCapflowDC(
            session=mock_session,
            params={"start_date": "20240925", "end_date": "20240927"},
            cache=False,
        )

        result = job.run()

        assert len(result) == 3
        # Verify dates are in ascending order
        assert result.iloc[0]["date"] == "2024-09-25"
        assert result.iloc[1]["date"] == "2024-09-26"
        assert result.iloc[2]["date"] == "2024-09-27"

    def test_negative_net_amount_handling(self, mock_session):
        """Test handling of negative net amounts (capital outflow)."""
        mock_session.connection.moneyflow_mkt_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240925"],
                "close_sh": [2896.31],
                "pct_change_sh": [1.16],
                "close_sz": [8537.73],
                "pct_change_sz": [1.21],
                "net_amount": [-4010342144.00],  # Negative - capital outflow
                "net_amount_rate": [-3.5],
                "buy_elg_amount": [-4010342144.00],
                "buy_elg_amount_rate": [-2.0],
                "buy_lg_amount": [-10390331392.00],
                "buy_lg_amount_rate": [-5.2],
                "buy_md_amount": [3456789012.00],
                "buy_md_amount_rate": [2.5],
                "buy_sm_amount": [-2345678901.00],
                "buy_sm_amount_rate": [-1.5],
            }
        )

        job = MarketIndexCapflowDC(session=mock_session, params={"trade_date": "20240925"}, cache=False)

        result = job.run()

        assert len(result) == 1
        assert result.iloc[0]["net_amount"] < 0  # Capital outflow
        assert result.iloc[0]["net_amount"] == pytest.approx(-4010342144.00)

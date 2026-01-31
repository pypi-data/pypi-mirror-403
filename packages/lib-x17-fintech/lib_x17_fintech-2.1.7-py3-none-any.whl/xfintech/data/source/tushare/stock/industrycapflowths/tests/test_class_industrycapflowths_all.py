from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session import Session
from xfintech.data.source.tushare.stock.industrycapflowths import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
    IndustryCapflowTHS,
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
    mock_connection.moneyflow_ind_ths = MagicMock()
    session.connection = mock_connection

    return session


# Test Class 1: Initialization Tests


class TestIndustryCapflowTHSInitialization:
    """Test IndustryCapflowTHS class initialization and configuration."""

    def test_name_constant(self):
        """Test NAME constant is set correctly."""
        assert NAME == "industrycapflowths"

    def test_key_constant(self):
        """Test KEY constant is set correctly."""
        assert KEY == "/tushare/industrycapflowths"

    def test_source_table_info(self):
        """Test SOURCE TableInfo configuration."""
        assert SOURCE.desc == "同花顺行业资金流向数据（tushare格式）"
        assert SOURCE.meta["provider"] == "tushare"
        assert SOURCE.meta["source"] == "moneyflow_ind_ths"
        assert SOURCE.meta["type"] == "partitioned"
        assert SOURCE.meta["scale"] == "crosssection"
        # Verify key columns exist
        column_names = SOURCE.list_column_names()
        assert "trade_date" in column_names
        assert "ts_code" in column_names
        assert "industry" in column_names
        assert "net_amount" in column_names

    def test_target_table_info(self):
        """Test TARGET TableInfo configuration."""
        assert TARGET.desc == "同花顺行业资金流向数据（xfinbatch标准格式）"
        assert TARGET.meta["key"] == KEY
        assert TARGET.meta["name"] == NAME
        assert TARGET.meta["type"] == "partitioned"
        assert TARGET.meta["scale"] == "crosssection"
        # Verify transformed columns exist
        column_names = TARGET.list_column_names()
        assert "code" in column_names
        assert "date" in column_names
        assert "datecode" in column_names
        assert "percent_change" in column_names

    def test_initialization_with_params(self, mock_session):
        """Test IndustryCapflowTHS initialization with parameters."""
        params = {"ts_code": "881267.TI", "start_date": "20240901", "end_date": "20240930"}
        job = IndustryCapflowTHS(session=mock_session, params=params)

        assert job.name == NAME
        assert job.key == KEY
        assert job.params.get("ts_code") == "881267.TI"

    def test_initialization_with_optional_components(self, mock_session):
        """Test initialization with optional coolant, retry, and cache."""
        coolant = Coolant(interval=1.0)
        retry = Retry(retry=3)
        cache = Cache(path="/tmp/test_cache")

        job = IndustryCapflowTHS(
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
        job = IndustryCapflowTHS(session=mock_session)

        assert job.name == NAME
        assert job.key == KEY


# Test Class 2: Transform Tests


class TestIndustryCapflowTHSTransform:
    """Test the transform method that converts Tushare format to xfinbatch format."""

    def test_transform_empty_dataframe(self, mock_session):
        """Test transform with empty DataFrame."""
        job = IndustryCapflowTHS(session=mock_session)

        empty_df = pd.DataFrame()
        result = job.transform(empty_df)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_none_input(self, mock_session):
        """Test transform with None input."""
        job = IndustryCapflowTHS(session=mock_session)

        result = job.transform(None)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_basic_data(self, mock_session):
        """Test transform with basic data."""
        job = IndustryCapflowTHS(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        result = job.transform(source_data)

        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]["code"] == "881267.TI"
        assert result.iloc[0]["date"] == "2024-09-27"
        assert result.iloc[0]["datecode"] == "20240927"
        assert result.iloc[0]["industry"] == "能源金属"
        assert result.iloc[0]["percent_change"] == pytest.approx(2.5)
        assert result.iloc[0]["company_num"] == 16

    def test_transform_multiple_industries(self, mock_session):
        """Test transform with multiple industries."""
        job = IndustryCapflowTHS(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240927", "20240926"],
                "ts_code": ["881267.TI", "881273.TI", "881267.TI"],
                "industry": ["能源金属", "白酒", "能源金属"],
                "lead_stock": ["股票A", "股票B", "股票A"],
                "close": [15021.70, 3251.85, 15000.50],
                "pct_change": [2.5, 1.2, 1.8],
                "company_num": [16, 20, 16],
                "pct_change_stock": [3.2, 2.1, 2.5],
                "close_price": [45.6, 123.4, 44.8],
                "net_buy_amount": [490.00, 1890.00, 450.00],
                "net_sell_amount": [46.00, 179.00, 40.00],
                "net_amount": [3.00, 10.00, 5.00],
            }
        )

        result = job.transform(source_data)

        assert len(result) == 3
        assert set(result["code"].unique()) == {"881267.TI", "881273.TI"}
        # Verify sorted by code then date
        assert result.iloc[0]["code"] == "881267.TI"
        assert result.iloc[1]["code"] == "881267.TI"
        assert result.iloc[2]["code"] == "881273.TI"

    def test_transform_numeric_conversion(self, mock_session):
        """Test that numeric fields are properly converted."""
        job = IndustryCapflowTHS(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": ["15021.70"],  # String
                "pct_change": ["2.5"],  # String
                "company_num": ["16"],  # String
                "pct_change_stock": ["3.2"],  # String
                "close_price": ["45.6"],  # String
                "net_buy_amount": ["490.00"],  # String
                "net_sell_amount": ["46.00"],  # String
                "net_amount": ["3.00"],  # String
            }
        )

        result = job.transform(source_data)

        # Verify all numeric fields are actually numeric
        assert isinstance(result.iloc[0]["percent_change"], (int, float))
        assert isinstance(result.iloc[0]["close"], (int, float))
        assert isinstance(result.iloc[0]["net_amount"], (int, float))
        # company_num is numpy int64, verify it's numeric
        assert pd.api.types.is_numeric_dtype(result["company_num"])
        assert result.iloc[0]["percent_change"] == pytest.approx(2.5)
        assert result.iloc[0]["company_num"] == 16

    def test_transform_handles_invalid_values(self, mock_session):
        """Test transform handles invalid numeric values gracefully."""
        job = IndustryCapflowTHS(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": ["invalid"],
                "pct_change": ["N/A"],
                "company_num": ["N/A"],
                "pct_change_stock": ["3.2"],
                "close_price": ["45.6"],
                "net_buy_amount": ["490.00"],
                "net_sell_amount": ["46.00"],
                "net_amount": ["3.00"],
            }
        )

        result = job.transform(source_data)

        # Should handle gracefully with NaN
        assert pd.isna(result.iloc[0]["percent_change"])
        assert pd.isna(result.iloc[0]["close"])
        assert result.iloc[0]["company_num"] == 0  # fillna(0) for integers

    def test_transform_removes_duplicates(self, mock_session):
        """Test that transform removes duplicate rows."""
        job = IndustryCapflowTHS(session=mock_session)

        # Create data with duplicates
        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240927"],
                "ts_code": ["881267.TI", "881267.TI"],
                "industry": ["能源金属", "能源金属"],
                "lead_stock": ["某股票", "某股票"],
                "close": [15021.70, 15021.70],
                "pct_change": [2.5, 2.5],
                "company_num": [16, 16],
                "pct_change_stock": [3.2, 3.2],
                "close_price": [45.6, 45.6],
                "net_buy_amount": [490.00, 490.00],
                "net_sell_amount": [46.00, 46.00],
                "net_amount": [3.00, 3.00],
            }
        )

        result = job.transform(source_data)

        # Should only have 1 row after deduplication
        assert len(result) == 1

    def test_transform_date_formatting(self, mock_session):
        """Test that dates are formatted correctly."""
        job = IndustryCapflowTHS(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240926"],
                "ts_code": ["881267.TI", "881273.TI"],
                "industry": ["能源金属", "白酒"],
                "lead_stock": ["股票A", "股票B"],
                "close": [15021.70, 3251.85],
                "pct_change": [2.5, 1.2],
                "company_num": [16, 20],
                "pct_change_stock": [3.2, 2.1],
                "close_price": [45.6, 123.4],
                "net_buy_amount": [490.00, 1890.00],
                "net_sell_amount": [46.00, 179.00],
                "net_amount": [3.00, 10.00],
            }
        )

        result = job.transform(source_data)

        # Result is sorted by code, then date
        assert result.iloc[0]["code"] == "881267.TI"
        assert result.iloc[0]["date"] == "2024-09-27"
        assert result.iloc[0]["datecode"] == "20240927"
        assert result.iloc[1]["code"] == "881273.TI"
        assert result.iloc[1]["date"] == "2024-09-26"
        assert result.iloc[1]["datecode"] == "20240926"

    def test_transform_all_target_columns_present(self, mock_session):
        """Test that all target columns are present in transformed data."""
        job = IndustryCapflowTHS(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        result = job.transform(source_data)

        expected_columns = TARGET.list_column_names()
        assert list(result.columns) == expected_columns


# Test Class 3: Run Method Tests


class TestIndustryCapflowTHSRun:
    """Test the _run method and parameter handling."""

    def test_run_with_string_date_params(self, mock_session):
        """Test _run with string date parameters."""
        # Mock the API response
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(
            session=mock_session,
            params={"ts_code": "881267.TI", "start_date": "20240901", "end_date": "20240930"},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        mock_session.connection.moneyflow_ind_ths.assert_called_once()
        call_kwargs = mock_session.connection.moneyflow_ind_ths.call_args[1]
        assert call_kwargs["ts_code"] == "881267.TI"
        assert call_kwargs["start_date"] == "20240901"
        assert call_kwargs["end_date"] == "20240930"

    def test_run_with_datetime_params(self, mock_session):
        """Test _run converts datetime parameters correctly."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(
            session=mock_session,
            params={"trade_date": datetime(2024, 9, 27)},
            cache=False,
        )
        result = job._run()
        assert not result.empty

    def test_run_with_trade_date(self, mock_session):
        """Test _run with single trade_date parameter."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        result = job._run()

        assert not result.empty
        call_kwargs = mock_session.connection.moneyflow_ind_ths.call_args[1]
        assert call_kwargs["trade_date"] == "20240927"

    def test_run_with_ts_code(self, mock_session):
        """Test _run with ts_code parameter."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(
            session=mock_session,
            params={"ts_code": "881267.TI", "start_date": "20240901", "end_date": "20240930"},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        assert result.iloc[0]["code"] == "881267.TI"

    def test_run_empty_result(self, mock_session):
        """Test _run handles empty API result."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame()

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240101"}, cache=False)

        result = job._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_run_api_called_with_correct_method(self, mock_session):
        """Test that _run calls moneyflow_ind_ths API method."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        job._run()

        # Verify the correct API method was called
        mock_session.connection.moneyflow_ind_ths.assert_called_once()


# Test Class 4: Cache Tests


class TestIndustryCapflowTHSCache:
    """Test caching functionality."""

    def test_cache_enabled(self, mock_session):
        """Test that cache is used when enabled."""
        cached_data = pd.DataFrame(
            {
                "code": ["881267.TI"],
                "date": ["2024-09-27"],
                "datecode": ["20240927"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "percent_change": [2.5],
                "company_num": [16],
                "percent_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240927"}, cache=True)

        # Mock _load_cache to return cached data
        with patch.object(job, "_load_cache", return_value=cached_data):
            result = job._run()

            # Should return cached data without calling API
            assert not result.empty
            mock_session.connection.moneyflow_ind_ths.assert_not_called()

    def test_cache_disabled(self, mock_session):
        """Test that API is called when cache is disabled."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        result = job._run()

        # Should call API
        assert not result.empty
        mock_session.connection.moneyflow_ind_ths.assert_called_once()

    def test_cache_save_called(self, mock_session):
        """Test that cache save is called after successful run."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927"],
                "ts_code": ["881267.TI"],
                "industry": ["能源金属"],
                "lead_stock": ["某股票"],
                "close": [15021.70],
                "pct_change": [2.5],
                "company_num": [16],
                "pct_change_stock": [3.2],
                "close_price": [45.6],
                "net_buy_amount": [490.00],
                "net_sell_amount": [46.00],
                "net_amount": [3.00],
            }
        )

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240927"}, cache=True)

        with patch.object(job, "_save_cache") as mock_save:
            job._run()
            # Should call save cache
            mock_save.assert_called_once()


# Test Class 5: Integration Tests


class TestIndustryCapflowTHSIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow_single_industry(self, mock_session):
        """Test complete workflow for single industry query."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240926", "20240925"],
                "ts_code": ["881267.TI", "881267.TI", "881267.TI"],
                "industry": ["能源金属", "能源金属", "能源金属"],
                "lead_stock": ["股票A", "股票A", "股票A"],
                "close": [15021.70, 15000.50, 14980.30],
                "pct_change": [2.5, 1.8, -0.5],
                "company_num": [16, 16, 16],
                "pct_change_stock": [3.2, 2.5, -0.8],
                "close_price": [45.6, 44.8, 44.2],
                "net_buy_amount": [490.00, 450.00, 380.00],
                "net_sell_amount": [46.00, 40.00, 45.00],
                "net_amount": [3.00, 5.00, -2.00],
            }
        )

        job = IndustryCapflowTHS(
            session=mock_session,
            params={"ts_code": "881267.TI", "start_date": "20240925", "end_date": "20240927"},
            cache=False,
        )

        result = job.run()

        assert len(result) == 3
        assert all(result["code"] == "881267.TI")
        assert all(result["industry"] == "能源金属")
        # Verify dates are in ascending order
        assert result.iloc[0]["date"] == "2024-09-25"
        assert result.iloc[1]["date"] == "2024-09-26"
        assert result.iloc[2]["date"] == "2024-09-27"

    def test_full_workflow_market_wide(self, mock_session):
        """Test complete workflow for market-wide query."""
        mock_session.connection.moneyflow_ind_ths.return_value = pd.DataFrame(
            {
                "trade_date": ["20240927", "20240927", "20240927"],
                "ts_code": ["881267.TI", "881273.TI", "881279.TI"],
                "industry": ["能源金属", "白酒", "光伏设备"],
                "lead_stock": ["股票A", "股票B", "股票C"],
                "close": [15021.70, 3251.85, 5940.19],
                "pct_change": [2.5, 1.2, 3.5],
                "company_num": [16, 20, 70],
                "pct_change_stock": [3.2, 2.1, 4.2],
                "close_price": [45.6, 123.4, 67.8],
                "net_buy_amount": [490.00, 1890.00, 1120.00],
                "net_sell_amount": [46.00, 179.00, 94.00],
                "net_amount": [3.00, 10.00, 17.00],
            }
        )

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        result = job.run()

        assert len(result) == 3
        assert set(result["code"].unique()) == {"881267.TI", "881273.TI", "881279.TI"}
        assert all(result["date"] == "2024-09-27")

    def test_error_handling_integration(self, mock_session):
        """Test error handling in full workflow."""
        # Simulate API returning None or error
        mock_session.connection.moneyflow_ind_ths.return_value = None

        job = IndustryCapflowTHS(session=mock_session, params={"trade_date": "20240927"}, cache=False)

        result = job._run()

        # Should handle gracefully with empty DataFrame
        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

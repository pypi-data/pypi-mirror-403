from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.session.session import Session
from xfintech.data.source.tushare.stock.capflowdc.capflowdc import CapflowDC
from xfintech.data.source.tushare.stock.capflowdc.constant import (
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
    mock_connection.moneyflow_dc = MagicMock()
    session.connection = mock_connection

    return session


# Test Class 1: Initialization Tests
class TestCapflowDCInitialization:
    """Test CapflowDC class initialization and configuration."""

    def test_name_constant(self):
        """Test NAME constant is set correctly."""
        assert NAME == "capflowdc"

    def test_key_constant(self):
        """Test KEY constant is set correctly."""
        assert KEY == "/tushare/capflowdc"

    def test_paginate_settings(self):
        """Test pagination settings are correct."""
        assert PAGINATE["pagesize"] == 6000
        assert PAGINATE["pagelimit"] == 1000

    def test_source_table_info(self):
        """Test SOURCE TableInfo configuration."""
        assert SOURCE.desc == "东方财富个股资金流向数据（tushare格式）"
        assert SOURCE.meta["provider"] == "tushare"
        assert SOURCE.meta["source"] == "moneyflow_dc"
        assert SOURCE.meta["type"] == "partitioned"
        assert SOURCE.meta["scale"] == "crosssection"
        # Verify key columns exist
        column_names = SOURCE.list_column_names()
        assert "trade_date" in column_names
        assert "ts_code" in column_names
        assert "name" in column_names
        assert "net_amount" in column_names

    def test_target_table_info(self):
        """Test TARGET TableInfo configuration."""
        assert TARGET.desc == "东方财富个股资金流向数据（xfinbatch标准格式）"
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
        """Test CapflowDC initialization with parameters."""
        params = {"ts_code": "002149.SZ", "start_date": "20240901", "end_date": "20240913"}
        job = CapflowDC(session=mock_session, params=params)

        assert job.name == NAME
        assert job.key == KEY
        assert job.params.get("ts_code") == "002149.SZ"

    def test_initialization_with_optional_components(self, mock_session):
        """Test initialization with optional coolant, retry, and cache."""
        coolant = Coolant(interval=1.0)
        retry = Retry(retry=3)
        cache = Cache(path="/tmp/test_cache")

        job = CapflowDC(
            session=mock_session,
            params={"trade_date": "20241011"},
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
        job = CapflowDC(session=mock_session)

        assert job.name == NAME
        assert job.key == KEY


# Test Class 2: Transform Tests


class TestCapflowDCTransform:
    """Test the transform method that converts Tushare format to xfinbatch format."""

    def test_transform_empty_dataframe(self, mock_session):
        """Test transform with empty DataFrame."""
        job = CapflowDC(session=mock_session)

        empty_df = pd.DataFrame()
        result = job.transform(empty_df)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_none_input(self, mock_session):
        """Test transform with None input."""
        job = CapflowDC(session=mock_session)

        result = job.transform(None)

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_transform_basic_data(self, mock_session):
        """Test transform with basic data."""
        job = CapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        result = job.transform(source_data)

        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]["code"] == "002149.SZ"
        assert result.iloc[0]["date"] == "2024-09-13"
        assert result.iloc[0]["datecode"] == "20240913"
        assert result.iloc[0]["name"] == "西部材料"
        assert result.iloc[0]["percent_change"] == pytest.approx(-1.34)
        assert result.iloc[0]["close"] == pytest.approx(15.25)

    def test_transform_multiple_stocks(self, mock_session):
        """Test transform with multiple stocks."""
        job = CapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240913", "20240913", "20240912"],
                "ts_code": ["002149.SZ", "000001.SZ", "002149.SZ"],
                "name": ["西部材料", "平安银行", "西部材料"],
                "pct_change": [-1.34, 0.52, 1.43],
                "close": [15.25, 12.30, 15.46],
                "net_amount": [-245.67, 123.45, 456.78],
                "net_amount_rate": [-6.77, 3.21, 10.89],
                "buy_elg_amount": [-183.55, 89.12, 234.56],
                "buy_elg_amount_rate": [-5.06, 2.31, 5.59],
                "buy_lg_amount": [-62.12, 34.33, 222.22],
                "buy_lg_amount_rate": [-1.71, 0.89, 5.30],
                "buy_md_amount": [-12.65, 23.45, 13.71],
                "buy_md_amount_rate": [-0.35, 0.61, 0.33],
                "buy_sm_amount": [-62.43, -23.45, -388.43],
                "buy_sm_amount_rate": [-1.72, -0.61, -9.25],
            }
        )

        result = job.transform(source_data)

        assert len(result) == 3
        assert set(result["code"].unique()) == {"002149.SZ", "000001.SZ"}
        # Verify sorted by code then date
        assert result.iloc[0]["code"] == "000001.SZ"
        assert result.iloc[1]["code"] == "002149.SZ"
        assert result.iloc[2]["code"] == "002149.SZ"

    def test_transform_numeric_conversion(self, mock_session):
        """Test that numeric fields are properly converted."""
        job = CapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": ["-1.34"],  # String
                "close": ["15.25"],  # String
                "net_amount": ["-245.67"],  # String
                "net_amount_rate": ["-6.77"],  # String
                "buy_elg_amount": ["-183.55"],  # String
                "buy_elg_amount_rate": ["-5.06"],  # String
                "buy_lg_amount": ["-62.12"],  # String
                "buy_lg_amount_rate": ["-1.71"],  # String
                "buy_md_amount": ["-12.65"],  # String
                "buy_md_amount_rate": ["-0.35"],  # String
                "buy_sm_amount": ["-62.43"],  # String
                "buy_sm_amount_rate": ["-1.72"],  # String
            }
        )

        result = job.transform(source_data)

        # Verify all numeric fields are actually numeric
        assert isinstance(result.iloc[0]["percent_change"], (int, float))
        assert isinstance(result.iloc[0]["close"], (int, float))
        assert isinstance(result.iloc[0]["net_amount"], (int, float))
        assert result.iloc[0]["percent_change"] == pytest.approx(-1.34)

    def test_transform_handles_invalid_values(self, mock_session):
        """Test transform handles invalid numeric values gracefully."""
        job = CapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": ["invalid"],
                "close": ["N/A"],
                "net_amount": ["-245.67"],
                "net_amount_rate": ["-6.77"],
                "buy_elg_amount": ["-183.55"],
                "buy_elg_amount_rate": ["-5.06"],
                "buy_lg_amount": ["-62.12"],
                "buy_lg_amount_rate": ["-1.71"],
                "buy_md_amount": ["-12.65"],
                "buy_md_amount_rate": ["-0.35"],
                "buy_sm_amount": ["-62.43"],
                "buy_sm_amount_rate": ["-1.72"],
            }
        )

        result = job.transform(source_data)

        # Should handle gracefully with NaN
        assert pd.isna(result.iloc[0]["percent_change"])
        assert pd.isna(result.iloc[0]["close"])

    def test_transform_removes_duplicates(self, mock_session):
        """Test that transform removes duplicate rows."""
        job = CapflowDC(session=mock_session)

        # Create data with duplicates
        source_data = pd.DataFrame(
            {
                "trade_date": ["20240913", "20240913"],
                "ts_code": ["002149.SZ", "002149.SZ"],
                "name": ["西部材料", "西部材料"],
                "pct_change": [-1.34, -1.34],
                "close": [15.25, 15.25],
                "net_amount": [-245.67, -245.67],
                "net_amount_rate": [-6.77, -6.77],
                "buy_elg_amount": [-183.55, -183.55],
                "buy_elg_amount_rate": [-5.06, -5.06],
                "buy_lg_amount": [-62.12, -62.12],
                "buy_lg_amount_rate": [-1.71, -1.71],
                "buy_md_amount": [-12.65, -12.65],
                "buy_md_amount_rate": [-0.35, -0.35],
                "buy_sm_amount": [-62.43, -62.43],
                "buy_sm_amount_rate": [-1.72, -1.72],
            }
        )

        result = job.transform(source_data)

        # Should only have 1 row after deduplication
        assert len(result) == 1

    def test_transform_date_formatting(self, mock_session):
        """Test that dates are formatted correctly."""
        job = CapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240913", "20241011"],
                "ts_code": ["002149.SZ", "000001.SZ"],
                "name": ["西部材料", "平安银行"],
                "pct_change": [-1.34, 0.52],
                "close": [15.25, 12.30],
                "net_amount": [-245.67, 123.45],
                "net_amount_rate": [-6.77, 3.21],
                "buy_elg_amount": [-183.55, 89.12],
                "buy_elg_amount_rate": [-5.06, 2.31],
                "buy_lg_amount": [-62.12, 34.33],
                "buy_lg_amount_rate": [-1.71, 0.89],
                "buy_md_amount": [-12.65, 23.45],
                "buy_md_amount_rate": [-0.35, 0.61],
                "buy_sm_amount": [-62.43, -23.45],
                "buy_sm_amount_rate": [-1.72, -0.61],
            }
        )

        result = job.transform(source_data)

        # Result is sorted by code, then date
        # 000001.SZ comes before 002149.SZ
        assert result.iloc[0]["code"] == "000001.SZ"
        assert result.iloc[0]["date"] == "2024-10-11"
        assert result.iloc[0]["datecode"] == "20241011"
        assert result.iloc[1]["code"] == "002149.SZ"
        assert result.iloc[1]["date"] == "2024-09-13"
        assert result.iloc[1]["datecode"] == "20240913"

    def test_transform_all_target_columns_present(self, mock_session):
        """Test that all target columns are present in transformed data."""
        job = CapflowDC(session=mock_session)

        source_data = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        result = job.transform(source_data)

        expected_columns = TARGET.list_column_names()
        assert list(result.columns) == expected_columns


# Test Class 3: Run Method Tests


class TestCapflowDCRun:
    """Test the _run method and parameter handling."""

    def test_run_with_string_date_params(self, mock_session):
        """Test _run with string date parameters."""
        # Mock the API response
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(
            session=mock_session,
            params={"ts_code": "002149.SZ", "start_date": "20240901", "end_date": "20240913"},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        mock_session.connection.moneyflow_dc.assert_called_once()
        call_kwargs = mock_session.connection.moneyflow_dc.call_args[1]
        assert call_kwargs["ts_code"] == "002149.SZ"
        assert call_kwargs["start_date"] == "20240901"
        assert call_kwargs["end_date"] == "20240913"

    def test_run_with_datetime_params(self, mock_session):
        """Test _run converts datetime parameters correctly."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(
            session=mock_session,
            params={"trade_date": datetime(2024, 9, 13)},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        call_kwargs = mock_session.connection.moneyflow_dc.call_args[1]
        assert call_kwargs["trade_date"] == "20240913"

    def test_run_with_date_params(self, mock_session):
        """Test _run converts date parameters correctly."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(
            session=mock_session,
            params={"start_date": date(2024, 9, 1), "end_date": date(2024, 9, 13)},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        call_kwargs = mock_session.connection.moneyflow_dc.call_args[1]
        assert call_kwargs["start_date"] == "20240901"
        assert call_kwargs["end_date"] == "20240913"

    def test_run_with_trade_date(self, mock_session):
        """Test _run with single trade_date parameter."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20241011"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(session=mock_session, params={"trade_date": "20241011"}, cache=False)

        result = job._run()

        assert not result.empty
        call_kwargs = mock_session.connection.moneyflow_dc.call_args[1]
        assert call_kwargs["trade_date"] == "20241011"

    def test_run_with_ts_code(self, mock_session):
        """Test _run with ts_code parameter."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(
            session=mock_session,
            params={"ts_code": "002149.SZ", "start_date": "20240901", "end_date": "20240913"},
            cache=False,
        )

        result = job._run()

        assert not result.empty
        assert result.iloc[0]["code"] == "002149.SZ"

    def test_run_empty_result(self, mock_session):
        """Test _run handles empty API result."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame()

        job = CapflowDC(session=mock_session, params={"trade_date": "20240101"}, cache=False)

        result = job._run()

        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

    def test_run_with_multiple_params(self, mock_session):
        """Test _run with multiple parameter types."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(
            session=mock_session,
            params={
                "ts_code": "002149.SZ",
                "start_date": date(2024, 9, 1),
                "end_date": datetime(2024, 9, 13),
            },
            cache=False,
        )

        job._run()

        call_kwargs = mock_session.connection.moneyflow_dc.call_args[1]
        assert call_kwargs["ts_code"] == "002149.SZ"
        assert call_kwargs["start_date"] == "20240901"
        assert call_kwargs["end_date"] == "20240913"

    def test_run_api_called_with_correct_method(self, mock_session):
        """Test that _run calls moneyflow_dc API method."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20241011"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(session=mock_session, params={"trade_date": "20241011"}, cache=False)

        job._run()

        # Verify the correct API method was called
        mock_session.connection.moneyflow_dc.assert_called_once()


# Test Class 4: Cache Tests


class TestCapflowDCCache:
    """Test caching functionality."""

    def test_cache_enabled(self, mock_session):
        """Test that cache is used when enabled."""
        cached_data = pd.DataFrame(
            {
                "code": ["002149.SZ"],
                "date": ["2024-09-13"],
                "datecode": ["20240913"],
                "name": ["西部材料"],
                "percent_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(session=mock_session, params={"trade_date": "20240913"}, cache=True)

        # Mock _load_cache to return cached data
        with patch.object(job, "_load_cache", return_value=cached_data):
            result = job._run()

            # Should return cached data without calling API
            assert not result.empty
            mock_session.connection.moneyflow_dc.assert_not_called()

    def test_cache_disabled(self, mock_session):
        """Test that API is called when cache is disabled."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(session=mock_session, params={"trade_date": "20240913"}, cache=False)

        result = job._run()

        # Should call API
        assert not result.empty
        mock_session.connection.moneyflow_dc.assert_called_once()

    def test_cache_save_called(self, mock_session):
        """Test that cache save is called after successful run."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913"],
                "ts_code": ["002149.SZ"],
                "name": ["西部材料"],
                "pct_change": [-1.34],
                "close": [15.25],
                "net_amount": [-245.67],
                "net_amount_rate": [-6.77],
                "buy_elg_amount": [-183.55],
                "buy_elg_amount_rate": [-5.06],
                "buy_lg_amount": [-62.12],
                "buy_lg_amount_rate": [-1.71],
                "buy_md_amount": [-12.65],
                "buy_md_amount_rate": [-0.35],
                "buy_sm_amount": [-62.43],
                "buy_sm_amount_rate": [-1.72],
            }
        )

        job = CapflowDC(session=mock_session, params={"trade_date": "20240913"}, cache=True)

        with patch.object(job, "_save_cache") as mock_save:
            job._run()

            # Should call save cache
            mock_save.assert_called_once()


# Test Class 5: Integration Tests


class TestCapflowDCIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow_single_stock(self, mock_session):
        """Test complete workflow for single stock query."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20240913", "20240912", "20240911"],
                "ts_code": ["002149.SZ", "002149.SZ", "002149.SZ"],
                "name": ["西部材料", "西部材料", "西部材料"],
                "pct_change": [-1.34, 1.43, -0.79],
                "close": [15.25, 15.46, 15.24],
                "net_amount": [-245.67, 456.78, -123.45],
                "net_amount_rate": [-6.77, 10.89, -7.94],
                "buy_elg_amount": [-183.55, 234.56, -89.12],
                "buy_elg_amount_rate": [-5.06, 5.59, -5.73],
                "buy_lg_amount": [-62.12, 222.22, -34.33],
                "buy_lg_amount_rate": [-1.71, 5.30, -2.21],
                "buy_md_amount": [-12.65, 13.71, -26.10],
                "buy_md_amount_rate": [-0.35, 0.33, -1.68],
                "buy_sm_amount": [-62.43, -388.43, 95.69],
                "buy_sm_amount_rate": [-1.72, -9.25, 6.15],
            }
        )

        job = CapflowDC(
            session=mock_session,
            params={"ts_code": "002149.SZ", "start_date": "20240911", "end_date": "20240913"},
            cache=False,
        )

        result = job.run()

        assert len(result) == 3
        assert all(result["code"] == "002149.SZ")
        assert all(result["name"] == "西部材料")
        # Verify dates are in ascending order
        assert result.iloc[0]["date"] == "2024-09-11"
        assert result.iloc[1]["date"] == "2024-09-12"
        assert result.iloc[2]["date"] == "2024-09-13"

    def test_full_workflow_market_wide(self, mock_session):
        """Test complete workflow for market-wide query."""
        mock_session.connection.moneyflow_dc.return_value = pd.DataFrame(
            {
                "trade_date": ["20241011", "20241011", "20241011"],
                "ts_code": ["002149.SZ", "000001.SZ", "600000.SH"],
                "name": ["西部材料", "平安银行", "浦发银行"],
                "pct_change": [-1.34, 0.52, 1.23],
                "close": [15.25, 12.30, 8.45],
                "net_amount": [-245.67, 123.45, 678.90],
                "net_amount_rate": [-6.77, 3.21, 15.32],
                "buy_elg_amount": [-183.55, 89.12, 456.78],
                "buy_elg_amount_rate": [-5.06, 2.31, 10.31],
                "buy_lg_amount": [-62.12, 34.33, 222.12],
                "buy_lg_amount_rate": [-1.71, 0.89, 5.01],
                "buy_md_amount": [-12.65, 23.45, 45.67],
                "buy_md_amount_rate": [-0.35, 0.61, 1.03],
                "buy_sm_amount": [-62.43, -23.45, -45.67],
                "buy_sm_amount_rate": [-1.72, -0.61, -1.03],
            }
        )

        job = CapflowDC(session=mock_session, params={"trade_date": "20241011"}, cache=False)

        result = job.run()

        assert len(result) == 3
        assert set(result["code"].unique()) == {"002149.SZ", "000001.SZ", "600000.SH"}
        assert all(result["date"] == "2024-10-11")

    def test_error_handling_integration(self, mock_session):
        """Test error handling in full workflow."""
        # Simulate API returning None or error
        mock_session.connection.moneyflow_dc.return_value = None

        job = CapflowDC(session=mock_session, params={"trade_date": "20240913"}, cache=False)

        result = job._run()

        # Should handle gracefully with empty DataFrame
        assert result.empty
        assert list(result.columns) == TARGET.list_column_names()

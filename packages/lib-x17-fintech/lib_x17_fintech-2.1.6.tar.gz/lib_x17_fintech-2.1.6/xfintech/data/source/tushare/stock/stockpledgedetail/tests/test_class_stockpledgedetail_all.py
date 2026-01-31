"""Comprehensive tests for StockPledgeDetail class"""

import pandas as pd
import pytest

from xfintech.data.source.tushare.stock.stockpledgedetail import StockPledgeDetail
from xfintech.data.source.tushare.stock.stockpledgedetail.constant import (
    KEY,
    NAME,
    SOURCE,
    TARGET,
)


# Test Fixtures
class FakeConnection:
    """Fake Tushare connection for testing"""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def pledge_detail(self, **kwargs):
        """Mock pledge_detail API call"""
        return self.frame


class FakeSession:
    """Fake session for testing"""

    def __init__(self, connection: FakeConnection):
        self.connection = connection


@pytest.fixture
def mock_session():
    """Create a mock session with empty data"""
    fake_conn = FakeConnection(frame=pd.DataFrame())
    return FakeSession(fake_conn)


@pytest.fixture
def sample_source_data():
    """Sample pledge detail data in Tushare format"""
    return pd.DataFrame(
        {
            "ts_code": ["000014.SZ", "000014.SZ", "600848.SH"],
            "ann_date": ["20180106", "20180115", "20180106"],
            "holder_name": ["中科汇通", "中科汇通", "某股东"],
            "pledge_amount": [500.0, 300.0, 200.0],
            "start_date": ["20171114", "20180101", "20171114"],
            "end_date": ["20191113", "20191113", "20191113"],
            "is_release": ["0", "0", "1"],
            "release_date": ["", "", "20190101"],
            "pledgor": ["某质押机构", "某质押机构", "某质押方"],
            "holding_amount": [2321.9955, 2021.9955, 800.0],
            "pledged_amount": [1422.0055, 1122.0055, 200.0],
            "p_total_ratio": [0.1564, 0.1064, 0.04],
            "h_total_ratio": [0.7268, 0.6468, 0.15],
            "is_buyback": ["0", "0", "0"],
        }
    )


# Initialization Tests
def test_stockpledgedetail_init_basic(mock_session):
    """Test basic initialization"""
    detail = StockPledgeDetail(session=mock_session)
    assert detail.name == NAME
    assert detail.key == KEY


def test_stockpledgedetail_init_with_params(mock_session):
    """Test initialization with params"""
    detail = StockPledgeDetail(session=mock_session, params={"ts_code": "000014.SZ"})
    assert detail.params.get("ts_code") == "000014.SZ"


# Transform Tests
def test_stockpledgedetail_transform_basic(mock_session, sample_source_data):
    """Test basic transform"""
    detail = StockPledgeDetail(session=mock_session)
    result = detail.transform(sample_source_data)
    assert len(result) == 3
    assert "code" in result.columns


def test_stockpledgedetail_transform_dates(mock_session, sample_source_data):
    """Test date transformations"""
    detail = StockPledgeDetail(session=mock_session)
    result = detail.transform(sample_source_data)
    assert result["ann_date"].iloc[0] == "2018-01-06"
    assert result["ann_datecode"].iloc[0] == "20180106"


# Run Tests
def test_stockpledgedetail_run_basic(sample_source_data):
    """Test basic run"""
    fake_conn = FakeConnection(frame=sample_source_data)
    session = FakeSession(fake_conn)
    detail = StockPledgeDetail(session=session, params={"ts_code": "000014.SZ"}, cache=False)
    result = detail.run()
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


# Module Tests
def test_stockpledgedetail_constants():
    """Test module constants"""
    assert NAME == "stockpledgedetail"
    assert KEY == "/tushare/stockpledgedetail"
    assert len(SOURCE.columns) == 14
    assert len(TARGET.columns) == 18

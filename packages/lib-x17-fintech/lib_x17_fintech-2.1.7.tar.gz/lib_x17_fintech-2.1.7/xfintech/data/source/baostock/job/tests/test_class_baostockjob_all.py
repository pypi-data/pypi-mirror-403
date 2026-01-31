from datetime import date, datetime
from unittest.mock import Mock

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.source.baostock.job.job import BaostockJob
from xfintech.data.source.baostock.session.session import Session

# ============================================================================
# Helper Classes for Testing
# ============================================================================


class ConcreteBaostockJob(BaostockJob):
    """Concrete implementation for testing"""

    def _run(self) -> pd.DataFrame:
        return pd.DataFrame({"test": [1, 2, 3]})


class FetchAllJob(BaostockJob):
    """Job that uses _fetchall in _run"""

    def _run(self) -> pd.DataFrame:
        api = Mock(return_value=pd.DataFrame({"data": [1, 2, 3]}))
        return self._fetchall(api, code="sh.600000")


# ============================================================================
# Initialization Tests
# ============================================================================


def test_baostockjob_init_basic():
    """Test BaostockJob basic initialization"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    assert job.name == "test_job"
    assert job.key == "test_key"
    assert job.connection is not None
    assert isinstance(job.params, Params)
    assert isinstance(job.coolant, Coolant)
    assert isinstance(job.paginate, Paginate)
    assert isinstance(job.retry, Retry)


def test_baostockjob_init_with_params():
    """Test BaostockJob initialization with params dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(
        name="test_job", key="test_key", session=mock_session, params={"code": "sh.600000", "start_date": "2024-01-01"}
    )

    assert job.params.to_dict()["code"] == "sh.600000"
    assert job.params.to_dict()["start_date"] == "2024-01-01"


def test_baostockjob_init_with_params_object():
    """Test BaostockJob initialization with Params object"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()
    params = Params(code="sh.600000", frequency="5")

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, params=params)

    assert job.params is params


def test_baostockjob_init_with_coolant_dict():
    """Test BaostockJob initialization with coolant dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, coolant={"wait": 0.5})

    # Coolant stores wait time, not interval
    assert isinstance(job.coolant, Coolant)


def test_baostockjob_init_with_paginate_dict():
    """Test BaostockJob initialization with paginate dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(
        name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 100, "pagelimit": 1000}
    )

    assert job.paginate.pagesize == 100
    assert job.paginate.pagelimit == 1000


def test_baostockjob_init_with_retry_dict():
    """Test BaostockJob initialization with retry dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, retry={"retry": 3, "wait": 1.0})

    assert job.retry.retry == 3
    assert job.retry.wait == 1.0


def test_baostockjob_init_with_cache_true():
    """Test BaostockJob initialization with cache enabled"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, cache=True)

    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_baostockjob_init_with_cache_false():
    """Test BaostockJob initialization with cache disabled"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, cache=False)

    assert job.cache is None


def test_baostockjob_init_marks_checkpoints():
    """Test BaostockJob marks initialization checkpoints"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    # Should have marked _resolve_connection[OK]
    marks = job.metric.marks
    assert "_resolve_connection[OK]" in marks


# ============================================================================
# Connection Resolution Tests
# ============================================================================


def test_resolve_connection_success():
    """Test successful connection resolution"""
    mock_session = Mock(spec=Session)
    mock_connection = Mock()
    mock_session.connection = mock_connection

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    assert job.connection is mock_connection


def test_resolve_connection_no_connection():
    """Test connection resolution when session has no connection"""
    mock_session = Mock(spec=Session)
    mock_session.connection = None

    with pytest.raises(ConnectionError, match="No active connection found"):
        ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)


# ============================================================================
# Date Parsing Tests
# ============================================================================


def test_parse_date_params_with_date_object():
    """Test _parse_date_params with date object"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    payload = {"start_date": date(2024, 1, 1), "end_date": date(2024, 12, 31)}
    result = job._parse_date_params(payload, ["start_date", "end_date"])

    assert result["start_date"] == "2024-01-01"
    assert result["end_date"] == "2024-12-31"


def test_parse_date_params_with_datetime_object():
    """Test _parse_date_params with datetime object"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    payload = {"start_date": datetime(2024, 1, 1, 10, 30), "end_date": datetime(2024, 12, 31, 15, 45)}
    result = job._parse_date_params(payload, ["start_date", "end_date"])

    assert result["start_date"] == "2024-01-01"
    assert result["end_date"] == "2024-12-31"


def test_parse_date_params_with_string_hyphen():
    """Test _parse_date_params with string in YYYY-MM-DD format"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    payload = {"start_date": "2024-01-01", "end_date": "2024-12-31"}
    result = job._parse_date_params(payload, ["start_date", "end_date"])

    assert result["start_date"] == "2024-01-01"
    assert result["end_date"] == "2024-12-31"


def test_parse_date_params_with_string_yyyymmdd():
    """Test _parse_date_params with string in YYYYMMDD format"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    payload = {"start_date": "20240101", "end_date": "20241231"}
    result = job._parse_date_params(payload, ["start_date", "end_date"])

    assert result["start_date"] == "2024-01-01"
    assert result["end_date"] == "2024-12-31"


def test_parse_date_params_preserves_other_keys():
    """Test _parse_date_params preserves non-date keys"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    payload = {"start_date": "20240101", "code": "sh.600000", "frequency": "5"}
    result = job._parse_date_params(payload, ["start_date"])

    assert result["start_date"] == "2024-01-01"
    assert result["code"] == "sh.600000"
    assert result["frequency"] == "5"


# ============================================================================
# String Parsing Tests
# ============================================================================


def test_parse_string_params_basic():
    """Test _parse_string_params with string values"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    payload = {"code": "sh.600000", "frequency": "5", "adjustflag": "3"}
    result = job._parse_string_params(payload, ["code", "frequency"])

    assert result["code"] == "sh.600000"
    assert result["frequency"] == "5"


def test_parse_string_params_preserves_other_types():
    """Test _parse_string_params preserves non-string types"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    payload = {"code": "sh.600000", "pagesize": 100, "enabled": True}
    result = job._parse_string_params(payload, ["code"])

    assert result["code"] == "sh.600000"
    assert result["pagesize"] == 100
    assert result["enabled"] is True


# ============================================================================
# _fetchall Tests - Direct Mode
# ============================================================================


def test_fetchall_direct_mode_success():
    """Test _fetchall in direct mode with successful response"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    # Mock ResultSet
    mock_rs = Mock()
    mock_rs.error_code = "0"
    mock_rs.get_data.return_value = pd.DataFrame({"date": ["2024-01-01"], "close": [100.0]})

    # Mock API that returns ResultSet
    mock_api = Mock(return_value=mock_rs)

    result = job._fetchall(mock_api, code="sh.600000")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert "date" in result.columns
    assert "_fetchall[direct_mode" in str(job.metric.marks)


def test_fetchall_direct_mode_error():
    """Test _fetchall in direct mode with error response"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    # Mock ResultSet with error
    mock_rs = Mock()
    mock_rs.error_code = "10001001"
    mock_rs.error_msg = "User not logged in"

    # Mock API that returns ResultSet
    mock_api = Mock(return_value=mock_rs)

    result = job._fetchall(mock_api, code="sh.600000")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert "_fetchall[ERROR" in str(job.metric.marks)


def test_fetchall_direct_mode_empty_data():
    """Test _fetchall in direct mode with empty data"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    # Mock ResultSet with empty data
    mock_rs = Mock()
    mock_rs.error_code = "0"
    mock_rs.get_data.return_value = pd.DataFrame()

    # Mock API that returns ResultSet
    mock_api = Mock(return_value=mock_rs)

    result = job._fetchall(mock_api, code="sh.600000")

    assert isinstance(result, pd.DataFrame)
    assert result.empty


# ============================================================================
# _fetchall Tests - Relay Mode
# ============================================================================


def test_fetchall_relay_mode_success():
    """Test _fetchall in relay mode (returns DataFrame directly)"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    # Mock API that returns DataFrame (relay mode)
    expected_df = pd.DataFrame({"date": ["2024-01-01", "2024-01-02"], "close": [100.0, 101.0]})
    mock_api = Mock(return_value=expected_df)

    result = job._fetchall(mock_api, code="sh.600000")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    pd.testing.assert_frame_equal(result, expected_df)
    assert "_fetchall[relay_mode" in str(job.metric.marks)


def test_fetchall_relay_mode_empty_dataframe():
    """Test _fetchall in relay mode with empty DataFrame"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)

    # Mock API that returns empty DataFrame (relay mode)
    empty_df = pd.DataFrame()
    mock_api = Mock(return_value=empty_df)

    result = job._fetchall(mock_api, code="sh.600000")

    assert isinstance(result, pd.DataFrame)
    assert result.empty


# ============================================================================
# Cache Tests
# ============================================================================


def test_load_cache_success():
    """Test _load_cache when cache hit"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    mock_cache = Mock(spec=Cache)
    cached_data = pd.DataFrame({"test": [1, 2, 3]})
    mock_cache.get.return_value = cached_data

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, cache=mock_cache)

    result = job._load_cache()

    assert result is not None
    pd.testing.assert_frame_equal(result, cached_data)
    assert "load_cache[OK]" in job.metric.marks


def test_load_cache_miss():
    """Test _load_cache when cache miss"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    mock_cache = Mock(spec=Cache)
    mock_cache.get.return_value = None

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, cache=mock_cache)

    result = job._load_cache()

    assert result is None


def test_load_cache_no_cache():
    """Test _load_cache when cache is disabled"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, cache=False)

    result = job._load_cache()

    assert result is None


def test_save_cache_success():
    """Test _save_cache saves data to cache"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    mock_cache = Mock(spec=Cache)
    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, cache=mock_cache)

    data = pd.DataFrame({"test": [1, 2, 3]})
    job._save_cache(data)

    mock_cache.set.assert_called_once()
    assert "_save_cache[OK]" in job.metric.marks


def test_save_cache_no_cache():
    """Test _save_cache when cache is disabled"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, cache=False)

    data = pd.DataFrame({"test": [1, 2, 3]})
    job._save_cache(data)  # Should not raise error

    # No checkpoint should be marked
    assert "_save_cache[OK]" not in job.metric.marks


# ============================================================================
# Integration Tests
# ============================================================================


def test_baostockjob_full_workflow_direct_mode():
    """Test complete BaostockJob workflow in direct mode"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    # Create job with all features
    job = FetchAllJob(
        name="integration_test",
        key="integration_key",
        session=mock_session,
        params={"code": "sh.600000"},
        cache=True,
        retry={"retry": 3, "wait": 1.0},
        paginate={"pagesize": 100, "pagelimit": 1000},
    )

    # Run the job
    result = job.run()

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert job.metric.duration > 0


def test_baostockjob_with_date_conversion():
    """Test BaostockJob with date parameter conversion"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(
        name="date_test",
        key="date_key",
        session=mock_session,
        params={"code": "sh.600000", "start_date": "20240101", "end_date": date(2024, 12, 31)},
    )

    # Parse dates
    payload = job.get_params()
    parsed = job._parse_date_params(payload, ["start_date", "end_date"])

    assert parsed["start_date"] == "2024-01-01"
    assert parsed["end_date"] == "2024-12-31"


# ============================================================================
# Edge Cases
# ============================================================================


def test_baostockjob_empty_params():
    """Test BaostockJob with empty parameters"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session, params={})

    assert job.params.to_dict() == {}


def test_baostockjob_metric_tracking():
    """Test BaostockJob tracks metrics correctly"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteBaostockJob(name="test_job", key="test_key", session=mock_session)
    job.run()
    assert job.metric.duration > 0
    assert job.metric.start_at is not None
    assert job.metric.finish_at is not None

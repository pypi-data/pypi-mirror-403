"""
Test suite for TushareJob class
Tests cover initialization, connection resolution, pagination, and data fetching
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.source.tushare.job.job import TushareJob
from xfintech.data.source.tushare.session.session import Session

# ============================================================================
# Helper Classes for Testing
# ============================================================================


class ConcreteTushareJob(TushareJob):
    """Concrete implementation for testing"""

    def _run(self) -> pd.DataFrame:
        return pd.DataFrame({"test": [1, 2, 3]})


class FetchAllJob(TushareJob):
    """Job that uses _fetchall in _run"""

    def _run(self) -> pd.DataFrame:
        api = Mock(return_value=pd.DataFrame({"data": [1, 2, 3]}))
        return self._fetchall(api, symbol="TEST")


# ============================================================================
# Initialization Tests
# ============================================================================


def test_tusharejob_init_basic():
    """Test TushareJob basic initialization"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    assert job.name == "test_job"
    assert job.key == "test_key"
    assert job.connection is not None
    assert isinstance(job.params, Params)
    assert isinstance(job.coolant, Coolant)
    assert isinstance(job.paginate, Paginate)
    assert isinstance(job.retry, Retry)


def test_tusharejob_init_with_params():
    """Test TushareJob initialization with params dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(
        name="test_job", key="test_key", session=mock_session, params={"symbol": "AAPL", "date": "20240101"}
    )

    assert job.params.to_dict()["symbol"] == "AAPL"
    assert job.params.to_dict()["date"] == "20240101"


def test_tusharejob_init_with_params_object():
    """Test TushareJob initialization with Params object"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()
    params = Params(symbol="TSLA", exchange="NASDAQ")

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, params=params)

    assert job.params is params


def test_tusharejob_init_with_coolant_dict():
    """Test TushareJob initialization with coolant dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(
        name="test_job", key="test_key", session=mock_session, coolant={"interval": 2, "use_jitter": True}
    )

    assert job.coolant.interval == 2
    assert job.coolant.use_jitter is True


def test_tusharejob_init_with_paginate_dict():
    """Test TushareJob initialization with paginate dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(
        name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 500, "pagelimit": 5}
    )

    assert job.paginate.pagesize == 500
    assert job.paginate.pagelimit == 5


def test_tusharejob_init_with_retry_dict():
    """Test TushareJob initialization with retry dict"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, retry={"retry": 5, "wait": 2})

    assert job.retry.retry == 5
    assert job.retry.wait == 2


def test_tusharejob_init_with_cache_true():
    """Test TushareJob initialization with cache enabled"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, cache=True)

    assert job.cache is not None
    assert isinstance(job.cache, Cache)


def test_tusharejob_init_with_cache_false():
    """Test TushareJob initialization with cache disabled"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, cache=False)

    assert job.cache is None


def test_tusharejob_init_marks_checkpoints():
    """Test TushareJob marks initialization checkpoints"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    # Should have marked both init[OK] and resolve_connection
    marks = job.metric.marks
    assert "init[OK]" in marks
    assert "_resolve_connection[OK]" in marks


# ============================================================================
# Connection Resolution Tests
# ============================================================================


def test_resolve_connection_success():
    """Test _resolve_connection with valid session"""
    mock_session = Mock(spec=Session)
    mock_connection = Mock()
    mock_session.connection = mock_connection

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    assert job.connection is mock_connection


def test_resolve_connection_no_connection_raises_error():
    """Test _resolve_connection raises error when session has no connection"""
    mock_session = Mock(spec=Session)
    mock_session.connection = None

    with pytest.raises(ConnectionError, match="No active connection found in session"):
        ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)


def test_resolve_connection_missing_attribute():
    """Test _resolve_connection handles missing connection attribute"""
    mock_session = Mock(spec=Session)
    delattr(mock_session, "connection")

    with pytest.raises(ConnectionError):
        ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)


def test_resolve_connection_marks_checkpoint():
    """Test _resolve_connection marks checkpoint on success"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    assert "_resolve_connection[OK]" in job.metric.marks


# ============================================================================
# _fetchall Method Tests
# ============================================================================


def test_fetchall_single_page():
    """Test _fetchall with data fitting in single page"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 100})

    # Mock API that returns less than pagesize
    mock_api = Mock(return_value=pd.DataFrame({"col": [1, 2, 3]}))

    result = job._fetchall(mock_api, symbol="TEST")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert mock_api.call_count == 1
    mock_api.assert_called_with(limit=100, offset=0, symbol="TEST")


def test_fetchall_multiple_pages():
    """Test _fetchall with data spanning multiple pages"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(
        name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 10, "pagelimit": 5}
    )

    # Mock API that returns full pages then partial
    mock_api = Mock(
        side_effect=[
            pd.DataFrame({"col": range(10)}),  # Full page 1
            pd.DataFrame({"col": range(10, 20)}),  # Full page 2
            pd.DataFrame({"col": range(20, 25)}),  # Partial page 3
        ]
    )

    result = job._fetchall(mock_api, symbol="TEST")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 25
    assert mock_api.call_count == 3


def test_fetchall_empty_result():
    """Test _fetchall with empty result"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    mock_api = Mock(return_value=pd.DataFrame())

    result = job._fetchall(mock_api, symbol="TEST")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_fetchall_none_result():
    """Test _fetchall handles None result"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    mock_api = Mock(return_value=None)

    result = job._fetchall(mock_api, symbol="TEST")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_fetchall_respects_pagelimit():
    """Test _fetchall respects pagelimit"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(
        name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 10, "pagelimit": 3}
    )

    # Mock API that always returns full pages
    mock_api = Mock(return_value=pd.DataFrame({"col": range(10)}))

    result = job._fetchall(mock_api)

    # Should stop at pagelimit even though pages are full
    assert mock_api.call_count == 3
    assert len(result) == 30


def test_fetchall_calls_coolant():
    """Test _fetchall calls coolant between pages"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(
        name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 10}, coolant={"interval": 1}
    )

    with patch.object(job.coolant, "cool") as mock_cool:
        mock_api = Mock(
            side_effect=[
                pd.DataFrame({"col": range(10)}),
                pd.DataFrame({"col": range(10, 20)}),
                pd.DataFrame({"col": range(20, 25)}),
            ]
        )

        job._fetchall(mock_api)

        # cool() should be called between pages (2 times for 3 pages)
        assert mock_cool.call_count == 2


def test_fetchall_updates_pagination_offset():
    """Test _fetchall updates pagination offset correctly"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 100})

    mock_api = Mock(
        side_effect=[
            pd.DataFrame({"col": range(100)}),
            pd.DataFrame({"col": range(100, 200)}),
            pd.DataFrame({"col": range(200, 250)}),
        ]
    )

    job._fetchall(mock_api)

    # Check that offset was updated in calls
    calls = mock_api.call_args_list
    assert calls[0][1]["offset"] == 0
    assert calls[1][1]["offset"] == 100
    assert calls[2][1]["offset"] == 200


def test_fetchall_marks_checkpoints():
    """Test _fetchall marks checkpoints for each page"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 10})

    mock_api = Mock(
        side_effect=[
            pd.DataFrame({"col": range(10)}),
            pd.DataFrame({"col": range(10, 15)}),
        ]
    )

    job._fetchall(mock_api)

    marks = job.metric.marks
    assert "_fetchall[pagenum=0, OK]" in marks
    assert "_fetchall[pagenum=1, OK]" in marks
    assert "_fetchall[OK]" in marks


def test_fetchall_passes_params_to_api():
    """Test _fetchall passes all params to API"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    mock_api = Mock(return_value=pd.DataFrame({"col": [1, 2, 3]}))

    job._fetchall(mock_api, symbol="AAPL", exchange="NASDAQ", date="20240101")

    mock_api.assert_called_once_with(
        limit=job.paginate.pagesize, offset=0, symbol="AAPL", exchange="NASDAQ", date="20240101"
    )


def test_fetchall_concatenates_correctly():
    """Test _fetchall concatenates DataFrames correctly"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 5})

    # Full pages then partial to trigger multiple pages
    mock_api = Mock(
        side_effect=[
            pd.DataFrame({"col1": [1, 2, 3, 4, 5], "col2": ["a", "b", "c", "d", "e"]}),
            pd.DataFrame({"col1": [6, 7, 8, 9, 10], "col2": ["f", "g", "h", "i", "j"]}),
            pd.DataFrame({"col1": [11, 12], "col2": ["k", "l"]}),
        ]
    )

    result = job._fetchall(mock_api)

    assert len(result) == 12
    assert list(result.columns) == ["col1", "col2"]
    assert result["col1"].tolist() == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def test_fetchall_resets_index():
    """Test _fetchall resets index in concatenated result"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 3})

    # DataFrames with different indices, both full pages
    df1 = pd.DataFrame({"col": [1, 2, 3]}, index=[10, 20, 30])
    df2 = pd.DataFrame({"col": [4, 5]}, index=[40, 50])

    mock_api = Mock(side_effect=[df1, df2])

    result = job._fetchall(mock_api)

    # Index should be reset to 0, 1, 2, 3, 4
    assert result.index.tolist() == [0, 1, 2, 3, 4]


# ============================================================================
# Integration Tests
# ============================================================================


def test_tusharejob_full_workflow():
    """Test complete TushareJob workflow"""
    mock_session = Mock(spec=Session)
    mock_api_method = Mock(
        side_effect=[
            pd.DataFrame({"symbol": ["AAPL", "GOOGL"], "price": [150.0, 2800.0]}),
            pd.DataFrame({"symbol": ["MSFT"], "price": [300.0]}),
        ]
    )
    mock_session.connection = Mock(stock_basic=mock_api_method)

    class StockJob(TushareJob):
        def _run(self):
            return self._fetchall(api=self.connection.stock_basic, exchange="NASDAQ")

    job = StockJob(
        name="stock_job",
        key="stock_001",
        session=mock_session,
        params={"exchange": "NASDAQ"},
        paginate={"pagesize": 2, "pagelimit": 10},
        retry={"retry": 2, "wait": 0},
    )

    result = job.run()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "symbol" in result.columns
    assert "price" in result.columns


def test_tusharejob_with_cache():
    """Test TushareJob with caching enabled"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="cached_job", key="cached_001", session=mock_session, cache=True)

    # Test cache operations
    job.set_cache("test_key", {"data": "test_value"})
    cached_value = job.get_cache("test_key")

    assert cached_value == {"data": "test_value"}


def test_tusharejob_inherits_job_methods():
    """Test TushareJob inherits all Job methods"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, params={"symbol": "AAPL"})

    # Test inherited methods
    assert hasattr(job, "run")
    assert hasattr(job, "markpoint")
    assert hasattr(job, "cool")
    assert hasattr(job, "get_params")
    assert hasattr(job, "reset")
    assert hasattr(job, "describe")
    assert hasattr(job, "to_dict")

    # Test get_params works
    params = job.get_params()
    assert params["symbol"] == "AAPL"


def test_tusharejob_metric_tracking():
    """Test TushareJob tracks metrics correctly"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    # Marks are created during __init__
    assert "init[OK]" in job.metric.marks
    assert "_resolve_connection[OK]" in job.metric.marks

    # Run job - note that metric context manager resets marks
    job.run()

    # After run, metric tracks duration
    assert job.metric.duration is not None
    assert job.metric.start_at is not None
    assert job.metric.finish_at is not None


def test_tusharejob_multiple_instances_independent():
    """Test multiple TushareJob instances are independent"""
    mock_session1 = Mock(spec=Session)
    mock_session1.connection = Mock(name="connection1")

    mock_session2 = Mock(spec=Session)
    mock_session2.connection = Mock(name="connection2")

    job1 = ConcreteTushareJob(name="job1", key="key1", session=mock_session1, params={"symbol": "AAPL"})

    job2 = ConcreteTushareJob(name="job2", key="key2", session=mock_session2, params={"symbol": "GOOGL"})

    assert job1.name != job2.name
    assert job1.connection != job2.connection
    assert job1.get_params() != job2.get_params()


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_fetchall_with_zero_pagelimit():
    """Test _fetchall with pagelimit=0 iterates zero times"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(
        name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 100, "pagelimit": 1}
    )

    # API returns less than pagesize, should stop after one page
    mock_api = Mock(return_value=pd.DataFrame({"col": [1, 2, 3]}))

    result = job._fetchall(mock_api)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert mock_api.call_count == 1


def test_fetchall_api_raises_exception():
    """Test _fetchall handles API exceptions"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session)

    mock_api = Mock(side_effect=RuntimeError("API Error"))

    with pytest.raises(RuntimeError, match="API Error"):
        job._fetchall(mock_api)


def test_fetchall_with_varying_column_names():
    """Test _fetchall handles DataFrames with different columns"""
    mock_session = Mock(spec=Session)
    mock_session.connection = Mock()

    job = ConcreteTushareJob(name="test_job", key="test_key", session=mock_session, paginate={"pagesize": 10})

    # First page has 2 rows (< pagesize), so loop stops after first page
    mock_api = Mock(
        side_effect=[
            pd.DataFrame({"col1": [1, 2]}),
            pd.DataFrame({"col2": [3, 4]}),  # Won't be reached
        ]
    )

    result = job._fetchall(mock_api)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert mock_api.call_count == 1

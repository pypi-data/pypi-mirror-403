"""
Test suite for Session class
Tests cover initialization, connection modes, state management, and session lifecycle
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from xfintech.data.source.baostock.session.session import Session

# ============================================================================
# Session Initialization Tests - Direct Mode
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_init_direct_mode_basic(mock_bs):
    """Test Session initialization in direct mode"""
    mock_bs.login.return_value = Mock()

    session = Session(mode="direct")

    assert session.mode == "direct"
    assert session._credential is None
    assert session.relay_url is None
    assert session.relay_secret is None
    assert len(session.id) == 8
    assert session.connected is True


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_init_direct_mode_default(mock_bs):
    """Test Session defaults to direct mode"""
    mock_bs.login.return_value = Mock()

    session = Session()

    assert session.mode == "direct"


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_init_direct_mode_uppercase(mock_bs):
    """Test Session handles uppercase mode"""
    mock_bs.login.return_value = Mock()

    session = Session(mode="DIRECT")

    assert session.mode == "direct"


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_init_direct_calls_login(mock_bs):
    """Test Session calls bs.login in direct mode"""
    mock_bs.login.return_value = Mock()

    Session(mode="direct")

    mock_bs.login.assert_called_once()


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_init_direct_creates_connection(mock_bs):
    """Test Session creates baostock connection"""
    mock_bs.login.return_value = Mock()

    session = Session(mode="direct")

    assert session.connection is mock_bs


# ============================================================================
# Session Resolve Methods Tests
# ============================================================================


def test_session_resolve_mode_invalid():
    """Test _resolve_mode raises error with invalid mode"""
    with pytest.raises(ValueError, match="Unsupported mode"):
        Session(mode="invalid")


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_resolve_mode_empty_returns_direct(mock_bs):
    """Test _resolve_mode returns 'direct' for empty string"""
    mock_bs.login.return_value = Mock()

    session = Session(mode="")

    assert session.mode == "direct"


# ============================================================================
# Session ID Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_id_length(mock_bs):
    """Test Session ID is 8 characters"""
    mock_bs.login.return_value = Mock()

    session = Session()

    assert len(session.id) == 8


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_id_unique(mock_bs):
    """Test different Sessions have different IDs"""
    mock_bs.login.return_value = Mock()

    session1 = Session()
    session2 = Session()

    assert session1.id != session2.id


# ============================================================================
# Session Properties Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_connected_property_true(mock_bs):
    """Test connected property returns True when connection exists"""
    mock_bs.login.return_value = Mock()

    session = Session()

    assert session.connected is True


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_connected_property_false(mock_bs):
    """Test connected property returns False when no connection"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.connection = None

    assert session.connected is False


@patch("xfintech.data.source.baostock.session.session.bs")
@patch("xfintech.data.source.baostock.session.session.pd.Timestamp")
def test_session_duration_property_no_start(mock_timestamp, mock_bs):
    """Test duration returns 0.0 when not started"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.start_at = None

    assert session.duration == 0.0


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_duration_property_ongoing(mock_bs):
    """Test duration calculates correctly for ongoing session"""
    mock_bs.login.return_value = Mock()

    # Create session
    session = Session()

    # Set times directly
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = None

    # Mock datetime.now to return a specific time
    with patch(
        "xfintech.data.source.baostock.session.session.datetime",
    ) as mock_datetime:
        mock_now = datetime(2024, 1, 15, 10, 0, 10)
        mock_datetime.now.return_value = mock_now

        duration = session.duration

        assert duration == 10.0


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_duration_property_finished(mock_bs):
    """Test duration calculates correctly for finished session"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")

    assert session.duration == 30.0


# ============================================================================
# Session String Representation Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_str(mock_bs):
    """Test __str__ returns session ID"""
    mock_bs.login.return_value = Mock()

    session = Session()

    assert str(session) == session.id


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_repr(mock_bs):
    """Test __repr__ includes class name, connected status, and mode"""
    mock_bs.login.return_value = Mock()

    session = Session(mode="direct")

    result = repr(session)
    assert "Session" in result
    assert "connected=True" in result
    assert "mode=direct" in result


@patch("xfintech.data.source.baostock.session.session.BaostockRelayClient")
def test_session_repr_relay_mode(mock_relay_client_class):
    """Test __repr__ shows relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True
    mock_relay_client_class.return_value = mock_client

    session = Session(
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )

    result = repr(session)
    assert "mode=relay" in result


# ============================================================================
# Session Start/End Methods Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
@patch("xfintech.data.source.baostock.session.session.pd.Timestamp")
def test_session_start_method(mock_timestamp, mock_bs):
    """Test start method sets start_at"""
    mock_bs.login.return_value = Mock()
    mock_now = pd.Timestamp("2024-01-15 10:00:00")
    mock_timestamp.now.return_value = mock_now

    session = Session()
    session.start_at = None
    session.start()

    assert session.start_at == mock_now


@patch("xfintech.data.source.baostock.session.session.bs")
@patch("xfintech.data.source.baostock.session.session.pd.Timestamp")
def test_session_end_method(mock_timestamp, mock_bs):
    """Test end method sets finish_at"""
    mock_bs.login.return_value = Mock()
    mock_now = pd.Timestamp("2024-01-15 10:00:30")
    mock_timestamp.now.return_value = mock_now

    session = Session()
    session.end()

    assert session.finish_at == mock_now


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_get_start_iso_none(mock_bs):
    """Test get_start_iso returns None when start_at is None"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.start_at = None

    assert session.get_start_iso() is None


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_get_start_iso_with_value(mock_bs):
    """Test get_start_iso returns ISO format"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")

    result = session.get_start_iso()
    assert "2024-01-15" in result


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_get_finish_iso_none(mock_bs):
    """Test get_finish_iso returns None when finish_at is None"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.finish_at = None

    assert session.get_finish_iso() is None


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_get_finish_iso_with_value(mock_bs):
    """Test get_finish_iso returns ISO format"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")
    session = Session()
    session.connection = None

    result = session.connect()

    assert result is not None


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_connect_already_connected(mock_bs):
    """Test connect returns existing connection if already connected"""
    mock_bs.login.return_value = Mock()

    session = Session()
    first_connection = session.connection

    # Reset call count
    mock_bs.login.reset_mock()

    # Try to connect again
    result = session.connect()

    assert result is first_connection
    # Should not call login again
    mock_bs.login.assert_not_called()


@patch("xfintech.data.source.baostock.session.session.bs")
@patch("xfintech.data.source.baostock.session.session.pd.Timestamp")
def test_session_disconnect_clears_connection(mock_timestamp, mock_bs):
    """Test disconnect clears connection"""
    mock_bs.login.return_value = Mock()
    mock_bs.logout.return_value = Mock()

    session = Session()
    assert session.connected is True

    session.disconnect()

    assert session.connection is None
    assert session.connected is False
    mock_bs.logout.assert_called_once()


@patch("xfintech.data.source.baostock.session.session.bs")
@patch("xfintech.data.source.baostock.session.session.pd.Timestamp")
def test_session_disconnect_sets_finish_time(mock_timestamp, mock_bs):
    """Test disconnect sets finish_at"""
    mock_bs.login.return_value = Mock()
    mock_bs.logout.return_value = Mock()
    mock_now = pd.Timestamp("2024-01-15 10:00:30")
    mock_timestamp.now.return_value = mock_now

    session = Session()
    session.disconnect()

    assert session.finish_at == mock_now


# ============================================================================
# Session Describe Method Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_describe_basic(mock_bs):
    """Test describe returns basic session info"""
    mock_bs.login.return_value = Mock()

    session = Session(mode="direct")
    result = session.describe()

    assert "id" in result
    assert result["id"] == session.id
    assert "mode" in result
    assert result["mode"] == "direct"
    assert "connected" in result
    assert result["connected"] is True


@patch("xfintech.data.source.baostock.session.session.BaostockRelayClient")
def test_session_describe_relay_mode(mock_relay_client_class):
    """Test describe includes relay info in relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_describe_with_timestamps(mock_bs):
    """Test describe includes timestamps when available"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")

    result = session.describe()

    assert "start_at" in result
    assert "finish_at" in result


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_describe_without_finish(mock_bs):
    """Test describe handles ongoing session"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.finish_at = None

    result = session.describe()

    assert "start_at" in result
    assert "finish_at" not in result


# ============================================================================
# Session To Dict Method Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_to_dict_structure(mock_bs):
    """Test to_dict returns expected structure"""
    mock_bs.login.return_value = Mock()

    session = Session(mode="direct")
    result = session.to_dict()

    assert "id" in result
    assert "connected" in result
    assert "mode" in result
    assert "relay" in result
    assert "start_at" in result
    assert "finish_at" in result
    assert "duration" in result


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_to_dict_includes_duration(mock_bs):
    """Test to_dict includes duration"""
    mock_bs.login.return_value = Mock()

    session = Session()
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")

    result = session.to_dict()

    assert result["duration"] == 30.0


# ============================================================================
# Integration Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_full_lifecycle_direct(mock_bs):
    """Test complete session lifecycle in direct mode"""
    mock_bs.login.return_value = Mock()
    mock_bs.logout.return_value = Mock()

    # Create session
    session = Session(mode="direct")
    assert session.connected is True

    # Use connection
    assert session.connection is mock_bs

    # Disconnect
    session.disconnect()
    assert session.connected is False
    assert session.finish_at is not None
    mock_bs.logout.assert_called_once()


@patch("xfintech.data.source.baostock.session.session.bs")
def test_session_reconnect(mock_bs):
    """Test reconnecting after disconnect"""
    mock_bs.login.return_value = Mock()
    mock_bs.logout.return_value = Mock()

    session = Session()
    session.disconnect()

    # Reconnect
    session.connect()

    assert session.connected is True
    assert session.connection is not None

"""
Test suite for Session class
Tests cover initialization, connection modes, state management, and session lifecycle
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from xfintech.data.source.tushare.session.relay import RelayConnection
from xfintech.data.source.tushare.session.session import Session

# ============================================================================
# Session Initialization Tests - Direct Mode
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_init_direct_mode_basic(mock_ts):
    """Test Session initialization in direct mode"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token", mode="direct")

    assert session.mode == "direct"
    assert session._credential == "test-token"
    assert session.relay_url is None
    assert session.relay_secret is None
    assert len(session.id) == 8
    assert session.connected is True


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_init_direct_mode_default(mock_ts):
    """Test Session defaults to direct mode"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")

    assert session.mode == "direct"


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_init_direct_mode_uppercase(mock_ts):
    """Test Session handles uppercase mode"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token", mode="DIRECT")

    assert session.mode == "direct"


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_init_direct_sets_token(mock_ts):
    """Test Session sets tushare token in direct mode"""
    mock_ts.pro_api.return_value = Mock()

    Session(credential="test-token", mode="direct")

    mock_ts.set_token.assert_called_once_with("test-token")


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_init_direct_creates_connection(mock_ts):
    """Test Session creates pro_api connection"""
    mock_api = Mock()
    mock_ts.pro_api.return_value = mock_api

    session = Session(credential="test-token", mode="direct")

    assert session.connection is mock_api
    mock_ts.pro_api.assert_called_once()


# ============================================================================
# Session Initialization Tests - Relay Mode
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_init_relay_mode_basic(mock_relay_client_class):
    """Test Session initialization in relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True
    mock_relay_client_class.return_value = mock_client

    session = Session(
        credential="test-token",
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )

    assert session.mode == "relay"
    assert session.relay_url == "https://relay.example.com"
    assert session.relay_secret == "relay-secret"
    assert session.connected is True


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_init_relay_mode_creates_client(mock_relay_client_class):
    """Test Session creates RelayClient in relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True
    mock_relay_client_class.return_value = mock_client

    Session(
        credential="test-token",
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )

    mock_relay_client_class.assert_called_once_with(
        url="https://relay.example.com",
        secret="relay-secret",
    )


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_init_relay_mode_checks_health(mock_relay_client_class):
    """Test Session checks health in relay mode"""
    mock_client = Mock()
    mock_relay_client_class.return_value = mock_client

    Session(
        credential="test-token",
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )

    mock_client.check_health.assert_called_once()


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_init_relay_mode_connection_type(mock_relay_client_class):
    """Test Session connection is RelayConnection in relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True
    mock_relay_client_class.return_value = mock_client

    session = Session(
        credential="test-token",
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )

    assert isinstance(session.connection, RelayConnection)


def test_session_init_relay_mode_missing_url():
    """Test Session raises error when relay_url is missing in relay mode"""
    with pytest.raises(ValueError, match="URL must be provided in relay mode"):
        Session(
            credential="test-token",
            mode="relay",
            relay_secret="relay-secret",
        )


def test_session_init_relay_mode_missing_secret():
    """Test Session raises error when relay_secret is missing in relay mode"""
    with pytest.raises(ValueError, match="Secret must be provided in relay mode"):
        Session(
            credential="test-token",
            mode="relay",
            relay_url="https://relay.example.com",
        )


# ============================================================================
# Session Resolve Methods Tests
# ============================================================================


def test_session_resolve_mode_invalid():
    """Test _resolve_mode raises error with invalid mode"""
    with pytest.raises(ValueError, match="Unsupported mode"):
        Session(credential="test-token", mode="invalid")


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_resolve_mode_empty_returns_direct(mock_ts):
    """Test _resolve_mode returns 'direct' for empty string"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token", mode="")

    assert session.mode == "direct"


# ============================================================================
# Session ID Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_id_length(mock_ts):
    """Test Session ID is 8 characters"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")

    assert len(session.id) == 8


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_id_unique(mock_ts):
    """Test different Sessions have different IDs"""
    mock_ts.pro_api.return_value = Mock()

    session1 = Session(credential="test-token")
    session2 = Session(credential="test-token")

    assert session1.id != session2.id


# ============================================================================
# Session Properties Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_connected_property_true(mock_ts):
    """Test connected property returns True when connection exists"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")

    assert session.connected is True


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_connected_property_false(mock_ts):
    """Test connected property returns False when no connection"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.connection = None

    assert session.connected is False


@patch("xfintech.data.source.tushare.session.session.ts")
@patch("xfintech.data.source.tushare.session.session.pd.Timestamp")
def test_session_duration_property_no_start(mock_timestamp, mock_ts):
    """Test duration returns 0.0 when not started"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.start_at = None

    assert session.duration == 0.0


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_duration_property_ongoing(mock_ts):
    """Test duration calculates correctly for ongoing session"""
    mock_ts.pro_api.return_value = Mock()

    # Create session
    session = Session(credential="test-token")

    # Set times directly
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = None

    # Mock datetime.now to return a specific time
    with patch(
        "xfintech.data.source.tushare.session.session.datetime",
    ) as mock_datetime:
        mock_now = datetime(2024, 1, 15, 10, 0, 10)
        mock_datetime.now.return_value = mock_now

        duration = session.duration

        assert duration == 10.0


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_duration_property_finished(mock_ts):
    """Test duration calculates correctly for finished session"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")

    assert session.duration == 30.0


# ============================================================================
# Session String Representation Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_str(mock_ts):
    """Test __str__ returns session ID"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")

    assert str(session) == session.id


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_repr(mock_ts):
    """Test __repr__ includes class name, connected status, and mode"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token", mode="direct")

    result = repr(session)
    assert "Session" in result
    assert "connected=True" in result
    assert "mode=direct" in result


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_repr_relay_mode(mock_relay_client_class):
    """Test __repr__ shows relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True
    mock_relay_client_class.return_value = mock_client

    session = Session(
        credential="test-token",
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )

    result = repr(session)
    assert "mode=relay" in result


# ============================================================================
# Session Start/End Methods Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
@patch("xfintech.data.source.tushare.session.session.pd.Timestamp")
def test_session_start_method(mock_timestamp, mock_ts):
    """Test start method sets start_at"""
    mock_ts.pro_api.return_value = Mock()
    mock_now = pd.Timestamp("2024-01-15 10:00:00")
    mock_timestamp.now.return_value = mock_now

    session = Session(credential="test-token")
    session.start_at = None
    session.start()

    assert session.start_at == mock_now


@patch("xfintech.data.source.tushare.session.session.ts")
@patch("xfintech.data.source.tushare.session.session.pd.Timestamp")
def test_session_end_method(mock_timestamp, mock_ts):
    """Test end method sets finish_at"""
    mock_ts.pro_api.return_value = Mock()
    mock_now = pd.Timestamp("2024-01-15 10:00:30")
    mock_timestamp.now.return_value = mock_now

    session = Session(credential="test-token")
    session.end()

    assert session.finish_at == mock_now


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_get_start_iso_none(mock_ts):
    """Test get_start_iso returns None when start_at is None"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.start_at = None

    assert session.get_start_iso() is None


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_get_start_iso_with_value(mock_ts):
    """Test get_start_iso returns ISO format"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")

    result = session.get_start_iso()
    assert "2024-01-15" in result


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_get_finish_iso_none(mock_ts):
    """Test get_finish_iso returns None when finish_at is None"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.finish_at = None

    assert session.get_finish_iso() is None


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_get_finish_iso_with_value(mock_ts):
    """Test get_finish_iso returns ISO format"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")

    result = session.get_finish_iso()
    assert "2024-01-15" in result


# ============================================================================
# Session Connect/Disconnect Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_connect_returns_connection(mock_ts):
    """Test connect returns connection object"""
    mock_api = Mock()
    mock_ts.pro_api.return_value = mock_api

    session = Session(credential="test-token")
    session.connection = None

    result = session.connect()

    assert result is not None


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_connect_already_connected(mock_ts):
    """Test connect returns existing connection if already connected"""
    mock_api = Mock()
    mock_ts.pro_api.return_value = mock_api

    session = Session(credential="test-token")
    first_connection = session.connection

    # Reset call count
    mock_ts.pro_api.reset_mock()

    # Try to connect again
    result = session.connect()

    assert result is first_connection
    # Should not create new connection
    mock_ts.pro_api.assert_not_called()


@patch("xfintech.data.source.tushare.session.session.ts")
@patch("xfintech.data.source.tushare.session.session.pd.Timestamp")
def test_session_disconnect_clears_connection(mock_timestamp, mock_ts):
    """Test disconnect clears connection"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    assert session.connected is True

    session.disconnect()

    assert session.connection is None
    assert session.connected is False


@patch("xfintech.data.source.tushare.session.session.ts")
@patch("xfintech.data.source.tushare.session.session.pd.Timestamp")
def test_session_disconnect_sets_finish_time(mock_timestamp, mock_ts):
    """Test disconnect sets finish_at"""
    mock_ts.pro_api.return_value = Mock()
    mock_now = pd.Timestamp("2024-01-15 10:00:30")
    mock_timestamp.now.return_value = mock_now

    session = Session(credential="test-token")
    session.disconnect()

    assert session.finish_at == mock_now


# ============================================================================
# Session Describe Method Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_describe_basic(mock_ts):
    """Test describe returns basic session info"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token", mode="direct")
    result = session.describe()

    assert "id" in result
    assert result["id"] == session.id
    assert "mode" in result
    assert result["mode"] == "direct"
    assert "connected" in result
    assert result["connected"] is True


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_describe_masks_credential(mock_ts):
    """Test describe masks credential"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    result = session.describe()

    assert result["credential"] == "******"


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_describe_no_credential(mock_ts):
    """Test describe handles None credential"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential=None)
    result = session.describe()

    assert "credential" not in result


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_describe_relay_mode(mock_relay_client_class):
    """Test describe includes relay info in relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True
    mock_relay_client_class.return_value = mock_client

    session = Session(
        credential="test-token",
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )
    result = session.describe()

    assert "relay" in result
    assert result["relay"]["url"] == "https://relay.example.com"
    assert result["relay"]["secret"] == "******"


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_describe_with_timestamps(mock_ts):
    """Test describe includes timestamps when available"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")

    result = session.describe()

    assert "start_at" in result
    assert "finish_at" in result


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_describe_without_finish(mock_ts):
    """Test describe handles ongoing session"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.finish_at = None

    result = session.describe()

    assert "start_at" in result
    assert "finish_at" not in result


# ============================================================================
# Session To Dict Method Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_to_dict_structure(mock_ts):
    """Test to_dict returns expected structure"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token", mode="direct")
    result = session.to_dict()

    assert "id" in result
    assert "connected" in result
    assert "credential" in result
    assert "mode" in result
    assert "relay" in result
    assert "start_at" in result
    assert "finish_at" in result
    assert "duration" in result


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_to_dict_masks_credential(mock_ts):
    """Test to_dict masks credential"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    result = session.to_dict()

    assert result["credential"] == "******"


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_to_dict_none_credential(mock_ts):
    """Test to_dict handles None credential"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential=None)
    result = session.to_dict()

    assert result["credential"] is None


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_to_dict_includes_duration(mock_ts):
    """Test to_dict includes duration"""
    mock_ts.pro_api.return_value = Mock()

    session = Session(credential="test-token")
    session.start_at = pd.Timestamp("2024-01-15 10:00:00")
    session.finish_at = pd.Timestamp("2024-01-15 10:00:30")

    result = session.to_dict()

    assert result["duration"] == 30.0


# ============================================================================
# Integration Tests
# ============================================================================


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_full_lifecycle_direct(mock_ts):
    """Test complete session lifecycle in direct mode"""
    mock_api = Mock()
    mock_ts.pro_api.return_value = mock_api

    # Create session
    session = Session(credential="test-token", mode="direct")
    assert session.connected is True

    # Use connection
    assert session.connection is mock_api

    # Disconnect
    session.disconnect()
    assert session.connected is False
    assert session.finish_at is not None


@patch("xfintech.data.source.tushare.session.session.TushareRelayClient")
def test_session_full_lifecycle_relay(mock_relay_client_class):
    """Test complete session lifecycle in relay mode"""
    mock_client = Mock()
    mock_client.check_health.return_value = True
    mock_relay_client_class.return_value = mock_client

    # Create session
    session = Session(
        credential="test-token",
        mode="relay",
        relay_url="https://relay.example.com",
        relay_secret="relay-secret",
    )
    assert session.connected is True
    assert isinstance(session.connection, RelayConnection)

    # Get description
    desc = session.describe()
    assert desc["mode"] == "relay"
    assert desc["relay"]["secret"] == "******"

    # Disconnect
    session.disconnect()
    assert session.connected is False


@patch("xfintech.data.source.tushare.session.session.ts")
def test_session_reconnect(mock_ts):
    """Test reconnecting after disconnect"""
    mock_api = Mock()
    mock_ts.pro_api.return_value = mock_api

    session = Session(credential="test-token")
    session.disconnect()

    # Reconnect
    session.connect()

    assert session.connected is True
    assert session.connection is not None

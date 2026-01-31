"""
Test suite for BaostockRelayClient and RelayConnection classes
Tests cover initialization, authentication, API calls, and health checks
"""

import gzip
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from xfintech.data.source.baostock.session.relay import BaostockRelayClient, RelayConnection

# ============================================================================
# BaostockRelayClient Initialization Tests
# ============================================================================


def test_relay_client_init_basic():
    """Test BaostockRelayClient initialization with basic parameters"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    assert client.url == "https://relay.example.com"
    assert client.secret == "test-secret"
    assert client.timeout == 180


def test_relay_client_init_custom_timeout():
    """Test BaostockRelayClient initialization with custom timeout"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
        timeout=300,
    )
    assert client.timeout == 300


def test_relay_client_init_strips_trailing_slash():
    """Test BaostockRelayClient strips trailing slash from URL"""
    client = BaostockRelayClient(
        url="https://relay.example.com/",
        secret="test-secret",
    )
    assert client.url == "https://relay.example.com"


def test_relay_client_init_multiple_trailing_slashes():
    """Test BaostockRelayClient strips multiple trailing slashes"""
    client = BaostockRelayClient(
        url="https://relay.example.com///",
        secret="test-secret",
    )
    assert client.url == "https://relay.example.com"


def test_relay_client_init_empty_url():
    """Test BaostockRelayClient raises error with empty URL"""
    with pytest.raises(ValueError, match="Relay URL must be provided"):
        BaostockRelayClient(
            url="",
            secret="test-secret",
        )


def test_relay_client_init_none_url():
    """Test BaostockRelayClient raises error with None URL"""
    with pytest.raises(ValueError, match="Relay URL must be provided"):
        BaostockRelayClient(
            url=None,
            secret="test-secret",
        )


def test_relay_client_init_empty_secret():
    """Test BaostockRelayClient raises error with empty secret"""
    with pytest.raises(ValueError, match="Relay secret must be provided"):
        BaostockRelayClient(url="https://relay.example.com", secret="")


def test_relay_client_init_none_secret():
    """Test BaostockRelayClient raises error with None secret"""
    with pytest.raises(ValueError, match="Relay secret must be provided"):
        BaostockRelayClient(url="https://relay.example.com", secret=None)


def test_relay_client_init_strips_secret_whitespace():
    """Test BaostockRelayClient strips whitespace from secret"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="  test-secret  ",
    )
    assert client.secret == "test-secret"


# ============================================================================
# BaostockRelayClient Resolve Methods Tests
# ============================================================================


def test_relay_client_resolve_timeout_default():
    """Test _resolve_timeout returns default when None"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    assert client._resolve_timeout(None) == 180


def test_relay_client_resolve_timeout_valid():
    """Test _resolve_timeout returns valid timeout"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    assert client._resolve_timeout(300) == 300


def test_relay_client_resolve_timeout_invalid_type():
    """Test _resolve_timeout raises error with invalid type"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    with pytest.raises(ValueError, match="Timeout must be an integer"):
        client._resolve_timeout("invalid")


def test_relay_client_resolve_timeout_zero():
    """Test _resolve_timeout returns default when zero"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    assert client._resolve_timeout(0) == 180


def test_relay_client_resolve_timeout_negative():
    """Test _resolve_timeout returns default when negative"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    assert client._resolve_timeout(-100) == 180


# ============================================================================
# BaostockRelayClient Canonical JSON Tests
# ============================================================================


def test_relay_client_canonical_json_simple():
    """Test canonical_json with simple data"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    result = client.canonical_json({"key": "value"})
    assert isinstance(result, bytes)
    assert result == b'{"key":"value"}'


def test_relay_client_canonical_json_sorted_keys():
    """Test canonical_json sorts keys"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    result = client.canonical_json({"z": 1, "a": 2, "m": 3})
    assert result == b'{"a":2,"m":3,"z":1}'


def test_relay_client_canonical_json_no_spaces():
    """Test canonical_json has no spaces"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    result = client.canonical_json({"key": "value", "num": 42})
    assert b" " not in result


def test_relay_client_canonical_json_unicode():
    """Test canonical_json handles unicode"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    result = client.canonical_json({"中文": "测试"})
    assert "中文" in result.decode("utf-8")


def test_relay_client_canonical_json_nested():
    """Test canonical_json with nested structure"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    data = {"outer": {"inner": {"deep": "value"}}}
    result = client.canonical_json(data)
    assert result == b'{"outer":{"inner":{"deep":"value"}}}'


# ============================================================================
# BaostockRelayClient Call Method Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.relay.requests.post")
@patch("xfintech.data.source.baostock.session.relay.pd.read_parquet")
def test_relay_client_call_basic(mock_read_parquet, mock_post):
    """Test call method with basic parameters"""
    # Setup mocks
    mock_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    mock_read_parquet.return_value = mock_df

    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    # Create client and call
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    result = client.call(
        method="query_history_k_data_plus",
        params={"code": "sh.600000", "start_date": "2024-01-01"},
    )

    # Verify
    assert isinstance(result, pd.DataFrame)
    assert mock_post.called
    assert mock_read_parquet.called


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_call_correct_url(mock_post):
    """Test call method uses correct URL"""
    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    with patch("xfintech.data.source.baostock.session.relay.pd.read_parquet"):
        client = BaostockRelayClient(
            url="https://relay.example.com",
            secret="test-secret",
        )

        client.call(method="query_history_k_data_plus", params={})

        call_args = mock_post.call_args
        assert call_args[0][0] == "https://relay.example.com/v2/baostock/call"


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_call_correct_headers(mock_post):
    """Test call method sends correct headers"""
    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    with patch("xfintech.data.source.baostock.session.relay.pd.read_parquet"):
        client = BaostockRelayClient(
            url="https://relay.example.com",
            secret="test-secret",
        )

        client.call(method="query_history_k_data_plus", params={})

        call_kwargs = mock_post.call_args[1]
        headers = call_kwargs["headers"]

        assert headers["Content-Type"] == "application/json"
        assert "X-YNONCE" in headers
        assert "X-YTS" in headers
        assert "X-YSIGN" in headers
        assert headers["X-Format"] == "parquet"
        assert headers["X-Compression"] == "zstd+gzip"


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_call_timeout(mock_post):
    """Test call method uses correct timeout"""
    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    with patch("xfintech.data.source.baostock.session.relay.pd.read_parquet"):
        client = BaostockRelayClient(
            url="https://relay.example.com",
            secret="test-secret",
            timeout=300,
        )

        client.call(method="query_history_k_data_plus", params={})

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 300


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_call_http_error(mock_post):
    """Test call method raises error on HTTP error"""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    with pytest.raises(requests.HTTPError):
        client.call(method="query_history_k_data_plus", params={})


# ============================================================================
# BaostockRelayClient Check Health Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.relay.requests.get")
def test_relay_client_check_health_ok(mock_get):
    """Test check_health returns True when status is ok"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    mock_get.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    result = client.check_health()
    assert result is True
    mock_get.assert_called_once_with("https://relay.example.com/health", timeout=180)


@patch("xfintech.data.source.baostock.session.relay.requests.get")
def test_relay_client_check_health_not_ok(mock_get):
    """Test check_health raises error when status is not ok"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "error"}
    mock_get.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    with pytest.raises(RuntimeError, match="Health check returned non-ok status"):
        client.check_health()


@patch("xfintech.data.source.baostock.session.relay.requests.get")
def test_relay_client_check_health_connection_error(mock_get):
    """Test check_health raises error on connection error"""
    mock_get.side_effect = requests.ConnectionError("Connection failed")

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    with pytest.raises(RuntimeError, match="Health check failed"):
        client.check_health()


@patch("xfintech.data.source.baostock.session.relay.requests.get")
def test_relay_client_check_health_timeout_error(mock_get):
    """Test check_health raises error on timeout"""
    mock_get.side_effect = requests.Timeout("Request timed out")

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    with pytest.raises(RuntimeError, match="Health check failed"):
        client.check_health()


@patch("xfintech.data.source.baostock.session.relay.requests.get")
def test_relay_client_check_health_custom_timeout(mock_get):
    """Test check_health uses custom timeout"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    mock_get.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
        timeout=60,
    )

    client.check_health()

    call_kwargs = mock_get.call_args[1]
    assert call_kwargs["timeout"] == 60


# ============================================================================
# RelayConnection Initialization Tests
# ============================================================================


def test_relay_connection_init():
    """Test RelayConnection initialization"""
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    connection = RelayConnection(client=client)
    assert connection.client is client


# ============================================================================
# RelayConnection Dynamic Method Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.relay.requests.post")
@patch("xfintech.data.source.baostock.session.relay.pd.read_parquet")
def test_relay_connection_dynamic_method_call(mock_read_parquet, mock_post):
    """Test RelayConnection dynamic method call"""
    mock_df = pd.DataFrame({"col1": [1, 2]})
    mock_read_parquet.return_value = mock_df

    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    connection = RelayConnection(client=client)

    # Call dynamic method
    result = connection.query_history_k_data_plus(code="sh.600000")

    assert isinstance(result, pd.DataFrame)


@patch("xfintech.data.source.baostock.session.relay.requests.post")
@patch("xfintech.data.source.baostock.session.relay.pd.read_parquet")
def test_relay_connection_multiple_methods(mock_read_parquet, mock_post):
    """Test RelayConnection can call multiple different methods"""
    mock_df = pd.DataFrame({"col1": [1, 2]})
    mock_read_parquet.return_value = mock_df

    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    connection = RelayConnection(client=client)

    # Call different methods
    connection.query_history_k_data_plus(code="sh.600000")
    connection.query_stock_basic()
    connection.query_trade_dates()

    assert mock_post.call_count == 3


@patch("xfintech.data.source.baostock.session.relay.requests.post")
@patch("xfintech.data.source.baostock.session.relay.pd.read_parquet")
def test_relay_connection_keyword_only_params(mock_read_parquet, mock_post):
    """Test RelayConnection enforces keyword-only parameters"""
    mock_df = pd.DataFrame({"col1": [1, 2]})
    mock_read_parquet.return_value = mock_df

    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    connection = RelayConnection(client=client)

    # Should work with keywords
    result = connection.query_history_k_data_plus(code="sh.600000", start_date="2024-01-01")
    assert isinstance(result, pd.DataFrame)


# ============================================================================
# Integration Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.relay.requests.post")
@patch("xfintech.data.source.baostock.session.relay.pd.read_parquet")
def test_relay_full_workflow(mock_read_parquet, mock_post):
    """Test complete relay workflow"""
    mock_df = pd.DataFrame(
        {
            "code": ["sh.600000", "sh.600001"],
            "date": ["2024-01-01", "2024-01-01"],
            "close": ["10.5", "20.3"],
        }
    )
    mock_read_parquet.return_value = mock_df

    mock_response = Mock()
    mock_response.content = gzip.compress(b"parquet_data")
    mock_post.return_value = mock_response

    # Create client and connection
    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
        timeout=120,
    )
    connection = RelayConnection(client=client)

    # Fetch data
    result = connection.query_history_k_data_plus(
        code="sh.600000",
        fields="date,code,open,high,low,close",
        start_date="2024-01-01",
        end_date="2024-01-31",
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert "code" in result.columns


def test_relay_client_constants():
    """Test BaostockRelayClient class constants"""
    assert BaostockRelayClient.DEFAULT_TIMEOUT == 180


# ============================================================================
# BaostockRelayClient Refresh Tests
# ============================================================================


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_success(mock_post):
    """Test refresh method with successful response"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok", "message": "Refreshed"}
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    result = client.refresh()

    assert result is True
    mock_post.assert_called_once()

    # Verify the endpoint
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://relay.example.com/v2/baostock/refresh"

    # Verify headers
    headers = call_args[1]["headers"]
    assert "X-YNONCE" in headers
    assert "X-YTS" in headers
    assert "X-YSIGN" in headers
    assert headers["Content-Type"] == "application/json"


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_non_ok_status(mock_post):
    """Test refresh method raises error on non-ok status"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "error", "message": "Failed"}
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    with pytest.raises(RuntimeError, match="Refresh returned non-ok status"):
        client.refresh()


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_http_error(mock_post):
    """Test refresh method handles HTTP errors"""
    mock_post.side_effect = requests.exceptions.HTTPError("500 Server Error")

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    with pytest.raises(RuntimeError, match="Baostock refresh failed"):
        client.refresh()


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_timeout(mock_post):
    """Test refresh method handles timeout errors"""
    mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
        timeout=5,
    )

    with pytest.raises(RuntimeError, match="Baostock refresh failed"):
        client.refresh()


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_uses_correct_timeout(mock_post):
    """Test refresh method uses client timeout setting"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
        timeout=300,
    )
    client.refresh()

    call_args = mock_post.call_args
    assert call_args[1]["timeout"] == 300


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_authentication(mock_post):
    """Test refresh method sends proper authentication"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="my-secret-key",
    )
    client.refresh()

    # Verify authentication headers are present
    call_args = mock_post.call_args
    headers = call_args[1]["headers"]

    assert len(headers["X-YNONCE"]) == 32  # 16 bytes hex = 32 chars
    assert headers["X-YTS"].isdigit()
    assert len(headers["X-YSIGN"]) == 64  # SHA256 hex = 64 chars


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_empty_payload(mock_post):
    """Test refresh method sends empty payload"""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )
    client.refresh()

    # Verify empty JSON payload
    call_args = mock_post.call_args
    data = call_args[1]["data"]
    assert data == b"{}"


@patch("xfintech.data.source.baostock.session.relay.requests.post")
def test_relay_client_refresh_json_decode_error(mock_post):
    """Test refresh method handles JSON decode errors"""
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_post.return_value = mock_response

    client = BaostockRelayClient(
        url="https://relay.example.com",
        secret="test-secret",
    )

    with pytest.raises(RuntimeError, match="Baostock refresh failed"):
        client.refresh()

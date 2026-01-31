"""
Test suite for RelayClient class
Tests cover initialization, URL/secret/timeout resolution, JSON serialization
"""

import json
from typing import Any

import pytest

from xfintech.data.relay.client import RelayClient

# ============================================================================
# Helper Classes for Testing
# ============================================================================


class ConcreteRelayClient(RelayClient):
    """Concrete implementation for testing"""

    def call(self) -> Any:
        return {"status": "success"}


class CustomRelayClient(RelayClient):
    """Custom client with overridden call"""

    def __init__(self, url: str, secret: str, timeout: int = None, **kwargs):
        super().__init__(url, secret, timeout, **kwargs)
        self.custom_attr = kwargs.get("custom_attr", "default")

    def call(self) -> dict:
        return {"url": self.url, "timeout": self.timeout, "custom": self.custom_attr}


# ============================================================================
# Initialization Tests
# ============================================================================


def test_relayclient_init_basic():
    """Test RelayClient basic initialization"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="test-secret")

    assert client.url == "https://relay.example.com"
    assert client.secret == "test-secret"
    assert client.timeout == RelayClient.DEFAULT_TIMEOUT


def test_relayclient_init_with_timeout():
    """Test RelayClient initialization with custom timeout"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="test-secret", timeout=120)

    assert client.timeout == 120


def test_relayclient_init_with_kwargs():
    """Test RelayClient initialization accepts kwargs"""
    client = CustomRelayClient(url="https://relay.example.com", secret="test-secret", custom_attr="custom_value")

    assert client.custom_attr == "custom_value"


def test_relayclient_init_strips_trailing_slash():
    """Test URL trailing slash is removed"""
    client = ConcreteRelayClient(url="https://relay.example.com/", secret="test-secret")

    assert client.url == "https://relay.example.com"


def test_relayclient_init_multiple_trailing_slashes():
    """Test multiple trailing slashes are removed"""
    client = ConcreteRelayClient(url="https://relay.example.com///", secret="test-secret")

    assert client.url == "https://relay.example.com"


def test_relayclient_init_strips_secret_whitespace():
    """Test secret whitespace is stripped"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="  test-secret  ")

    assert client.secret == "test-secret"


def test_relayclient_default_timeout_constant():
    """Test DEFAULT_TIMEOUT constant value"""
    assert RelayClient.DEFAULT_TIMEOUT == 180


# ============================================================================
# URL Resolution Tests
# ============================================================================


def test_resolve_url_valid():
    """Test _resolve_url with valid URL"""
    client = ConcreteRelayClient(url="https://api.example.com", secret="secret")

    assert client.url == "https://api.example.com"


def test_resolve_url_empty_string_raises_error():
    """Test _resolve_url raises error for empty string"""
    with pytest.raises(ValueError, match="Relay URL must be provided"):
        ConcreteRelayClient(url="", secret="secret")


def test_resolve_url_with_path():
    """Test _resolve_url preserves path"""
    client = ConcreteRelayClient(url="https://relay.example.com/api/v1", secret="secret")

    assert client.url == "https://relay.example.com/api/v1"


def test_resolve_url_with_path_and_trailing_slash():
    """Test _resolve_url preserves path but removes trailing slash"""
    client = ConcreteRelayClient(url="https://relay.example.com/api/v1/", secret="secret")

    assert client.url == "https://relay.example.com/api/v1"


def test_resolve_url_localhost():
    """Test _resolve_url with localhost"""
    client = ConcreteRelayClient(url="http://localhost:8080", secret="secret")

    assert client.url == "http://localhost:8080"


# ============================================================================
# Secret Resolution Tests
# ============================================================================


def test_resolve_secret_valid():
    """Test _resolve_secret with valid secret"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="my-secret-key")

    assert client.secret == "my-secret-key"


def test_resolve_secret_empty_string_raises_error():
    """Test _resolve_secret raises error for empty string"""
    with pytest.raises(ValueError, match="Relay secret must be provided"):
        ConcreteRelayClient(url="https://relay.example.com", secret="")


def test_resolve_secret_whitespace_only_raises_error():
    """Test _resolve_secret raises error for whitespace-only string"""
    with pytest.raises(ValueError, match="Relay secret must be provided"):
        ConcreteRelayClient(url="https://relay.example.com", secret="   ")


def test_resolve_secret_with_leading_whitespace():
    """Test _resolve_secret strips leading whitespace"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="   my-secret")

    assert client.secret == "my-secret"


def test_resolve_secret_with_trailing_whitespace():
    """Test _resolve_secret strips trailing whitespace"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="my-secret   ")

    assert client.secret == "my-secret"


def test_resolve_secret_with_internal_whitespace():
    """Test _resolve_secret preserves internal whitespace"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="my secret key")

    assert client.secret == "my secret key"


def test_resolve_secret_special_characters():
    """Test _resolve_secret accepts special characters"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret!@#$%^&*()_+-=[]{}|")

    assert client.secret == "secret!@#$%^&*()_+-=[]{}|"


# ============================================================================
# Timeout Resolution Tests
# ============================================================================


def test_resolve_timeout_none_uses_default():
    """Test _resolve_timeout uses default when None"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret", timeout=None)

    assert client.timeout == RelayClient.DEFAULT_TIMEOUT


def test_resolve_timeout_valid_integer():
    """Test _resolve_timeout with valid integer"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret", timeout=60)

    assert client.timeout == 60


def test_resolve_timeout_zero_uses_default():
    """Test _resolve_timeout uses default for zero"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret", timeout=0)

    assert client.timeout == RelayClient.DEFAULT_TIMEOUT


def test_resolve_timeout_negative_uses_default():
    """Test _resolve_timeout uses default for negative"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret", timeout=-10)

    assert client.timeout == RelayClient.DEFAULT_TIMEOUT


def test_resolve_timeout_string_raises_error():
    """Test _resolve_timeout raises error for string"""
    with pytest.raises(ValueError, match="Timeout must be an integer"):
        ConcreteRelayClient(url="https://relay.example.com", secret="secret", timeout="60")


def test_resolve_timeout_float_raises_error():
    """Test _resolve_timeout raises error for float"""
    with pytest.raises(ValueError, match="Timeout must be an integer"):
        ConcreteRelayClient(url="https://relay.example.com", secret="secret", timeout=60.5)


def test_resolve_timeout_large_value():
    """Test _resolve_timeout accepts large values"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret", timeout=3600)

    assert client.timeout == 3600


# ============================================================================
# canonical_json Method Tests
# ============================================================================


def test_canonical_json_simple_dict():
    """Test canonical_json with simple dictionary"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"name": "test", "value": 42}
    result = client.canonical_json(data)

    assert isinstance(result, bytes)
    assert result == b'{"name":"test","value":42}'


def test_canonical_json_sorted_keys():
    """Test canonical_json sorts keys"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"z": 1, "a": 2, "m": 3}
    result = client.canonical_json(data)

    assert result == b'{"a":2,"m":3,"z":1}'


def test_canonical_json_no_spaces():
    """Test canonical_json has no spaces"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"key1": "value1", "key2": "value2"}
    result = client.canonical_json(data)

    assert b" " not in result
    assert result == b'{"key1":"value1","key2":"value2"}'


def test_canonical_json_nested_dict():
    """Test canonical_json with nested dictionary"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"outer": {"inner": "value"}}
    result = client.canonical_json(data)

    assert result == b'{"outer":{"inner":"value"}}'


def test_canonical_json_list():
    """Test canonical_json with list"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = [1, 2, 3]
    result = client.canonical_json(data)

    assert result == b"[1,2,3]"


def test_canonical_json_mixed_types():
    """Test canonical_json with mixed types"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"string": "text", "number": 123, "float": 45.67, "bool": True, "null": None, "list": [1, 2, 3]}
    result = client.canonical_json(data)

    assert isinstance(result, bytes)
    # Verify it's valid JSON
    parsed = json.loads(result)
    assert parsed["string"] == "text"
    assert parsed["number"] == 123
    assert parsed["bool"] is True
    assert parsed["null"] is None


def test_canonical_json_unicode():
    """Test canonical_json handles unicode"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"name": "测试", "symbol": "€"}
    result = client.canonical_json(data)

    assert isinstance(result, bytes)
    # Should preserve unicode, not escape it
    assert "测试".encode("utf-8") in result
    assert "€".encode("utf-8") in result


def test_canonical_json_empty_dict():
    """Test canonical_json with empty dictionary"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {}
    result = client.canonical_json(data)

    assert result == b"{}"


def test_canonical_json_empty_list():
    """Test canonical_json with empty list"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = []
    result = client.canonical_json(data)

    assert result == b"[]"


def test_canonical_json_returns_bytes():
    """Test canonical_json always returns bytes"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    result = client.canonical_json({"test": "data"})

    assert type(result) is bytes


# ============================================================================
# call Method Tests
# ============================================================================


def test_call_not_implemented():
    """Test call raises NotImplementedError in base class"""
    client = RelayClient(url="https://relay.example.com", secret="secret")

    with pytest.raises(NotImplementedError):
        client.call()


def test_call_implemented_in_subclass():
    """Test call can be implemented in subclass"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    result = client.call()

    assert result == {"status": "success"}


def test_call_custom_implementation():
    """Test call with custom implementation"""
    client = CustomRelayClient(url="https://relay.example.com", secret="secret", timeout=100, custom_attr="test")

    result = client.call()

    assert result["url"] == "https://relay.example.com"
    assert result["timeout"] == 100
    assert result["custom"] == "test"


# ============================================================================
# Integration Tests
# ============================================================================


def test_relayclient_full_initialization():
    """Test complete RelayClient initialization workflow"""
    client = ConcreteRelayClient(url="https://relay.example.com/api/v1/", secret="  my-secret-key  ", timeout=300)

    assert client.url == "https://relay.example.com/api/v1"
    assert client.secret == "my-secret-key"
    assert client.timeout == 300


def test_relayclient_json_serialization_workflow():
    """Test JSON serialization workflow"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"endpoint": client.url, "timeout": client.timeout, "data": {"key": "value"}}

    json_bytes = client.canonical_json(data)

    # Verify it can be deserialized
    parsed = json.loads(json_bytes)
    assert parsed["endpoint"] == client.url
    assert parsed["timeout"] == 180


def test_relayclient_multiple_instances_independent():
    """Test multiple RelayClient instances are independent"""
    client1 = ConcreteRelayClient(url="https://relay1.example.com", secret="secret1", timeout=60)

    client2 = ConcreteRelayClient(url="https://relay2.example.com", secret="secret2", timeout=120)

    assert client1.url != client2.url
    assert client1.secret != client2.secret
    assert client1.timeout != client2.timeout


def test_relayclient_protocol_compliance():
    """Test RelayClient implements RelayClientLike protocol"""
    from xfintech.data.relay.clientlike import RelayClientLike

    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    # Should have all required attributes
    assert hasattr(client, "url")
    assert hasattr(client, "secret")
    assert hasattr(client, "timeout")
    assert hasattr(client, "call")
    assert callable(client.call)

    # Should be recognized as RelayClientLike
    assert isinstance(client, RelayClientLike)


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_relayclient_url_with_query_params():
    """Test URL with query parameters"""
    client = ConcreteRelayClient(url="https://relay.example.com/api?key=value", secret="secret")

    assert client.url == "https://relay.example.com/api?key=value"


def test_relayclient_url_with_fragment():
    """Test URL with fragment"""
    client = ConcreteRelayClient(url="https://relay.example.com/api#section", secret="secret")

    assert client.url == "https://relay.example.com/api#section"


def test_relayclient_very_long_secret():
    """Test with very long secret"""
    long_secret = "x" * 1000
    client = ConcreteRelayClient(url="https://relay.example.com", secret=long_secret)

    assert len(client.secret) == 1000


def test_canonical_json_large_data():
    """Test canonical_json with large data structure"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    large_data = {f"key_{i}": f"value_{i}" for i in range(100)}
    result = client.canonical_json(large_data)

    assert isinstance(result, bytes)
    parsed = json.loads(result)
    assert len(parsed) == 100


def test_canonical_json_deeply_nested():
    """Test canonical_json with deeply nested structure"""
    client = ConcreteRelayClient(url="https://relay.example.com", secret="secret")

    data = {"level1": {"level2": {"level3": {"level4": "deep"}}}}
    result = client.canonical_json(data)

    parsed = json.loads(result)
    assert parsed["level1"]["level2"]["level3"]["level4"] == "deep"

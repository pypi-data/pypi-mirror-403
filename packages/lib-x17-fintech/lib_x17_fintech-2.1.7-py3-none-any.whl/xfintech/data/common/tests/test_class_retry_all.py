import time

import backoff
import pytest

from xfintech.data.common.retry import Retry

# ==================== Retry Initialization Tests ====================


def test_retry_init_defaults():
    """Test Retry initialization with default values"""
    retry = Retry()

    assert retry.retry == 0
    assert retry.wait == 0
    assert retry.rate == 1.0
    assert retry.exceptions == (Exception,)
    assert retry.jitter is True
    assert retry.jitter_fn is not None


def test_retry_init_custom_values():
    """Test Retry initialization with custom values"""
    retry = Retry(retry=5, wait=2.0, rate=1.5, jitter=False)

    assert retry.retry == 5
    assert retry.wait == 2.0
    assert retry.rate == 1.5
    assert retry.jitter is False
    assert retry.jitter_fn is None


def test_retry_init_custom_exceptions():
    """Test Retry initialization with custom exceptions"""
    retry = Retry(exceptions=[ValueError, TypeError])

    assert retry.exceptions == (ValueError, TypeError)


def test_retry_init_single_exception():
    """Test Retry initialization with single exception"""
    retry = Retry(exceptions=[ConnectionError])

    assert retry.exceptions == (ConnectionError,)


def test_retry_init_none_exceptions():
    """Test Retry initialization with None exceptions defaults to Exception"""
    retry = Retry(exceptions=None)

    assert retry.exceptions == (Exception,)


# ==================== Jitter Function Tests ====================


def test_retry_jitter_enabled():
    """Test jitter_fn is set when jitter is True"""
    retry = Retry(jitter=True)

    assert retry.jitter_fn is not None
    assert retry.jitter_fn == backoff.full_jitter


def test_retry_jitter_disabled():
    """Test jitter_fn is None when jitter is False"""
    retry = Retry(jitter=False)

    assert retry.jitter_fn is None


def test_retry_resolve_jitter_fn():
    """Test _resolve_jitter_fn method"""
    retry = Retry(jitter=True)
    jitter_fn = retry._resolve_jitter_fn()

    assert jitter_fn is not None
    assert callable(jitter_fn)


# ==================== No Retry Tests ====================


def test_retry_zero_returns_original():
    """Test retry=0 returns original function without decoration"""
    retry = Retry(retry=0)

    @retry
    def sample_func():
        return "result"

    assert sample_func() == "result"
    # Function should be the original, not wrapped
    assert sample_func.__name__ == "sample_func"


def test_retry_negative_returns_original():
    """Test negative retry returns original function"""
    retry = Retry(retry=-1)

    call_count = 0

    @retry
    def sample_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Error")

    with pytest.raises(ValueError):
        sample_func()

    # Should fail immediately without retry
    assert call_count == 1


# ==================== Constant Interval Tests ====================


def test_retry_constant_interval():
    """Test retry with constant interval (rate=1.0)"""
    retry = Retry(retry=3, wait=0.01, rate=1.0, jitter=False)

    call_count = 0

    @retry
    def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Failed")
        return "success"

    result = failing_func()

    assert result == "success"
    assert call_count == 3


def test_retry_constant_interval_all_fail():
    """Test retry with constant interval when all attempts fail"""
    retry = Retry(retry=3, wait=0.01, rate=1.0, jitter=False)

    call_count = 0

    @retry
    def always_fail():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_fail()

    assert call_count == 3


# ==================== Exponential Backoff Tests ====================


def test_retry_exponential_backoff():
    """Test retry with exponential backoff (rate>1.0)"""
    retry = Retry(retry=4, wait=0.01, rate=2.0, jitter=False)

    call_count = 0

    @retry
    def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Connection failed")
        return "connected"

    result = failing_func()

    assert result == "connected"
    assert call_count == 3


def test_retry_exponential_backoff_all_fail():
    """Test exponential backoff when all attempts fail"""
    retry = Retry(retry=3, wait=0.01, rate=2.0, jitter=False)

    call_count = 0

    @retry
    def always_fail():
        nonlocal call_count
        call_count += 1
        raise TimeoutError("Timeout")

    with pytest.raises(TimeoutError, match="Timeout"):
        always_fail()

    assert call_count == 3


# ==================== Exception Handling Tests ====================


def test_retry_specific_exception():
    """Test retry only catches specified exceptions"""
    retry = Retry(retry=3, wait=0.01, exceptions=[ValueError])

    call_count = 0

    @retry
    def mixed_exceptions():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Retryable")
        raise TypeError("Not retryable")

    with pytest.raises(TypeError, match="Not retryable"):
        mixed_exceptions()

    # Should retry once for ValueError, then fail on TypeError
    assert call_count == 2


def test_retry_multiple_exceptions():
    """Test retry with multiple exception types"""
    retry = Retry(retry=3, wait=0.01, exceptions=[ValueError, TypeError])

    call_count = 0

    @retry
    def multiple_errors():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First error")
        if call_count == 2:
            raise TypeError("Second error")
        return "success"

    result = multiple_errors()

    assert result == "success"
    assert call_count == 3


def test_retry_non_matching_exception():
    """Test retry doesn't catch non-matching exceptions"""
    retry = Retry(retry=3, wait=0.01, exceptions=[ValueError])

    call_count = 0

    @retry
    def wrong_exception():
        nonlocal call_count
        call_count += 1
        raise KeyError("Not handled")

    with pytest.raises(KeyError, match="Not handled"):
        wrong_exception()

    # Should fail immediately without retry
    assert call_count == 1


def test_retry_success_on_first_try():
    """Test function that succeeds on first try"""
    retry = Retry(retry=3, wait=0.01)

    call_count = 0

    @retry
    def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = success_func()

    assert result == "success"
    assert call_count == 1


# ==================== Function Decoration Tests ====================


def test_retry_preserves_function_name():
    """Test retry decorator preserves function name"""
    retry = Retry(retry=3, wait=0.01)

    @retry
    def my_function():
        return "result"

    assert my_function.__name__ == "my_function"


def test_retry_with_arguments():
    """Test retry works with functions that have arguments"""
    retry = Retry(retry=3, wait=0.01)

    call_count = 0

    @retry
    def func_with_args(a, b, c=10):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Fail")
        return a + b + c

    result = func_with_args(1, 2, c=3)

    assert result == 6
    assert call_count == 2


def test_retry_with_kwargs():
    """Test retry works with keyword arguments"""
    retry = Retry(retry=3, wait=0.01)

    call_count = 0

    @retry
    def func_with_kwargs(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Fail")
        return kwargs

    result = func_with_kwargs(x=1, y=2, z=3)

    assert result == {"x": 1, "y": 2, "z": 3}
    assert call_count == 2


def test_retry_with_mixed_args():
    """Test retry with positional and keyword arguments"""
    retry = Retry(retry=3, wait=0.01)

    call_count = 0

    @retry
    def mixed_args(a, b, *args, x=10, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Fail")
        return a, b, args, x, kwargs

    result = mixed_args(1, 2, 3, 4, x=5, y=6)

    assert result == (1, 2, (3, 4), 5, {"y": 6})
    assert call_count == 2


def test_retry_decorator_as_variable():
    """Test using retry as a variable instead of decorator"""
    retry = Retry(retry=3, wait=0.01)

    call_count = 0

    def original_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Fail")
        return "success"

    wrapped_func = retry(original_func)
    result = wrapped_func()

    assert result == "success"
    assert call_count == 2


# ==================== String Representation Tests ====================


def test_retry_str():
    """Test __str__ returns retry count"""
    retry = Retry(retry=5)

    assert str(retry) == "5"


def test_retry_str_zero():
    """Test __str__ with zero retry"""
    retry = Retry(retry=0)

    assert str(retry) == "0"


def test_retry_repr():
    """Test __repr__ returns detailed representation"""
    retry = Retry(retry=3, wait=1.5, rate=2.0)

    repr_str = repr(retry)

    assert "Retry" in repr_str
    assert "retry=3" in repr_str
    assert "wait=1.5" in repr_str
    assert "rate=2.0" in repr_str
    assert "exceptions=" in repr_str


def test_retry_repr_custom_exceptions():
    """Test __repr__ with custom exceptions"""
    retry = Retry(retry=3, exceptions=[ValueError, TypeError])

    repr_str = repr(retry)

    assert "ValueError" in repr_str
    assert "TypeError" in repr_str


# ==================== To Dict / Describe Tests ====================


def test_retry_to_dict():
    """Test to_dict returns configuration dictionary"""
    retry = Retry(retry=5, wait=2.0, rate=1.5)

    result = retry.to_dict()

    assert isinstance(result, dict)
    assert result["retry"] == 5
    assert result["wait"] == 2.0
    assert result["rate"] == 1.5
    assert "exceptions" in result


def test_retry_to_dict_exception_names():
    """Test to_dict returns exception names as strings"""
    retry = Retry(retry=3, exceptions=[ValueError, TypeError, ConnectionError])

    result = retry.to_dict()

    assert result["exceptions"] == ["ValueError", "TypeError", "ConnectionError"]


def test_retry_describe():
    """Test describe returns same as to_dict"""
    retry = Retry(retry=3, wait=1.0, rate=2.0)

    describe_result = retry.describe()
    to_dict_result = retry.to_dict()

    assert describe_result == to_dict_result


def test_retry_to_dict_default_exception():
    """Test to_dict with default Exception"""
    retry = Retry()

    result = retry.to_dict()

    assert result["exceptions"] == ["Exception"]


# ==================== Integration Tests ====================


def test_retry_real_world_api_call():
    """Test retry with simulated API call scenario"""
    retry = Retry(retry=4, wait=0.01, rate=2.0, exceptions=[ConnectionError, TimeoutError])

    call_count = 0
    errors = []

    @retry
    def api_call(endpoint):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            errors.append("connection_error")
            raise ConnectionError("Network unreachable")
        elif call_count == 2:
            errors.append("timeout")
            raise TimeoutError("Request timeout")
        else:
            return f"Data from {endpoint}"

    result = api_call("/api/data")

    assert result == "Data from /api/data"
    assert call_count == 3
    assert len(errors) == 2


def test_retry_database_connection():
    """Test retry with simulated database connection scenario"""
    retry = Retry(retry=3, wait=0.01, exceptions=[ConnectionError])

    attempts = []

    @retry
    def connect_db(host, port):
        attempts.append({"host": host, "port": port})
        if len(attempts) < 3:
            raise ConnectionError("Connection refused")
        return f"Connected to {host}:{port}"

    result = connect_db("localhost", 5432)

    assert result == "Connected to localhost:5432"
    assert len(attempts) == 3


def test_retry_with_cleanup():
    """Test retry preserves function behavior with cleanup logic"""
    retry = Retry(retry=3, wait=0.01)

    resources = []

    @retry
    def process_with_cleanup():
        resources.append("acquired")
        try:
            if len(resources) < 2:
                raise ValueError("Processing failed")
            return "success"
        finally:
            # Cleanup happens regardless
            resources.append("released")

    result = process_with_cleanup()

    assert result == "success"
    # Should have acquired and released for each attempt
    assert len(resources) == 4  # 2 attempts * (acquire + release)


def test_retry_timing_constant():
    """Test retry timing with constant interval"""
    retry = Retry(retry=3, wait=0.05, rate=1.0, jitter=False)

    call_times = []

    @retry
    def timed_func():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise ValueError("Not yet")
        return "done"

    result = timed_func()

    assert result == "done"
    assert len(call_times) == 3

    # Check intervals are approximately constant
    interval1 = call_times[1] - call_times[0]
    interval2 = call_times[2] - call_times[1]

    assert 0.04 < interval1 < 0.15  # Allow some tolerance
    assert 0.04 < interval2 < 0.15


def test_retry_max_retries_exhausted():
    """Test behavior when max retries are exhausted"""
    retry = Retry(retry=3, wait=0.01)

    call_count = 0

    @retry
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError(f"Attempt {call_count}")

    with pytest.raises(ValueError, match="Attempt 3"):
        always_fails()

    assert call_count == 3


def test_retry_with_return_values():
    """Test retry with different return values"""
    retry = Retry(retry=3, wait=0.01)

    results = []

    @retry
    def generate_result():
        results.append(len(results) + 1)
        if len(results) < 2:
            raise ValueError("Not ready")
        return {"attempt": results[-1], "data": "success"}

    result = generate_result()

    assert result == {"attempt": 2, "data": "success"}
    assert len(results) == 2


def test_retry_class_method():
    """Test retry works with class methods"""

    class Service:
        def __init__(self):
            self.attempts = 0

        @Retry(retry=3, wait=0.01)
        def fetch(self):
            self.attempts += 1
            if self.attempts < 2:
                raise ConnectionError("Failed")
            return "data"

    service = Service()
    result = service.fetch()

    assert result == "data"
    assert service.attempts == 2


def test_retry_static_method():
    """Test retry works with static methods"""

    call_count = 0

    class Utils:
        @staticmethod
        @Retry(retry=3, wait=0.01)
        def process():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            return "processed"

    result = Utils.process()

    assert result == "processed"
    assert call_count == 2


def test_retry_multiple_decorators():
    """Test retry can be combined with other decorators"""
    retry = Retry(retry=3, wait=0.01)

    call_log = []
    attempt_count = 0

    def log_calls(func):
        def wrapper(*args, **kwargs):
            call_log.append("outer_called")
            return func(*args, **kwargs)

        return wrapper

    @log_calls
    @retry
    def decorated_func():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ValueError("Fail")
        return "success"

    result = decorated_func()

    assert result == "success"
    # Log should be called once (outer decorator)
    # but retry happens inside with 2 attempts
    assert len(call_log) == 1
    assert attempt_count == 2


def test_retry_different_exception_types():
    """Test retry behavior with different exception types in sequence"""
    retry = Retry(retry=4, wait=0.01, exceptions=[ValueError, TypeError, KeyError])

    call_count = 0

    @retry
    def multi_exception_func():
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise ValueError("Error 1")
        elif call_count == 2:
            raise TypeError("Error 2")
        elif call_count == 3:
            raise KeyError("Error 3")
        return "finally succeeded"

    result = multi_exception_func()

    assert result == "finally succeeded"
    assert call_count == 4


def test_retry_configuration_immutability():
    """Test retry configuration doesn't change after decoration"""
    retry = Retry(retry=3, wait=0.5, rate=2.0)

    @retry
    def some_func():
        return "result"

    # Configuration should remain unchanged
    assert retry.retry == 3
    assert retry.wait == 0.5
    assert retry.rate == 2.0

    # Calling function shouldn't affect configuration
    some_func()

    assert retry.retry == 3
    assert retry.wait == 0.5
    assert retry.rate == 2.0

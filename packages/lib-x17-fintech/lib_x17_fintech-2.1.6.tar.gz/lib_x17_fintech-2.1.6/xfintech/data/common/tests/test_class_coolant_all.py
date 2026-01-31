import time
from unittest.mock import patch

from xfintech.data.common.coolant import Coolant

# ==================== Coolant Initialization Tests ====================


def test_coolant_init_defaults():
    """Test Coolant initialization with default values"""
    coolant = Coolant()

    assert coolant.interval == 0
    assert coolant.use_jitter is False
    assert coolant.jitter_min == 0.0
    assert coolant.jitter_max == 0.0


def test_coolant_init_with_interval():
    """Test Coolant initialization with custom interval"""
    coolant = Coolant(interval=5)

    assert coolant.interval == 5
    assert coolant.use_jitter is False
    assert coolant.jitter_min == 0.0
    assert coolant.jitter_max == 0.0


def test_coolant_init_with_jitter():
    """Test Coolant initialization with jitter enabled"""
    coolant = Coolant(use_jitter=True)

    assert coolant.interval == 0
    assert coolant.use_jitter is True
    assert coolant.jitter_min == 0.1
    assert coolant.jitter_max == 3.0


def test_coolant_init_custom_jitter_range():
    """Test Coolant initialization with custom jitter range"""
    coolant = Coolant(use_jitter=True, jitter_min=0.5, jitter_max=2.5)

    assert coolant.use_jitter is True
    assert coolant.jitter_min == 0.5
    assert coolant.jitter_max == 2.5


def test_coolant_init_complete():
    """Test Coolant initialization with all parameters"""
    coolant = Coolant(interval=3, use_jitter=True, jitter_min=0.2, jitter_max=1.5)

    assert coolant.interval == 3
    assert coolant.use_jitter is True
    assert coolant.jitter_min == 0.2
    assert coolant.jitter_max == 1.5


def test_coolant_init_jitter_without_flag():
    """Test jitter params ignored when use_jitter is False"""
    coolant = Coolant(use_jitter=False, jitter_min=1.0, jitter_max=2.0)

    assert coolant.use_jitter is False
    assert coolant.jitter_min == 0.0
    assert coolant.jitter_max == 0.0


def test_coolant_init_interval_zero():
    """Test Coolant initialization with zero interval"""
    coolant = Coolant(interval=0)

    assert coolant.interval == 0


def test_coolant_init_interval_negative():
    """Test Coolant initialization with negative interval"""
    coolant = Coolant(interval=-5)

    assert coolant.interval == -5


# ==================== Class Constants Tests ====================


def test_coolant_default_constants():
    """Test class default constants are set correctly"""
    assert Coolant.DEFAULT_INTERVAL == 0
    assert Coolant.DEFAULT_JITTER_MIN == 0.1
    assert Coolant.DEFAULT_JITTER_MAX == 3.0


# ==================== Resolve Methods Tests ====================


def test_coolant_resolve_interval_with_value():
    """Test _resolve_interval with explicit value"""
    coolant = Coolant()
    result = coolant._resolve_interval(10)

    assert result == 10


def test_coolant_resolve_interval_none():
    """Test _resolve_interval with None returns default"""
    coolant = Coolant()
    result = coolant._resolve_interval(None)

    assert result == Coolant.DEFAULT_INTERVAL


def test_coolant_resolve_jitter_min_with_jitter_enabled():
    """Test _resolve_jitter_min with jitter enabled"""
    coolant = Coolant(use_jitter=True)
    result = coolant._resolve_jitter_min(0.5)

    assert result == 0.5


def test_coolant_resolve_jitter_min_with_jitter_disabled():
    """Test _resolve_jitter_min with jitter disabled"""
    coolant = Coolant(use_jitter=False)
    result = coolant._resolve_jitter_min(0.5)

    assert result == 0.0


def test_coolant_resolve_jitter_min_none_with_jitter():
    """Test _resolve_jitter_min returns default when None and jitter enabled"""
    coolant = Coolant(use_jitter=True)
    result = coolant._resolve_jitter_min(None)

    assert result == Coolant.DEFAULT_JITTER_MIN


def test_coolant_resolve_jitter_max_with_jitter_enabled():
    """Test _resolve_jitter_max with jitter enabled"""
    coolant = Coolant(use_jitter=True)
    result = coolant._resolve_jitter_max(2.5)

    assert result == 2.5


def test_coolant_resolve_jitter_max_with_jitter_disabled():
    """Test _resolve_jitter_max with jitter disabled"""
    coolant = Coolant(use_jitter=False)
    result = coolant._resolve_jitter_max(2.5)

    assert result == 0.0


def test_coolant_resolve_jitter_max_none_with_jitter():
    """Test _resolve_jitter_max returns default when None and jitter enabled"""
    coolant = Coolant(use_jitter=True)
    result = coolant._resolve_jitter_max(None)

    assert result == Coolant.DEFAULT_JITTER_MAX


def test_coolant_resolve_jitter_min_int_conversion():
    """Test _resolve_jitter_min converts int to float"""
    coolant = Coolant(use_jitter=True)
    result = coolant._resolve_jitter_min(1)

    assert result == 1.0
    assert isinstance(result, float)


def test_coolant_resolve_jitter_max_int_conversion():
    """Test _resolve_jitter_max converts int to float"""
    coolant = Coolant(use_jitter=True)
    result = coolant._resolve_jitter_max(3)

    assert result == 3.0
    assert isinstance(result, float)


# ==================== Jitter Method Tests ====================


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_jitter_enabled(mock_uniform, mock_sleep):
    """Test jitter() with jitter enabled"""
    mock_uniform.return_value = 1.5
    coolant = Coolant(use_jitter=True, jitter_min=0.5, jitter_max=2.0)

    coolant.jitter()

    mock_uniform.assert_called_once_with(0.5, 2.0)
    mock_sleep.assert_called_once_with(1.5)


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_jitter_disabled(mock_uniform, mock_sleep):
    """Test jitter() with jitter disabled does nothing"""
    coolant = Coolant(use_jitter=False)

    coolant.jitter()

    mock_uniform.assert_not_called()
    mock_sleep.assert_not_called()


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_jitter_rounding(mock_uniform, mock_sleep):
    """Test jitter() rounds to 1 decimal place"""
    mock_uniform.return_value = 1.567
    coolant = Coolant(use_jitter=True)

    coolant.jitter()

    mock_sleep.assert_called_once_with(1.6)


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_jitter_uses_configured_range(mock_uniform, mock_sleep):
    """Test jitter() uses configured min/max range"""
    mock_uniform.return_value = 0.75
    coolant = Coolant(use_jitter=True, jitter_min=0.3, jitter_max=0.8)

    coolant.jitter()

    mock_uniform.assert_called_once_with(0.3, 0.8)


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_jitter_default_range(mock_uniform, mock_sleep):
    """Test jitter() uses default range when not specified"""
    mock_uniform.return_value = 1.0
    coolant = Coolant(use_jitter=True)

    coolant.jitter()

    mock_uniform.assert_called_once_with(0.1, 3.0)


# ==================== Cool Method Tests ====================


@patch("time.sleep")
def test_coolant_cool_zero_interval_no_jitter(mock_sleep):
    """Test cool() with zero interval and no jitter returns immediately"""
    coolant = Coolant(interval=0, use_jitter=False)

    coolant.cool()

    mock_sleep.assert_not_called()


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_cool_zero_interval_with_jitter(mock_uniform, mock_sleep):
    """Test cool() with zero interval but jitter enabled applies jitter"""
    mock_uniform.return_value = 1.5
    coolant = Coolant(interval=0, use_jitter=True)

    coolant.cool()

    # Should only call sleep once for jitter
    assert mock_sleep.call_count == 1
    mock_sleep.assert_called_with(1.5)


@patch("time.sleep")
def test_coolant_cool_with_interval_no_jitter(mock_sleep):
    """Test cool() with interval but no jitter"""
    coolant = Coolant(interval=3, use_jitter=False)

    coolant.cool()

    mock_sleep.assert_called_once_with(3)


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_cool_with_interval_and_jitter(mock_uniform, mock_sleep):
    """Test cool() with both interval and jitter"""
    mock_uniform.return_value = 0.5
    coolant = Coolant(interval=2, use_jitter=True, jitter_min=0.1, jitter_max=1.0)

    coolant.cool()

    # Should call sleep twice: once for interval, once for jitter
    assert mock_sleep.call_count == 2
    calls = mock_sleep.call_args_list
    assert calls[0][0][0] == 2  # interval
    assert calls[1][0][0] == 0.5  # jitter


@patch("time.sleep")
def test_coolant_cool_negative_interval(mock_sleep):
    """Test cool() with negative interval applies jitter if enabled"""
    coolant = Coolant(interval=-1, use_jitter=False)

    coolant.cool()

    # Negative interval treated as <= 0, so should return early
    mock_sleep.assert_not_called()


@patch("time.sleep")
def test_coolant_cool_interval_rounding(mock_sleep):
    """Test cool() rounds interval to 1 decimal place"""
    coolant = Coolant(interval=5, use_jitter=False)

    coolant.cool()

    mock_sleep.assert_called_once_with(5)


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_cool_order_of_operations(mock_uniform, mock_sleep):
    """Test cool() applies interval before jitter"""
    mock_uniform.return_value = 0.3
    coolant = Coolant(interval=1, use_jitter=True)

    coolant.cool()

    # Verify order: interval sleep, then jitter sleep
    calls = mock_sleep.call_args_list
    assert len(calls) == 2
    assert calls[0][0][0] == 1  # First call is interval
    assert calls[1][0][0] == 0.3  # Second call is jitter


# ==================== Integration Tests ====================


def test_coolant_cool_actual_timing_no_jitter():
    """Test cool() actually waits for the specified interval"""
    coolant = Coolant(interval=0.1, use_jitter=False)

    start = time.time()
    coolant.cool()
    elapsed = time.time() - start

    assert 0.09 <= elapsed <= 0.2  # Allow some tolerance


def test_coolant_cool_actual_timing_with_jitter():
    """Test cool() waits for interval plus jitter"""
    coolant = Coolant(interval=0.1, use_jitter=True, jitter_min=0.1, jitter_max=0.2)

    start = time.time()
    coolant.cool()
    elapsed = time.time() - start

    # Should be at least interval + jitter_min
    assert elapsed >= 0.19  # 0.1 interval + 0.1 jitter min (with tolerance)
    # Should be at most interval + jitter_max (with some tolerance)
    assert elapsed <= 0.4


def test_coolant_cool_zero_interval_actual():
    """Test cool() with zero interval completes quickly"""
    coolant = Coolant(interval=0, use_jitter=False)

    start = time.time()
    coolant.cool()
    elapsed = time.time() - start

    assert elapsed < 0.01  # Should be nearly instant


def test_coolant_multiple_cool_calls():
    """Test multiple sequential cool() calls"""
    coolant = Coolant(interval=0.05, use_jitter=False)

    start = time.time()
    coolant.cool()
    coolant.cool()
    coolant.cool()
    elapsed = time.time() - start

    # 0.05 rounds to 0.1, so 3 * 0.1 = 0.3 seconds
    assert 0.28 <= elapsed <= 0.35


def test_coolant_reuse():
    """Test Coolant instance can be reused"""
    coolant = Coolant(interval=0.05, use_jitter=False)

    # First use
    start = time.time()
    coolant.cool()
    elapsed1 = time.time() - start

    # Second use
    start = time.time()
    coolant.cool()
    elapsed2 = time.time() - start

    # 0.05 rounds to 0.1 when sleeping
    assert 0.09 <= elapsed1 <= 0.15
    assert 0.09 <= elapsed2 <= 0.15


def test_coolant_different_instances():
    """Test different Coolant instances are independent"""
    coolant1 = Coolant(interval=0.1, use_jitter=False)
    coolant2 = Coolant(interval=0.2, use_jitter=False)

    start = time.time()
    coolant1.cool()
    elapsed1 = time.time() - start

    start = time.time()
    coolant2.cool()
    elapsed2 = time.time() - start

    assert 0.09 <= elapsed1 <= 0.15
    assert 0.19 <= elapsed2 <= 0.25
    assert elapsed2 > elapsed1


# ==================== Edge Cases and Special Scenarios ====================


def test_coolant_jitter_min_equals_max():
    """Test jitter with min equal to max"""
    coolant = Coolant(use_jitter=True, jitter_min=1.0, jitter_max=1.0)

    assert coolant.jitter_min == 1.0
    assert coolant.jitter_max == 1.0


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_jitter_min_equals_max_sleep(mock_uniform, mock_sleep):
    """Test jitter sleep when min equals max"""
    mock_uniform.return_value = 1.0
    coolant = Coolant(use_jitter=True, jitter_min=1.0, jitter_max=1.0)

    coolant.jitter()

    mock_uniform.assert_called_once_with(1.0, 1.0)
    mock_sleep.assert_called_once_with(1.0)


def test_coolant_very_small_interval():
    """Test coolant with very small interval"""
    coolant = Coolant(interval=0.01, use_jitter=False)

    start = time.time()
    coolant.cool()
    elapsed = time.time() - start

    assert elapsed < 0.05


def test_coolant_jitter_only():
    """Test coolant with only jitter, no base interval"""
    coolant = Coolant(interval=0, use_jitter=True, jitter_min=0.05, jitter_max=0.1)

    start = time.time()
    coolant.cool()
    elapsed = time.time() - start

    # Should only apply jitter
    assert 0.04 <= elapsed <= 0.15


@patch("time.sleep")
def test_coolant_cool_preserves_state(mock_sleep):
    """Test cool() doesn't modify instance state"""
    coolant = Coolant(interval=2, use_jitter=True, jitter_min=0.5, jitter_max=1.5)

    original_interval = coolant.interval
    original_jitter = coolant.use_jitter
    original_min = coolant.jitter_min
    original_max = coolant.jitter_max

    coolant.cool()

    assert coolant.interval == original_interval
    assert coolant.use_jitter == original_jitter
    assert coolant.jitter_min == original_min
    assert coolant.jitter_max == original_max


def test_coolant_rate_limiting_scenario():
    """Test coolant for rate limiting scenario"""
    coolant = Coolant(interval=0.05, use_jitter=False)

    operations = []
    start_time = time.time()

    for i in range(3):
        operations.append(time.time() - start_time)
        if i < 2:  # Don't cool after last operation
            coolant.cool()

    # Check spacing between operations
    assert operations[1] - operations[0] >= 0.04
    assert operations[2] - operations[1] >= 0.04


def test_coolant_api_throttling_scenario():
    """Test coolant for API throttling with jitter"""
    coolant = Coolant(interval=0.05, use_jitter=True, jitter_min=0.01, jitter_max=0.05)

    call_times = []
    start = time.time()

    for i in range(3):
        call_times.append(time.time() - start)
        if i < 2:
            coolant.cool()

    # Each gap should be at least interval + jitter_min
    for i in range(1, len(call_times)):
        gap = call_times[i] - call_times[i - 1]
        assert gap >= 0.05  # At least the interval


@patch("time.sleep")
@patch("random.uniform")
def test_coolant_configuration_independence(mock_uniform, mock_sleep):
    """Test coolant configuration doesn't affect other instances"""
    mock_uniform.return_value = 0.5

    coolant1 = Coolant(interval=1, use_jitter=True, jitter_min=0.1, jitter_max=0.5)
    coolant2 = Coolant(interval=2, use_jitter=False)

    coolant1.cool()
    coolant2.cool()

    # coolant1 should have interval + jitter
    # coolant2 should only have interval
    assert mock_sleep.call_count == 3  # 1 interval + 1 jitter + 1 interval

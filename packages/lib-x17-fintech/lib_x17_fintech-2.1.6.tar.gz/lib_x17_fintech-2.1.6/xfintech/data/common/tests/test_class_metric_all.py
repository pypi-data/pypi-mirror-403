import time

import pandas as pd
import pytest

from xfintech.data.common.metric import Metric

# ==================== Metric Initialization Tests ====================


def test_metric_init():
    """Test Metric initialization creates correct default attributes"""
    metric = Metric()

    assert metric.start_at is None
    assert metric.finish_at is None
    assert isinstance(metric.marks, dict)
    assert len(metric.marks) == 0
    assert isinstance(metric.errors, list)
    assert len(metric.errors) == 0


def test_metric_init_multiple_instances():
    """Test that multiple Metric instances are independent"""
    m1 = Metric()
    m2 = Metric()

    m1.start()
    m1.mark("test")

    assert m1.start_at is not None
    assert m2.start_at is None
    assert "test" in m1.marks
    assert "test" not in m2.marks


# ==================== Start/Finish Tests ====================


def test_metric_start():
    """Test start() records start timestamp"""
    metric = Metric()
    before = pd.Timestamp.now()

    metric.start()

    after = pd.Timestamp.now()
    assert metric.start_at is not None
    assert isinstance(metric.start_at, pd.Timestamp)
    assert before <= metric.start_at <= after


def test_metric_finish():
    """Test finish() records finish timestamp"""
    metric = Metric()
    metric.start()
    time.sleep(0.01)

    metric.finish()

    assert metric.finish_at is not None
    assert isinstance(metric.finish_at, pd.Timestamp)
    assert metric.finish_at > metric.start_at


def test_metric_start_multiple_times():
    """Test calling start() multiple times updates start_at"""
    metric = Metric()

    metric.start()
    first_start = metric.start_at
    time.sleep(0.01)

    metric.start()
    second_start = metric.start_at

    assert second_start > first_start


def test_metric_finish_without_start():
    """Test finish() can be called without start()"""
    metric = Metric()

    metric.finish()

    assert metric.start_at is None
    assert metric.finish_at is not None


# ==================== Duration Property Tests ====================


def test_metric_duration_not_started():
    """Test duration returns 0.0 when not started"""
    metric = Metric()

    assert metric.duration == 0.0


def test_metric_duration_started_not_finished():
    """Test duration calculates time from start to now when not finished"""
    metric = Metric()
    metric.start()
    time.sleep(0.05)

    duration = metric.duration

    assert duration >= 0.05
    assert duration < 0.2  # reasonable upper bound


def test_metric_duration_finished():
    """Test duration calculates time from start to finish"""
    metric = Metric()
    metric.start()
    time.sleep(0.05)
    metric.finish()

    duration = metric.duration

    assert duration >= 0.05
    assert duration < 0.2
    # Duration should be stable after finish
    time.sleep(0.01)
    assert metric.duration == duration


def test_metric_duration_precision():
    """Test duration calculation precision"""
    metric = Metric()
    metric.start()
    metric.finish()

    duration = metric.duration

    assert isinstance(duration, float)
    assert duration >= 0


# ==================== Mark Tests ====================


def test_metric_mark():
    """Test mark() records a named timestamp"""
    metric = Metric()
    before = pd.Timestamp.now()

    metric.mark("checkpoint")

    after = pd.Timestamp.now()
    assert "checkpoint" in metric.marks
    assert isinstance(metric.marks["checkpoint"], pd.Timestamp)
    assert before <= metric.marks["checkpoint"] <= after


def test_metric_mark_multiple():
    """Test marking multiple checkpoints"""
    metric = Metric()

    metric.mark("step1")
    time.sleep(0.01)
    metric.mark("step2")
    time.sleep(0.01)
    metric.mark("step3")

    assert len(metric.marks) == 3
    assert "step1" in metric.marks
    assert "step2" in metric.marks
    assert "step3" in metric.marks
    assert metric.marks["step1"] < metric.marks["step2"] < metric.marks["step3"]


def test_metric_mark_overwrite():
    """Test marking with same name overwrites previous mark"""
    metric = Metric()

    metric.mark("test")
    first_mark = metric.marks["test"]
    time.sleep(0.01)

    metric.mark("test")
    second_mark = metric.marks["test"]

    assert len(metric.marks) == 1
    assert second_mark > first_mark


def test_metric_mark_without_start():
    """Test mark() works without calling start()"""
    metric = Metric()

    metric.mark("standalone")

    assert "standalone" in metric.marks
    assert metric.start_at is None


# ==================== Reset Tests ====================


def test_metric_reset():
    """Test reset() clears all state"""
    metric = Metric()
    metric.start()
    metric.mark("test")
    metric.errors = ["error1"]
    metric.finish()

    metric.reset()

    assert metric.start_at is None
    assert metric.finish_at is None
    assert len(metric.marks) == 0
    assert len(metric.errors) == 0


def test_metric_reset_empty():
    """Test reset() on already empty metric"""
    metric = Metric()

    metric.reset()

    assert metric.start_at is None
    assert metric.finish_at is None
    assert len(metric.marks) == 0
    assert len(metric.errors) == 0


def test_metric_reset_reusability():
    """Test metric can be reused after reset"""
    metric = Metric()
    metric.start()
    metric.finish()
    first_duration = metric.duration

    metric.reset()
    metric.start()
    time.sleep(0.01)
    metric.finish()
    second_duration = metric.duration

    assert first_duration != second_duration
    assert metric.duration > 0


# ==================== ISO Format Tests ====================


def test_metric_get_start_iso_none():
    """Test get_start_iso() returns None when not started"""
    metric = Metric()

    assert metric.get_start_iso() is None


def test_metric_get_start_iso_format():
    """Test get_start_iso() returns valid ISO format string"""
    metric = Metric()
    metric.start()

    iso_str = metric.get_start_iso()

    assert iso_str is not None
    assert isinstance(iso_str, str)
    # Should be able to parse back
    parsed = pd.Timestamp(iso_str)
    assert isinstance(parsed, pd.Timestamp)


def test_metric_get_finish_iso_none():
    """Test get_finish_iso() returns None when not finished"""
    metric = Metric()

    assert metric.get_finish_iso() is None


def test_metric_get_finish_iso_format():
    """Test get_finish_iso() returns valid ISO format string"""
    metric = Metric()
    metric.finish()

    iso_str = metric.get_finish_iso()

    assert iso_str is not None
    assert isinstance(iso_str, str)
    # Should be able to parse back
    parsed = pd.Timestamp(iso_str)
    assert isinstance(parsed, pd.Timestamp)


def test_metric_get_mark_iso_empty():
    """Test get_mark_iso() returns empty dict when no marks"""
    metric = Metric()

    marks_iso = metric.get_mark_iso()

    assert isinstance(marks_iso, dict)
    assert len(marks_iso) == 0


def test_metric_get_mark_iso_format():
    """Test get_mark_iso() returns marks in ISO format"""
    metric = Metric()
    metric.mark("test1")
    metric.mark("test2")

    marks_iso = metric.get_mark_iso()

    assert len(marks_iso) == 2
    assert "test1" in marks_iso
    assert "test2" in marks_iso
    assert isinstance(marks_iso["test1"], str)
    assert isinstance(marks_iso["test2"], str)
    # Should be able to parse back
    parsed1 = pd.Timestamp(marks_iso["test1"])
    parsed2 = pd.Timestamp(marks_iso["test2"])
    assert isinstance(parsed1, pd.Timestamp)
    assert isinstance(parsed2, pd.Timestamp)


# ==================== Context Manager Tests ====================


def test_metric_context_manager_success():
    """Test Metric as context manager with successful execution"""
    with Metric() as metric:
        assert metric.start_at is not None
        time.sleep(0.01)
        metric.mark("checkpoint")

    assert metric.finish_at is not None
    assert metric.duration > 0
    assert "checkpoint" in metric.marks
    assert len(metric.errors) == 0


def test_metric_context_manager_returns_self():
    """Test context manager returns the metric instance"""
    metric = Metric()

    with metric as m:
        assert m is metric


def test_metric_context_manager_resets_on_enter():
    """Test context manager resets state on __enter__"""
    metric = Metric()
    metric.start()
    metric.mark("old")
    metric.errors = ["old_error"]

    with metric as m:
        assert m.start_at is not None
        assert len(m.marks) == 0
        assert len(m.errors) == 0


def test_metric_context_manager_exception_capture():
    """Test context manager captures exceptions"""
    try:
        with Metric() as metric:
            raise ValueError("Test exception")
    except ValueError:
        pass  # Exception propagated but captured in metric

    # Exception should be captured in errors
    assert len(metric.errors) > 0
    assert any("ValueError" in error for error in metric.errors)
    assert any("Test exception" in error for error in metric.errors)


def test_metric_context_manager_exception_propagation():
    """Test context manager doesn't suppress exceptions"""
    with pytest.raises(ValueError, match="Test error"):
        with Metric():
            raise ValueError("Test error")


def test_metric_context_manager_exception_traceback():
    """Test context manager captures full traceback"""
    try:
        with Metric() as metric:

            def inner_function():
                raise RuntimeError("Inner error")

            inner_function()
    except RuntimeError:
        pass

    assert len(metric.errors) > 0
    # Should contain traceback information
    full_traceback = "\n".join(metric.errors)
    assert "RuntimeError" in full_traceback
    assert "Inner error" in full_traceback
    assert "inner_function" in full_traceback


def test_metric_context_manager_no_exception():
    """Test context manager with no exception"""
    with Metric() as metric:
        time.sleep(0.01)

    assert len(metric.errors) == 0
    assert metric.finish_at is not None


# ==================== Describe Method Tests ====================


def test_metric_describe_empty():
    """Test describe() with no data"""
    metric = Metric()

    result = metric.describe()

    assert isinstance(result, dict)
    assert "duration" in result
    assert result["duration"] == 0.0
    # Should not include None fields
    assert "started_at" not in result
    assert "finished_at" not in result
    assert "errors" not in result
    assert "marks" not in result


def test_metric_describe_started():
    """Test describe() with only start"""
    metric = Metric()
    metric.start()

    result = metric.describe()

    assert "started_at" in result
    assert "duration" in result
    assert result["duration"] > 0
    assert "finished_at" not in result


def test_metric_describe_finished():
    """Test describe() with start and finish"""
    metric = Metric()
    metric.start()
    time.sleep(0.01)
    metric.finish()

    result = metric.describe()

    assert "started_at" in result
    assert "finished_at" in result
    assert "duration" in result
    assert result["duration"] > 0


def test_metric_describe_with_marks():
    """Test describe() includes marks"""
    metric = Metric()
    metric.start()
    metric.mark("checkpoint")
    metric.finish()

    result = metric.describe()

    assert "marks" in result
    assert isinstance(result["marks"], dict)
    assert "checkpoint" in result["marks"]


def test_metric_describe_with_errors():
    """Test describe() includes errors"""
    metric = Metric()
    try:
        with metric:
            raise ValueError("Test")
    except ValueError:
        pass

    result = metric.describe()

    assert "errors" in result
    assert isinstance(result["errors"], list)
    assert len(result["errors"]) > 0


def test_metric_describe_complete():
    """Test describe() with all fields populated"""
    metric = Metric()
    try:
        with metric:
            metric.mark("step1")
            raise Exception("test error")
    except Exception:
        pass

    result = metric.describe()

    assert "started_at" in result
    assert "finished_at" in result
    assert "duration" in result
    assert "marks" in result
    assert "errors" in result


# ==================== To Dict Method Tests ====================


def test_metric_to_dict_empty():
    """Test to_dict() with no data includes all fields"""
    metric = Metric()

    result = metric.to_dict()

    assert isinstance(result, dict)
    assert "started_at" in result
    assert "finished_at" in result
    assert "duration" in result
    assert "errors" in result
    assert "marks" in result
    # Values should be None/empty but keys present
    assert result["started_at"] is None
    assert result["finished_at"] is None
    assert result["duration"] == 0.0
    assert result["errors"] == []
    assert result["marks"] == {}


def test_metric_to_dict_with_data():
    """Test to_dict() returns complete dictionary"""
    metric = Metric()
    metric.start()
    metric.mark("test")
    time.sleep(0.01)
    metric.finish()

    result = metric.to_dict()

    assert result["started_at"] is not None
    assert result["finished_at"] is not None
    assert result["duration"] > 0
    assert len(result["marks"]) == 1
    assert "test" in result["marks"]


def test_metric_to_dict_vs_describe():
    """Test to_dict() includes None values while describe() omits them"""
    metric = Metric()

    to_dict_result = metric.to_dict()
    describe_result = metric.describe()

    # to_dict should have None values
    assert "started_at" in to_dict_result
    assert to_dict_result["started_at"] is None

    # describe should not have None values
    assert "started_at" not in describe_result


def test_metric_to_dict_structure():
    """Test to_dict() returns expected structure"""
    metric = Metric()
    metric.mark("test")

    result = metric.to_dict()

    # Result should have correct structure
    assert "marks" in result
    assert "errors" in result
    assert "test" in result["marks"]
    assert isinstance(result["errors"], list)

    # Note: to_dict returns references to internal state, not deep copies
    # This is a known behavior where modifying result affects metric


# ==================== Integration Tests ====================


def test_metric_full_workflow():
    """Test complete metric workflow"""
    metric = Metric()

    # Start timing
    metric.start()
    assert metric.start_at is not None

    # Do some work with marks
    time.sleep(0.01)
    metric.mark("phase1")

    time.sleep(0.01)
    metric.mark("phase2")

    time.sleep(0.01)
    metric.mark("phase3")

    # Finish
    metric.finish()

    # Verify results
    assert metric.duration >= 0.03
    assert len(metric.marks) == 3
    assert len(metric.errors) == 0

    # Check ordering
    assert metric.start_at < metric.marks["phase1"]
    assert metric.marks["phase1"] < metric.marks["phase2"]
    assert metric.marks["phase2"] < metric.marks["phase3"]
    assert metric.marks["phase3"] < metric.finish_at


def test_metric_context_manager_full_workflow():
    """Test complete metric workflow with context manager"""
    with Metric() as metric:
        time.sleep(0.01)
        metric.mark("step1")

        time.sleep(0.01)
        metric.mark("step2")

        time.sleep(0.01)

    # Verify
    assert metric.duration >= 0.03
    assert len(metric.marks) == 2
    assert len(metric.errors) == 0

    # Check data availability
    describe = metric.describe()
    assert "started_at" in describe
    assert "finished_at" in describe
    assert "marks" in describe


def test_metric_reuse_after_context():
    """Test metric can be reused after context manager"""
    metric = Metric()

    # First use
    with metric:
        metric.mark("first")

    first_duration = metric.duration

    # Second use
    with metric:
        time.sleep(0.02)
        metric.mark("second")

    second_duration = metric.duration

    # Second use should have different timing
    assert second_duration != first_duration
    assert "first" not in metric.marks
    assert "second" in metric.marks


def test_metric_error_handling_workflow():
    """Test metric properly handles errors in workflow"""
    results = []

    for i in range(3):
        m = Metric()
        try:
            with m:
                m.mark(f"attempt_{i}")
                if i < 2:
                    raise ValueError(f"Error {i}")
        except ValueError:
            pass

        results.append({"attempt": i, "duration": m.duration, "has_errors": len(m.errors) > 0})

    # First two should have errors
    assert results[0]["has_errors"]
    assert results[1]["has_errors"]
    assert not results[2]["has_errors"]


def test_metric_performance_tracking():
    """Test metric for performance tracking scenario"""
    metric = Metric()
    metric.start()

    # Simulate different stages
    stages = ["load", "process", "validate", "save"]

    for stage in stages:
        time.sleep(0.01)
        metric.mark(stage)

    metric.finish()

    # Verify all stages recorded
    assert len(metric.marks) == len(stages)
    for stage in stages:
        assert stage in metric.marks

    # Verify total duration
    assert metric.duration >= 0.04

    # Get report
    report = metric.describe()
    assert "marks" in report
    assert len(report["marks"]) == len(stages)

import pytest

from xfintech.data.job.errors import (
    JobAlreadyRegisteredError,
    JobNameError,
    JobNotFoundError,
)

# ==================== JobNotFoundError Tests ====================


def test_jobnotfounderror_is_keyerror():
    """Test JobNotFoundError inherits from KeyError"""
    assert issubclass(JobNotFoundError, KeyError)


def test_jobnotfounderror_can_be_raised():
    """Test JobNotFoundError can be raised with message"""
    with pytest.raises(JobNotFoundError) as exc_info:
        raise JobNotFoundError("test job not found")

    assert "test job not found" in str(exc_info.value)


def test_jobnotfounderror_can_be_caught_as_keyerror():
    """Test JobNotFoundError can be caught as KeyError"""
    try:
        raise JobNotFoundError("missing")
    except KeyError as e:
        assert "missing" in str(e)


def test_jobnotfounderror_with_empty_message():
    """Test JobNotFoundError with empty message"""
    with pytest.raises(JobNotFoundError):
        raise JobNotFoundError("")


def test_jobnotfounderror_str_representation():
    """Test JobNotFoundError string representation"""
    error = JobNotFoundError("my_job")
    error_str = str(error)

    assert "my_job" in error_str


# ==================== JobAlreadyRegisteredError Tests ====================


def test_jobalreadyregisterederror_is_keyerror():
    """Test JobAlreadyRegisteredError inherits from KeyError"""
    assert issubclass(JobAlreadyRegisteredError, KeyError)


def test_jobalreadyregisterederror_can_be_raised():
    """Test JobAlreadyRegisteredError can be raised with message"""
    with pytest.raises(JobAlreadyRegisteredError) as exc_info:
        raise JobAlreadyRegisteredError("job already exists")

    assert "job already exists" in str(exc_info.value)


def test_jobalreadyregisterederror_can_be_caught_as_keyerror():
    """Test JobAlreadyRegisteredError can be caught as KeyError"""
    try:
        raise JobAlreadyRegisteredError("duplicate")
    except KeyError as e:
        assert "duplicate" in str(e)


def test_jobalreadyregisterederror_with_job_name():
    """Test JobAlreadyRegisteredError with specific job name"""
    job_name = "stock_daily_job"
    error = JobAlreadyRegisteredError(f"Job already registered: {job_name}")

    assert job_name in str(error)


def test_jobalreadyregisterederror_with_alias_info():
    """Test JobAlreadyRegisteredError with alias information"""
    alias = "daily"
    error = JobAlreadyRegisteredError(f"Alias already used: {alias}")

    assert alias in str(error)


# ==================== JobNameError Tests ====================


def test_jobnameerror_is_valueerror():
    """Test JobNameError inherits from ValueError"""
    assert issubclass(JobNameError, ValueError)


def test_jobnameerror_can_be_raised():
    """Test JobNameError can be raised with message"""
    with pytest.raises(JobNameError) as exc_info:
        raise JobNameError("invalid job name")

    assert "invalid job name" in str(exc_info.value)


def test_jobnameerror_can_be_caught_as_valueerror():
    """Test JobNameError can be caught as ValueError"""
    try:
        raise JobNameError("bad name")
    except ValueError as e:
        assert "bad name" in str(e)


def test_jobnameerror_for_empty_name():
    """Test JobNameError for empty name scenario"""
    with pytest.raises(JobNameError) as exc_info:
        raise JobNameError("job name cannot be empty")

    assert "empty" in str(exc_info.value).lower()


def test_jobnameerror_for_wrong_type():
    """Test JobNameError for wrong type scenario"""
    wrong_type = int
    error = JobNameError(f"job name must be str, got {wrong_type}")

    assert "str" in str(error)
    assert "int" in str(error)


# ==================== Error Comparison Tests ====================


def test_all_errors_are_exceptions():
    """Test all custom errors are Exception subclasses"""
    assert issubclass(JobNotFoundError, Exception)
    assert issubclass(JobAlreadyRegisteredError, Exception)
    assert issubclass(JobNameError, Exception)


def test_errors_have_different_base_classes():
    """Test errors have appropriate base classes"""
    # KeyError-based
    assert issubclass(JobNotFoundError, KeyError)
    assert issubclass(JobAlreadyRegisteredError, KeyError)

    # ValueError-based
    assert issubclass(JobNameError, ValueError)

    # Not related
    assert not issubclass(JobNameError, KeyError)
    assert not issubclass(JobNotFoundError, ValueError)


def test_catching_multiple_error_types():
    """Test catching multiple custom error types"""
    caught_errors = []

    for error_class in [JobNotFoundError, JobAlreadyRegisteredError, JobNameError]:
        try:
            raise error_class("test error")
        except (JobNotFoundError, JobAlreadyRegisteredError, JobNameError) as e:
            caught_errors.append(type(e))

    assert JobNotFoundError in caught_errors
    assert JobAlreadyRegisteredError in caught_errors
    assert JobNameError in caught_errors


# ==================== Error Message Tests ====================


def test_jobnotfounderror_descriptive_message():
    """Test JobNotFoundError provides descriptive message"""
    job_name = "nonexistent_job"
    error = JobNotFoundError(f"job not found: {job_name}")

    message = str(error)
    assert "not found" in message.lower()
    assert job_name in message


def test_jobalreadyregisterederror_descriptive_message():
    """Test JobAlreadyRegisteredError provides descriptive message"""
    job_name = "duplicate_job"
    error = JobAlreadyRegisteredError(f"Job already registered: {job_name}")

    message = str(error)
    assert "already" in message.lower()
    assert job_name in message


def test_jobnameerror_descriptive_message():
    """Test JobNameError provides descriptive message"""
    error = JobNameError("job name cannot be empty")

    message = str(error)
    assert "name" in message.lower()
    assert "empty" in message.lower()


# ==================== Integration with Python's Exception Hierarchy ====================


def test_errors_can_be_caught_with_base_exception():
    """Test custom errors can be caught with base Exception"""
    for error_class in [JobNotFoundError, JobAlreadyRegisteredError, JobNameError]:
        try:
            raise error_class("test")
        except Exception:
            pass  # Should catch without error


def test_errors_preserve_traceback():
    """Test custom errors preserve traceback information"""
    import traceback

    try:
        raise JobNotFoundError("test error")
    except JobNotFoundError:
        tb = traceback.format_exc()
        assert "JobNotFoundError" in tb
        assert "test error" in tb


def test_errors_with_multiple_args():
    """Test custom errors with multiple arguments"""
    error = JobNotFoundError("arg1", "arg2", "arg3")

    # KeyError formats args as tuple if multiple
    assert len(error.args) == 3


def test_error_repr():
    """Test error __repr__ method"""
    error = JobNotFoundError("my_job")
    repr_str = repr(error)

    assert "JobNotFoundError" in repr_str


# ==================== Edge Cases ====================


def test_error_with_none_message():
    """Test errors can be created with None as message"""
    JobNameError(None)


def test_error_with_numeric_message():
    """Test errors with numeric messages"""
    JobNotFoundError(404)


def test_error_with_unicode_message():
    """Test errors with unicode messages"""
    error = JobNotFoundError("找不到任务")
    assert "找不到" in str(error)


def test_errors_are_distinct_types():
    """Test that each error type is distinct"""
    e1 = JobNotFoundError("test")
    e2 = JobAlreadyRegisteredError("test")
    e3 = JobNameError("test")

    assert type(e1) is not type(e2)
    assert type(e2) is not type(e3)
    assert type(e1) is not type(e3)


def test_error_equality():
    """Test error equality based on message"""
    e1 = JobNotFoundError("test")
    e2 = JobNotFoundError("test")

    # Exceptions with same message should be equal in args
    assert e1.args == e2.args

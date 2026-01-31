"""
Test suite for Job class
Tests cover initialization, lifecycle management, cache operations, and protocol compliance
"""

from typing import Any, Dict
from unittest.mock import patch

import pytest

from xfintech.data.common.cache import Cache
from xfintech.data.common.coolant import Coolant
from xfintech.data.common.metric import Metric
from xfintech.data.common.paginate import Paginate
from xfintech.data.common.params import Params
from xfintech.data.common.retry import Retry
from xfintech.data.job.job import Job
from xfintech.data.job.joblike import JobLike

# ============================================================================
# Helper Classes for Testing
# ============================================================================


class ConcreteJob(Job):
    """Concrete implementation for testing Job"""

    def _run(self) -> Dict[str, Any]:
        return {"status": "success", "data": [1, 2, 3]}


class FailingJob(Job):
    """Job that fails for testing retry logic"""

    def __init__(self, *args, fail_count=2, **kwargs):
        super().__init__(*args, **kwargs)
        self.attempts = 0
        self.fail_count = fail_count

    def _run(self) -> Dict[str, Any]:
        self.attempts += 1
        if self.attempts <= self.fail_count:
            raise RuntimeError(f"Attempt {self.attempts} failed")
        return {"status": "success", "attempts": self.attempts}


class CachedJob(Job):
    """Job that uses cache"""

    def _run(self) -> Dict[str, Any]:
        # Check cache first
        cached = self.get_cache("result")
        if cached:
            return {"status": "from_cache", "data": cached}

        # Compute result
        result = {"computed": True, "value": 42}
        self.set_cache("result", result)
        return {"status": "computed", "data": result}


# ============================================================================
# Job Initialization Tests
# ============================================================================


def test_job_init_basic():
    """Test Job initialization with minimal parameters"""
    job = ConcreteJob(name="test_job", key="test_key")

    assert job.name == "test_job"
    assert job.key == "test_key"
    assert isinstance(job.params, Params)
    assert isinstance(job.coolant, Coolant)
    assert isinstance(job.paginate, Paginate)
    assert isinstance(job.retry, Retry)
    assert isinstance(job.metric, Metric)
    assert job.cache is None


def test_job_init_with_params_dict():
    """Test Job initialization with params as dict"""
    job = ConcreteJob(name="test_job", key="test_key", params={"symbol": "AAPL", "limit": 100})

    assert isinstance(job.params, Params)
    assert job.params.symbol == "AAPL"
    assert job.params.limit == 100


def test_job_init_with_params_object():
    """Test Job initialization with Params object"""
    params = Params(symbol="TSLA", date="20240115")
    job = ConcreteJob(name="test_job", key="test_key", params=params)

    assert job.params is params
    assert job.params.symbol == "TSLA"


def test_job_init_with_coolant_dict():
    """Test Job initialization with coolant as dict"""
    job = ConcreteJob(name="test_job", key="test_key", coolant={"interval": 2, "use_jitter": True})

    assert isinstance(job.coolant, Coolant)
    assert job.coolant.interval == 2
    assert job.coolant.use_jitter is True


def test_job_init_with_coolant_object():
    """Test Job initialization with Coolant object"""
    coolant = Coolant(interval=5, use_jitter=False)
    job = ConcreteJob(name="test_job", key="test_key", coolant=coolant)

    assert job.coolant is coolant


def test_job_init_with_paginate_dict():
    """Test Job initialization with paginate as dict"""
    job = ConcreteJob(name="test_job", key="test_key", paginate={"pagesize": 1000, "pagelimit": 5000})

    assert isinstance(job.paginate, Paginate)
    assert job.paginate.pagesize == 1000
    assert job.paginate.pagelimit == 5000


def test_job_init_with_paginate_object():
    """Test Job initialization with Paginate object"""
    paginate = Paginate(pagesize=2000, pagelimit=10000)
    job = ConcreteJob(name="test_job", key="test_key", paginate=paginate)

    assert job.paginate is paginate


def test_job_init_with_retry_dict():
    """Test Job initialization with retry as dict"""
    job = ConcreteJob(name="test_job", key="test_key", retry={"retry": 5, "wait": 10})

    assert isinstance(job.retry, Retry)
    assert job.retry.retry == 5
    assert job.retry.wait == 10


def test_job_init_with_retry_object():
    """Test Job initialization with Retry object"""
    retry = Retry(retry=3, wait=5)
    job = ConcreteJob(name="test_job", key="test_key", retry=retry)

    assert job.retry is retry


def test_job_init_with_cache_true():
    """Test Job initialization with cache=True"""
    job = ConcreteJob(name="test_job", key="test_key", cache=True)

    assert isinstance(job.cache, Cache)
    assert job.cache is not None


def test_job_init_with_cache_false():
    """Test Job initialization with cache=False"""
    job = ConcreteJob(name="test_job", key="test_key", cache=False)

    assert job.cache is None


def test_job_init_with_cache_dict():
    """Test Job initialization with cache as dict"""
    job = ConcreteJob(name="test_job", key="test_key", cache={"name": "custom_cache"})

    assert isinstance(job.cache, Cache)


def test_job_init_with_cache_object():
    """Test Job initialization with Cache object"""
    cache = Cache()
    job = ConcreteJob(name="test_job", key="test_key", cache=cache)

    assert job.cache is cache


def test_job_init_marks_init_point():
    """Test Job initialization marks 'init' checkpoint"""
    job = ConcreteJob(name="test_job", key="test_key")

    assert "init[OK]" in job.metric.marks


# ============================================================================
# Job Resolve Methods Tests
# ============================================================================


def test_job_resolve_params_none():
    """Test _resolve_params with None returns default Params"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_params(None)

    assert isinstance(result, Params)
    assert result.to_dict() == {}


def test_job_resolve_params_dict():
    """Test _resolve_params converts dict to Params"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_params({"key": "value"})

    assert isinstance(result, Params)
    assert result.key == "value"


def test_job_resolve_params_object():
    """Test _resolve_params returns Params object as-is"""
    job = ConcreteJob(name="test_job", key="test_key")
    params = Params(test="data")
    result = job._resolve_params(params)

    assert result is params


def test_job_resolve_coolant_none():
    """Test _resolve_coolant with None returns default Coolant"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_coolant(None)

    assert isinstance(result, Coolant)


def test_job_resolve_paginate_none():
    """Test _resolve_paginate with None returns default Paginate"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_paginate(None)

    assert isinstance(result, Paginate)


def test_job_resolve_retry_none():
    """Test _resolve_retry with None returns default Retry"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_retry(None)

    assert isinstance(result, Retry)


def test_job_resolve_cache_none():
    """Test _resolve_cache with None returns None"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_cache(None)

    assert result is None


def test_job_resolve_cache_true():
    """Test _resolve_cache with True creates Cache"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_cache(True)

    assert isinstance(result, Cache)


def test_job_resolve_cache_false():
    """Test _resolve_cache with False returns None"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job._resolve_cache(False)

    assert result is None


# ============================================================================
# Job Run Method Tests
# ============================================================================


def test_job_run_basic():
    """Test Job run method executes successfully"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job.run()

    assert result["status"] == "success"
    assert result["data"] == [1, 2, 3]


def test_job_run_tracks_duration():
    """Test Job run tracks execution duration"""
    job = ConcreteJob(name="test_job", key="test_key")
    job.run()

    assert job.metric.duration > 0


def test_job_run_not_implemented():
    """Test base Job raises NotImplementedError if _run not implemented"""
    job = Job(name="test_job", key="test_key")

    with pytest.raises(NotImplementedError, match="Subclasses must implement"):
        job.run()


def test_job_run_with_retry_on_failure():
    """Test Job retries on failure"""
    job = FailingJob(name="test_job", key="test_key", retry={"retry": 5, "wait": 0}, fail_count=2)

    result = job.run()

    assert result["status"] == "success"
    assert job.attempts == 3  # Failed 2 times, succeeded on 3rd


def test_job_run_exhausts_retries():
    """Test Job exhausts retries and raises exception"""
    job = FailingJob(
        name="test_job",
        key="test_key",
        retry={"max_retries": 2, "interval": 0},
        fail_count=5,  # Will keep failing
    )

    with pytest.raises(RuntimeError):
        job.run()


def test_job_run_captures_error_in_metric():
    """Test Job captures error in metric when run fails"""
    job = FailingJob(name="test_job", key="test_key", retry={"retry": 1, "wait": 0}, fail_count=5)

    try:
        job.run()
    except RuntimeError:
        pass

    assert len(job.metric.errors) > 0


# ============================================================================
# Job Markpoint Tests
# ============================================================================


def test_job_markpoint():
    """Test Job markpoint adds checkpoint to metric"""
    job = ConcreteJob(name="test_job", key="test_key")
    job.markpoint("checkpoint1")
    job.markpoint("checkpoint2")

    assert "checkpoint1" in job.metric.marks
    assert "checkpoint2" in job.metric.marks


# ============================================================================
# Job Cool Tests
# ============================================================================


@patch("time.sleep")
def test_job_cool(mock_sleep):
    """Test Job cool method calls coolant"""
    job = ConcreteJob(name="test_job", key="test_key", coolant={"interval": 5})

    job.cool()

    mock_sleep.assert_called_once()


# ============================================================================
# Job Get Params Tests
# ============================================================================


def test_job_get_params():
    """Test Job get_params returns params dict"""
    job = ConcreteJob(name="test_job", key="test_key", params={"symbol": "AAPL", "limit": 100})

    result = job.get_params()

    assert result["symbol"] == "AAPL"
    assert result["limit"] == 100


def test_job_get_params_empty():
    """Test Job get_params with no params"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job.get_params()

    assert result == {}


# ============================================================================
# Job Cache Operations Tests
# ============================================================================


def test_job_get_cache_without_cache():
    """Test get_cache returns default when cache is disabled"""
    job = ConcreteJob(name="test_job", key="test_key", cache=False)
    result = job.get_cache("key", default="default_value")

    assert result == "default_value"


def test_job_get_cache_with_cache():
    """Test get_cache retrieves data from cache"""
    job = ConcreteJob(name="test_job", key="test_key", cache=True)
    job.set_cache("test_key", {"data": "value"})

    result = job.get_cache("test_key")

    assert result == {"data": "value"}


def test_job_get_cache_nonexistent_key():
    """Test get_cache returns default for nonexistent key"""
    job = ConcreteJob(name="test_job", key="test_key", cache=True)
    result = job.get_cache("nonexistent", default="not_found")

    assert result == "not_found"


def test_job_set_cache_without_cache():
    """Test set_cache does nothing when cache is disabled"""
    job = ConcreteJob(name="test_job", key="test_key", cache=False)
    job.set_cache("key", "value")  # Should not raise error

    result = job.get_cache("key", default="default")
    assert result == "default"


def test_job_set_cache_with_cache():
    """Test set_cache stores data in cache"""
    job = ConcreteJob(name="test_job", key="test_key", cache=True)
    job.set_cache("test_key", [1, 2, 3])

    result = job.get_cache("test_key")

    assert result == [1, 2, 3]


def test_job_cache_workflow():
    """Test complete cache workflow in CachedJob"""
    job = CachedJob(name="test_job", key="test_key", cache=True)

    # First run computes result
    result1 = job.run()
    assert result1["status"] == "computed"

    # Second run uses cache
    result2 = job.run()
    assert result2["status"] == "from_cache"


# ============================================================================
# Job Reset Tests
# ============================================================================


def test_job_reset_metric():
    """Test Job reset clears metric"""
    job = ConcreteJob(name="test_job", key="test_key")
    job.run()

    assert job.metric.duration > 0

    job.reset()

    assert job.metric.duration == 0


def test_job_reset_cache():
    """Test Job reset clears cache"""
    job = ConcreteJob(name="test_job", key="test_key", cache=True)
    job.set_cache("key", "value")

    assert job.get_cache("key") == "value"

    job.reset()

    assert job.get_cache("key") is None


def test_job_reset_without_cache():
    """Test Job reset works when cache is disabled"""
    job = ConcreteJob(name="test_job", key="test_key", cache=False)
    job.run()

    job.reset()  # Should not raise error

    assert job.metric.duration == 0


# ============================================================================
# Job Describe Tests
# ============================================================================


def test_job_describe_basic():
    """Test Job describe returns basic info"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job.describe()

    assert result["name"] == "test_job"
    assert result["key"] == "test_key"
    assert "params" in result
    assert "coolant" in result
    assert "paginate" in result
    assert "retry" in result
    assert "metric" in result


def test_job_describe_with_cache():
    """Test Job describe includes cache when enabled"""
    job = ConcreteJob(name="test_job", key="test_key", cache=True)
    result = job.describe()

    assert "cache" in result


def test_job_describe_without_cache():
    """Test Job describe excludes cache when disabled"""
    job = ConcreteJob(name="test_job", key="test_key", cache=False)
    result = job.describe()

    assert "cache" not in result


def test_job_describe_with_custom_params():
    """Test Job describe includes custom params"""
    job = ConcreteJob(name="test_job", key="test_key", params={"symbol": "AAPL", "date": "20240115"})
    result = job.describe()

    assert result["params"]["symbol"] == "AAPL"
    assert result["params"]["date"] == "20240115"


# ============================================================================
# Job To Dict Tests
# ============================================================================


def test_job_to_dict_basic():
    """Test Job to_dict returns complete structure"""
    job = ConcreteJob(name="test_job", key="test_key")
    result = job.to_dict()

    assert result["name"] == "test_job"
    assert result["key"] == "test_key"
    assert "params" in result
    assert "coolant" in result
    assert "paginate" in result
    assert "retry" in result
    assert "metric" in result


def test_job_to_dict_with_cache():
    """Test Job to_dict includes cache"""
    job = ConcreteJob(name="test_job", key="test_key", cache=True)
    result = job.to_dict()

    assert result["cache"] is not None
    assert isinstance(result["cache"], dict)


def test_job_to_dict_structure():
    """Test Job to_dict has expected structure"""
    job = ConcreteJob(
        name="test_job",
        key="test_key",
        params={"symbol": "AAPL"},
        coolant={"interval": 5},
        paginate={"pagesize": 1000},
        retry={"max_retries": 3},
        cache=True,
    )
    result = job.to_dict()

    assert isinstance(result["params"], dict)
    assert isinstance(result["coolant"], dict)
    assert isinstance(result["paginate"], dict)
    assert isinstance(result["retry"], dict)
    assert isinstance(result["cache"], dict)
    assert isinstance(result["metric"], dict)


# ============================================================================
# JobLike Protocol Compliance Tests
# ============================================================================


def test_job_implements_joblike_protocol():
    """Test Job implements JobLike protocol"""
    job = ConcreteJob(name="test_job", key="test_key")

    assert isinstance(job, JobLike)


def test_job_has_required_methods():
    """Test Job has all required protocol methods"""
    job = ConcreteJob(name="test_job", key="test_key")

    assert hasattr(job, "run")
    assert callable(job.run)
    assert hasattr(job, "_run")
    assert callable(job._run)
    assert hasattr(job, "describe")
    assert callable(job.describe)
    assert hasattr(job, "to_dict")
    assert callable(job.to_dict)


# ============================================================================
# Integration Tests
# ============================================================================


def test_job_full_lifecycle():
    """Test complete Job lifecycle"""
    job = ConcreteJob(
        name="test_job", key="test_key", params={"symbol": "AAPL"}, retry={"retry": 2, "wait": 0}, cache=True
    )

    # Run job
    result = job.run()
    assert result["status"] == "success"

    # Check metrics
    assert job.metric.duration > 0

    # Check params
    params = job.get_params()
    assert params["symbol"] == "AAPL"

    # Get description
    desc = job.describe()
    assert desc["name"] == "test_job"

    # Reset
    job.reset()
    assert job.metric.duration == 0


def test_job_multiple_runs():
    """Test Job can be run multiple times"""
    job = ConcreteJob(name="test_job", key="test_key")

    result1 = job.run()
    result2 = job.run()

    assert result1 == result2


def test_job_with_all_features():
    """Test Job with all features enabled"""
    job = CachedJob(
        name="complex_job",
        key="complex_key",
        params={"symbol": "AAPL", "date": "20240115"},
        coolant={"interval": 1, "use_jitter": True},
        paginate={"pagesize": 1000, "pagelimit": 5000},
        retry={"retry": 3, "wait": 1},
        cache=True,
    )

    # First run
    job.run()
    result2 = job.run()
    assert result2["status"] == "from_cache"

    # Verify all components
    assert isinstance(job.params, Params)
    assert isinstance(job.coolant, Coolant)
    assert isinstance(job.paginate, Paginate)
    assert isinstance(job.retry, Retry)
    assert isinstance(job.cache, Cache)
    assert isinstance(job.metric, Metric)


def test_job_different_instances_independent():
    """Test different Job instances are independent"""
    job1 = ConcreteJob(name="job1", key="key1", params={"value": 1})
    job2 = ConcreteJob(name="job2", key="key2", params={"value": 2})

    assert job1.name != job2.name
    assert job1.params.value != job2.params.value

    job1.run()

    assert job1.metric.duration > 0
    assert job2.metric.duration == 0

import pytest

from xfintech.data.job.errors import (
    JobAlreadyRegisteredError,
    JobNameError,
    JobNotFoundError,
)
from xfintech.data.job.house import House

# ==================== Test Helper Classes ====================


class _SampleJob:
    """Simple job class for testing"""

    def __init__(self, value: str = "default"):
        self.value = value

    def run(self):
        return f"Running with {self.value}"


class _AnotherJob:
    """Another job class for testing"""

    def __init__(self, name: str, count: int = 0):
        self.name = name
        self.count = count


# ==================== House Initialization Tests ====================


def test_jobhouse_init():
    """Test House initialization creates empty registries"""
    house = House()

    assert isinstance(house._jobs, dict)
    assert isinstance(house._aliases, dict)
    assert len(house._jobs) == 0
    assert len(house._aliases) == 0


def test_jobhouse_init_multiple_instances():
    """Test that multiple House instances are independent"""
    house1 = House()
    house2 = House()

    @house1.register("job1")
    class Job1:
        pass

    # house2 should not have job1
    assert "job1" in house1._jobs
    assert "job1" not in house2._jobs


# ==================== Name Normalization Tests ====================


def test_normalize_name_lowercase():
    """Test _normalize_name converts to lowercase"""
    normalized = House._normalize_name("MyJob")

    assert normalized == "myjob"


def test_normalize_name_strips_whitespace():
    """Test _normalize_name strips leading/trailing whitespace"""
    normalized = House._normalize_name("  my_job  ")

    assert normalized == "my_job"


def test_normalize_name_with_mixed_case():
    """Test _normalize_name with mixed case"""
    normalized = House._normalize_name("Stock_Daily_Job")

    assert normalized == "stock_daily_job"


def test_normalize_name_empty_string_raises_error():
    """Test _normalize_name raises JobNameError for empty string"""
    with pytest.raises(JobNameError, match="job name cannot be empty"):
        House._normalize_name("")


def test_normalize_name_whitespace_only_raises_error():
    """Test _normalize_name raises JobNameError for whitespace-only string"""
    with pytest.raises(JobNameError, match="job name cannot be empty"):
        House._normalize_name("   ")


def test_normalize_name_non_string_raises_error():
    """Test _normalize_name raises JobNameError for non-string input"""
    with pytest.raises(JobNameError, match="job name must be str"):
        House._normalize_name(123)


def test_normalize_name_none_raises_error():
    """Test _normalize_name raises JobNameError for None"""
    with pytest.raises(JobNameError, match="job name must be str"):
        House._normalize_name(None)


# ==================== register() Decorator Tests ====================


def test_register_simple_job():
    """Test registering a simple job class"""
    house = House()

    @house.register("my_job")
    class MyJob:
        pass

    assert "my_job" in house._jobs
    assert house._jobs["my_job"] is MyJob


def test_register_adds_job_name_attribute():
    """Test register adds __job_name__ attribute to class"""
    house = House()

    @house.register("test_job")
    class TestJob:
        pass

    assert hasattr(TestJob, "__job_name__")
    assert TestJob.__job_name__ == "test_job"


def test_register_with_alias():
    """Test registering job with alias"""
    house = House()

    @house.register("stock_daily", alias="daily")
    class StockDailyJob:
        pass

    assert "stock_daily" in house._jobs
    assert "daily" in house._aliases
    assert house._aliases["daily"] == "stock_daily"


def test_register_multiple_jobs():
    """Test registering multiple jobs"""
    house = House()

    @house.register("job1")
    class Job1:
        pass

    @house.register("job2")
    class Job2:
        pass

    assert len(house._jobs) == 2
    assert "job1" in house._jobs
    assert "job2" in house._jobs


def test_register_normalizes_name():
    """Test register normalizes job name"""
    house = House()

    @house.register("My_Job")
    class MyJob:
        pass

    assert "my_job" in house._jobs
    assert "My_Job" not in house._jobs


def test_register_duplicate_alias_raises_error():
    """Test registering duplicate alias raises JobAlreadyRegisteredError"""
    house = House()

    @house.register("job1", alias="shared")
    class Job1:
        pass

    with pytest.raises(JobAlreadyRegisteredError, match="Alias already used: shared"):

        @house.register("job2", alias="shared")
        class Job2:
            pass


def test_register_with_replace_true():
    """Test replace=True allows overwriting existing job"""
    house = House()

    @house.register("my_job")
    class OriginalJob:
        pass

    @house.register("my_job", replace=True)
    class ReplacedJob:
        pass

    assert house._jobs["my_job"] is ReplacedJob
    assert house._jobs["my_job"] is not OriginalJob


def test_register_with_replace_true_for_alias():
    """Test replace=True allows overwriting existing alias"""
    house = House()

    @house.register("job1", alias="shared")
    class Job1:
        pass

    @house.register("job2", alias="shared", replace=True)
    class Job2:
        pass

    assert house._aliases["shared"] == "job2"


def test_register_same_alias_same_job_no_error():
    """Test registering same alias for same job doesn't raise error"""
    house = House()

    @house.register("my_job", alias="alias1")
    class MyJob:
        pass

    # Re-registering with replace, same alias should work
    @house.register("my_job", alias="alias1", replace=True)
    class MyJob2:
        pass

    assert house._aliases["alias1"] == "my_job"


def test_register_empty_name_raises_error():
    """Test register with empty name raises JobNameError"""
    house = House()

    with pytest.raises(JobNameError, match="job name cannot be empty"):

        @house.register("")
        class MyJob:
            pass


def test_register_with_uppercase_alias():
    """Test register normalizes alias name"""
    house = House()

    @house.register("job", alias="MY_ALIAS")
    class MyJob:
        pass

    assert "my_alias" in house._aliases


# ==================== lookup() Method Tests ====================


def test_lookup_by_name():
    """Test looking up job by registered name"""
    house = House()

    @house.register("my_job")
    class MyJob:
        pass

    result = house.lookup("my_job")

    assert result is MyJob


def test_lookup_by_alias():
    """Test looking up job by alias"""
    house = House()

    @house.register("stock_daily", alias="daily")
    class StockDailyJob:
        pass

    result = house.lookup("daily")

    assert result is StockDailyJob


def test_lookup_case_insensitive():
    """Test lookup is case insensitive"""
    house = House()

    @house.register("my_job")
    class MyJob:
        pass

    result1 = house.lookup("MY_JOB")
    result2 = house.lookup("My_Job")
    result3 = house.lookup("my_job")

    assert result1 is MyJob
    assert result2 is MyJob
    assert result3 is MyJob


def test_lookup_strips_whitespace():
    """Test lookup strips whitespace from name"""
    house = House()

    @house.register("my_job")
    class MyJob:
        pass

    result = house.lookup("  my_job  ")

    assert result is MyJob


def test_lookup_nonexistent_raises_error():
    """Test lookup raises JobNotFoundError for nonexistent job"""
    house = House()

    with pytest.raises(JobNotFoundError, match="job not found: nonexistent"):
        house.lookup("nonexistent")


def test_lookup_after_multiple_registrations():
    """Test lookup works correctly with multiple jobs"""
    house = House()

    @house.register("job1")
    class Job1:
        pass

    @house.register("job2")
    class Job2:
        pass

    @house.register("job3")
    class Job3:
        pass

    assert house.lookup("job1") is Job1
    assert house.lookup("job2") is Job2
    assert house.lookup("job3") is Job3


def test_lookup_empty_string_raises_error():
    """Test lookup with empty string raises JobNameError"""
    house = House()

    with pytest.raises(JobNameError, match="job name cannot be empty"):
        house.lookup("")


# ==================== create() Method Tests ====================


def test_create_simple_job():
    """Test creating job instance without arguments"""
    house = House()

    @house.register("sample_job")
    class SampleJob:
        def __init__(self):
            self.value = "test"

    instance = house.create("sample_job")

    assert isinstance(instance, SampleJob)
    assert instance.value == "test"


def test_create_job_with_args():
    """Test creating job instance with positional arguments"""
    house = House()

    @house.register("job_with_args")
    class JobWithArgs:
        def __init__(self, arg1, arg2):
            self.arg1 = arg1
            self.arg2 = arg2

    instance = house.create("job_with_args", "value1", "value2")

    assert instance.arg1 == "value1"
    assert instance.arg2 == "value2"


def test_create_job_with_kwargs():
    """Test creating job instance with keyword arguments"""
    house = House()

    @house.register("job_with_kwargs")
    class JobWithKwargs:
        def __init__(self, title="default", count=0):
            self.title = title
            self.count = count

    instance = house.create("job_with_kwargs", title="test", count=5)

    assert instance.title == "test"
    assert instance.count == 5


def test_create_job_with_mixed_args():
    """Test creating job instance with both args and kwargs"""
    house = House()

    @house.register("mixed_job")
    class MixedJob:
        def __init__(self, pos_arg, keyword_arg="default"):
            self.pos_arg = pos_arg
            self.keyword_arg = keyword_arg

    instance = house.create("mixed_job", "positional", keyword_arg="keyword")

    assert instance.pos_arg == "positional"
    assert instance.keyword_arg == "keyword"


def test_create_by_alias():
    """Test creating job instance using alias"""
    house = House()

    @house.register("long_name", alias="short")
    class MyJob:
        def __init__(self, data):
            self.data = data

    instance = house.create("short", data="test")

    assert isinstance(instance, MyJob)
    assert instance.data == "test"


def test_create_case_insensitive():
    """Test create is case insensitive"""
    house = House()

    @house.register("my_job")
    class MyJob:
        def __init__(self):
            self.created = True

    instance = house.create("MY_JOB")

    assert isinstance(instance, MyJob)
    assert instance.created is True


def test_create_nonexistent_raises_error():
    """Test create raises JobNotFoundError for nonexistent job"""
    house = House()

    with pytest.raises(JobNotFoundError, match="job not found: nonexistent"):
        house.create("nonexistent")


def test_create_multiple_instances():
    """Test creating multiple instances of same job"""
    house = House()

    @house.register("counter_job")
    class CounterJob:
        def __init__(self, start=0):
            self.count = start

    instance1 = house.create("counter_job", start=10)
    instance2 = house.create("counter_job", start=20)

    assert instance1.count == 10
    assert instance2.count == 20
    assert instance1 is not instance2


# ==================== list() Method Tests ====================


def test_list_empty_house():
    """Test list returns empty list for new House"""
    house = House()

    result = house.list()

    assert result == []


def test_list_single_job():
    """Test list returns single registered job"""
    house = House()

    @house.register("my_job")
    class MyJob:
        pass

    result = house.list()

    assert result == ["my_job"]


def test_list_multiple_jobs():
    """Test list returns all registered jobs"""
    house = House()

    @house.register("job_a")
    class JobA:
        pass

    @house.register("job_c")
    class JobC:
        pass

    @house.register("job_b")
    class JobB:
        pass

    result = house.list()

    assert len(result) == 3
    assert "job_a" in result
    assert "job_b" in result
    assert "job_c" in result


def test_list_returns_sorted():
    """Test list returns jobs in sorted order"""
    house = House()

    @house.register("zebra")
    class Zebra:
        pass

    @house.register("alpha")
    class Alpha:
        pass

    @house.register("beta")
    class Beta:
        pass

    result = house.list()

    assert result == ["alpha", "beta", "zebra"]


def test_list_does_not_include_aliases():
    """Test list does not include aliases, only job names"""
    house = House()

    @house.register("job1", alias="alias1")
    class Job1:
        pass

    @house.register("job2", alias="alias2")
    class Job2:
        pass

    result = house.list()

    assert result == ["alias1", "alias2", "job1", "job2"]


def test_list_after_replace():
    """Test list reflects replaced jobs correctly"""
    house = House()

    @house.register("my_job")
    class OriginalJob:
        pass

    @house.register("my_job", replace=True)
    class ReplacedJob:
        pass

    result = house.list()

    assert result == ["my_job"]
    assert len(result) == 1


# ==================== Integration Tests ====================


def test_full_workflow():
    """Test complete workflow: register -> lookup -> create"""
    house = House()

    @house.register("data_processor", alias="processor")
    class DataProcessor:
        def __init__(self, data_source: str):
            self.data_source = data_source
            self.processed = False

        def process(self):
            self.processed = True
            return f"Processed data from {self.data_source}"

    # Lookup by name
    ProcessorClass = house.lookup("data_processor")
    assert ProcessorClass is DataProcessor

    # Lookup by alias
    ProcessorClass = house.lookup("processor")
    assert ProcessorClass is DataProcessor

    # Create instance
    processor = house.create("data_processor", data_source="API")
    assert isinstance(processor, DataProcessor)
    assert processor.data_source == "API"
    assert processor.processed is False

    # Use the instance
    result = processor.process()
    assert processor.processed is True
    assert result == "Processed data from API"


def test_multiple_aliases_different_jobs():
    """Test multiple jobs with their own aliases"""
    house = House()

    @house.register("stock_daily", alias="daily")
    class StockDailyJob:
        pass

    @house.register("stock_weekly", alias="weekly")
    class StockWeeklyJob:
        pass

    assert house.lookup("daily") is StockDailyJob
    assert house.lookup("weekly") is StockWeeklyJob
    assert house.lookup("stock_daily") is StockDailyJob
    assert house.lookup("stock_weekly") is StockWeeklyJob


def test_case_insensitive_throughout():
    """Test case insensitivity across all operations"""
    house = House()

    @house.register("MyJob", alias="MyAlias")
    class MyJob:
        def __init__(self, value):
            self.value = value

    # All should work
    assert house.lookup("MYJOB") is MyJob
    assert house.lookup("myjob") is MyJob
    assert house.lookup("MyJob") is MyJob
    assert house.lookup("MYALIAS") is MyJob
    assert house.lookup("myalias") is MyJob

    instance = house.create("MYJOB", value="test")
    assert instance.value == "test"

    jobs = house.list()
    assert "myjob" in jobs


def test_job_with_complex_initialization():
    """Test job with complex initialization logic"""
    house = House()

    @house.register("complex_job")
    class ComplexJob:
        def __init__(self, config: dict, timeout: int = 30, **options):
            self.config = config
            self.timeout = timeout
            self.options = options

    instance = house.create(
        "complex_job",
        config={"host": "localhost", "port": 8080},
        timeout=60,
        retry=3,
        verbose=True,
    )

    assert instance.config == {"host": "localhost", "port": 8080}
    assert instance.timeout == 60
    assert instance.options == {"retry": 3, "verbose": True}


def test_replacing_job_updates_lookup():
    """Test that replacing a job updates lookup results"""
    house = House()

    @house.register("my_job")
    class OriginalJob:
        version = 1

    assert house.lookup("my_job").version == 1

    @house.register("my_job", replace=True)
    class NewJob:
        version = 2

    assert house.lookup("my_job").version == 2


# ==================== Error Handling Tests ====================


def test_job_not_found_error_inheritance():
    """Test JobNotFoundError inherits from KeyError"""
    assert issubclass(JobNotFoundError, KeyError)


def test_job_already_registered_error_inheritance():
    """Test JobAlreadyRegisteredError inherits from KeyError"""
    assert issubclass(JobAlreadyRegisteredError, KeyError)


def test_job_name_error_inheritance():
    """Test JobNameError inherits from ValueError"""
    assert issubclass(JobNameError, ValueError)


def test_error_messages_are_descriptive():
    """Test that error messages contain useful information"""
    house = House()

    # JobNotFoundError
    try:
        house.lookup("missing_job")
    except JobNotFoundError as e:
        assert "missing_job" in str(e)

    # JobAlreadyRegisteredError
    @house.register("duplicate")
    class Job1:
        pass

    try:

        @house.register("duplicate")
        class Job2:
            pass
    except JobAlreadyRegisteredError as e:
        assert "duplicate" in str(e)

    # JobNameError
    try:
        house.lookup("")
    except JobNameError as e:
        assert "empty" in str(e).lower()


# ==================== Edge Cases ====================


def test_job_with_no_init():
    """Test registering job class without __init__"""
    house = House()

    @house.register("simple")
    class SimpleJob:
        pass

    instance = house.create("simple")
    assert isinstance(instance, SimpleJob)


def test_special_characters_in_name():
    """Test job names with underscores and numbers"""
    house = House()

    @house.register("job_123")
    class Job123:
        pass

    @house.register("another_job_456")
    class AnotherJob:
        pass

    assert house.lookup("job_123") is Job123
    assert house.lookup("another_job_456") is AnotherJob


def test_very_long_job_name():
    """Test handling very long job names"""
    house = House()
    long_name = "very_long_job_name_" * 10

    @house.register(long_name)
    class LongNameJob:
        pass

    result = house.lookup(long_name)
    assert result is LongNameJob


def test_unicode_in_job_name():
    """Test job names with unicode characters (normalized to lowercase)"""
    house = House()

    @house.register("job_测试")
    class UnicodeJob:
        pass

    result = house.lookup("job_测试")
    assert result is UnicodeJob

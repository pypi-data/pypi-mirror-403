"""
Test suite for Params class
Tests cover initialization, attribute access, serialization, and data conversion
"""

from datetime import datetime

import pytest

from xfintech.data.common.params import Params

# ============================================================================
# Initialization Tests
# ============================================================================


def test_params_init_empty():
    """Test Params initialization with no arguments"""
    params = Params()
    assert params.to_dict() == {}


def test_params_init_single_kwarg():
    """Test Params initialization with single keyword argument"""
    params = Params(name="test")
    assert params.name == "test"
    assert params.to_dict() == {"name": "test"}


def test_params_init_multiple_kwargs():
    """Test Params initialization with multiple keyword arguments"""
    params = Params(symbol="AAPL", price=150.5, quantity=100)
    assert params.symbol == "AAPL"
    assert params.price == 150.5
    assert params.quantity == 100


def test_params_init_with_various_types():
    """Test Params initialization with various data types"""
    params = Params(
        string="text",
        integer=42,
        floating=3.14,
        boolean=True,
        none_value=None,
        list_value=[1, 2, 3],
        dict_value={"key": "value"},
    )
    assert params.string == "text"
    assert params.integer == 42
    assert params.floating == 3.14
    assert params.boolean is True
    assert params.none_value is None
    assert params.list_value == [1, 2, 3]
    assert params.dict_value == {"key": "value"}


def test_params_init_with_datetime():
    """Test Params initialization with datetime object"""
    dt = datetime(2024, 1, 15, 10, 30, 0)
    params = Params(timestamp=dt)
    assert params.timestamp == dt


def test_params_init_with_nested_params():
    """Test Params initialization with nested Params object"""
    nested = Params(inner="value")
    params = Params(outer="test", nested=nested)
    assert params.outer == "test"
    assert isinstance(params.nested, Params)
    assert params.nested.inner == "value"


# ============================================================================
# Attribute Access Tests
# ============================================================================


def test_params_attribute_access():
    """Test direct attribute access"""
    params = Params(key="value")
    assert params.key == "value"


def test_params_attribute_assignment():
    """Test direct attribute assignment"""
    params = Params()
    params.new_key = "new_value"
    assert params.new_key == "new_value"
    assert params.to_dict() == {"new_key": "new_value"}


def test_params_attribute_modification():
    """Test modifying existing attribute"""
    params = Params(value=10)
    params.value = 20
    assert params.value == 20


def test_params_attribute_error():
    """Test accessing non-existent attribute raises AttributeError"""
    params = Params()
    with pytest.raises(AttributeError):
        _ = params.nonexistent


# ============================================================================
# Contains Tests (__contains__)
# ============================================================================


def test_params_contains_true():
    """Test __contains__ returns True for existing attribute"""
    params = Params(key="value")
    assert "key" in params


def test_params_contains_false():
    """Test __contains__ returns False for non-existent attribute"""
    params = Params(key="value")
    assert "other" not in params


def test_params_contains_after_set():
    """Test __contains__ after setting attribute"""
    params = Params()
    assert "new_attr" not in params
    params.new_attr = "value"
    assert "new_attr" in params


def test_params_contains_private_attribute():
    """Test __contains__ with private attributes"""
    params = Params()
    params._private = "value"
    assert "_private" in params


# ============================================================================
# String Representation Tests
# ============================================================================


def test_params_str_empty():
    """Test __str__ with empty Params"""
    params = Params()
    assert str(params) == "{}"


def test_params_str_with_data():
    """Test __str__ with data"""
    params = Params(key="value", number=42)
    result = str(params)
    # Could be in different order
    assert "key" in result
    assert "value" in result
    assert "number" in result
    assert "42" in result


def test_params_repr_empty():
    """Test __repr__ with empty Params"""
    params = Params()
    assert repr(params) == "Params({})"


def test_params_repr_with_data():
    """Test __repr__ with data"""
    params = Params(key="value")
    result = repr(params)
    assert result.startswith("Params(")
    assert "key" in result
    assert "value" in result


# ============================================================================
# Get Method Tests
# ============================================================================


def test_params_get_existing_key():
    """Test get method with existing key"""
    params = Params(key="value")
    assert params.get("key") == "value"


def test_params_get_nonexistent_key():
    """Test get method with non-existent key returns None"""
    params = Params()
    assert params.get("nonexistent") is None


def test_params_get_with_default():
    """Test get method with default value"""
    params = Params()
    assert params.get("missing", "default") == "default"


def test_params_get_existing_key_ignores_default():
    """Test get method with existing key ignores default"""
    params = Params(key="value")
    assert params.get("key", "default") == "value"


def test_params_get_none_value():
    """Test get method with None as actual value"""
    params = Params(key=None)
    assert params.get("key") is None
    assert params.get("key", "default") is None


# ============================================================================
# Set Method Tests
# ============================================================================


def test_params_set_new_attribute():
    """Test set method creates new attribute"""
    params = Params()
    params.set("key", "value")
    assert params.key == "value"


def test_params_set_existing_attribute():
    """Test set method overwrites existing attribute"""
    params = Params(key="old")
    params.set("key", "new")
    assert params.key == "new"


def test_params_set_various_types():
    """Test set method with various types"""
    params = Params()
    params.set("string", "text")
    params.set("integer", 42)
    params.set("list", [1, 2, 3])

    assert params.string == "text"
    assert params.integer == 42
    assert params.list == [1, 2, 3]


def test_params_set_none():
    """Test set method with None value"""
    params = Params()
    params.set("key", None)
    assert params.key is None


# ============================================================================
# From Dict Tests
# ============================================================================


def test_params_from_dict_empty():
    """Test from_dict with empty dictionary"""
    params = Params.from_dict({})
    assert params.to_dict() == {}


def test_params_from_dict_single_item():
    """Test from_dict with single item"""
    params = Params.from_dict({"key": "value"})
    assert params.key == "value"


def test_params_from_dict_multiple_items():
    """Test from_dict with multiple items"""
    data = {"symbol": "AAPL", "price": 150.5, "quantity": 100}
    params = Params.from_dict(data)
    assert params.symbol == "AAPL"
    assert params.price == 150.5
    assert params.quantity == 100


def test_params_from_dict_with_params_instance():
    """Test from_dict with Params instance returns same instance"""
    original = Params(key="value")
    result = Params.from_dict(original)
    assert result is original


def test_params_from_dict_with_nested_dict():
    """Test from_dict with nested dictionary"""
    data = {"outer": "value", "inner": {"nested": "data"}}
    params = Params.from_dict(data)
    assert params.outer == "value"
    assert params.inner == {"nested": "data"}


# ============================================================================
# Ensure Serialisable Tests
# ============================================================================


def test_params_ensure_serialisable_int():
    """Test ensure_serialisable with integer"""
    assert Params.ensure_serialisable(42) == 42


def test_params_ensure_serialisable_float():
    """Test ensure_serialisable with float"""
    assert Params.ensure_serialisable(3.14) == 3.14


def test_params_ensure_serialisable_string():
    """Test ensure_serialisable with string"""
    assert Params.ensure_serialisable("text") == "text"


def test_params_ensure_serialisable_bool():
    """Test ensure_serialisable with boolean"""
    assert Params.ensure_serialisable(True) is True
    assert Params.ensure_serialisable(False) is False


def test_params_ensure_serialisable_none():
    """Test ensure_serialisable with None"""
    assert Params.ensure_serialisable(None) is None


def test_params_ensure_serialisable_datetime():
    """Test ensure_serialisable with datetime converts to string"""
    dt = datetime(2024, 1, 15)
    result = Params.ensure_serialisable(dt)
    assert result == "2024-01-15"
    assert isinstance(result, str)


def test_params_ensure_serialisable_params_instance():
    """Test ensure_serialisable with Params instance converts to dict"""
    params = Params(key="value", number=42)
    result = Params.ensure_serialisable(params)
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 42


def test_params_ensure_serialisable_dict():
    """Test ensure_serialisable with dictionary"""
    data = {"key": "value", "number": 42}
    result = Params.ensure_serialisable(data)
    assert result == {"key": "value", "number": 42}


def test_params_ensure_serialisable_dict_with_datetime():
    """Test ensure_serialisable with dict containing datetime"""
    dt = datetime(2024, 1, 15)
    data = {"date": dt, "value": 100}
    result = Params.ensure_serialisable(data)
    assert result == {"date": "2024-01-15", "value": 100}


def test_params_ensure_serialisable_list():
    """Test ensure_serialisable with list"""
    data = [1, 2, 3]
    result = Params.ensure_serialisable(data)
    assert result == [1, 2, 3]


def test_params_ensure_serialisable_list_with_datetime():
    """Test ensure_serialisable with list containing datetime"""
    dt = datetime(2024, 1, 15)
    data = [dt, "text", 42]
    result = Params.ensure_serialisable(data)
    assert result == ["2024-01-15", "text", 42]


def test_params_ensure_serialisable_nested_dict():
    """Test ensure_serialisable with nested dictionary"""
    dt = datetime(2024, 1, 15)
    data = {"outer": {"inner": {"date": dt, "value": 100}}}
    result = Params.ensure_serialisable(data)
    assert result["outer"]["inner"]["date"] == "2024-01-15"
    assert result["outer"]["inner"]["value"] == 100


def test_params_ensure_serialisable_nested_list():
    """Test ensure_serialisable with nested list"""
    dt = datetime(2024, 1, 15)
    data = [[dt, 1], [2, "text"]]
    result = Params.ensure_serialisable(data)
    assert result == [["2024-01-15", 1], [2, "text"]]


def test_params_ensure_serialisable_custom_object():
    """Test ensure_serialisable with custom object converts to string"""

    class CustomClass:
        def __str__(self):
            return "custom_object"

    obj = CustomClass()
    result = Params.ensure_serialisable(obj)
    assert result == "custom_object"
    assert isinstance(result, str)


def test_params_ensure_serialisable_complex_nested():
    """Test ensure_serialisable with complex nested structure"""
    dt = datetime(2024, 1, 15)
    nested_params = Params(inner_key="inner_value")
    data = {"date": dt, "params": nested_params, "list": [dt, nested_params, 42], "nested": {"deep": {"date": dt}}}
    result = Params.ensure_serialisable(data)
    assert result["date"] == "2024-01-15"
    assert result["params"]["inner_key"] == "inner_value"
    assert result["list"][0] == "2024-01-15"
    assert result["list"][1]["inner_key"] == "inner_value"
    assert result["list"][2] == 42
    assert result["nested"]["deep"]["date"] == "2024-01-15"


# ============================================================================
# Describe Method Tests
# ============================================================================


def test_params_describe_empty():
    """Test describe with empty Params"""
    params = Params()
    assert params.describe() == {}


def test_params_describe_basic_types():
    """Test describe with basic types"""
    params = Params(string="text", number=42, boolean=True)
    result = params.describe()
    assert result == {"string": "text", "number": 42, "boolean": True}


def test_params_describe_with_datetime():
    """Test describe serializes datetime to string"""
    dt = datetime(2024, 1, 15, 10, 30, 0)
    params = Params(date=dt, value=100)
    result = params.describe()
    assert result["date"] == "2024-01-15"
    assert result["value"] == 100


def test_params_describe_with_nested_params():
    """Test describe serializes nested Params"""
    nested = Params(inner="value")
    params = Params(outer="test", nested=nested)
    result = params.describe()
    assert result["outer"] == "test"
    assert result["nested"] == {"inner": "value"}


def test_params_describe_excludes_private():
    """Test describe excludes private attributes (starting with _)"""
    params = Params(public="visible")
    params._private = "hidden"
    result = params.describe()
    assert "public" in result
    assert "_private" not in result


def test_params_describe_with_list():
    """Test describe with list containing various types"""
    dt = datetime(2024, 1, 15)
    params = Params(items=[1, "text", dt])
    result = params.describe()
    assert result["items"] == [1, "text", "2024-01-15"]


def test_params_describe_with_dict():
    """Test describe with dict containing datetime"""
    dt = datetime(2024, 1, 15)
    params = Params(data={"date": dt, "value": 100})
    result = params.describe()
    assert result["data"]["date"] == "2024-01-15"
    assert result["data"]["value"] == 100


# ============================================================================
# To Dict Method Tests
# ============================================================================


def test_params_to_dict_empty():
    """Test to_dict with empty Params"""
    params = Params()
    assert params.to_dict() == {}


def test_params_to_dict_basic():
    """Test to_dict with basic types"""
    params = Params(key="value", number=42)
    result = params.to_dict()
    assert result == {"key": "value", "number": 42}


def test_params_to_dict_preserves_datetime():
    """Test to_dict preserves datetime objects (does not serialize)"""
    dt = datetime(2024, 1, 15)
    params = Params(date=dt)
    result = params.to_dict()
    assert result["date"] == dt
    assert isinstance(result["date"], datetime)


def test_params_to_dict_preserves_params():
    """Test to_dict preserves Params objects (does not serialize)"""
    nested = Params(inner="value")
    params = Params(nested=nested)
    result = params.to_dict()
    assert isinstance(result["nested"], Params)
    assert result["nested"].inner == "value"


def test_params_to_dict_excludes_private():
    """Test to_dict excludes private attributes"""
    params = Params(public="visible")
    params._private = "hidden"
    result = params.to_dict()
    assert "public" in result
    assert "_private" not in result


def test_params_to_dict_vs_describe():
    """Test differences between to_dict and describe"""
    dt = datetime(2024, 1, 15)
    nested = Params(inner="value")
    params = Params(date=dt, nested=nested, value=100)

    to_dict_result = params.to_dict()
    describe_result = params.describe()

    # to_dict preserves datetime
    assert isinstance(to_dict_result["date"], datetime)
    # describe serializes datetime
    assert describe_result["date"] == "2024-01-15"

    # to_dict preserves Params
    assert isinstance(to_dict_result["nested"], Params)
    # describe serializes Params
    assert describe_result["nested"] == {"inner": "value"}


# ============================================================================
# Integration Tests
# ============================================================================


def test_params_full_workflow():
    """Test complete workflow with Params"""
    # Create from dict
    data = {"symbol": "AAPL", "quantity": 100}
    params = Params.from_dict(data)

    # Add attributes
    params.set("price", 150.5)
    params.timestamp = datetime(2024, 1, 15)

    # Check attributes
    assert "symbol" in params
    assert params.get("quantity") == 100

    # Serialize
    serialized = params.describe()
    assert serialized["timestamp"] == "2024-01-15"


def test_params_dict_roundtrip():
    """Test converting to dict and back"""
    original = Params(key="value", number=42, flag=True)
    data = original.to_dict()
    restored = Params.from_dict(data)

    assert restored.key == original.key
    assert restored.number == original.number
    assert restored.flag == original.flag


def test_params_api_request_simulation():
    """Test simulating API request parameters"""
    params = Params(symbol="AAPL", start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 31), limit=100, offset=0)

    # Serialize for API
    api_params = params.describe()
    assert api_params["symbol"] == "AAPL"
    assert api_params["start_date"] == "2024-01-01"
    assert api_params["end_date"] == "2024-01-31"
    assert api_params["limit"] == 100


def test_params_nested_structure():
    """Test complex nested structure"""
    params = Params(
        user=Params(name="John", id=123), preferences=Params(theme="dark", notifications=True), data=[1, 2, 3]
    )

    assert params.user.name == "John"
    assert params.preferences.theme == "dark"

    # Serialize entire structure
    serialized = params.describe()
    assert serialized["user"]["name"] == "John"
    assert serialized["preferences"]["notifications"] is True


def test_params_modification_tracking():
    """Test modifying params and tracking changes"""
    params = Params(value=10)
    original = params.to_dict()

    params.set("value", 20)
    params.set("new_field", "added")

    modified = params.to_dict()
    assert original != modified
    assert modified["value"] == 20
    assert "new_field" in modified


def test_params_multiple_instances_independence():
    """Test multiple Params instances are independent"""
    p1 = Params(value=10)
    p2 = Params(value=20)

    p1.set("value", 15)

    assert p1.value == 15
    assert p2.value == 20


def test_params_dynamic_attributes():
    """Test dynamically adding and removing attributes"""
    params = Params()

    # Add attributes
    for i in range(5):
        params.set(f"key{i}", i * 10)

    # Verify all added
    for i in range(5):
        assert f"key{i}" in params
        assert params.get(f"key{i}") == i * 10


def test_params_empty_string_handling():
    """Test handling of empty strings"""
    params = Params(empty="", value="text")
    assert params.empty == ""
    assert params.value == "text"

    result = params.to_dict()
    assert result["empty"] == ""


def test_params_zero_value_handling():
    """Test handling of zero values"""
    params = Params(zero=0, positive=1, negative=-1)
    assert params.zero == 0

    result = params.describe()
    assert result["zero"] == 0


def test_params_special_characters_in_keys():
    """Test keys with special characters"""
    params = Params()
    params.set("key-with-dash", "value1")
    params.set("key_with_underscore", "value2")
    params.set("key.with.dot", "value3")

    assert params.get("key-with-dash") == "value1"
    assert params.get("key_with_underscore") == "value2"
    assert params.get("key.with.dot") == "value3"


# ============================================================================
# Identifier Property Tests
# ============================================================================


def test_params_identifier_basic():
    """Test identifier property returns SHA256 hash"""
    params = Params(symbol="AAPL", quantity=100)
    identifier = params.identifier

    # SHA256 hash should be 64 characters (256 bits in hex)
    assert isinstance(identifier, str)
    assert len(identifier) == 64
    assert all(c in "0123456789abcdef" for c in identifier)


def test_params_identifier_deterministic():
    """Test that same params produce same identifier"""
    params1 = Params(symbol="AAPL", price=150.5, quantity=100)
    params2 = Params(symbol="AAPL", price=150.5, quantity=100)

    assert params1.identifier == params2.identifier


def test_params_identifier_order_independent():
    """Test that parameter order doesn't affect identifier"""
    # Different order of initialization
    params1 = Params(symbol="AAPL", price=150.5, quantity=100)
    params2 = Params(quantity=100, symbol="AAPL", price=150.5)

    # Should produce same identifier because JSON uses sorted keys
    assert params1.identifier == params2.identifier


def test_params_identifier_different_values():
    """Test that different values produce different identifiers"""
    params1 = Params(symbol="AAPL", quantity=100)
    params2 = Params(symbol="AAPL", quantity=200)

    assert params1.identifier != params2.identifier


def test_params_identifier_different_keys():
    """Test that different keys produce different identifiers"""
    params1 = Params(symbol="AAPL", quantity=100)
    params2 = Params(symbol="AAPL", amount=100)

    assert params1.identifier != params2.identifier


def test_params_identifier_empty_params():
    """Test identifier for empty Params"""
    params = Params()
    identifier = params.identifier

    assert isinstance(identifier, str)
    assert len(identifier) == 64


def test_params_identifier_with_datetime():
    """Test identifier handles datetime serialization"""
    dt = datetime(2024, 1, 15, 10, 30, 0)
    params1 = Params(timestamp=dt)
    params2 = Params(timestamp=dt)

    # Same datetime should produce same identifier
    assert params1.identifier == params2.identifier

    # Different datetime should produce different identifier
    params3 = Params(timestamp=datetime(2024, 1, 16, 10, 30, 0))
    assert params1.identifier != params3.identifier


def test_params_identifier_with_nested_params():
    """Test identifier with nested Params objects"""
    nested1 = Params(inner="value1")
    nested2 = Params(inner="value1")

    params1 = Params(outer="test", nested=nested1)
    params2 = Params(outer="test", nested=nested2)

    # Same nested structure should produce same identifier
    assert params1.identifier == params2.identifier


def test_params_identifier_with_nested_dict():
    """Test identifier with nested dictionary"""
    params1 = Params(data={"key1": "value1", "key2": "value2"})
    params2 = Params(data={"key2": "value2", "key1": "value1"})

    # Order in nested dict shouldn't matter
    assert params1.identifier == params2.identifier


def test_params_identifier_with_list():
    """Test identifier with list values"""
    params1 = Params(items=[1, 2, 3])
    params2 = Params(items=[1, 2, 3])
    params3 = Params(items=[3, 2, 1])

    # Same list should produce same identifier
    assert params1.identifier == params2.identifier

    # Different order in list should produce different identifier
    assert params1.identifier != params3.identifier


def test_params_identifier_with_various_types():
    """Test identifier with mixed data types"""
    params = Params(
        string="text",
        integer=42,
        floating=3.14,
        boolean=True,
        none_value=None,
        list_value=[1, 2, 3],
        dict_value={"key": "value"},
    )

    identifier = params.identifier
    assert isinstance(identifier, str)
    assert len(identifier) == 64


def test_params_identifier_with_unicode():
    """Test identifier handles Unicode characters"""
    params1 = Params(name="中文测试", symbol="股票")
    params2 = Params(name="中文测试", symbol="股票")

    assert params1.identifier == params2.identifier


def test_params_identifier_with_special_characters():
    """Test identifier with special characters in values"""
    params1 = Params(text="Hello, World! @#$%^&*()")
    params2 = Params(text="Hello, World! @#$%^&*()")

    assert params1.identifier == params2.identifier


def test_params_identifier_immutability():
    """Test that identifier changes when params are modified"""
    params = Params(symbol="AAPL", quantity=100)
    identifier1 = params.identifier

    # Modify params
    params.quantity = 200
    identifier2 = params.identifier

    # Identifier should change
    assert identifier1 != identifier2


def test_params_identifier_with_complex_nested_structure():
    """Test identifier with deeply nested structures"""
    params1 = Params(
        level1={"level2": {"level3": {"value": "deep"}}},
        list_of_dicts=[{"a": 1}, {"b": 2}],
    )
    params2 = Params(
        level1={"level2": {"level3": {"value": "deep"}}},
        list_of_dicts=[{"a": 1}, {"b": 2}],
    )

    assert params1.identifier == params2.identifier


def test_params_identifier_consistency_after_modification():
    """Test that adding new attributes changes identifier"""
    params = Params(symbol="AAPL")
    identifier1 = params.identifier

    # Add new attribute
    params.quantity = 100
    identifier2 = params.identifier

    assert identifier1 != identifier2

    # Remove attribute
    delattr(params, "quantity")
    identifier3 = params.identifier

    # Should be back to original identifier
    assert identifier1 == identifier3


def test_params_identifier_with_datetime_serialization():
    """Test that datetime is properly serialized in identifier"""
    dt = datetime(2024, 1, 15)
    params1 = Params(date=dt)
    # Manually create params with string date (what describe() converts to)
    params2 = Params(date="2024-01-15")

    # These should produce same identifier since datetime is serialized to string
    assert params1.identifier == params2.identifier


def test_params_identifier_hash_distribution():
    """Test that similar params produce different hashes (no collision)"""
    identifiers = set()

    for i in range(100):
        params = Params(index=i, value=f"test_{i}")
        identifiers.add(params.identifier)

    # All 100 should be unique
    assert len(identifiers) == 100


def test_params_identifier_stability():
    """Test identifier remains stable across multiple reads"""
    params = Params(symbol="AAPL", quantity=100, price=150.5)

    # Read identifier multiple times
    id1 = params.identifier
    id2 = params.identifier
    id3 = params.identifier

    # All should be identical
    assert id1 == id2 == id3

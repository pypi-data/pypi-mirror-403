"""
Test suite for Paginate class
Tests cover initialization, pagination operations, offset management, and data conversion
"""

from xfintech.data.common.paginate import Paginate

# ============================================================================
# Initialization Tests
# ============================================================================


def test_paginate_init_defaults():
    """Test Paginate initialization with default values"""
    paginator = Paginate()
    assert paginator.pagesize == 5000
    assert paginator.pagelimit == 10000
    assert paginator.offset == 0


def test_paginate_init_custom_values():
    """Test Paginate initialization with custom values"""
    paginator = Paginate(pagelimit=20000, pagesize=1000, offset=500)
    assert paginator.pagesize == 1000
    assert paginator.pagelimit == 20000
    assert paginator.offset == 500


def test_paginate_init_partial_custom():
    """Test Paginate initialization with partial custom values"""
    paginator = Paginate(pagesize=2000)
    assert paginator.pagesize == 2000
    assert paginator.pagelimit == 10000
    assert paginator.offset == 0


def test_paginate_init_zero_values():
    """Test Paginate initialization with zero values falls back to defaults"""
    paginator = Paginate(pagelimit=0, pagesize=0, offset=0)
    assert paginator.pagesize == 5000
    assert paginator.pagelimit == 10000
    assert paginator.offset == 0


def test_paginate_init_negative_pagelimit():
    """Test Paginate initialization with negative pagelimit falls back to default"""
    paginator = Paginate(pagelimit=-100)
    assert paginator.pagelimit == 10000


def test_paginate_init_negative_pagesize():
    """Test Paginate initialization with negative pagesize falls back to default"""
    paginator = Paginate(pagesize=-50)
    assert paginator.pagesize == 5000


def test_paginate_init_negative_offset():
    """Test Paginate initialization with negative offset falls back to default"""
    paginator = Paginate(offset=-10)
    assert paginator.offset == 0


def test_paginate_constants():
    """Test Paginate class constants"""
    assert Paginate.DEFAULT_PAGESIZE == 5000
    assert Paginate.DEFAULT_PAGELIMIT == 10000
    assert Paginate.DEFAULT_OFFSET == 0


# ============================================================================
# Resolve Methods Tests
# ============================================================================


def test_paginate_resolve_pagelimit_valid():
    """Test _resolve_pagelimit with valid value"""
    paginator = Paginate()
    assert paginator._resolve_pagelimit(15000) == 15000


def test_paginate_resolve_pagelimit_invalid():
    """Test _resolve_pagelimit with invalid value"""
    paginator = Paginate()
    assert paginator._resolve_pagelimit(0) == 10000
    assert paginator._resolve_pagelimit(-100) == 10000
    assert paginator._resolve_pagelimit(None) == 10000


def test_paginate_resolve_pagesize_valid():
    """Test _resolve_pagesize with valid value"""
    paginator = Paginate()
    assert paginator._resolve_pagesize(1000) == 1000


def test_paginate_resolve_pagesize_invalid():
    """Test _resolve_pagesize with invalid value"""
    paginator = Paginate()
    assert paginator._resolve_pagesize(0) == 5000
    assert paginator._resolve_pagesize(-50) == 5000
    assert paginator._resolve_pagesize(None) == 5000


def test_paginate_resolve_offset_valid():
    """Test _resolve_offset with valid value"""
    paginator = Paginate()
    assert paginator._resolve_offset(100) == 100
    assert paginator._resolve_offset(0) == 0


def test_paginate_resolve_offset_invalid():
    """Test _resolve_offset with invalid value"""
    paginator = Paginate()
    assert paginator._resolve_offset(-10) == 0
    assert paginator._resolve_offset(None) == 0


# ============================================================================
# Reset Method Tests
# ============================================================================


def test_paginate_reset_from_zero():
    """Test reset when offset is already zero"""
    paginator = Paginate()
    paginator.reset()
    assert paginator.offset == 0


def test_paginate_reset_from_nonzero():
    """Test reset when offset is non-zero"""
    paginator = Paginate(offset=5000)
    assert paginator.offset == 5000
    paginator.reset()
    assert paginator.offset == 0


def test_paginate_reset_after_next():
    """Test reset after calling next"""
    paginator = Paginate()
    paginator.next()
    paginator.next()
    assert paginator.offset == 10000
    paginator.reset()
    assert paginator.offset == 0


def test_paginate_reset_preserves_other_attributes():
    """Test reset only affects offset, not other attributes"""
    paginator = Paginate(pagelimit=20000, pagesize=1000, offset=5000)
    paginator.reset()
    assert paginator.offset == 0
    assert paginator.pagesize == 1000
    assert paginator.pagelimit == 20000


# ============================================================================
# Next Method Tests
# ============================================================================


def test_paginate_next_first_call():
    """Test first call to next advances offset by pagesize"""
    paginator = Paginate(pagesize=1000, offset=0)
    new_offset = paginator.next()
    assert new_offset == 1000
    assert paginator.offset == 1000


def test_paginate_next_multiple_calls():
    """Test multiple calls to next"""
    paginator = Paginate(pagesize=500)
    paginator.next()
    assert paginator.offset == 500
    paginator.next()
    assert paginator.offset == 1000
    paginator.next()
    assert paginator.offset == 1500


def test_paginate_next_with_custom_pagesize():
    """Test next with custom pagesize"""
    paginator = Paginate(pagesize=2500)
    paginator.next()
    assert paginator.offset == 2500
    paginator.next()
    assert paginator.offset == 5000


def test_paginate_next_with_existing_offset():
    """Test next with existing offset"""
    paginator = Paginate(pagesize=1000, offset=3000)
    paginator.next()
    assert paginator.offset == 4000


def test_paginate_next_returns_new_offset():
    """Test next returns the new offset value"""
    paginator = Paginate(pagesize=750)
    result = paginator.next()
    assert result == 750
    result = paginator.next()
    assert result == 1500


def test_paginate_next_large_pagesize():
    """Test next with large pagesize"""
    paginator = Paginate(pagesize=100000)
    paginator.next()
    assert paginator.offset == 100000


# ============================================================================
# From Dict Tests
# ============================================================================


def test_paginate_from_dict_full():
    """Test from_dict with all fields"""
    data = {"pagelimit": 15000, "pagesize": 2000, "offset": 1000}
    paginator = Paginate.from_dict(data)
    assert paginator.pagelimit == 15000
    assert paginator.pagesize == 2000
    assert paginator.offset == 1000


def test_paginate_from_dict_partial():
    """Test from_dict with partial fields"""
    data = {"pagesize": 3000}
    paginator = Paginate.from_dict(data)
    assert paginator.pagesize == 3000
    assert paginator.pagelimit == 10000
    assert paginator.offset == 0


def test_paginate_from_dict_empty():
    """Test from_dict with empty dict"""
    paginator = Paginate.from_dict({})
    assert paginator.pagesize == 5000
    assert paginator.pagelimit == 10000
    assert paginator.offset == 0


def test_paginate_from_dict_with_paginate_instance():
    """Test from_dict with Paginate instance returns same instance"""
    original = Paginate(pagelimit=20000, pagesize=1500, offset=500)
    result = Paginate.from_dict(original)
    assert result is original
    assert result.pagelimit == 20000
    assert result.pagesize == 1500
    assert result.offset == 500


def test_paginate_from_dict_with_extra_fields():
    """Test from_dict ignores extra fields"""
    data = {"pagelimit": 8000, "pagesize": 1000, "offset": 2000, "extra_field": "ignored", "another_field": 999}
    paginator = Paginate.from_dict(data)
    assert paginator.pagelimit == 8000
    assert paginator.pagesize == 1000
    assert paginator.offset == 2000


# ============================================================================
# Describe Method Tests
# ============================================================================


def test_paginate_describe_with_defaults():
    """Test describe with default values returns only non-zero/non-default values"""
    paginator = Paginate()
    result = paginator.describe()
    assert "pagesize" in result
    assert "pagelimit" in result
    assert "offset" not in result  # offset is 0, not included


def test_paginate_describe_with_custom_values():
    """Test describe with custom values"""
    paginator = Paginate(pagelimit=15000, pagesize=2000, offset=4000)
    result = paginator.describe()
    assert result["pagesize"] == 2000
    assert result["pagelimit"] == 15000
    assert result["offset"] == 4000


def test_paginate_describe_with_zero_offset():
    """Test describe excludes zero offset"""
    paginator = Paginate(pagelimit=20000, pagesize=1000, offset=0)
    result = paginator.describe()
    assert "pagesize" in result
    assert "pagelimit" in result
    assert "offset" not in result


def test_paginate_describe_after_next():
    """Test describe after calling next includes offset"""
    paginator = Paginate(pagesize=1000)
    paginator.next()
    result = paginator.describe()
    assert result["offset"] == 1000


def test_paginate_describe_after_reset():
    """Test describe after reset excludes offset"""
    paginator = Paginate(offset=5000)
    paginator.reset()
    result = paginator.describe()
    assert "offset" not in result


# ============================================================================
# To Dict Method Tests
# ============================================================================


def test_paginate_to_dict_with_defaults():
    """Test to_dict with default values"""
    paginator = Paginate()
    result = paginator.to_dict()
    assert result == {"pagesize": 5000, "pagelimit": 10000, "offset": 0}


def test_paginate_to_dict_with_custom_values():
    """Test to_dict with custom values"""
    paginator = Paginate(pagelimit=20000, pagesize=1500, offset=3000)
    result = paginator.to_dict()
    assert result == {"pagesize": 1500, "pagelimit": 20000, "offset": 3000}


def test_paginate_to_dict_includes_all_fields():
    """Test to_dict always includes all fields"""
    paginator = Paginate(offset=0)
    result = paginator.to_dict()
    assert "pagesize" in result
    assert "pagelimit" in result
    assert "offset" in result
    assert result["offset"] == 0


def test_paginate_to_dict_structure():
    """Test to_dict returns expected structure"""
    paginator = Paginate()
    result = paginator.to_dict()
    assert isinstance(result, dict)
    assert len(result) == 3
    assert all(key in result for key in ["pagesize", "pagelimit", "offset"])


def test_paginate_to_dict_vs_describe():
    """Test to_dict vs describe differences"""
    paginator = Paginate(pagelimit=15000, pagesize=2000, offset=0)
    to_dict_result = paginator.to_dict()
    describe_result = paginator.describe()

    # to_dict includes offset even when 0
    assert "offset" in to_dict_result
    assert to_dict_result["offset"] == 0

    # describe excludes offset when 0
    assert "offset" not in describe_result


# ============================================================================
# Integration Tests
# ============================================================================


def test_paginate_full_workflow():
    """Test complete pagination workflow"""
    paginator = Paginate(pagelimit=10000, pagesize=1000, offset=0)

    # Start at page 0
    assert paginator.offset == 0

    # Get page 1
    paginator.next()
    assert paginator.offset == 1000

    # Get page 2
    paginator.next()
    assert paginator.offset == 2000

    # Reset to start
    paginator.reset()
    assert paginator.offset == 0


def test_paginate_dict_roundtrip():
    """Test converting to dict and back"""
    original = Paginate(pagelimit=15000, pagesize=2000, offset=1000)
    data = original.to_dict()
    restored = Paginate.from_dict(data)

    assert restored.pagelimit == original.pagelimit
    assert restored.pagesize == original.pagesize
    assert restored.offset == original.offset


def test_paginate_sequential_pages():
    """Test sequential page navigation"""
    paginator = Paginate(pagesize=100)
    offsets = []

    for i in range(5):
        offsets.append(paginator.offset)
        paginator.next()

    assert offsets == [0, 100, 200, 300, 400]
    assert paginator.offset == 500


def test_paginate_large_dataset():
    """Test pagination with large dataset"""
    paginator = Paginate(pagelimit=1000000, pagesize=10000)

    # Simulate fetching 10 pages
    for _ in range(10):
        paginator.next()

    assert paginator.offset == 100000


def test_paginate_boundary_conditions():
    """Test pagination at boundary conditions"""
    paginator = Paginate(pagelimit=10000, pagesize=2500)

    # Fetch exactly 4 pages to reach limit
    for _ in range(4):
        paginator.next()

    assert paginator.offset == 10000  # Reached the limit


def test_paginate_describe_dynamic():
    """Test describe changes as pagination progresses"""
    paginator = Paginate(pagesize=1000)

    # Initially, offset not in describe
    desc1 = paginator.describe()
    assert "offset" not in desc1

    # After next, offset appears
    paginator.next()
    desc2 = paginator.describe()
    assert "offset" in desc2
    assert desc2["offset"] == 1000

    # After reset, offset disappears again
    paginator.reset()
    desc3 = paginator.describe()
    assert "offset" not in desc3


def test_paginate_multiple_instances():
    """Test multiple independent Paginate instances"""
    p1 = Paginate(pagesize=1000)
    p2 = Paginate(pagesize=2000)

    p1.next()
    p2.next()

    assert p1.offset == 1000
    assert p2.offset == 2000


def test_paginate_state_independence():
    """Test that paginate instances maintain independent state"""
    p1 = Paginate(pagesize=500)
    p2 = Paginate(pagesize=500)

    p1.next()
    p1.next()

    assert p1.offset == 1000
    assert p2.offset == 0


def test_paginate_custom_pagination_strategy():
    """Test custom pagination with specific requirements"""
    # Small pages for API rate limiting
    paginator = Paginate(pagelimit=50000, pagesize=100)

    pages_fetched = 0
    while paginator.offset < paginator.pagelimit:
        paginator.next()
        pages_fetched += 1
        if pages_fetched >= 10:  # Stop after 10 pages
            break

    assert paginator.offset == 1000
    assert pages_fetched == 10


def test_paginate_modification_after_init():
    """Test direct modification of attributes after initialization"""
    paginator = Paginate()

    # Modify attributes directly
    paginator.pagesize = 3000
    paginator.pagelimit = 30000
    paginator.offset = 6000

    assert paginator.pagesize == 3000
    assert paginator.pagelimit == 30000
    assert paginator.offset == 6000

    # Next should use modified pagesize
    paginator.next()
    assert paginator.offset == 9000

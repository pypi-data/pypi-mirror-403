import pytest
from nestedutils import get_at
from nestedutils.exceptions import PathError, PathErrorCode


class TestGetBasic:
    """Basic get_at functionality tests."""
    
    def test_get_simple(self):
        """Get value from simple dict."""
        d = {"a": 1}
        assert get_at(d, "a") == 1
    
    def test_get_nested_dict(self):
        """Get value from deeply nested dict."""
        d = {"a": {"b": {"c": 5}}}
        assert get_at(d, "a.b.c") == 5
    
    def test_get_intermediate_nested_object(self):
        """Get intermediate path returns complete nested object."""
        data = {
            "user": {
                "profile": {
                    "email": "john@example.com",
                    "address": {"city": "SF", "zip": "94102"}
                }
            }
        }
        # Getting intermediate path should return complete nested structure
        profile = get_at(data, "user.profile")
        assert profile == {
            "email": "john@example.com",
            "address": {"city": "SF", "zip": "94102"}
        }
        # Can also get deeper values
        assert get_at(data, "user.profile.address.city") == "SF"
    
    def test_get_missing_returns_default(self):
        """Get missing key returns default value."""
        d = {"a": {"b": 1}}
        assert get_at(d, "a.c", default=99) == 99
        assert get_at(d, "x.y.z") is None
        assert get_at(d, "x.y.z", default="missing") == "missing"
    
    def test_get_list_index(self):
        """Get value from list using index."""
        d = {"a": [10, 20, 30]}
        assert get_at(d, "a.1") == 20
        assert get_at(d, "a.0") == 10
        assert get_at(d, "a.2") == 30
    
    def test_get_negative_list_index(self):
        """Get value using negative list index."""
        d = {"a": [10, 20, 30]}
        assert get_at(d, "a.-1") == 30
        assert get_at(d, "a.-2") == 20
        assert get_at(d, "a.-3") == 10
    
    def test_get_negative_index_nested_structure(self):
        """Get value using negative index in nested list-dict structure."""
        d = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert get_at(d, "items.-1.name") == "banana"
        assert get_at(d, "items.-2.name") == "apple"
        assert get_at(d, "items.-1") == {"name": "banana"}
    
    def test_get_negative_index_out_of_bounds(self):
        """Get with out-of-bounds negative index returns default."""
        d = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert get_at(d, "items.-5.name") is None
        assert get_at(d, "items.-5.name", default="not found") == "not found"
        assert get_at(d, "items.-10") is None
    
    def test_get_negative_index_deeply_nested(self):
        """Get with negative index in deeply nested structure."""
        d = {"data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        assert get_at(d, "data.-1.-1") == 9
        assert get_at(d, "data.-1.0") == 7
        assert get_at(d, "data.-2.-1") == 6
    
    def test_get_nested_list_dict_mix(self):
        """Get value from mixed nested list and dict."""
        d = {"a": [{"b": 1}, {"b": 2}]}
        assert get_at(d, "a.1.b") == 2
        assert get_at(d, "a.0.b") == 1
    
    def test_get_list_index_out_of_bounds(self):
        """Get from out-of-bounds list index returns default."""
        d = {"a": [10, 20]}
        assert get_at(d, "a.5") is None
        assert get_at(d, "a.5", default=-1) == -1
        assert get_at(d, "a.-10") is None
        # Test both positive and negative out-of-bounds
        assert get_at(d, "a.100") is None
        assert get_at(d, "a.-100") is None
        assert get_at(d, "a.-3") is None  # Just out of bounds for length 2
    
    def test_get_list_index_non_integer(self):
        """Get with non-integer key on list returns default."""
        d = {"a": [1]}
        assert get_at(d, "a.x") is None
        assert get_at(d, "a.x", default="not found") == "not found"


class TestGetPathNormalization:
    """Tests for path normalization (list form, unicode, etc.)."""
    
    def test_path_as_list_form(self):
        """Get using list form path."""
        d = {"a": {"b": {"c": 1}}}
        assert get_at(d, ["a", "b", "c"]) == 1
    
    def test_path_list_mixed_int(self):
        """Get using list form with integer keys."""
        d = {"a": [{"b": 3}]}
        assert get_at(d, ["a", 0, "b"]) == 3
    
    def test_path_list_with_negative_index(self):
        """Get using list form with negative index."""
        d = {"a": [10, 20, 30]}
        assert get_at(d, ["a", -1]) == 30
        assert get_at(d, ["a", -2]) == 20
        assert get_at(d, ["a", -3]) == 10
    
    def test_path_list_with_negative_index_nested(self):
        """Get using list form with negative index in nested structure."""
        d = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert get_at(d, ["items", -1, "name"]) == "banana"
        assert get_at(d, ["items", -2, "name"]) == "apple"
    
    def test_unicode_keys(self):
        """Get with unicode keys."""
        d = {}
        d["你好"] = {"world": {"🌍": 42}}
        assert get_at(d, "你好.world.🌍") == 42
        assert get_at(d, ["你好", "world", "🌍"]) == 42
    
    def test_keys_with_dots_in_list_form(self):
        """List form allows keys with dots."""
        d = {"a.b": {"c.d": 10}}
        assert get_at(d, ["a.b", "c.d"]) == 10
    
    def test_complex_keys_in_list_form(self):
        """List form handles any key type: special characters, dots, integers."""
        # Create data structure with complex keys
        data = {
            "user-info": {
                "first.name": {
                    123: "found it!"
                }
            }
        }
        
        # Verify each level works independently
        assert get_at(data, ["user-info"]) == {"first.name": {123: "found it!"}}
        assert get_at(data, ["user-info", "first.name"]) == {123: "found it!"}
        
        # String form cannot handle these keys (dots would be interpreted as separators)
        # But list form works perfectly
        assert get_at(data, ["user-info", "first.name", 123]) == "found it!"
        
        # Test with default for missing path
        assert get_at(data, ["user-info", "first.name", 999], default="not found") == "not found"


class TestGetEdgeCases:
    """Edge cases for get_at."""
    
    def test_get_empty_dict(self):
        """Get from empty dict."""
        d = {}
        assert get_at(d, "a") is None
        assert get_at(d, "a.b.c") is None
    
    def test_get_empty_list(self):
        """Get from empty list."""
        d = {"a": []}
        assert get_at(d, "a.0") is None
    
    def test_get_none_value(self):
        """Get None value explicitly stored."""
        d = {"a": None}
        assert get_at(d, "a") is None
    
    def test_none_blocks_navigation(self):
        """None as intermediate value should block navigation and return default."""
        # None at first level blocks further navigation
        d = {"a": None}
        assert get_at(d, "a.b") is None
        assert get_at(d, "a.b", default="missing") == "missing"
        assert get_at(d, "a.b.c") is None
        assert get_at(d, "a.b.c", default=99) == 99
        
        # None at deeper level also blocks navigation
        d2 = {"a": {"b": None}}
        assert get_at(d2, "a.b.c") is None
        assert get_at(d2, "a.b.c", default="not found") == "not found"
        assert get_at(d2, "a.b.c.d.e") is None
        
        # None in list should also block navigation
        d3 = {"items": [None, {"name": "apple"}]}
        assert get_at(d3, "items.0.name") is None
        assert get_at(d3, "items.0.name", default="no name") == "no name"
        
        # None in nested structure
        d4 = {"data": {"user": None, "other": {"value": 42}}}
        assert get_at(d4, "data.user.name") is None
        assert get_at(d4, "data.user.name", default="default") == "default"
        # But other paths should still work
        assert get_at(d4, "data.other.value") == 42
    
    def test_get_false_value(self):
        """Get False value (should not be confused with missing)."""
        d = {"a": False}
        assert get_at(d, "a") is False
        assert get_at(d, "a", default=True) is False  # Should return False, not default
    
    def test_get_zero_value(self):
        """Get zero value (should not be confused with missing)."""
        d = {"a": 0}
        assert get_at(d, "a") == 0
    
    def test_get_empty_string_value(self):
        """Get empty string value."""
        d = {"a": ""}
        assert get_at(d, "a") == ""
    
    def test_get_very_deep_nesting(self):
        """Get from very deeply nested structure."""
        d = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 42}}}}}}}
        assert get_at(d, "a.b.c.d.e.f.g") == 42
    
    def test_get_from_dict_with_numeric_keys(self):
        """Get from dict with numeric string keys."""
        d = {"0": {"1": {"2": 5}}}
        assert get_at(d, "0.1.2") == 5
    
    def test_get_dict_with_integer_vs_string_keys(self):
        """Test that integer and string keys are correctly distinguished.
        
        The library correctly preserves key types in list form paths, allowing
        access to both integer keys and string keys with the same numeric value.
        """
        # Dictionary with both integer key and string key
        data = {0: "int_value", "0": "string_value"}
        
        # Using integer in path accesses integer key
        assert get_at(data, [0]) == "int_value"
        
        # Using string in path accesses string key
        assert get_at(data, ["0"]) == "string_value"
        
        # Verify direct access matches
        assert data[0] == "int_value"
        assert data["0"] == "string_value"
        
        # Both keys are distinct and accessible
        assert get_at(data, [0]) != get_at(data, ["0"])
    
    def test_get_mixed_types(self):
        """Get from structure with mixed types."""
        d = {
            "a": [1, "two", {"three": 3}],
            "b": {"list": [10, 20], "dict": {"nested": "value"}}
        }
        assert get_at(d, "a.0") == 1
        assert get_at(d, "a.1") == "two"
        assert get_at(d, "a.2.three") == 3
        assert get_at(d, "b.list.1") == 20
        assert get_at(d, "b.dict.nested") == "value"


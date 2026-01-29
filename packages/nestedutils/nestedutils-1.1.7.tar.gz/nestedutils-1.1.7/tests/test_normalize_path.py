"""Tests for normalize_path helper function."""

import pytest
from nestedutils.helpers import normalize_path
from nestedutils.exceptions import PathError
from nestedutils.enums import PathErrorCode


class TestNormalizePathValid:
    """Test valid path normalization."""
    
    @pytest.mark.parametrize("path,expected", [
        # String paths
        ("a", ["a"]),
        ("a.b", ["a", "b"]),
        ("a.b.c", ["a", "b", "c"]),
        ("user.profile.name", ["user", "profile", "name"]),
        ("items.0.name", ["items", "0", "name"]),
        ("data.-1", ["data", "-1"]),
        
        # List paths - simple
        (["a"], ["a"]),
        (["a", "b"], ["a", "b"]),
        (["a", "b", "c"], ["a", "b", "c"]),
        
        # List paths - mixed types (converted to strings)
        (["user", 0, "name"], ["user", 0, "name"]),
        ([0, 1, 2], [0, 1, 2]),
        (["items", -1], ["items", -1]),
    ])
    def test_valid_paths(self, path, expected):
        """Test that valid paths are normalized correctly."""
        assert normalize_path(path) == expected


class TestNormalizePathInvalid:
    """Test invalid path handling."""
    
    @pytest.mark.parametrize("path,error_code", [
        # Empty paths
        ("", PathErrorCode.EMPTY_PATH),
        ([], PathErrorCode.EMPTY_PATH),
        
        # Empty keys in string paths
        (".a", PathErrorCode.EMPTY_PATH),          # Leading dot
        ("a.", PathErrorCode.EMPTY_PATH),          # Trailing dot
        ("a..b", PathErrorCode.EMPTY_PATH),        # Double dot
        (".a.b", PathErrorCode.EMPTY_PATH),        # Leading dot
        ("a.b.", PathErrorCode.EMPTY_PATH),        # Trailing dot
        ("..", PathErrorCode.EMPTY_PATH),          # Just dots
        ("...", PathErrorCode.EMPTY_PATH),         # Multiple dots
        
        # Empty keys in list paths
        ([""], PathErrorCode.EMPTY_PATH),
        (["a", ""], PathErrorCode.EMPTY_PATH),
        (["", "a"], PathErrorCode.EMPTY_PATH),
        (["a", "", "b"], PathErrorCode.EMPTY_PATH),
    ])
    def test_invalid_paths_raise_error(self, path, error_code):
        """Test that invalid paths raise PathError with correct code."""
        with pytest.raises(PathError) as exc_info:
            normalize_path(path)
        assert exc_info.value.code == error_code
    
    @pytest.mark.parametrize("path", [
        123,           # Integer
        12.34,         # Float
        None,          # None
        {"a": 1},      # Dict
        True,          # Boolean
    ])
    def test_invalid_types(self, path):
        """Test that invalid path types raise PathError."""
        with pytest.raises(PathError) as exc_info:
            normalize_path(path)
        assert exc_info.value.code == PathErrorCode.INVALID_PATH


class TestNormalizePathDepth:
    """Test path depth validation."""
    
    def test_max_depth_string(self):
        """Test that paths exceeding max depth raise error."""
        # Create a path with 101 keys (MAX_DEPTH is 100)
        deep_path = ".".join(str(i) for i in range(101))
        with pytest.raises(PathError) as exc_info:
            normalize_path(deep_path)
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_max_depth_list(self):
        """Test that list paths exceeding max depth raise error."""
        deep_path = [str(i) for i in range(101)]
        with pytest.raises(PathError) as exc_info:
            normalize_path(deep_path)
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_exactly_max_depth(self):
        """Test that paths at exactly max depth are valid."""
        # Create a path with exactly 100 keys
        path = ".".join(str(i) for i in range(100))
        result = normalize_path(path)
        assert len(result) == 100

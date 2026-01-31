"""
Tests for Nexus error handling and Result type.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_core.errors import (
    NexusError, ErrorCode, Result,
    MemoryError, JSONError, AuthError
)


class TestErrorCodes:
    def test_error_codes_exist(self):
        assert ErrorCode.SUCCESS == 0
        assert ErrorCode.MEMORY_NOT_FOUND == 1001
        assert ErrorCode.JSON_PARSE_ERROR == 2001
        assert ErrorCode.AUTH_FAILED == 3001


class TestNexusError:
    def test_error_creation(self):
        error = NexusError(1001, "Test error", {"file": "test.txt"})
        assert error.code == 1001
        assert error.message == "Test error"
        assert error.details["file"] == "test.txt"
    
    def test_error_to_dict(self):
        error = NexusError(1001, "Test error")
        d = error.to_dict()
        assert d["error"] == True
        assert d["code"] == 1001
        assert d["message"] == "Test error"
    
    def test_specific_errors(self):
        mem_err = MemoryError(ErrorCode.MEMORY_FULL, "Out of space")
        assert mem_err.code == ErrorCode.MEMORY_FULL
        
        json_err = JSONError(ErrorCode.JSON_PARSE_ERROR, "Bad JSON")
        assert json_err.code == ErrorCode.JSON_PARSE_ERROR


class TestResult:
    def test_ok_result(self):
        result = Result.ok(42)
        assert result.is_ok()
        assert not result.is_err()
        assert result.unwrap() == 42
    
    def test_err_result(self):
        error = NexusError(1001, "Failed")
        result = Result.err(error)
        assert result.is_err()
        assert not result.is_ok()
        
        with pytest.raises(NexusError):
            result.unwrap()
    
    def test_unwrap_or(self):
        ok_result = Result.ok(42)
        assert ok_result.unwrap_or(0) == 42
        
        err_result = Result.err(NexusError(1001, "Failed"))
        assert err_result.unwrap_or(0) == 0
    
    def test_map(self):
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_ok()
        assert mapped.unwrap() == 10
    
    def test_map_on_error(self):
        result = Result.err(NexusError(1001, "Failed"))
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

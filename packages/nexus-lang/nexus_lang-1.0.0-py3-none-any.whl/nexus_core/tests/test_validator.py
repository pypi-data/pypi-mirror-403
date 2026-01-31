"""
Tests for Nexus validator module.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_core.validator import SchemaValidator, InputSanitizer, RateLimiter


class TestSchemaValidator:
    def test_validate_simple_schema(self):
        schema = {"name": "", "age": 0, "active": True}
        validator = SchemaValidator(schema)
        
        result = validator.validate({"name": "Test", "age": 25, "active": False})
        assert result.is_ok()
    
    def test_validate_nested_schema(self):
        schema = {
            "user": {"name": "", "email": ""},
            "settings": {"theme": ""}
        }
        validator = SchemaValidator(schema)
        
        result = validator.validate({
            "user": {"name": "John", "email": "john@test.com"},
            "settings": {"theme": "dark"}
        })
        assert result.is_ok()
    
    def test_validate_type_mismatch(self):
        schema = {"count": 0}
        validator = SchemaValidator(schema)
        
        result = validator.validate({"count": "not a number"})
        assert result.is_err()


class TestInputSanitizer:
    def test_sanitize_string(self):
        unsafe = "<script>alert('xss')</script>"
        safe = InputSanitizer.sanitize_string(unsafe)
        assert "<script>" not in safe
        assert "&lt;script&gt;" in safe
    
    def test_is_safe(self):
        assert InputSanitizer.is_safe("Hello World")
        assert not InputSanitizer.is_safe("<script>bad</script>")
        assert not InputSanitizer.is_safe("onclick=evil()")
    
    def test_sanitize_json(self):
        data = {
            "name": "<b>Test</b>",
            "items": ["<script>bad</script>"]
        }
        safe = InputSanitizer.sanitize_json(data)
        assert "&lt;b&gt;" in safe["name"]
        assert "&lt;script&gt;" in safe["items"][0]


class TestRateLimiter:
    def test_allow_requests(self):
        limiter = RateLimiter(rate=10, per_seconds=1)
        
        for _ in range(10):
            assert limiter.is_allowed("user1")
    
    def test_block_excess_requests(self):
        limiter = RateLimiter(rate=5, per_seconds=1)
        
        for _ in range(5):
            limiter.is_allowed("user2")
        
        assert not limiter.is_allowed("user2")
    
    def test_different_keys(self):
        limiter = RateLimiter(rate=5, per_seconds=1)
        
        for _ in range(5):
            limiter.is_allowed("user3")
        
        # Different key should still be allowed
        assert limiter.is_allowed("user4")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

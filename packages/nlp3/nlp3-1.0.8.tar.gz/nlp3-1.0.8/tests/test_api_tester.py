"""
Tests for Data API Tester
"""

import pytest
import asyncio
from src.api_tester import (
    APITester,
    APIType,
    ValidationStatus,
    APIEndpoint,
    ValidationRule,
    ResponseValidator,
    RESTAdapter,
)


class TestResponseValidator:
    """Tests for ResponseValidator"""

    def test_validate_simple_path(self):
        validator = ResponseValidator()
        data = {"name": "John", "age": 30}
        rules = [
            ValidationRule(name="name_check", path="$.name", expected="John"),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "passed"

    def test_validate_nested_path(self):
        validator = ResponseValidator()
        data = {"user": {"profile": {"city": "Warsaw"}}}
        rules = [
            ValidationRule(name="city_check", path="$.user.profile.city", expected="Warsaw"),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "passed"

    def test_validate_array_index(self):
        validator = ResponseValidator()
        data = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
        rules = [
            ValidationRule(name="second_item", path="$.items[1].id", expected=2),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "passed"

    def test_validate_type_check(self):
        validator = ResponseValidator()
        data = {"count": 42, "name": "test"}
        rules = [
            ValidationRule(name="count_is_int", path="$.count", type_check="integer"),
            ValidationRule(name="name_is_string", path="$.name", type_check="string"),
        ]
        results = validator.validate(data, rules)
        assert all(r["status"] == "passed" for r in results)

    def test_validate_type_mismatch(self):
        validator = ResponseValidator()
        data = {"count": "not a number"}
        rules = [
            ValidationRule(name="count_is_int", path="$.count", type_check="integer"),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "failed"

    def test_validate_required_missing(self):
        validator = ResponseValidator()
        data = {"name": "John"}
        rules = [
            ValidationRule(name="email_required", path="$.email", required=True),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "failed"

    def test_validate_optional_missing(self):
        validator = ResponseValidator()
        data = {"name": "John"}
        rules = [
            ValidationRule(name="email_optional", path="$.email", required=False),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "skipped"

    def test_validate_pattern(self):
        validator = ResponseValidator()
        data = {"email": "test@example.com"}
        rules = [
            ValidationRule(
                name="email_format",
                path="$.email",
                pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"
            ),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "passed"

    def test_validate_min_length(self):
        validator = ResponseValidator()
        data = {"items": [1, 2, 3]}
        rules = [
            ValidationRule(name="min_items", path="$.items", min_length=2),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "passed"

    def test_validate_max_length(self):
        validator = ResponseValidator()
        data = {"name": "John"}
        rules = [
            ValidationRule(name="name_length", path="$.name", max_length=10),
        ]
        results = validator.validate(data, rules)
        assert results[0]["status"] == "passed"


class TestAPIEndpoint:
    """Tests for APIEndpoint model"""

    def test_endpoint_defaults(self):
        endpoint = APIEndpoint(name="test", url="/api/test")
        assert endpoint.method.value == "GET"
        assert endpoint.timeout == 30.0
        assert endpoint.expected_status == 200

    def test_endpoint_with_validations(self):
        endpoint = APIEndpoint(
            name="test",
            url="/api/users",
            validations=[
                ValidationRule(name="check", path="$.data", type_check="array")
            ]
        )
        assert len(endpoint.validations) == 1


class TestAPITester:
    """Tests for main APITester class"""

    def test_register_adapter(self):
        tester = APITester()
        adapter = RESTAdapter("http://localhost:3000")
        tester.register_adapter(APIType.REST, adapter)
        assert APIType.REST in tester.adapters

    def test_add_endpoint(self):
        tester = APITester()
        endpoint = APIEndpoint(name="test", url="/test")
        tester.add_endpoint(endpoint, APIType.REST)
        assert len(tester.endpoints) == 1


class TestValidationStatus:
    """Tests for ValidationStatus enum"""

    def test_status_values(self):
        assert ValidationStatus.PASSED.value == "passed"
        assert ValidationStatus.FAILED.value == "failed"
        assert ValidationStatus.ERROR.value == "error"
        assert ValidationStatus.SKIPPED.value == "skipped"


# =============================================================================
# Integration Tests (require running services)
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_adapter_real():
    """Integration test for REST adapter (requires running service)"""
    adapter = RESTAdapter("http://localhost:3000")
    endpoint = APIEndpoint(
        name="Health Check",
        url="/health",
        expected_status=200,
    )
    result = await adapter.execute(endpoint)
    assert result.status == ValidationStatus.PASSED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_test_suite():
    """Integration test for full test suite"""
    from pathlib import Path
    
    tester = APITester(Path("config/test-config.yaml"))
    result = await tester.run_tests(tags=["smoke"])
    assert result.total_tests > 0

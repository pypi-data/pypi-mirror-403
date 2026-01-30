"""
Tests for Validators Module
"""

import pytest
from src.validators import (
    CustomValidators,
    CompositeValidator,
    create_composite_validator,
)


class TestCustomValidators:
    """Tests for CustomValidators"""

    def test_is_email_valid(self):
        is_valid, msg = CustomValidators.is_email("test@example.com")
        assert is_valid is True

    def test_is_email_invalid(self):
        is_valid, msg = CustomValidators.is_email("invalid-email")
        assert is_valid is False

    def test_is_email_not_string(self):
        is_valid, msg = CustomValidators.is_email(123)
        assert is_valid is False

    def test_is_url_valid(self):
        is_valid, msg = CustomValidators.is_url("https://example.com/path")
        assert is_valid is True

    def test_is_url_invalid(self):
        is_valid, msg = CustomValidators.is_url("not-a-url")
        assert is_valid is False

    def test_is_uuid_valid(self):
        is_valid, msg = CustomValidators.is_uuid("550e8400-e29b-41d4-a716-446655440000")
        assert is_valid is True

    def test_is_uuid_invalid(self):
        is_valid, msg = CustomValidators.is_uuid("not-a-uuid")
        assert is_valid is False

    def test_is_iso_datetime_valid(self):
        is_valid, msg = CustomValidators.is_iso_datetime("2026-01-25T10:30:00Z")
        assert is_valid is True

    def test_is_iso_datetime_invalid(self):
        is_valid, msg = CustomValidators.is_iso_datetime("25-01-2026")
        assert is_valid is False

    def test_is_phone_valid(self):
        is_valid, msg = CustomValidators.is_phone("+48 123 456 789")
        assert is_valid is True

    def test_is_phone_invalid(self):
        is_valid, msg = CustomValidators.is_phone("123")
        assert is_valid is False

    def test_is_positive_valid(self):
        is_valid, msg = CustomValidators.is_positive(42)
        assert is_valid is True

    def test_is_positive_invalid(self):
        is_valid, msg = CustomValidators.is_positive(-1)
        assert is_valid is False

    def test_is_positive_zero(self):
        is_valid, msg = CustomValidators.is_positive(0)
        assert is_valid is False

    def test_is_non_negative_valid(self):
        is_valid, msg = CustomValidators.is_non_negative(0)
        assert is_valid is True

    def test_is_in_range(self):
        validator = CustomValidators.is_in_range(1, 10)
        
        is_valid, msg = validator(5)
        assert is_valid is True
        
        is_valid, msg = validator(15)
        assert is_valid is False

    def test_is_one_of(self):
        validator = CustomValidators.is_one_of(["a", "b", "c"])
        
        is_valid, msg = validator("b")
        assert is_valid is True
        
        is_valid, msg = validator("d")
        assert is_valid is False

    def test_matches_pattern(self):
        validator = CustomValidators.matches_pattern(r"^[A-Z]{3}-\d{4}$")
        
        is_valid, msg = validator("ABC-1234")
        assert is_valid is True
        
        is_valid, msg = validator("abc-1234")
        assert is_valid is False

    def test_has_length(self):
        validator = CustomValidators.has_length(min_len=2, max_len=5)
        
        is_valid, msg = validator("abc")
        assert is_valid is True
        
        is_valid, msg = validator("a")
        assert is_valid is False
        
        is_valid, msg = validator("abcdef")
        assert is_valid is False


class TestCompositeValidator:
    """Tests for CompositeValidator"""

    def test_create_with_defaults(self):
        validator = create_composite_validator()
        assert "email" in validator.validators
        assert "url" in validator.validators
        assert "uuid" in validator.validators

    def test_validate_known_validator(self):
        validator = CompositeValidator()
        is_valid, msg = validator.validate("test@example.com", "email")
        assert is_valid is True

    def test_validate_unknown_validator(self):
        validator = CompositeValidator()
        is_valid, msg = validator.validate("value", "nonexistent")
        assert is_valid is False
        assert "Unknown validator" in msg

    def test_register_custom(self):
        validator = CompositeValidator()
        
        def custom_validator(value):
            return value == "special", "Must be special"
        
        validator.register("special", custom_validator)
        
        is_valid, msg = validator.validate("special", "special")
        assert is_valid is True
        
        is_valid, msg = validator.validate("other", "special")
        assert is_valid is False

    def test_validate_all_pass(self):
        validator = CompositeValidator()
        validator.register("positive", CustomValidators.is_positive)
        validator.register("range", CustomValidators.is_in_range(1, 100))
        
        is_valid, errors = validator.validate_all(50, ["positive", "range"])
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_all_fail(self):
        validator = CompositeValidator()
        validator.register("positive", CustomValidators.is_positive)
        validator.register("range", CustomValidators.is_in_range(1, 10))
        
        is_valid, errors = validator.validate_all(50, ["positive", "range"])
        assert is_valid is False
        assert len(errors) == 1  # range fails

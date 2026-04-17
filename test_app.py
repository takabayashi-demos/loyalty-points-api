"""Tests for loyalty-points-api validation helpers."""
import pytest
from app import validate_name, validate_value, NAME_MAX_LENGTH, VALUE_MAX


class TestValidateName:
    def test_valid_name(self):
        name, error = validate_name("Premium Rewards")
        assert name == "Premium Rewards"
        assert error is None

    def test_name_with_whitespace(self):
        name, error = validate_name("  Gold Member  ")
        assert name == "Gold Member"
        assert error is None

    def test_missing_name(self):
        name, error = validate_name(None)
        assert name is None
        assert error == "name is required and must be a string"

    def test_blank_name(self):
        name, error = validate_name("   ")
        assert name is None
        assert error == "name must not be blank"

    def test_name_too_long(self):
        long_name = "x" * (NAME_MAX_LENGTH + 1)
        name, error = validate_name(long_name)
        assert name is None
        assert error == f"name must be {NAME_MAX_LENGTH} characters or fewer"


class TestValidateValue:
    def test_valid_integer(self):
        value, error = validate_value(100)
        assert value == 100
        assert error is None

    def test_valid_float(self):
        value, error = validate_value(99.99)
        assert value == 99.99
        assert error is None

    def test_missing_value(self):
        value, error = validate_value(None)
        assert value is None
        assert error == "value is required"

    def test_zero_value(self):
        value, error = validate_value(0)
        assert value is None
        assert error == "value must be a positive number"

    def test_negative_value(self):
        value, error = validate_value(-10)
        assert value is None
        assert error == "value must be a positive number"

    def test_value_exceeds_max(self):
        value, error = validate_value(VALUE_MAX + 1)
        assert value is None
        assert error == f"value must not exceed {VALUE_MAX}"

    def test_boolean_rejected(self):
        value, error = validate_value(True)
        assert value is None
        assert error == "value must be a number"

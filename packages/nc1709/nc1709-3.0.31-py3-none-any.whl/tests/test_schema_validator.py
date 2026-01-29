"""
NC1709 Schema Validator Tests

Tests for the JSON Schema validation implementation.
"""

import pytest
from nc1709.utils.schema_validator import (
    JSONSchemaValidator,
    ValidationResult,
    ValidationError,
    validate_tool_parameters,
    create_parameter_schema,
)


class TestTypeValidation:
    """Test type validation"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator(coerce_types=True)

    def test_string_type(self, validator):
        """String type validation"""
        schema = {"type": "string"}

        result = validator.validate("hello", schema)
        assert result.is_valid

        result = validator.validate(123, schema)
        assert result.is_valid  # Coerced to "123"
        assert result.coerced_value == "123"

    def test_integer_type(self, validator):
        """Integer type validation"""
        schema = {"type": "integer"}

        result = validator.validate(42, schema)
        assert result.is_valid

        result = validator.validate("42", schema)
        assert result.is_valid  # Coerced
        assert result.coerced_value == 42

        result = validator.validate("not a number", schema)
        assert not result.is_valid

    def test_number_type(self, validator):
        """Number type validation"""
        schema = {"type": "number"}

        result = validator.validate(3.14, schema)
        assert result.is_valid

        result = validator.validate(42, schema)  # int is also number
        assert result.is_valid

        result = validator.validate("3.14", schema)
        assert result.is_valid
        assert result.coerced_value == 3.14

    def test_boolean_type(self, validator):
        """Boolean type validation"""
        schema = {"type": "boolean"}

        result = validator.validate(True, schema)
        assert result.is_valid

        result = validator.validate("true", schema)
        assert result.is_valid
        assert result.coerced_value is True

        result = validator.validate("false", schema)
        assert result.is_valid
        assert result.coerced_value is False

    def test_array_type(self, validator):
        """Array type validation"""
        schema = {"type": "array"}

        result = validator.validate([1, 2, 3], schema)
        assert result.is_valid

        result = validator.validate("not array", schema)
        assert not result.is_valid

    def test_object_type(self, validator):
        """Object type validation"""
        schema = {"type": "object"}

        result = validator.validate({"key": "value"}, schema)
        assert result.is_valid

        result = validator.validate("not object", schema)
        assert not result.is_valid

    def test_null_type(self, validator):
        """Null type validation"""
        schema = {"type": "null"}

        result = validator.validate(None, schema)
        assert result.is_valid

        result = validator.validate("not null", schema)
        assert not result.is_valid

    def test_union_type(self, validator):
        """Union type validation"""
        schema = {"type": ["string", "integer"]}

        result = validator.validate("hello", schema)
        assert result.is_valid

        result = validator.validate(42, schema)
        assert result.is_valid

        result = validator.validate([], schema)
        assert not result.is_valid


class TestStringConstraints:
    """Test string validation constraints"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator()

    def test_min_length(self, validator):
        """minLength constraint"""
        schema = {"type": "string", "minLength": 3}

        result = validator.validate("hello", schema)
        assert result.is_valid

        result = validator.validate("hi", schema)
        assert not result.is_valid

    def test_max_length(self, validator):
        """maxLength constraint"""
        schema = {"type": "string", "maxLength": 5}

        result = validator.validate("hello", schema)
        assert result.is_valid

        result = validator.validate("hello world", schema)
        assert not result.is_valid

    def test_pattern(self, validator):
        """pattern constraint"""
        schema = {"type": "string", "pattern": r"^\d{3}-\d{4}$"}

        result = validator.validate("123-4567", schema)
        assert result.is_valid

        result = validator.validate("invalid", schema)
        assert not result.is_valid

    def test_format_email(self, validator):
        """Email format validation"""
        schema = {"type": "string", "format": "email"}

        result = validator.validate("test@example.com", schema)
        assert result.is_valid

        result = validator.validate("not-an-email", schema)
        assert not result.is_valid

    def test_format_uri(self, validator):
        """URI format validation"""
        schema = {"type": "string", "format": "uri"}

        result = validator.validate("https://example.com", schema)
        assert result.is_valid

        result = validator.validate("not-a-uri", schema)
        assert not result.is_valid


class TestNumberConstraints:
    """Test numeric validation constraints"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator()

    def test_minimum(self, validator):
        """minimum constraint"""
        schema = {"type": "number", "minimum": 0}

        result = validator.validate(5, schema)
        assert result.is_valid

        result = validator.validate(-1, schema)
        assert not result.is_valid

    def test_maximum(self, validator):
        """maximum constraint"""
        schema = {"type": "number", "maximum": 100}

        result = validator.validate(50, schema)
        assert result.is_valid

        result = validator.validate(150, schema)
        assert not result.is_valid

    def test_exclusive_minimum(self, validator):
        """exclusiveMinimum constraint"""
        schema = {"type": "number", "exclusiveMinimum": 0}

        result = validator.validate(1, schema)
        assert result.is_valid

        result = validator.validate(0, schema)
        assert not result.is_valid

    def test_exclusive_maximum(self, validator):
        """exclusiveMaximum constraint"""
        schema = {"type": "number", "exclusiveMaximum": 100}

        result = validator.validate(99, schema)
        assert result.is_valid

        result = validator.validate(100, schema)
        assert not result.is_valid

    def test_multiple_of(self, validator):
        """multipleOf constraint"""
        schema = {"type": "integer", "multipleOf": 5}

        result = validator.validate(15, schema)
        assert result.is_valid

        result = validator.validate(17, schema)
        assert not result.is_valid


class TestArrayConstraints:
    """Test array validation constraints"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator()

    def test_min_items(self, validator):
        """minItems constraint"""
        schema = {"type": "array", "minItems": 2}

        result = validator.validate([1, 2, 3], schema)
        assert result.is_valid

        result = validator.validate([1], schema)
        assert not result.is_valid

    def test_max_items(self, validator):
        """maxItems constraint"""
        schema = {"type": "array", "maxItems": 3}

        result = validator.validate([1, 2], schema)
        assert result.is_valid

        result = validator.validate([1, 2, 3, 4], schema)
        assert not result.is_valid

    def test_unique_items(self, validator):
        """uniqueItems constraint"""
        schema = {"type": "array", "uniqueItems": True}

        result = validator.validate([1, 2, 3], schema)
        assert result.is_valid

        result = validator.validate([1, 2, 2], schema)
        assert not result.is_valid

    def test_items_schema(self, validator):
        """items schema validation"""
        schema = {
            "type": "array",
            "items": {"type": "integer", "minimum": 0}
        }

        result = validator.validate([1, 2, 3], schema)
        assert result.is_valid

        result = validator.validate([1, -1, 3], schema)
        assert not result.is_valid


class TestObjectConstraints:
    """Test object validation constraints"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator()

    def test_required_properties(self, validator):
        """required properties validation"""
        schema = {
            "type": "object",
            "required": ["name", "age"]
        }

        result = validator.validate({"name": "John", "age": 30}, schema)
        assert result.is_valid

        result = validator.validate({"name": "John"}, schema)
        assert not result.is_valid

    def test_properties_schema(self, validator):
        """properties schema validation"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            }
        }

        result = validator.validate({"name": "John", "age": 30}, schema)
        assert result.is_valid

        result = validator.validate({"name": "John", "age": -1}, schema)
        assert not result.is_valid

    def test_additional_properties_false(self, validator):
        """additionalProperties=false validation"""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False
        }

        result = validator.validate({"name": "John"}, schema)
        assert result.is_valid

        result = validator.validate({"name": "John", "extra": "value"}, schema)
        assert not result.is_valid

    def test_additional_properties_schema(self, validator):
        """additionalProperties with schema validation"""
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "additionalProperties": {"type": "string"}
        }

        result = validator.validate({"id": 1, "name": "John"}, schema)
        assert result.is_valid

        result = validator.validate({"id": 1, "count": 42}, schema)
        assert not result.is_valid


class TestEnumAndConst:
    """Test enum and const validation"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator()

    def test_enum(self, validator):
        """enum validation"""
        schema = {"enum": ["red", "green", "blue"]}

        result = validator.validate("red", schema)
        assert result.is_valid

        result = validator.validate("yellow", schema)
        assert not result.is_valid

    def test_const(self, validator):
        """const validation"""
        schema = {"const": "fixed_value"}

        result = validator.validate("fixed_value", schema)
        assert result.is_valid

        result = validator.validate("other_value", schema)
        assert not result.is_valid


class TestNullHandling:
    """Test null/None handling"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator()

    def test_null_not_allowed_by_default(self, validator):
        """Null fails for non-null types"""
        schema = {"type": "string"}

        result = validator.validate(None, schema)
        assert not result.is_valid

    def test_nullable_allows_null(self, validator):
        """nullable=true allows null"""
        schema = {"type": "string", "nullable": True}

        result = validator.validate(None, schema)
        assert result.is_valid


class TestTypeCoercion:
    """Test type coercion behavior"""

    def test_coercion_enabled(self):
        """Coercion converts types"""
        validator = JSONSchemaValidator(coerce_types=True)
        schema = {"type": "integer"}

        result = validator.validate("42", schema)
        assert result.is_valid
        assert result.coerced_value == 42

    def test_coercion_disabled(self):
        """Coercion disabled rejects mismatched types"""
        validator = JSONSchemaValidator(coerce_types=False)
        schema = {"type": "integer"}

        result = validator.validate("42", schema)
        assert not result.is_valid


class TestValidationResult:
    """Test ValidationResult functionality"""

    def test_error_messages(self):
        """error_messages returns formatted messages"""
        result = ValidationResult(
            is_valid=False,
            errors=[
                ValidationError("name", "Required field", expected="string"),
                ValidationError("age", "Must be positive", value=-1),
            ]
        )

        messages = result.error_messages()
        assert len(messages) == 2
        assert "name:" in messages[0]
        assert "age:" in messages[1]


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_validate_tool_parameters(self):
        """validate_tool_parameters works correctly"""
        schema = {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["file_path"]
        }

        result = validate_tool_parameters(
            {"file_path": "/tmp/test.txt", "limit": "100"},
            schema
        )

        assert result.is_valid
        assert result.coerced_value["limit"] == 100

    def test_create_parameter_schema(self):
        """create_parameter_schema creates valid schema"""
        schema = create_parameter_schema(
            name="count",
            param_type="integer",
            description="Number of items",
            minimum=0,
            maximum=100
        )

        assert schema["type"] == "integer"
        assert schema["description"] == "Number of items"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 100


class TestNestedValidation:
    """Test nested structure validation"""

    @pytest.fixture
    def validator(self):
        return JSONSchemaValidator()

    def test_nested_objects(self, validator):
        """Nested object validation"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["name"]
                }
            }
        }

        result = validator.validate({
            "user": {
                "name": "John",
                "email": "john@example.com"
            }
        }, schema)
        assert result.is_valid

        result = validator.validate({
            "user": {
                "email": "john@example.com"  # Missing name
            }
        }, schema)
        assert not result.is_valid

    def test_nested_arrays(self, validator):
        """Nested array validation"""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"}
                },
                "required": ["id"]
            }
        }

        result = validator.validate([
            {"id": 1},
            {"id": 2}
        ], schema)
        assert result.is_valid

        result = validator.validate([
            {"id": 1},
            {"name": "no id"}  # Missing required id
        ], schema)
        assert not result.is_valid

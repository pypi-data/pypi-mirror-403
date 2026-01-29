"""
NC1709 JSON Schema Validator

Provides JSON Schema validation for tool parameters and API requests.
Ensures type safety and data integrity at runtime.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error"""
    path: str           # JSON path to the error (e.g., "parameters.file_path")
    message: str        # Human-readable error message
    value: Any = None   # The invalid value
    expected: str = ""  # Expected type/format


@dataclass
class ValidationResult:
    """Result of schema validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    coerced_value: Any = None  # Value after type coercion (if applicable)

    def error_messages(self) -> List[str]:
        """Get list of error messages"""
        return [f"{e.path}: {e.message}" for e in self.errors]


class JSONSchemaValidator:
    """
    Validates data against JSON Schema.

    Supports JSON Schema draft-07 compatible schemas with the following features:
    - Type validation (string, integer, number, boolean, array, object, null)
    - Required properties
    - Enum values
    - String patterns (regex)
    - Numeric constraints (minimum, maximum, exclusiveMinimum, exclusiveMaximum)
    - String constraints (minLength, maxLength, pattern)
    - Array constraints (minItems, maxItems, items)
    - Object constraints (properties, additionalProperties)
    - Optional type coercion
    """

    def __init__(self, coerce_types: bool = True):
        """
        Initialize validator.

        Args:
            coerce_types: If True, attempt to coerce values to expected types
        """
        self.coerce_types = coerce_types

    def validate(
        self,
        data: Any,
        schema: Dict[str, Any],
        path: str = ""
    ) -> ValidationResult:
        """
        Validate data against schema.

        Args:
            data: The data to validate
            schema: JSON Schema to validate against
            path: Current path for error reporting

        Returns:
            ValidationResult with validity status and any errors
        """
        errors: List[ValidationError] = []
        coerced = data

        # Handle null/None
        if data is None:
            if schema.get("type") == "null" or "null" in schema.get("type", []):
                return ValidationResult(is_valid=True, coerced_value=None)
            if schema.get("nullable", False):
                return ValidationResult(is_valid=True, coerced_value=None)
            errors.append(ValidationError(
                path=path or "root",
                message="Value cannot be null",
                value=data,
                expected=schema.get("type", "non-null")
            ))
            return ValidationResult(is_valid=False, errors=errors)

        # Type validation
        schema_type = schema.get("type")
        if schema_type:
            type_result = self._validate_type(data, schema_type, path, schema)
            if not type_result.is_valid:
                return type_result
            coerced = type_result.coerced_value

        # Enum validation
        if "enum" in schema:
            if coerced not in schema["enum"]:
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"Value must be one of: {schema['enum']}",
                    value=coerced,
                    expected=f"one of {schema['enum']}"
                ))
                return ValidationResult(is_valid=False, errors=errors)

        # Const validation
        if "const" in schema:
            if coerced != schema["const"]:
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"Value must be exactly: {schema['const']}",
                    value=coerced,
                    expected=str(schema["const"])
                ))
                return ValidationResult(is_valid=False, errors=errors)

        # Type-specific validation
        if schema_type == "string" or isinstance(coerced, str):
            string_errors = self._validate_string(coerced, schema, path)
            errors.extend(string_errors)

        elif schema_type == "number" or schema_type == "integer" or isinstance(coerced, (int, float)):
            number_errors = self._validate_number(coerced, schema, path)
            errors.extend(number_errors)

        elif schema_type == "array" or isinstance(coerced, list):
            array_result = self._validate_array(coerced, schema, path)
            if not array_result.is_valid:
                return array_result
            coerced = array_result.coerced_value

        elif schema_type == "object" or isinstance(coerced, dict):
            object_result = self._validate_object(coerced, schema, path)
            if not object_result.is_valid:
                return object_result
            coerced = object_result.coerced_value

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            coerced_value=coerced
        )

    def _validate_type(
        self,
        data: Any,
        schema_type: Union[str, List[str]],
        path: str,
        schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate and optionally coerce type"""
        errors = []

        # Handle union types
        if isinstance(schema_type, list):
            for t in schema_type:
                result = self._validate_type(data, t, path, schema)
                if result.is_valid:
                    return result
            errors.append(ValidationError(
                path=path or "root",
                message=f"Value does not match any of types: {schema_type}",
                value=data,
                expected=f"one of {schema_type}"
            ))
            return ValidationResult(is_valid=False, errors=errors)

        # Type mapping
        type_checks = {
            "string": (str, lambda x: str(x) if self.coerce_types else x),
            "integer": (int, lambda x: int(x) if self.coerce_types and str(x).lstrip('-').isdigit() else x),
            "number": ((int, float), lambda x: float(x) if self.coerce_types else x),
            "boolean": (bool, self._coerce_boolean),
            "array": (list, lambda x: list(x) if self.coerce_types and hasattr(x, '__iter__') and not isinstance(x, (str, dict)) else x),
            "object": (dict, lambda x: x),
            "null": (type(None), lambda x: x),
        }

        if schema_type not in type_checks:
            # Unknown type, accept anything
            return ValidationResult(is_valid=True, coerced_value=data)

        expected_type, coercer = type_checks[schema_type]

        # Check type
        if isinstance(data, expected_type):
            return ValidationResult(is_valid=True, coerced_value=data)

        # Try coercion
        if self.coerce_types:
            try:
                coerced = coercer(data)
                if isinstance(coerced, expected_type):
                    return ValidationResult(is_valid=True, coerced_value=coerced)
            except (ValueError, TypeError):
                pass

        errors.append(ValidationError(
            path=path or "root",
            message=f"Expected type '{schema_type}', got '{type(data).__name__}'",
            value=data,
            expected=schema_type
        ))
        return ValidationResult(is_valid=False, errors=errors)

    def _coerce_boolean(self, value: Any) -> bool:
        """Coerce value to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            if value.lower() in ('false', '0', 'no', 'off'):
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return value

    def _validate_string(
        self,
        data: str,
        schema: Dict[str, Any],
        path: str
    ) -> List[ValidationError]:
        """Validate string constraints"""
        errors = []

        if not isinstance(data, str):
            return errors

        # minLength
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(ValidationError(
                path=path or "root",
                message=f"String length {len(data)} is less than minimum {schema['minLength']}",
                value=data,
                expected=f"length >= {schema['minLength']}"
            ))

        # maxLength
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(ValidationError(
                path=path or "root",
                message=f"String length {len(data)} exceeds maximum {schema['maxLength']}",
                value=data,
                expected=f"length <= {schema['maxLength']}"
            ))

        # pattern
        if "pattern" in schema:
            try:
                if not re.match(schema["pattern"], data):
                    errors.append(ValidationError(
                        path=path or "root",
                        message=f"String does not match pattern: {schema['pattern']}",
                        value=data,
                        expected=f"match pattern {schema['pattern']}"
                    ))
            except re.error:
                pass  # Invalid regex, skip

        # format (basic support)
        if "format" in schema:
            format_errors = self._validate_format(data, schema["format"], path)
            errors.extend(format_errors)

        return errors

    def _validate_format(
        self,
        data: str,
        format_type: str,
        path: str
    ) -> List[ValidationError]:
        """Validate string format"""
        errors = []

        format_patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "uri": r'^https?://[^\s]+$',
            "date": r'^\d{4}-\d{2}-\d{2}$',
            "date-time": r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        }

        if format_type in format_patterns:
            if not re.match(format_patterns[format_type], data, re.IGNORECASE):
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"String does not match format '{format_type}'",
                    value=data,
                    expected=f"format {format_type}"
                ))

        return errors

    def _validate_number(
        self,
        data: Union[int, float],
        schema: Dict[str, Any],
        path: str
    ) -> List[ValidationError]:
        """Validate numeric constraints"""
        errors = []

        if not isinstance(data, (int, float)):
            return errors

        # minimum
        if "minimum" in schema:
            if data < schema["minimum"]:
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"Value {data} is less than minimum {schema['minimum']}",
                    value=data,
                    expected=f">= {schema['minimum']}"
                ))

        # maximum
        if "maximum" in schema:
            if data > schema["maximum"]:
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"Value {data} exceeds maximum {schema['maximum']}",
                    value=data,
                    expected=f"<= {schema['maximum']}"
                ))

        # exclusiveMinimum
        if "exclusiveMinimum" in schema:
            if data <= schema["exclusiveMinimum"]:
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"Value {data} must be greater than {schema['exclusiveMinimum']}",
                    value=data,
                    expected=f"> {schema['exclusiveMinimum']}"
                ))

        # exclusiveMaximum
        if "exclusiveMaximum" in schema:
            if data >= schema["exclusiveMaximum"]:
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"Value {data} must be less than {schema['exclusiveMaximum']}",
                    value=data,
                    expected=f"< {schema['exclusiveMaximum']}"
                ))

        # multipleOf
        if "multipleOf" in schema:
            if data % schema["multipleOf"] != 0:
                errors.append(ValidationError(
                    path=path or "root",
                    message=f"Value {data} is not a multiple of {schema['multipleOf']}",
                    value=data,
                    expected=f"multiple of {schema['multipleOf']}"
                ))

        return errors

    def _validate_array(
        self,
        data: list,
        schema: Dict[str, Any],
        path: str
    ) -> ValidationResult:
        """Validate array constraints"""
        errors = []
        coerced = []

        if not isinstance(data, list):
            return ValidationResult(is_valid=True, coerced_value=data)

        # minItems
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(ValidationError(
                path=path or "root",
                message=f"Array has {len(data)} items, minimum is {schema['minItems']}",
                value=data,
                expected=f"at least {schema['minItems']} items"
            ))

        # maxItems
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append(ValidationError(
                path=path or "root",
                message=f"Array has {len(data)} items, maximum is {schema['maxItems']}",
                value=data,
                expected=f"at most {schema['maxItems']} items"
            ))

        # uniqueItems
        if schema.get("uniqueItems", False):
            try:
                if len(data) != len(set(str(item) for item in data)):
                    errors.append(ValidationError(
                        path=path or "root",
                        message="Array items must be unique",
                        value=data,
                        expected="unique items"
                    ))
            except TypeError:
                pass  # Items not hashable

        # items validation
        if "items" in schema:
            items_schema = schema["items"]
            for i, item in enumerate(data):
                item_path = f"{path}[{i}]" if path else f"[{i}]"
                result = self.validate(item, items_schema, item_path)
                if not result.is_valid:
                    errors.extend(result.errors)
                coerced.append(result.coerced_value)
        else:
            coerced = data

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            coerced_value=coerced
        )

    def _validate_object(
        self,
        data: dict,
        schema: Dict[str, Any],
        path: str
    ) -> ValidationResult:
        """Validate object constraints"""
        errors = []
        coerced = {}

        if not isinstance(data, dict):
            return ValidationResult(is_valid=True, coerced_value=data)

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_allowed = schema.get("additionalProperties", True)

        # Check required properties
        for prop in required:
            if prop not in data:
                errors.append(ValidationError(
                    path=f"{path}.{prop}" if path else prop,
                    message=f"Missing required property: {prop}",
                    expected=f"property '{prop}'"
                ))

        # Validate each property
        for key, value in data.items():
            prop_path = f"{path}.{key}" if path else key

            if key in properties:
                result = self.validate(value, properties[key], prop_path)
                if not result.is_valid:
                    errors.extend(result.errors)
                coerced[key] = result.coerced_value
            elif additional_allowed is False:
                errors.append(ValidationError(
                    path=prop_path,
                    message=f"Additional property not allowed: {key}",
                    value=value,
                    expected="no additional properties"
                ))
            elif isinstance(additional_allowed, dict):
                result = self.validate(value, additional_allowed, prop_path)
                if not result.is_valid:
                    errors.extend(result.errors)
                coerced[key] = result.coerced_value
            else:
                coerced[key] = value

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            coerced_value=coerced
        )


def validate_tool_parameters(
    parameters: Dict[str, Any],
    schema: Dict[str, Any],
    coerce_types: bool = True
) -> ValidationResult:
    """
    Convenience function to validate tool parameters against schema.

    Args:
        parameters: Parameter dictionary to validate
        schema: JSON Schema for the parameters
        coerce_types: Whether to coerce types

    Returns:
        ValidationResult
    """
    validator = JSONSchemaValidator(coerce_types=coerce_types)
    return validator.validate(parameters, schema)


def create_parameter_schema(
    name: str,
    param_type: str = "string",
    description: str = "",
    required: bool = True,
    default: Any = None,
    enum: Optional[List[Any]] = None,
    **constraints
) -> Dict[str, Any]:
    """
    Create a JSON Schema for a single parameter.

    Args:
        name: Parameter name
        param_type: JSON Schema type
        description: Parameter description
        required: Whether parameter is required
        default: Default value
        enum: Allowed values
        **constraints: Additional constraints (minLength, maximum, etc.)

    Returns:
        JSON Schema dictionary
    """
    schema = {
        "type": param_type,
        "description": description,
    }

    if default is not None:
        schema["default"] = default

    if enum:
        schema["enum"] = enum

    schema.update(constraints)

    return schema

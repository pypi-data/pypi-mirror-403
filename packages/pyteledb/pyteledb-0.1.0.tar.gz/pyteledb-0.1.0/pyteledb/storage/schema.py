"""Record schema definition and validation.

Defines the structure of records and provides type validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pyteledb.exceptions import ValidationError


class FieldType(Enum):
    """Supported field types for schema definition."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


@dataclass
class Field:
    """
    Schema field definition.

    Attributes:
        name: Field name.
        field_type: Type of the field.
        required: Whether the field is required.
        default: Default value if not provided.
        nullable: Whether the field can be None.
    """

    name: str
    field_type: FieldType = FieldType.ANY
    required: bool = True
    default: Any = None
    nullable: bool = False

    def validate(self, value: Any) -> Any:
        """
        Validate a value against this field definition.

        Args:
            value: Value to validate.

        Returns:
            The validated (possibly coerced) value.

        Raises:
            ValidationError: If validation fails.
        """
        # Handle None
        if value is None:
            if self.nullable:
                return None
            if not self.required and self.default is not None:
                return self.default
            if self.required:
                raise ValidationError(f"Field '{self.name}' is required but got None")
            return None

        # Type validation
        type_validators = {
            FieldType.STRING: lambda v: isinstance(v, str),
            FieldType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            FieldType.FLOAT: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            FieldType.BOOLEAN: lambda v: isinstance(v, bool),
            FieldType.LIST: lambda v: isinstance(v, list),
            FieldType.DICT: lambda v: isinstance(v, dict),
            FieldType.ANY: lambda _: True,
        }

        validator = type_validators.get(self.field_type, lambda _: True)
        if not validator(value):
            raise ValidationError(
                f"Field '{self.name}' expected type {self.field_type.value}, "
                f"got {type(value).__name__}"
            )

        return value


@dataclass
class Schema:
    """
    Record schema definition.

    Attributes:
        name: Schema name for identification.
        version: Schema version for migrations.
        fields: List of field definitions.
    """

    name: str
    version: int = 1
    fields: list[Field] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Build field lookup for efficient validation."""
        self._field_map: dict[str, Field] = {f.name: f for f in self.fields}

    def add_field(self, field_def: Field) -> Schema:
        """
        Add a field to the schema.

        Args:
            field_def: Field definition to add.

        Returns:
            Self for chaining.
        """
        self.fields.append(field_def)
        self._field_map[field_def.name] = field_def
        return self

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data against this schema.

        Args:
            data: Dictionary of field values.

        Returns:
            Validated data with defaults applied.

        Raises:
            ValidationError: If validation fails.
        """
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict, got {type(data).__name__}")

        result: dict[str, Any] = {}

        # Validate defined fields
        for field_def in self.fields:
            value = data.get(field_def.name)
            if value is None and field_def.required:
                if field_def.default is not None:
                    result[field_def.name] = field_def.default
                elif not field_def.nullable:
                    raise ValidationError(f"Missing required field: '{field_def.name}'")
                else:
                    result[field_def.name] = None
            else:
                result[field_def.name] = field_def.validate(value)

        # Copy through extra fields not in schema
        for key, value in data.items():
            if key not in self._field_map:
                result[key] = value

        return result

    def get_field(self, name: str) -> Field | None:
        """
        Get a field definition by name.

        Args:
            name: Field name.

        Returns:
            Field definition or None if not found.
        """
        return self._field_map.get(name)

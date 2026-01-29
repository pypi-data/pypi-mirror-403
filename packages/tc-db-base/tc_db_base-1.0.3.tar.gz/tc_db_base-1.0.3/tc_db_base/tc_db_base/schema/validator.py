"""Schema Validator - Validate documents against schema."""

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from tc_db_base.schema import get_schema

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Validation error with details."""

    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        self.message = message
        self.field = field
        self.errors = errors or [message]
        super().__init__(message)


class SchemaValidator:
    """Validate documents against collection schema."""

    TYPE_VALIDATORS = {
        'string': lambda v: isinstance(v, str),
        'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        'boolean': lambda v: isinstance(v, bool),
        'array': lambda v: isinstance(v, list),
        'object': lambda v: isinstance(v, dict),
        'datetime': lambda v: isinstance(v, (datetime, str)),
    }

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._schema_loader = get_schema()
        self._schema = self._schema_loader.get_collection(collection_name)
        self._fields = self._schema.get('fields', {}) if self._schema else {}

    def validate(self, data: Dict[str, Any], partial: bool = False) -> Tuple[bool, List[str]]:
        """Validate document against schema."""
        errors = []

        if not self._schema:
            return True, []

        # Check required fields (unless partial update)
        if not partial:
            required = self._schema_loader.get_required_fields(self.collection_name)
            for field in required:
                if field not in data or data[field] is None:
                    errors.append(f"Required field '{field}' is missing")

        # Validate each field
        for field_name, value in data.items():
            if value is None:
                continue
            field_config = self._fields.get(field_name)
            if not field_config:
                continue
            field_errors = self._validate_field(field_name, value, field_config)
            errors.extend(field_errors)

        return len(errors) == 0, errors

    def validate_or_raise(self, data: Dict[str, Any], partial: bool = False):
        """Validate and raise exception if invalid."""
        is_valid, errors = self.validate(data, partial)
        if not is_valid:
            raise ValidationError(
                message=f"Validation failed: {'; '.join(errors)}",
                errors=errors
            )

    def _validate_field(self, field_name: str, value: Any, config: Dict) -> List[str]:
        """Validate a single field."""
        errors = []

        # Type check
        field_type = config.get('type')
        if field_type:
            validator = self.TYPE_VALIDATORS.get(field_type)
            if validator and not validator(value):
                errors.append(f"Field '{field_name}' must be of type {field_type}")
                return errors

        # Enum check
        enum_values = config.get('enum')
        if enum_values and value not in enum_values:
            errors.append(f"Field '{field_name}' must be one of: {', '.join(str(v) for v in enum_values)}")

        # Format check
        format_type = config.get('format')
        if format_type:
            format_error = self._validate_format(field_name, value, format_type)
            if format_error:
                errors.append(format_error)

        # Array items check
        if field_type == 'array' and 'items' in config:
            items_type = config['items']
            for i, item in enumerate(value):
                item_validator = self.TYPE_VALIDATORS.get(items_type)
                if item_validator and not item_validator(item):
                    errors.append(f"Field '{field_name}[{i}]' must be of type {items_type}")

        return errors

    def _validate_format(self, field_name: str, value: Any, format_type: str) -> Optional[str]:
        """Validate field format."""
        if format_type == 'email':
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, str(value)):
                return f"Field '{field_name}' is not a valid email"
        elif format_type == 'url':
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(pattern, str(value)):
                return f"Field '{field_name}' is not a valid URL"
        elif format_type == 'phone':
            pattern = r'^[\d\s\-\+\(\)]+$'
            if not re.match(pattern, str(value)):
                return f"Field '{field_name}' is not a valid phone number"
        return None

    def apply_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values to document."""
        result = data.copy()
        for field_name, config in self._fields.items():
            if field_name not in result or result[field_name] is None:
                default = config.get('default')
                if default is not None:
                    result[field_name] = default
        return result

    def apply_auto_fields(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Apply auto-generated fields (timestamps)."""
        result = data.copy()
        now = datetime.utcnow()

        for field_name, config in self._fields.items():
            auto = config.get('auto')
            if auto == 'create' and not is_update:
                if field_name not in result:
                    result[field_name] = now
            elif auto == 'update':
                result[field_name] = now

        return result

    def sanitize(self, data: Dict[str, Any], remove_sensitive: bool = False) -> Dict[str, Any]:
        """Sanitize document for output."""
        result = data.copy()

        if remove_sensitive:
            for field_name, config in self._fields.items():
                if config.get('sensitive') and field_name in result:
                    del result[field_name]

        if '_id' in result:
            result['_id'] = str(result['_id'])

        return result

    def get_projection(self, exclude_sensitive: bool = True) -> Dict[str, int]:
        """Get MongoDB projection to exclude sensitive fields."""
        if not exclude_sensitive:
            return {}

        projection = {}
        for field_name, config in self._fields.items():
            if config.get('sensitive'):
                projection[field_name] = 0

        return projection


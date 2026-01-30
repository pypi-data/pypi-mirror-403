"""
Schema utilities for the Laurent pipeline.

This module provides access to JSON schemas, configuration files, and examples
for the Laurent series fitting and analytic continuation pipeline.

Functions:
    get_schema(name): Load a JSON schema by name
    get_config(name): Load a configuration file by name
    get_example(name): Load an example file by name
    validate(data, schema_name): Validate data against a schema (requires jsonschema)
    list_schemas(): List available schema names
    list_configs(): List available config names
    list_examples(): List available example names
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "get_schema",
    "get_config",
    "get_example",
    "validate",
    "list_schemas",
    "list_configs",
    "list_examples",
    "SchemaNotFoundError",
    "ValidationError",
]

# Base path for schema resources
_SCHEMAS_DIR = Path(__file__).parent


class SchemaNotFoundError(Exception):
    """Raised when a requested schema, config, or example is not found."""
    pass


class ValidationError(Exception):
    """Raised when data fails schema validation."""
    pass


def _load_json_file(directory: Path, name: str, file_type: str) -> Dict[str, Any]:
    """Load a JSON file from the specified directory.

    Args:
        directory: Directory containing the file
        name: Name of the file (with or without .json extension)
        file_type: Type of file for error messages ('schema', 'config', 'example')

    Returns:
        Parsed JSON content as a dictionary

    Raises:
        SchemaNotFoundError: If the file is not found
    """
    # Add .json extension if not present
    if not name.endswith('.json'):
        name = f"{name}.json"

    file_path = directory / name

    if not file_path.exists():
        available = [f.stem for f in directory.glob('*.json')]
        raise SchemaNotFoundError(
            f"{file_type.capitalize()} '{name}' not found. "
            f"Available {file_type}s: {available}"
        )

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_schema(name: str) -> Dict[str, Any]:
    """Load a JSON schema by name.

    Args:
        name: Schema name (e.g., 'types', 'function_contracts')
              The .json extension is optional.

    Returns:
        The parsed JSON schema as a dictionary

    Raises:
        SchemaNotFoundError: If the schema is not found

    Examples:
        >>> types_schema = get_schema('types')
        >>> contracts = get_schema('function_contracts')
    """
    return _load_json_file(_SCHEMAS_DIR, name, 'schema')


def get_config(name: str) -> Dict[str, Any]:
    """Load a configuration file by name.

    Args:
        name: Config name (e.g., 'pipeline_config')
              The .json extension is optional.

    Returns:
        The parsed configuration as a dictionary

    Raises:
        SchemaNotFoundError: If the config is not found

    Examples:
        >>> config = get_config('pipeline_config')
        >>> print(config['pipeline'])
    """
    config_dir = _SCHEMAS_DIR / 'config'
    return _load_json_file(config_dir, name, 'config')


def get_example(name: str) -> Dict[str, Any]:
    """Load an example file by name.

    Args:
        name: Example name (e.g., 'spline_export.sample')
              The .json extension is optional.

    Returns:
        The parsed example data as a dictionary

    Raises:
        SchemaNotFoundError: If the example is not found

    Examples:
        >>> spline_data = get_example('spline_export.sample')
        >>> print(spline_data['version'])
    """
    examples_dir = _SCHEMAS_DIR / 'examples'
    return _load_json_file(examples_dir, name, 'example')


def list_schemas() -> List[str]:
    """List available schema names.

    Returns:
        List of schema names (without .json extension)
    """
    return sorted(f.stem for f in _SCHEMAS_DIR.glob('*.json'))


def list_configs() -> List[str]:
    """List available configuration names.

    Returns:
        List of config names (without .json extension)
    """
    config_dir = _SCHEMAS_DIR / 'config'
    return sorted(f.stem for f in config_dir.glob('*.json'))


def list_examples() -> List[str]:
    """List available example names.

    Returns:
        List of example names (without .json extension)
    """
    examples_dir = _SCHEMAS_DIR / 'examples'
    return sorted(f.stem for f in examples_dir.glob('*.json'))


def validate(data: Dict[str, Any], schema_name: str) -> bool:
    """Validate data against a named schema.

    This function requires the optional `jsonschema` dependency.
    Install with: pip install analytic-continuation[validation]

    Note: The schemas in this package are type definitions rather than
    JSON Schema format. This function performs structural validation
    by checking that required keys exist in the data.

    Args:
        data: Data to validate
        schema_name: Name of the schema to validate against

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails
        ImportError: If jsonschema is not installed
        SchemaNotFoundError: If the schema is not found

    Examples:
        >>> from analytic_continuation.schemas import validate
        >>> validate({'re': 1.0, 'im': 2.0}, 'types')  # validates Complex type
    """
    try:
        import jsonschema as _jsonschema
    except ImportError:
        raise ImportError(
            "The 'jsonschema' package is required for validation. "
            "Install with: pip install analytic-continuation[validation]"
        )

    schema = get_schema(schema_name)

    # Our schemas are type definitions, not JSON Schema format
    # Perform structural validation based on the type definitions
    errors = _validate_against_type_schema(data, schema)

    if errors:
        raise ValidationError(
            f"Validation failed for schema '{schema_name}':\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return True


def _validate_against_type_schema(
    data: Any,
    schema: Dict[str, Any],
    path: str = "",
    type_name: Optional[str] = None
) -> List[str]:
    """Recursively validate data against type definition schema.

    Args:
        data: Data to validate
        schema: Type definition schema
        path: Current path in the data structure (for error messages)
        type_name: Specific type name to validate against

    Returns:
        List of validation error messages
    """
    errors: List[str] = []

    if type_name:
        # Validate against a specific type definition
        if type_name not in schema:
            errors.append(f"Unknown type: {type_name}")
            return errors

        type_def = schema[type_name]
        if isinstance(type_def, dict):
            if not isinstance(data, dict):
                errors.append(f"{path or 'root'}: expected object, got {type(data).__name__}")
                return errors

            # Check required fields
            for field, field_type in type_def.items():
                field_path = f"{path}.{field}" if path else field
                if field not in data:
                    errors.append(f"{field_path}: missing required field")
                else:
                    # Recursively validate if the field type is a known type
                    if isinstance(field_type, str) and field_type in schema:
                        sub_errors = _validate_against_type_schema(
                            data[field], schema, field_path, field_type
                        )
                        errors.extend(sub_errors)
    else:
        # No specific type - validate data has dict structure
        if not isinstance(data, dict):
            errors.append(f"{path or 'root'}: expected object, got {type(data).__name__}")

    return errors

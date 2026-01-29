"""OpenAPI specification utilities."""

import json
from typing import Any, Dict

from openapi_core import OpenAPI


def _normalize_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an OpenAPI specification to ensure all dictionary keys are strings.

    Django Ninja's get_openapi_schema() returns integer keys for HTTP status codes
    (e.g., 200, 404) instead of string keys ("200", "404"). The OpenAPI specification
    requires these to be strings, and jsonschema validation fails with integer keys.

    This function performs a JSON round-trip to convert all keys to strings,
    which is the standard behavior when serializing to JSON.

    Args:
        spec: OpenAPI specification dictionary (may contain integer keys)

    Returns:
        Normalized specification with all keys as strings
    """
    return json.loads(json.dumps(spec))


def load_and_resolve_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load and resolve all $ref references in an OpenAPI specification.

    Args:
        spec: OpenAPI specification as dictionary

    Returns:
        Resolved specification with $refs dereferenced

    Raises:
        ValueError: If spec is invalid
    """
    try:
        # Normalize the spec to ensure all keys are strings
        # This handles Django Ninja which uses integer keys for status codes
        normalized_spec = _normalize_spec(spec)

        # Use openapi-core to parse and validate
        openapi = OpenAPI.from_dict(normalized_spec)

        # Access the dereferenced spec
        # openapi-core stores the spec in a way we can access
        resolved = openapi.spec.contents()

        return dict(resolved)
    except Exception as e:
        raise ValueError(f"Invalid OpenAPI specification: {e}") from e

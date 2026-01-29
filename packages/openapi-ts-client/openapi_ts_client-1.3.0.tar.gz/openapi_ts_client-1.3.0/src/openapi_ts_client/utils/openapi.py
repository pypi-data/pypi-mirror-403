"""OpenAPI specification utilities."""

from typing import Any, Dict

from openapi_core import OpenAPI


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
        # Use openapi-core to parse and validate
        openapi = OpenAPI.from_dict(spec)

        # Access the dereferenced spec
        # openapi-core stores the spec in a way we can access
        resolved = openapi.spec.contents()

        return dict(resolved)
    except Exception as e:
        raise ValueError(f"Invalid OpenAPI specification: {e}") from e

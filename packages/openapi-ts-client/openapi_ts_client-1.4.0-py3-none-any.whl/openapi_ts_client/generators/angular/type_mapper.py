"""Map OpenAPI types to TypeScript types."""

from typing import Any, Dict, Optional, Set, Tuple

from openapi_ts_client.utils import schema_to_type_name


def map_openapi_type(
    schema: Dict[str, Any], registry: Optional[Dict[str, Dict[str, Any]]] = None
) -> str:
    """
    Map an OpenAPI schema to a TypeScript type string.

    Args:
        schema: OpenAPI schema object
        registry: Optional extraction registry for titled anyOf schemas

    Returns:
        TypeScript type string
    """
    result, _ = map_openapi_type_with_imports(schema, registry)
    return result


def map_openapi_type_with_imports(
    schema: Dict[str, Any], registry: Optional[Dict[str, Dict[str, Any]]] = None
) -> Tuple[str, Set[str]]:
    """
    Map an OpenAPI schema to a TypeScript type string, tracking imports.

    Args:
        schema: OpenAPI schema object
        registry: Optional extraction registry for titled anyOf schemas

    Returns:
        Tuple of (TypeScript type string, set of required imports)
    """
    if registry is None:
        registry = {}

    imports: Set[str] = set()

    if not schema:
        return "any", imports

    # Handle $ref
    if "$ref" in schema:
        ref = schema["$ref"]
        # Extract schema name from "#/components/schemas/Name"
        raw_name = ref.split("/")[-1]
        # Convert to PascalCase for TypeScript type name
        type_name = schema_to_type_name(raw_name)
        imports.add(type_name)
        return type_name, imports

    # Handle anyOf (commonly used for nullable types)
    if "anyOf" in schema:
        # Check if this is a titled anyOf that should use extracted type
        if "title" in schema:
            type_name = _lookup_extracted_type(schema, registry)
            if type_name:
                imports.add(type_name)
                # Check if anyOf includes null - if so, add | null to the type
                has_null = any(s.get("type") == "null" for s in schema["anyOf"])
                if has_null:
                    return f"{type_name} | null", imports
                return type_name, imports

        # Fall back to inline union
        types = []
        for sub_schema in schema["anyOf"]:
            if sub_schema.get("type") == "null":
                types.append("null")
            else:
                sub_type, sub_imports = map_openapi_type_with_imports(sub_schema, registry)
                types.append(sub_type)
                imports.update(sub_imports)
        return " | ".join(types), imports

    schema_type = schema.get("type")

    # Handle arrays
    if schema_type == "array":
        items = schema.get("items", {})
        item_type, item_imports = map_openapi_type_with_imports(items, registry)
        imports.update(item_imports)
        return f"Array<{item_type}>", imports

    # Handle object with additionalProperties (map types)
    if schema_type == "object" and "additionalProperties" in schema:
        additional_props = schema["additionalProperties"]
        if additional_props and isinstance(additional_props, dict):
            value_type, value_imports = map_openapi_type_with_imports(additional_props, registry)
            imports.update(value_imports)
            return f"{{ [key: string]: {value_type}; }}", imports

    # Handle enum types (string or integer with enum values)
    if "enum" in schema:
        enum_values = schema["enum"]
        if schema_type == "string":
            # String enum - create union of string literals
            return " | ".join(f"'{v}'" for v in enum_values), imports
        elif schema_type in ("integer", "number"):
            # Numeric enum - create union of number literals
            return " | ".join(str(v) for v in enum_values), imports

    # Handle string with format: binary -> Blob
    if schema_type == "string" and schema.get("format") == "binary":
        return "Blob", imports

    # Basic type mapping
    type_map = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "object": "object",
    }

    if schema_type in type_map:
        return type_map[schema_type], imports

    return "any", imports


def _lookup_extracted_type(
    schema: Dict[str, Any], registry: Dict[str, Dict[str, Any]]
) -> Optional[str]:
    """
    Look up extracted type name for a schema in the registry.

    Matches by schema object identity (same dict instance).

    Args:
        schema: OpenAPI schema object to look up
        registry: Extraction registry mapping paths to type info

    Returns:
        Type name if found in registry, None otherwise
    """
    for info in registry.values():
        if info["schema"] is schema:
            return info["type_name"]
    return None

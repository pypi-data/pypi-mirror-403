"""Map OpenAPI types to TypeScript types."""

from typing import Any, Dict, Optional, Set, Tuple

from openapi_ts_client.utils import schema_to_type_name


def _is_primitive_or_array_schema(schema: Dict[str, Any]) -> bool:
    """Check if a schema is a primitive type or array (not an object with properties)."""
    schema_type = schema.get("type")

    # Has properties - it's a complex object, not primitive
    if schema.get("properties"):
        return False

    # Primitive types
    if schema_type in ("string", "integer", "number", "boolean"):
        # But if it's an enum, it's a named type, not primitive inline
        if "enum" in schema:
            return False
        return True

    # Array types should be resolved inline
    if schema_type == "array":
        return True

    return False


def map_openapi_type(
    schema: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
    use_date_type: bool = True,
    use_model_prefix: bool = True,
    all_schemas: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Map an OpenAPI schema to a TypeScript type string.

    Args:
        schema: OpenAPI schema object
        registry: Optional extraction registry for titled anyOf schemas
        use_date_type: If True, map date/date-time to Date; if False, use string
        use_model_prefix: If True, add Model prefix for reserved names (Fetch style)
        all_schemas: Optional dict of all schemas for resolving refs to primitives/arrays

    Returns:
        TypeScript type string
    """
    result, _ = map_openapi_type_with_imports(
        schema, registry, use_date_type, use_model_prefix, all_schemas
    )
    return result


def map_openapi_type_with_imports(
    schema: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
    use_date_type: bool = True,
    use_model_prefix: bool = True,
    all_schemas: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[str, Set[str]]:
    """
    Map an OpenAPI schema to a TypeScript type string, tracking imports.

    Args:
        schema: OpenAPI schema object
        registry: Optional extraction registry for titled anyOf schemas
        use_date_type: If True, map date/date-time to Date; if False, use string
        use_model_prefix: If True, add Model prefix for reserved names (Fetch style)
        all_schemas: Optional dict of all schemas for resolving refs to primitives/arrays

    Returns:
        Tuple of (TypeScript type string, set of required imports)
    """
    if registry is None:
        registry = {}
    if all_schemas is None:
        all_schemas = {}

    imports: Set[str] = set()

    if not schema:
        return "any", imports

    # Handle $ref
    if "$ref" in schema:
        ref = schema["$ref"]
        # Extract schema name from "#/components/schemas/Name"
        raw_name = ref.split("/")[-1]

        # Check if the referenced schema is a primitive/array type that should be inlined
        if all_schemas and raw_name in all_schemas:
            referenced_schema = all_schemas[raw_name]
            if _is_primitive_or_array_schema(referenced_schema):
                # Resolve inline instead of returning the ref name
                return map_openapi_type_with_imports(
                    referenced_schema, registry, use_date_type, use_model_prefix, all_schemas
                )

        # Convert to type name (handles reserved names like ApiResponse -> ModelApiResponse)
        if use_model_prefix:
            type_name = schema_to_type_name(raw_name)
        else:
            type_name = schema_to_type_name(raw_name)  # Always capitalize for consistency
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
                sub_type, sub_imports = map_openapi_type_with_imports(
                    sub_schema, registry, use_date_type, use_model_prefix, all_schemas
                )
                types.append(sub_type)
                imports.update(sub_imports)
        return " | ".join(types), imports

    schema_type = schema.get("type")

    # Handle arrays
    if schema_type == "array":
        items = schema.get("items", {})
        item_type, item_imports = map_openapi_type_with_imports(
            items, registry, use_date_type, use_model_prefix, all_schemas
        )
        imports.update(item_imports)
        return f"Array<{item_type}>", imports

    # Handle object with additionalProperties (map types)
    if schema_type == "object" and "additionalProperties" in schema:
        additional_props = schema["additionalProperties"]
        if additional_props and isinstance(additional_props, dict):
            value_type, value_imports = map_openapi_type_with_imports(
                additional_props, registry, use_date_type, use_model_prefix, all_schemas
            )
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

    # Handle string with format
    if schema_type == "string":
        format_val = schema.get("format")
        if format_val == "binary":
            return "Blob", imports
        if format_val in ("date", "date-time"):
            # Use Date type for Fetch, string for Angular
            return "Date" if use_date_type else "string", imports

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

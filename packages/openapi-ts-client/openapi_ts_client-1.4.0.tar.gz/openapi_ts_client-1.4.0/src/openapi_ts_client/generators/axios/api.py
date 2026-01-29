"""Generate api.ts for axios client - contains all models and API classes."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, PackageLoader

from openapi_ts_client.generators.shared import (
    create_extraction_registry,
)
from openapi_ts_client.utils.naming import operation_id_to_method_name, schema_to_type_name


def _get_template_env() -> Environment:
    """Get Jinja2 environment with axios templates loaded."""
    return Environment(
        loader=PackageLoader("openapi_ts_client", "templates/axios"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def _is_string_enum_schema(schema: Dict[str, Any]) -> bool:
    """
    Check if a schema is a string enum.

    String enums should be generated as:
    export const Name = { ... } as const;
    export type Name = typeof Name[keyof typeof Name];
    """
    if "enum" not in schema:
        return False

    schema_type = schema.get("type")
    if schema_type is not None and schema_type != "string":
        return False

    # Should not have properties (that would make it an object)
    if schema.get("properties"):
        return False

    return True


def _is_primitive_schema(schema: Dict[str, Any]) -> bool:
    """Check if a schema represents a primitive type (not an object or enum)."""
    schema_type = schema.get("type")

    # Has properties - it's a complex object
    if schema.get("properties"):
        return False

    # Has enum - it's a named type
    if "enum" in schema:
        return False

    # Primitive types
    if schema_type in ("string", "integer", "number", "boolean"):
        return True

    # Array types
    if schema_type == "array":
        return True

    return False


def _enum_value_to_key(value: str) -> str:
    """
    Convert an enum value to a valid TypeScript const key name.

    Special characters get converted to descriptive names.
    """
    special_chars = {
        ".": "Period",
        "-": "Hyphen",
        "_": "Underscore",
        " ": "Space",
        "/": "Slash",
        "\\": "Backslash",
        "+": "Plus",
        "*": "Asterisk",
        "?": "Question",
        "!": "Exclamation",
        "@": "At",
        "#": "Hash",
        "$": "Dollar",
        "%": "Percent",
        "^": "Caret",
        "&": "Ampersand",
        "(": "LeftParen",
        ")": "RightParen",
        "[": "LeftBracket",
        "]": "RightBracket",
        "{": "LeftBrace",
        "}": "RightBrace",
        "<": "LessThan",
        ">": "GreaterThan",
        "=": "Equals",
        ":": "Colon",
        ";": "Semicolon",
        ",": "Comma",
        "|": "Pipe",
        "~": "Tilde",
        "`": "Backtick",
        '"': "DoubleQuote",
        "'": "SingleQuote",
    }

    if value in special_chars:
        return special_chars[value]

    if value and value[0] in special_chars:
        return special_chars[value[0]] + value[1:].capitalize()

    if value:
        return value[0].upper() + value[1:] if len(value) > 1 else value.upper()

    return value


def _resolve_parameter_ref(param: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve a parameter reference to its actual definition."""
    if "$ref" in param:
        ref_path = param["$ref"]
        parts = ref_path.split("/")
        if len(parts) >= 4 and parts[1] == "components" and parts[2] == "parameters":
            param_name = parts[3]
            resolved = spec.get("components", {}).get("parameters", {}).get(param_name, {})
            return resolved
    return param


def _resolve_schema_ref(schema: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve a schema reference to its actual definition."""
    if "$ref" in schema:
        ref_path = schema["$ref"]
        parts = ref_path.split("/")
        if len(parts) >= 4 and parts[1] == "components" and parts[2] == "schemas":
            schema_name = parts[3]
            return spec.get("components", {}).get("schemas", {}).get(schema_name, {})
    return schema


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _to_camel_case(name: str) -> str:
    """Convert snake_case or kebab-case to camelCase."""
    parts = re.split(r"[_-]", name)
    if not parts:
        return name
    return parts[0] + "".join(word.title() for word in parts[1:])


def _tag_to_api_class_name(tag: str) -> str:
    """
    Convert OpenAPI tag to API class name.

    Examples:
        Feedings -> FeedingsApi
        HTTPMetrics -> HTTPMetricsApi
        Care Plans -> CarePlansApi
    """
    words = tag.split()
    class_name = "".join(word[0].upper() + word[1:] if word else "" for word in words)
    return f"{class_name}Api"


def _map_openapi_type_to_ts(
    schema: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
    all_schemas: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Map OpenAPI schema to TypeScript type for axios interfaces.

    Unlike fetch, axios doesn't use FromJSON/ToJSON so we just need simple types.
    """
    if registry is None:
        registry = {}
    if all_schemas is None:
        all_schemas = {}

    if not schema:
        return "any"

    # Handle $ref
    if "$ref" in schema:
        raw_name = schema["$ref"].split("/")[-1]
        # Check if the referenced schema is a primitive or enum
        referenced = all_schemas.get(raw_name, {})
        if _is_string_enum_schema(referenced) or referenced.get("properties"):
            # Use PascalCase for enums and object schemas
            return schema_to_type_name(raw_name, add_model_prefix=False)
        # Primitive types are inlined
        if _is_primitive_schema(referenced):
            return _map_openapi_type_to_ts(referenced, registry, all_schemas)
        return schema_to_type_name(raw_name, add_model_prefix=False)

    # Handle anyOf (commonly used for nullable types)
    if "anyOf" in schema:
        non_null_schemas = [s for s in schema["anyOf"] if s.get("type") != "null"]
        has_null = any(s.get("type") == "null" for s in schema["anyOf"])

        if non_null_schemas:
            ts_type = _map_openapi_type_to_ts(non_null_schemas[0], registry, all_schemas)
            if has_null:
                return f"{ts_type} | null"
            return ts_type

        return "any"

    schema_type = schema.get("type")

    # Handle arrays
    if schema_type == "array":
        items = schema.get("items", {})
        item_type = _map_openapi_type_to_ts(items, registry, all_schemas)
        return f"Array<{item_type}>"

    # Handle object with additionalProperties
    if schema_type == "object" and "additionalProperties" in schema:
        additional = schema["additionalProperties"]
        if additional and isinstance(additional, dict):
            value_type = _map_openapi_type_to_ts(additional, registry, all_schemas)
            return f"{{ [key: string]: {value_type}; }}"
        return "object"

    # Handle basic types
    type_map = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "object": "object",
    }

    return type_map.get(schema_type, "any")


def _extract_models(
    spec: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract model information from OpenAPI schemas.

    Args:
        spec: OpenAPI specification dict
        registry: Extraction registry for titled anyOf schemas

    Returns:
        Tuple of (interfaces, enums) where:
        - interfaces: List of interface model info dicts
        - enums: List of enum info dicts for const/type pattern
    """
    if registry is None:
        registry = {}

    schemas = spec.get("components", {}).get("schemas", {})
    interfaces = []
    enums = []
    all_schemas = spec.get("components", {}).get("schemas", {})

    for schema_name, schema in schemas.items():
        # Handle string enums with const/type pattern
        if _is_string_enum_schema(schema):
            type_name = schema_to_type_name(schema_name, add_model_prefix=False)
            enum_values = schema.get("enum", [])
            enum_members = []
            for value in enum_values:
                key = _enum_value_to_key(str(value))
                enum_members.append({"key": key, "value": value})

            enums.append(
                {
                    "name": type_name,
                    "description": schema.get("description", ""),
                    "members": enum_members,
                }
            )
            continue

        # Skip primitive schemas (they don't need interface definitions)
        if _is_primitive_schema(schema):
            continue

        # Handle object schemas (interfaces)
        type_name = schema_to_type_name(schema_name, add_model_prefix=False)
        properties_schema = schema.get("properties", {})
        required_props = schema.get("required", [])

        properties = []
        for prop_name, prop_schema in properties_schema.items():
            is_required = prop_name in required_props
            ts_type = _map_openapi_type_to_ts(prop_schema, registry, all_schemas)

            # Handle nullable
            is_nullable = prop_schema.get("nullable", False)
            if "anyOf" in prop_schema:
                is_nullable = any(s.get("type") == "null" for s in prop_schema["anyOf"])

            # Add | null for nullable types (if not already included)
            if is_nullable and " | null" not in ts_type:
                ts_type = f"{ts_type} | null"

            properties.append(
                {
                    "name": prop_name,
                    "ts_name": _snake_to_camel(prop_name),
                    "ts_type": ts_type,
                    "required": is_required,
                    "nullable": is_nullable,
                    "description": prop_schema.get("description", ""),
                }
            )

        interfaces.append(
            {
                "name": type_name,
                "description": schema.get("description", ""),
                "properties": properties,
            }
        )

    return interfaces, enums


def _get_typescript_type_for_param(
    param: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
    all_schemas: Optional[Dict[str, Any]] = None,
) -> str:
    """Get TypeScript type for a parameter schema."""
    if all_schemas is None:
        all_schemas = {}
    schema = param.get("schema", {})

    # Handle anyOf patterns (nullable types)
    if "anyOf" in schema:
        non_null_types = [s for s in schema["anyOf"] if s.get("type") != "null"]
        has_null = any(s.get("type") == "null" for s in schema["anyOf"])
        if non_null_types:
            ts_type = _map_openapi_type_to_ts(non_null_types[0], registry, all_schemas)
            if has_null:
                return f"{ts_type} | null"
            return ts_type

    return _map_openapi_type_to_ts(schema, registry, all_schemas)


def _extract_response_type(
    operation: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
    all_schemas: Optional[Dict[str, Any]] = None,
) -> str:
    """Extract response type from operation responses."""
    if all_schemas is None:
        all_schemas = {}
    responses = operation.get("responses", {})

    # Look for 200, 201, or 204 response
    for status in ["200", "201"]:
        if status in responses:
            response = responses[status]
            content = response.get("content", {})

            if not content:
                return "void"

            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                return _map_openapi_type_to_ts(schema, registry, all_schemas)

    if "204" in responses:
        return "void"

    return "any"


def _extract_request_body_info(
    operation: Dict[str, Any],
    spec: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Extract request body parameter info.

    Returns:
        Tuple of (param_name, param_type, is_required)
    """
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    is_required = request_body.get("required", False)

    if not content:
        return None, None, False

    # Check for JSON content
    if "application/json" in content:
        schema = content["application/json"].get("schema", {})

        if "$ref" in schema:
            raw_name = schema["$ref"].split("/")[-1]

            # Check if the referenced schema is a primitive type
            referenced_schema = spec.get("components", {}).get("schemas", {}).get(raw_name, {})
            schema_type = referenced_schema.get("type")

            # Primitive types (including string enums) use 'body' with the base type
            if schema_type in ("string", "integer", "number", "boolean"):
                return "body", schema_type, is_required

            # Complex types use the schema name
            type_name = schema_to_type_name(raw_name, add_model_prefix=False)
            param_name = type_name[0].lower() + type_name[1:]
            return param_name, type_name, is_required

        if schema.get("type") == "array":
            items = schema.get("items", {})
            if "$ref" in items:
                raw_item = items["$ref"].split("/")[-1]
                item_type = schema_to_type_name(raw_item, add_model_prefix=False)
                param_name = item_type[0].lower() + item_type[1:]
                return param_name, f"Array<{item_type}>", is_required

    return None, None, False


def group_operations_by_tag(
    paths: Dict[str, Any], spec: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """Group path operations by their tags, resolving parameter refs."""
    tag_operations: Dict[str, List[Dict[str, Any]]] = {}

    for path, path_item in paths.items():
        # Get path-level parameters and resolve refs
        path_level_params = path_item.get("parameters", [])
        resolved_path_params = [_resolve_parameter_ref(p, spec) for p in path_level_params]

        for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
            if method in path_item:
                operation = path_item[method].copy()
                tags = operation.get("tags", ["default"])

                # Merge path-level parameters with operation-level parameters
                operation_params = operation.get("parameters", [])
                resolved_op_params = [_resolve_parameter_ref(p, spec) for p in operation_params]

                # Merge: operation params override path params with same name
                merged_params = {}
                for p in resolved_path_params:
                    if p.get("name"):
                        merged_params[p["name"]] = p
                for p in resolved_op_params:
                    if p.get("name"):
                        merged_params[p["name"]] = p

                operation["parameters"] = list(merged_params.values())

                for tag in tags:
                    if tag not in tag_operations:
                        tag_operations[tag] = []

                    tag_operations[tag].append(
                        {
                            "path": path,
                            "http_method": method.upper(),
                            "operation": operation,
                        }
                    )

    return tag_operations


def _extract_api_data(
    tag: str,
    operations: List[Dict[str, Any]],
    spec: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Extract data needed to render an API class."""
    if registry is None:
        registry = {}

    methods = []

    for op in operations:
        path = op["path"]
        http_method = op["http_method"]
        operation = op["operation"]

        operation_id = operation.get("operationId", "")
        method_name = operation_id_to_method_name(operation_id)
        summary = operation.get("summary", "")
        description = operation.get("description", "")

        # Extract parameters
        parameters = operation.get("parameters", [])
        path_params = [p for p in parameters if p.get("in") == "path"]
        query_params = [p for p in parameters if p.get("in") == "query"]

        # Get all schemas for type resolution
        all_schemas = spec.get("components", {}).get("schemas", {})

        # Process path parameters
        path_param_data = []
        for p in path_params:
            param_name = p["name"]
            ts_type = _get_typescript_type_for_param(p, registry, all_schemas)
            path_param_data.append(
                {
                    "name": param_name,
                    "type": ts_type,
                    "required": True,
                    "description": p.get("description", ""),
                }
            )

        # Process query parameters
        query_param_data = []
        for p in query_params:
            param_name = p["name"]
            ts_name = _to_camel_case(param_name)
            ts_type = _get_typescript_type_for_param(p, registry, all_schemas)
            query_param_data.append(
                {
                    "original_name": param_name,
                    "ts_name": ts_name,
                    "type": ts_type,
                    "required": p.get("required", False),
                    "description": p.get("description", ""),
                }
            )

        # Extract request body
        body_param_name, body_param_type, body_required = _extract_request_body_info(
            operation, spec, registry
        )

        # Extract response type
        return_type = _extract_response_type(operation, registry, all_schemas)

        # Build all parameters list for method signature
        all_params = []
        for p in path_param_data:
            all_params.append(
                {
                    "name": p["name"],
                    "type": p["type"],
                    "required": True,
                    "description": p.get("description", ""),
                }
            )
        if body_param_name:
            all_params.append(
                {
                    "name": body_param_name,
                    "type": body_param_type,
                    "required": body_required,
                    "description": "",
                }
            )
        for p in query_param_data:
            all_params.append(
                {
                    "name": p["ts_name"],
                    "type": p["type"],
                    "required": p["required"],
                    "description": p.get("description", ""),
                }
            )

        methods.append(
            {
                "method_name": method_name,
                "summary": summary,
                "description": description,
                "http_method": http_method,
                "path": path,
                "path_params": path_param_data,
                "query_params": query_param_data,
                "has_body": body_param_name is not None,
                "body_param_name": body_param_name,
                "body_param_type": body_param_type,
                "body_required": body_required,
                "return_type": return_type,
                "all_params": all_params,
                "has_required_params": any(p["required"] for p in all_params),
            }
        )

    # Sort methods alphabetically
    methods.sort(key=lambda m: m["method_name"])

    return {
        "class_name": _tag_to_api_class_name(tag),
        "methods": methods,
    }


def generate_api_ts(
    spec: Dict[str, Any],
    output_path: Path,
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """
    Generate api.ts file containing all models and API classes.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write api.ts to
        registry: Extraction registry for titled anyOf schemas
    """
    if registry is None:
        registry = create_extraction_registry(spec)

    env = _get_template_env()
    template = env.get_template("api.ts.j2")

    # Extract API metadata
    info = spec.get("info", {})
    api_title = info.get("title", "")
    api_description = info.get("description", "")
    api_version = info.get("version", "")

    # Extract models (now returns interfaces and enums separately)
    interfaces, enums = _extract_models(spec, registry)

    # Extract API classes
    paths = spec.get("paths", {})
    tag_operations = group_operations_by_tag(paths, spec)

    api_classes = []
    for tag in sorted(tag_operations.keys()):
        api_data = _extract_api_data(tag, tag_operations[tag], spec, registry)
        api_classes.append(api_data)

    # Render template
    content = template.render(
        api_title=api_title,
        api_description=api_description,
        api_version=api_version,
        models=interfaces,
        enums=enums,
        api_classes=api_classes,
    )

    # Write the output file
    (output_path / "api.ts").write_text(content)

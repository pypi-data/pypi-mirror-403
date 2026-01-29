"""Generate api.ts for axios client - contains all models and API classes."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, PackageLoader

from openapi_ts_client.generators.shared import (
    create_extraction_registry,
)
from openapi_ts_client.utils.naming import operation_id_to_method_name


def _get_template_env() -> Environment:
    """Get Jinja2 environment with axios templates loaded."""
    return Environment(
        loader=PackageLoader("openapi_ts_client", "templates/axios"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


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
) -> str:
    """
    Map OpenAPI schema to TypeScript type for axios interfaces.

    Unlike fetch, axios doesn't use FromJSON/ToJSON so we just need simple types.
    """
    if registry is None:
        registry = {}

    if not schema:
        return "any"

    # Handle $ref
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]

    # Handle anyOf (commonly used for nullable types)
    if "anyOf" in schema:
        non_null_schemas = [s for s in schema["anyOf"] if s.get("type") != "null"]
        has_null = any(s.get("type") == "null" for s in schema["anyOf"])

        if non_null_schemas:
            ts_type = _map_openapi_type_to_ts(non_null_schemas[0], registry)
            if has_null:
                return f"{ts_type} | null"
            return ts_type

        return "any"

    schema_type = schema.get("type")

    # Handle arrays
    if schema_type == "array":
        items = schema.get("items", {})
        item_type = _map_openapi_type_to_ts(items, registry)
        return f"Array<{item_type}>"

    # Handle object with additionalProperties
    if schema_type == "object" and "additionalProperties" in schema:
        additional = schema["additionalProperties"]
        if additional and isinstance(additional, dict):
            value_type = _map_openapi_type_to_ts(additional, registry)
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
) -> List[Dict[str, Any]]:
    """
    Extract model information from OpenAPI schemas.

    Args:
        spec: OpenAPI specification dict
        registry: Extraction registry for titled anyOf schemas

    Returns:
        List of model info dicts for template rendering
    """
    if registry is None:
        registry = {}

    schemas = spec.get("components", {}).get("schemas", {})
    models = []

    for schema_name, schema in schemas.items():
        properties_schema = schema.get("properties", {})
        required_props = schema.get("required", [])

        properties = []
        for prop_name, prop_schema in properties_schema.items():
            is_required = prop_name in required_props
            ts_type = _map_openapi_type_to_ts(prop_schema, registry)

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

        models.append(
            {
                "name": schema_name,
                "description": schema.get("description", ""),
                "properties": properties,
            }
        )

    return models


def _get_typescript_type_for_param(
    param: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """Get TypeScript type for a parameter schema."""
    schema = param.get("schema", {})

    # Handle anyOf patterns (nullable types)
    if "anyOf" in schema:
        non_null_types = [s for s in schema["anyOf"] if s.get("type") != "null"]
        has_null = any(s.get("type") == "null" for s in schema["anyOf"])
        if non_null_types:
            ts_type = _map_openapi_type_to_ts(non_null_types[0], registry)
            if has_null:
                return f"{ts_type} | null"
            return ts_type

    return _map_openapi_type_to_ts(schema, registry)


def _extract_response_type(
    operation: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """Extract response type from operation responses."""
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
                return _map_openapi_type_to_ts(schema, registry)

    if "204" in responses:
        return "void"

    return "any"


def _extract_request_body_info(
    operation: Dict[str, Any],
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
            type_name = schema["$ref"].split("/")[-1]
            param_name = type_name[0].lower() + type_name[1:]
            return param_name, type_name, is_required

        if schema.get("type") == "array":
            items = schema.get("items", {})
            if "$ref" in items:
                item_type = items["$ref"].split("/")[-1]
                param_name = item_type[0].lower() + item_type[1:]
                return param_name, f"Array<{item_type}>", is_required

    return None, None, False


def group_operations_by_tag(paths: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Group path operations by their tags."""
    tag_operations: Dict[str, List[Dict[str, Any]]] = {}

    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
            if method in path_item:
                operation = path_item[method]
                tags = operation.get("tags", ["default"])

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

        # Process path parameters
        path_param_data = []
        for p in path_params:
            param_name = p["name"]
            ts_type = _get_typescript_type_for_param(p, registry)
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
            ts_type = _get_typescript_type_for_param(p, registry)
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
            operation, registry
        )

        # Extract response type
        return_type = _extract_response_type(operation, registry)

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

    # Extract models
    models = _extract_models(spec, registry)

    # Extract API classes
    paths = spec.get("paths", {})
    tag_operations = group_operations_by_tag(paths)

    api_classes = []
    for tag in sorted(tag_operations.keys()):
        api_data = _extract_api_data(tag, tag_operations[tag], registry)
        api_classes.append(api_data)

    # Render template
    content = template.render(
        api_title=api_title,
        api_description=api_description,
        api_version=api_version,
        models=models,
        api_classes=api_classes,
    )

    # Write the output file
    (output_path / "api.ts").write_text(content)

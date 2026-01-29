"""Generate Angular service classes from OpenAPI paths."""

import html
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from jinja2 import Environment, PackageLoader, select_autoescape

from openapi_ts_client.generators.angular.type_mapper import map_openapi_type_with_imports
from openapi_ts_client.utils.naming import (
    operation_id_to_method_name,
    schema_to_filename,
    tag_to_service_filename,
    tag_to_service_name,
)

# Strict mode reserved words that cannot be used as variable names
# Note: 'type' is a contextual keyword and CAN be used as a variable name
PARAM_RESERVED_WORDS = {
    "break",
    "case",
    "catch",
    "class",
    "const",
    "continue",
    "debugger",
    "default",
    "delete",
    "do",
    "else",
    "enum",
    "export",
    "extends",
    "false",
    "finally",
    "for",
    "function",
    "if",
    "import",
    "in",
    "instanceof",
    "new",
    "null",
    "return",
    "super",
    "switch",
    "this",
    "throw",
    "true",
    "try",
    "typeof",
    "var",
    "void",
    "while",
    "with",
    "yield",
    "let",
    "static",
    "implements",
    "interface",
    "package",
    "private",
    "protected",
    "public",
}


def _resolve_parameter_ref(param: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve a parameter $ref to its actual parameter definition.

    Args:
        param: Parameter object (may contain $ref)
        spec: Full OpenAPI spec for resolving refs

    Returns:
        Resolved parameter definition
    """
    if "$ref" not in param:
        return param

    ref = param["$ref"]
    # Parse ref path like "#/components/parameters/rowParam"
    if ref.startswith("#/"):
        parts = ref[2:].split("/")
        resolved = spec
        for part in parts:
            resolved = resolved.get(part, {})
        return resolved

    return param


def _resolve_schema_ref(schema: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve a schema $ref to its actual schema definition.

    Args:
        schema: Schema object (may contain $ref)
        spec: Full OpenAPI spec for resolving refs

    Returns:
        Resolved schema definition
    """
    if "$ref" not in schema:
        return schema

    ref = schema["$ref"]
    # Parse ref path like "#/components/schemas/coordinate"
    if ref.startswith("#/"):
        parts = ref[2:].split("/")
        resolved = spec
        for part in parts:
            resolved = resolved.get(part, {})
        return resolved

    return schema


def _escape_description(text: str) -> str:
    """Escape HTML entities in description text, matching OpenAPI Generator output."""
    # First apply standard HTML escaping
    escaped = html.escape(text)
    # Also escape = as &#x3D; to match OpenAPI Generator
    escaped = escaped.replace("=", "&#x3D;")
    return escaped


def _schema_to_filename_filter(name: str) -> str:
    """Jinja2 filter to convert schema name to filename without .ts extension."""
    filename = schema_to_filename(name)
    return filename[:-3] if filename.endswith(".ts") else filename


def get_template_env() -> Environment:
    """Get Jinja2 environment with templates loaded."""
    env = Environment(
        loader=PackageLoader("openapi_ts_client", "templates/angular"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["schema_to_filename_filter"] = _schema_to_filename_filter
    return env


def _to_camel_case(name: str) -> str:
    """Convert snake_case or kebab-case to camelCase."""
    # Split by underscore or hyphen
    parts = re.split(r"[_-]", name)
    if not parts:
        return name
    # First part lowercase, rest title case
    return parts[0] + "".join(word.title() for word in parts[1:])


def _to_param_name(name: str) -> str:
    """Convert parameter name to TypeScript-safe variable name.

    Converts snake_case to camelCase and escapes reserved words.
    """
    camel = _to_camel_case(name)
    if camel in PARAM_RESERVED_WORDS:
        return f"_{camel}"
    return camel


def _extract_path_params(path: str) -> List[str]:
    """Extract path parameter names from a path template."""
    return re.findall(r"\{(\w+)\}", path)


def _get_typescript_type_for_param(param: Dict[str, Any]) -> Tuple[str, Set[str]]:
    """Get TypeScript type for a parameter schema."""
    schema = param.get("schema", {})

    # Handle anyOf patterns (nullable types)
    if "anyOf" in schema:
        non_null_types = [s for s in schema["anyOf"] if s.get("type") != "null"]
        if non_null_types:
            return map_openapi_type_with_imports(non_null_types[0])

    return map_openapi_type_with_imports(schema)


def _build_path_template(path: str, path_params: List[Dict[str, Any]]) -> str:
    """Build the path template string for the service method."""
    result = path

    for param in path_params:
        name = param["name"]
        schema = param.get("schema", {})
        data_type = "number" if schema.get("type") in ("integer", "number") else "string"
        data_format = schema.get("format")

        # Replace {name} with template expression
        placeholder = f"{{{name}}}"
        data_format_str = f'"{data_format}"' if data_format else "undefined"
        replacement = (
            f'${{this.configuration.encodeParam({{name: "{name}", value: {name}, '
            f'in: "path", style: "simple", explode: false, '
            f'dataType: "{data_type}", dataFormat: {data_format_str}}})}}'
        )
        result = result.replace(placeholder, replacement)

    return result


def _extract_response_type(operation: Dict[str, Any]) -> Tuple[str, Set[str]]:
    """Extract the response type from operation responses."""
    responses = operation.get("responses", {})

    # Look for 200 or 201 response
    for status in ["200", "201"]:
        if status in responses:
            response = responses[status]
            content = response.get("content", {})

            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                return map_openapi_type_with_imports(schema)

            # Handle binary response types (e.g., application/pdf, application/octet-stream)
            for _content_type, content_info in content.items():
                schema = content_info.get("schema", {})
                if schema.get("type") == "string" and schema.get("format") == "binary":
                    return "Blob", set()

    return "any", set()


def _extract_request_body_info(
    operation: Dict[str, Any],
    spec: Dict[str, Any] = None,
) -> Tuple[Optional[str], Optional[str], Set[str], List[str], bool, str]:
    """Extract request body parameter name, type, imports, content types, required flag, and description."""
    if spec is None:
        spec = {}

    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    is_required = request_body.get("required", False)
    description = request_body.get("description", "")

    # Get all content types
    content_types = list(content.keys())

    if not content_types:
        return None, None, set(), [], False, ""

    # Find a schema to determine the type (prefer application/json)
    schema = None
    for ct in ["application/json", "application/xml", "application/x-www-form-urlencoded"]:
        if ct in content:
            schema = content[ct].get("schema", {})
            break

    if schema:
        # Handle $ref
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            # Check if the referenced schema is a primitive type
            # If so, use 'body' as parameter name and the underlying type
            referenced_schema = spec.get("components", {}).get("schemas", {}).get(ref_name, {})
            schema_type = referenced_schema.get("type")

            # Primitive types (including string enums) use 'body' with the base type
            if schema_type in ("string", "integer", "number", "boolean"):
                return "body", schema_type, set(), content_types, is_required, description

            # Complex types use the schema name
            type_name = ref_name
            # Convert to camelCase for parameter name
            param_name = type_name[0].lower() + type_name[1:]
            return param_name, type_name, {type_name}, content_types, is_required, description

        # Handle array type
        if schema.get("type") == "array":
            items = schema.get("items", {})
            if "$ref" in items:
                item_type = items["$ref"].split("/")[-1]
                # Use the item type name for parameter (lowercase first char)
                param_name = item_type[0].lower() + item_type[1:]
                return (
                    param_name,
                    f"Array<{item_type}>",
                    {item_type},
                    content_types,
                    is_required,
                    description,
                )

    # Handle octet-stream (binary) body
    if "application/octet-stream" in content:
        return "body", "Blob", set(), content_types, is_required, description

    return None, None, set(), content_types, False, ""


def _extract_accept_types(operation: Dict[str, Any]) -> List[str]:
    """Extract Accept content types from responses."""
    responses = operation.get("responses", {})

    for status in ["200", "201"]:
        if status in responses:
            response = responses[status]
            content = response.get("content", {})
            return list(content.keys())

    return []


def extract_service_data(
    tag: str,
    operations: List[Dict[str, Any]],
    api_title: str,
    contact_email: str,
    spec: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Extract data needed to render a service template.

    Args:
        tag: The OpenAPI tag name
        operations: List of operations for this tag
        api_title: API title for header comment
        contact_email: Contact email for header comment
        spec: Full OpenAPI spec for resolving refs

    Returns:
        Dictionary with template data
    """
    if spec is None:
        spec = {}
    model_imports: Set[str] = set()
    methods: List[Dict[str, Any]] = []

    for op in operations:
        path = op["path"]
        http_method = op["http_method"]
        operation = op["operation"]
        path_level_params = op.get("path_level_params", [])

        operation_id = operation.get("operationId", "")
        method_name = operation_id_to_method_name(operation_id)
        summary = operation.get("summary", "")
        description = _escape_description(operation.get("description", ""))

        # Extract parameters - merge path-level params with operation-level params
        # Operation-level params override path-level params with the same name
        operation_params = operation.get("parameters", [])
        operation_param_names = {p.get("name") for p in operation_params}
        # Add path-level params that aren't overridden by operation-level params
        parameters = list(operation_params)
        for p in path_level_params:
            if p.get("name") not in operation_param_names:
                parameters.append(p)

        path_params = [p for p in parameters if p.get("in") == "path"]
        query_params = [p for p in parameters if p.get("in") == "query"]
        header_params = [p for p in parameters if p.get("in") == "header"]

        # Extract security requirements
        security = operation.get("security", [])
        auth_methods = []
        for sec in security:
            for scheme_name in sec.keys():
                # Determine auth type based on scheme name (simplified)
                if scheme_name == "api_key":
                    auth_methods.append(
                        {
                            "name": scheme_name,
                            "type": "apiKey",
                            "header_name": "api_key",
                            "prefix": "",
                        }
                    )
                else:
                    # Assume oauth2 for other schemes
                    auth_methods.append(
                        {
                            "name": scheme_name,
                            "type": "oauth2",
                            "header_name": "Authorization",
                            "prefix": "Bearer ",
                        }
                    )

        # Build required params list (path params are always required)
        required_params = []
        for p in path_params:
            ts_type, imports = _get_typescript_type_for_param(p)
            model_imports.update(imports)
            required_params.append(
                {
                    "name": p["name"],
                    "type": ts_type,
                    "description": p.get("description", ""),
                }
            )

        # Handle request body
        (
            body_param_name,
            body_param_type,
            body_imports,
            content_types,
            body_is_required,
            body_description,
        ) = _extract_request_body_info(operation, spec)
        model_imports.update(body_imports)

        if body_param_name and body_is_required:
            required_params.append(
                {
                    "name": body_param_name,
                    "type": body_param_type,
                    "description": body_description,
                }
            )

        # Add required query params to required_params for validation
        for p in query_params:
            if p.get("required", False):
                ts_type, imports = _get_typescript_type_for_param(p)
                model_imports.update(imports)
                required_params.append(
                    {
                        "name": p["name"],
                        "type": ts_type,
                        "description": p.get("description", ""),
                    }
                )

        # Extract response type
        return_type, return_imports = _extract_response_type(operation)
        model_imports.update(return_imports)

        # Build path template
        path_template = _build_path_template(path, path_params)

        # Build accept types
        accept_list = _extract_accept_types(operation)
        if accept_list:
            accept_types = "'" + "' | '".join(accept_list) + "'"
        else:
            accept_types = "undefined"

        # Build header params data
        header_param_data = []
        for p in header_params:
            ts_type, imports = _get_typescript_type_for_param(p)
            model_imports.update(imports)
            param_name = _to_camel_case(p["name"])
            header_param_data.append(
                {
                    "name": param_name,  # camelCase for variable
                    "header_name": p["name"],  # original for HTTP header
                    "type": ts_type,
                    "required": p.get("required", False),
                    "description": p.get("description", ""),
                }
            )

        # Build parameter signatures
        all_params = []

        # Path parameters first
        for p in path_params:
            ts_type, _ = _get_typescript_type_for_param(p)
            all_params.append(
                {
                    "name": p["name"],
                    "type": ts_type,
                    "required": True,
                    "description": p.get("description", ""),
                }
            )

        # Header parameters next (optional)
        for p in header_params:
            ts_type, _ = _get_typescript_type_for_param(p)
            param_name = _to_camel_case(p["name"])
            all_params.append(
                {
                    "name": param_name,  # camelCase for variable
                    "type": ts_type,
                    "required": p.get("required", False),
                    "description": p.get("description", ""),
                }
            )

        # Query parameters next (optional)
        for p in query_params:
            ts_type, imports = _get_typescript_type_for_param(p)
            model_imports.update(imports)
            all_params.append(
                {
                    "name": _to_param_name(p["name"]),
                    "type": ts_type,
                    "required": p.get("required", False),
                    "description": p.get("description", ""),
                }
            )

        # Request body last
        if body_param_name:
            all_params.append(
                {
                    "name": body_param_name,
                    "type": body_param_type,
                    "required": body_is_required,
                    "description": body_description,
                }
            )

        # Build signature strings
        sig_parts = []
        for p in all_params:
            optional = "?" if not p["required"] else ""
            sig_parts.append(f"{p['name']}{optional}: {p['type']}")

        params_signature = ", ".join(sig_parts)
        if params_signature:
            params_signature += ", "

        # Query params for method
        query_param_data = []
        for p in query_params:
            ts_type, _ = _get_typescript_type_for_param(p)
            query_param_data.append(
                {
                    "name": _to_param_name(p["name"]),  # TypeScript variable name
                    "original_name": p["name"],  # HTTP query parameter name
                    "type": ts_type,
                }
            )

        methods.append(
            {
                "method_name": method_name,
                "summary": summary,
                "description": description,
                "http_method": http_method,
                "path": path,
                "path_template": path_template,
                "parameters": all_params,
                "required_params": required_params,
                "query_params": query_param_data,
                "header_params": header_param_data,
                "auth_methods": auth_methods,
                "has_body": body_param_name is not None,
                "body_param_name": body_param_name,
                "content_types": content_types,
                "return_type": return_type,
                "accept_types": accept_types,
                "accept_list": accept_list,
                "params_signature_body": params_signature,
                "params_signature_response": params_signature,
                "params_signature_events": params_signature,
                "params_signature_impl": params_signature,
            }
        )

    # Sort methods alphabetically by method_name
    methods.sort(key=lambda m: m["method_name"])

    return {
        "api_title": api_title,
        "contact_email": contact_email,
        "service_name": tag_to_service_name(tag),
        "model_imports": model_imports,
        "methods": methods,
    }


def generate_service(
    tag: str,
    operations: List[Dict[str, Any]],
    api_title: str,
    contact_email: str,
    spec: Dict[str, Any] = None,
) -> str:
    """
    Generate TypeScript service code for a tag.

    Args:
        tag: The OpenAPI tag name
        operations: List of operations for this tag
        api_title: API title for header comment
        contact_email: Contact email for header comment
        spec: Full OpenAPI spec for resolving refs

    Returns:
        Generated TypeScript code as string
    """
    if spec is None:
        spec = {}

    env = get_template_env()
    template = env.get_template("service.ts.j2")

    data = extract_service_data(tag, operations, api_title, contact_email, spec)

    return template.render(**data)


def group_operations_by_tag(
    paths: Dict[str, Any], spec: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group path operations by their tags.

    Args:
        paths: OpenAPI paths object
        spec: Full OpenAPI spec for resolving refs

    Returns:
        Dictionary mapping tag names to list of operations
    """
    tag_operations: Dict[str, List[Dict[str, Any]]] = {}

    for path, path_item in paths.items():
        # Get path-level parameters (shared by all methods)
        path_level_params = path_item.get("parameters", [])
        # Resolve $ref in path-level parameters
        resolved_path_params = [_resolve_parameter_ref(p, spec) for p in path_level_params]
        # Also resolve schema $refs inside parameters
        for param in resolved_path_params:
            if "schema" in param and "$ref" in param.get("schema", {}):
                param["schema"] = _resolve_schema_ref(param["schema"], spec)

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
                            "http_method": method,
                            "operation": operation,
                            "path_level_params": resolved_path_params,
                        }
                    )

    return tag_operations


def generate_all_services(
    paths: Dict[str, Any],
    output_path: Path,
    api_title: str,
    contact_email: str,
    spec: Dict[str, Any] = None,
) -> List[str]:
    """
    Generate all service files from OpenAPI paths.

    Args:
        paths: OpenAPI paths object
        output_path: Directory to write service files
        api_title: API title for header comments
        contact_email: Contact email for header comments
        spec: Full OpenAPI spec for resolving refs

    Returns:
        List of generated service class names
    """
    if spec is None:
        spec = {}

    env = get_template_env()
    service_names = []

    tag_operations = group_operations_by_tag(paths, spec)

    for tag, operations in sorted(tag_operations.items()):
        service_name = tag_to_service_name(tag)
        service_names.append(service_name)

        content = generate_service(tag, operations, api_title, contact_email, spec)
        filename = tag_to_service_filename(tag)
        (output_path / filename).write_text(content)

    # Generate barrel export (api.ts)
    api_template = env.get_template("api.ts.j2")
    api_content = api_template.render(
        services=[
            {
                "name": tag_to_service_name(tag),
                "filename": tag_to_service_filename(tag)[:-3],  # Remove .ts
            }
            for tag in sorted(tag_operations.keys(), key=tag_to_service_filename)
        ]
    )
    (output_path / "api.ts").write_text(api_content)

    return service_names

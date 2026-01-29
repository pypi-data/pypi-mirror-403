"""Generate API class files for fetch client."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from jinja2 import Environment, PackageLoader, select_autoescape

from openapi_ts_client.generators.shared import map_openapi_type_with_imports
from openapi_ts_client.utils.naming import operation_id_to_method_name, schema_to_type_name

# TypeScript reserved words that need escaping as method/param names
TYPESCRIPT_RESERVED_WORDS = {
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


def get_template_env() -> Environment:
    """Get Jinja2 environment with templates loaded."""
    env = Environment(
        loader=PackageLoader("openapi_ts_client", "templates/fetch"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def _to_camel_case(name: str) -> str:
    """Convert snake_case or kebab-case to camelCase."""
    parts = re.split(r"[_-]", name)
    if not parts:
        return name
    return parts[0] + "".join(word.title() for word in parts[1:])


def _escape_reserved(name: str) -> str:
    """Escape TypeScript reserved words by prefixing with underscore."""
    if name in TYPESCRIPT_RESERVED_WORDS:
        return f"_{name}"
    return name


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


def _get_typescript_type_for_param(
    param: Dict[str, Any],
    method_name: str = "",
    param_name: str = "",
) -> Tuple[str, Set[str], Optional[Dict[str, Any]]]:
    """
    Get TypeScript type for a parameter schema.

    Returns:
        Tuple of (ts_type, imports, enum_info)
        enum_info is None if not an enum, otherwise dict with name and values
    """
    schema = param.get("schema", {})

    # Handle anyOf patterns (nullable types)
    if "anyOf" in schema:
        non_null_types = [s for s in schema["anyOf"] if s.get("type") != "null"]
        has_null = any(s.get("type") == "null" for s in schema["anyOf"])
        if non_null_types:
            ts_type, imports = map_openapi_type_with_imports(non_null_types[0])
            if has_null:
                ts_type = f"{ts_type} | null"
            return ts_type, imports, None

    # Check for enum in string schema
    if schema.get("type") == "string" and "enum" in schema:
        # Generate enum name: MethodNameParamNameEnum
        # e.g., findPetsByStatus + status -> FindPetsByStatusStatusEnum
        cap_method = method_name[0].upper() + method_name[1:] if method_name else ""
        cap_param = param_name[0].upper() + param_name[1:] if param_name else ""
        enum_name = f"{cap_method}{cap_param}Enum"
        enum_values = schema["enum"]
        enum_info = {
            "name": enum_name,
            "enum_values": enum_values,
        }
        return enum_name, set(), enum_info

    ts_type, imports = map_openapi_type_with_imports(schema)
    return ts_type, imports, None


def _extract_response_info(
    operation: Dict[str, Any],
) -> Tuple[str, Set[str], bool, bool, bool, Optional[str], Optional[str]]:
    """
    Extract response type info from operation responses.

    Returns:
        Tuple of (return_type, imports, is_primitive, is_array, is_blob, item_type, deserializer)
    """
    responses = operation.get("responses", {})

    # Look for 200, 201, or 204 response
    for status in ["200", "201"]:
        if status in responses:
            response = responses[status]
            content = response.get("content", {})

            # If there's no content, this is a void response
            if not content:
                return "void", set(), False, False, False, None, None

            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                return _schema_to_response_info(schema)

            # Check for binary content types (application/pdf, application/octet-stream, etc.)
            for _content_type, content_info in content.items():
                schema = content_info.get("schema", {})
                if schema.get("type") == "string" and schema.get("format") == "binary":
                    return "Blob", set(), False, False, True, None, None

    # Check for 204 No Content
    if "204" in responses:
        return "void", set(), False, False, False, None, None

    return "any", set(), False, False, False, None, None


def _schema_to_response_info(
    schema: Dict[str, Any],
) -> Tuple[str, Set[str], bool, bool, bool, Optional[str], Optional[str]]:
    """
    Convert a schema to response info.

    Returns:
        Tuple of (return_type, imports, is_primitive, is_array, is_blob, item_type, deserializer)
    """
    if not schema:
        return "any", set(), False, False, False, None, None

    # Handle $ref
    if "$ref" in schema:
        raw_name = schema["$ref"].split("/")[-1]
        type_name = schema_to_type_name(raw_name)
        return type_name, {type_name}, False, False, False, None, f"{type_name}FromJSON"

    # Handle array type
    if schema.get("type") == "array":
        items = schema.get("items", {})
        if "$ref" in items:
            raw_item = items["$ref"].split("/")[-1]
            item_type = schema_to_type_name(raw_item)
            return (
                f"Array<{item_type}>",
                {item_type},
                False,
                True,
                False,
                item_type,
                f"{item_type}FromJSON",
            )
        else:
            item_ts_type, item_imports = map_openapi_type_with_imports(items)
            return f"Array<{item_ts_type}>", item_imports, True, True, False, item_ts_type, None

    # Handle object with additionalProperties (map type)
    if schema.get("type") == "object" and "additionalProperties" in schema:
        additional = schema["additionalProperties"]
        if additional:
            value_type, value_imports = map_openapi_type_with_imports(additional)
            return (
                f"{{ [key: string]: {value_type}; }}",
                value_imports,
                False,
                False,
                False,
                None,
                None,
            )

    # Handle primitive types
    schema_type = schema.get("type")
    if schema_type in ("string", "integer", "number", "boolean"):
        type_map = {
            "string": "string",
            "integer": "number",
            "number": "number",
            "boolean": "boolean",
        }
        ts_type = type_map.get(schema_type, "any")
        return ts_type, set(), True, False, False, None, None

    return "any", set(), False, False, False, None, None


def _extract_request_body_info(
    operation: Dict[str, Any],
    spec: Dict[str, Any] = None,
) -> Tuple[Optional[str], Optional[str], Set[str], bool, bool, Optional[str], Optional[str]]:
    """
    Extract request body parameter name, type, imports, required flag, and serializer.

    Args:
        operation: Operation object
        spec: Full OpenAPI spec for resolving refs

    Returns:
        Tuple of (param_name, param_type, imports, is_required, is_array, serializer, content_type)
    """
    if spec is None:
        spec = {}

    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    is_required = request_body.get("required", False)

    if not content:
        return None, None, set(), False, False, None, None

    # Check for binary/octet-stream content
    if "application/octet-stream" in content:
        schema = content["application/octet-stream"].get("schema", {})
        if schema.get("type") == "string" and schema.get("format") == "binary":
            return "body", "Blob", set(), is_required, False, None, "application/octet-stream"

    # Find schema (prefer application/json)
    schema = None
    if "application/json" in content:
        schema = content["application/json"].get("schema", {})

    if not schema:
        return None, None, set(), False, False, None, None

    # Handle $ref
    if "$ref" in schema:
        raw_name = schema["$ref"].split("/")[-1]

        # Check if the referenced schema is a primitive type
        # If so, use 'body' as parameter name and the underlying type
        referenced_schema = spec.get("components", {}).get("schemas", {}).get(raw_name, {})
        schema_type = referenced_schema.get("type")

        # Primitive types (including string enums) use 'body' with the base type
        if schema_type in ("string", "integer", "number", "boolean"):
            return (
                "body",
                schema_type,
                set(),
                is_required,
                False,
                None,  # No serializer for primitives
                "application/json",
            )

        # Complex types use the schema name
        type_name = schema_to_type_name(raw_name)
        param_name = type_name[0].lower() + type_name[1:]
        return (
            param_name,
            type_name,
            {type_name},
            is_required,
            False,
            f"{type_name}ToJSON",
            "application/json",
        )

    # Handle array type
    if schema.get("type") == "array":
        items = schema.get("items", {})
        if "$ref" in items:
            raw_item = items["$ref"].split("/")[-1]
            item_type = schema_to_type_name(raw_item)
            param_name = item_type[0].lower() + item_type[1:]
            return (
                param_name,
                f"Array<{item_type}>",
                {item_type},
                is_required,
                True,
                f"{item_type}ToJSON",
                "application/json",
            )

    return None, None, set(), False, False, None, None


def _extract_security_info(
    operation: Dict[str, Any],
    security_schemes: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extract security requirements for an operation.

    Returns a list of security items, each with:
        - type: 'oauth2', 'apiKey', 'http', etc.
        - name: the security scheme name
        - scopes: list of required scopes (for OAuth)
        - header_name: header name for apiKey types
        - scheme: 'bearer' or 'basic' for http types

    Items are returned in the order they appear in the security requirement.
    """
    security_reqs = operation.get("security", [])
    items = []

    for req in security_reqs:
        for scheme_name, scopes in req.items():
            scheme = security_schemes.get(scheme_name, {})
            scheme_type = scheme.get("type", "")

            if scheme_type == "http":
                http_scheme = scheme.get("scheme", "").lower()
                if http_scheme == "bearer":
                    items.append(
                        {
                            "type": "http",
                            "name": scheme_name,
                            "scheme": "bearer",
                        }
                    )
            elif scheme_type == "oauth2":
                items.append(
                    {
                        "type": "oauth2",
                        "name": scheme_name,
                        "scopes": scopes,
                    }
                )
            elif scheme_type == "apiKey":
                in_location = scheme.get("in", "header")
                if in_location == "header":
                    items.append(
                        {
                            "type": "apiKey",
                            "name": scheme_name,
                            "header_name": scheme.get("name", scheme_name),
                        }
                    )

    return items


def _build_request_interface_name(
    method_name: str, api_class_name: str = "", use_prefix: bool = True
) -> str:
    """
    Build the request interface name from method name and API class name.

    Prefixes with API class name to avoid collisions when multiple APIs
    have operations with the same name (e.g., clone, create, delete).

    When there's only one API (single tag), the prefix is not used for cleaner
    interface names.

    Args:
        method_name: The method name
        api_class_name: The API class name
        use_prefix: If True, prefix with API class name (default for multi-tag specs)
                   If False, use simple names (for single-tag specs)

    Examples:
        method=listAll, api=DBMetricsApi, use_prefix=True -> DBMetricsApiListAllRequest
        method=getSquare, api=GameplayApi, use_prefix=False -> GetSquareRequest
    """
    # Strip leading underscore if present
    name = method_name.lstrip("_")
    # Capitalize first letter, keep rest as-is to preserve camelCase internal caps
    method_part = name[0].upper() + name[1:] + "Request"
    if api_class_name and use_prefix:
        return f"{api_class_name}{method_part}"
    return method_part


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
                            "http_method": method.upper(),
                            "operation": operation,
                            "path_level_params": resolved_path_params,
                        }
                    )

    return tag_operations


def extract_api_data(
    tag: str,
    operations: List[Dict[str, Any]],
    api_title: str,
    api_description: str,
    api_version: str,
    contact_email: str,
    security_schemes: Optional[Dict[str, Any]] = None,
    spec: Optional[Dict[str, Any]] = None,
    use_api_prefix: bool = True,
) -> Dict[str, Any]:
    """
    Extract data needed to render an API class template.

    Args:
        tag: The OpenAPI tag name
        operations: List of operations for this tag
        api_title: API title for header comment
        api_description: API description for header comment
        api_version: API version for header comment
        contact_email: Contact email for header comment
        security_schemes: Security schemes from spec components
        spec: Full OpenAPI spec for resolving refs
        use_api_prefix: If True, prefix request interfaces with API class name

    Returns:
        Dictionary with template data
    """
    if security_schemes is None:
        security_schemes = {}
    if spec is None:
        spec = {}
    # Compute class name early so we can use it for request interface naming
    api_class_name = _tag_to_api_class_name(tag)
    model_imports: Set[str] = set()
    request_interfaces: List[Dict[str, Any]] = []
    methods: List[Dict[str, Any]] = []

    for op in operations:
        path = op["path"]
        http_method = op["http_method"]
        operation = op["operation"]
        path_level_params = op.get("path_level_params", [])

        operation_id = operation.get("operationId", "")
        method_name = operation_id_to_method_name(operation_id)
        summary = operation.get("summary", "")
        description = operation.get("description", "")

        # Extract security requirements
        security_info = _extract_security_info(operation, security_schemes)

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

        # Collect all params for request interface
        interface_params: List[Dict[str, Any]] = []
        validations: List[Dict[str, str]] = []
        enum_defs: List[Dict[str, Any]] = []

        # Path parameters - always required
        for p in path_params:
            param_name = p["name"]
            ts_type, imports, enum_info = _get_typescript_type_for_param(p, method_name, param_name)
            model_imports.update(imports)
            if enum_info:
                enum_defs.append(enum_info)
            interface_params.append(
                {
                    "name": param_name,
                    "type": ts_type,
                    "required": True,
                }
            )
            validations.append({"param": param_name})

        # Query parameters
        query_param_data = []
        for p in query_params:
            original_name = p["name"]
            # Convert to camelCase for TypeScript interface
            ts_name = _to_camel_case(original_name)
            # Handle reserved words for query params like "package" -> "_package"
            if ts_name in TYPESCRIPT_RESERVED_WORDS:
                ts_name = f"_{ts_name}"
            ts_type, imports, enum_info = _get_typescript_type_for_param(p, method_name, ts_name)
            model_imports.update(imports)
            if enum_info:
                enum_defs.append(enum_info)
            interface_params.append(
                {
                    "name": ts_name,
                    "type": ts_type,
                    "required": p.get("required", False),
                }
            )
            query_param_data.append(
                {
                    "original_name": original_name,
                    "ts_name": ts_name,
                }
            )
            if p.get("required", False):
                validations.append({"param": ts_name})

        # Header parameters
        header_param_data = []
        for p in header_params:
            original_name = p["name"]
            # Convert to camelCase for TypeScript interface
            ts_name = _to_camel_case(original_name)
            # Handle reserved words
            if ts_name in TYPESCRIPT_RESERVED_WORDS:
                ts_name = f"_{ts_name}"
            ts_type, imports, enum_info = _get_typescript_type_for_param(p, method_name, ts_name)
            model_imports.update(imports)
            if enum_info:
                enum_defs.append(enum_info)
            interface_params.append(
                {
                    "name": ts_name,
                    "type": ts_type,
                    "required": p.get("required", False),
                }
            )
            header_param_data.append(
                {
                    "original_name": original_name,
                    "ts_name": ts_name,
                }
            )
            if p.get("required", False):
                validations.append({"param": ts_name})

        # Request body
        (
            body_param_name,
            body_param_type,
            body_imports,
            body_required,
            body_is_array,
            body_serializer,
            body_content_type,
        ) = _extract_request_body_info(operation, spec)
        model_imports.update(body_imports)

        has_body = body_param_name is not None
        is_binary_body = body_content_type == "application/octet-stream"
        body_serializer_expr = None
        if has_body:
            interface_params.append(
                {
                    "name": body_param_name,
                    "type": body_param_type,
                    "required": body_required,
                }
            )
            if body_required:
                validations.append({"param": body_param_name})

            # Build serializer expression
            if is_binary_body:
                # Binary bodies are passed directly without serialization
                body_serializer_expr = f"requestParameters['{body_param_name}'] as any"
            elif body_serializer is None:
                # Primitive types don't need a serializer function
                body_serializer_expr = f"requestParameters['{body_param_name}'] as any"
            elif body_is_array:
                body_serializer_expr = (
                    f"requestParameters['{body_param_name}']!.map({body_serializer})"
                )
            else:
                body_serializer_expr = f"{body_serializer}(requestParameters['{body_param_name}'])"

        # Extract response type
        return_type, return_imports, is_primitive, is_array, is_blob, item_type, deserializer = (
            _extract_response_info(operation)
        )
        model_imports.update(return_imports)

        # Determine if we need a request interface
        has_request_params = len(interface_params) > 0
        has_all_optional = all(not p["required"] for p in interface_params)
        request_interface_name = None

        if has_request_params:
            request_interface_name = _build_request_interface_name(
                method_name, api_class_name, use_prefix=use_api_prefix
            )
            request_interfaces.append(
                {
                    "name": request_interface_name,
                    "params": interface_params,
                }
            )

        # Build path params data for URL replacement
        path_param_data = [{"name": p["name"]} for p in path_params]

        # Determine if return is a generic "any" that doesn't need conversion
        is_any_return = return_type in (
            "any",
            "{ [key: string]: number; }",
            "{ [key: string]: string; }",
        )
        if return_type.startswith("{ [key: string]:"):
            is_any_return = True

        methods.append(
            {
                "method_name": method_name,
                "summary": summary,
                "description": description,
                "http_method": http_method,
                "path": path,
                "path_params": path_param_data,
                "query_params": query_param_data,
                "header_params": header_param_data,
                "validations": validations,
                "has_body": has_body,
                "body_serializer": body_serializer_expr,
                "body_content_type": body_content_type,
                "has_request_params": has_request_params,
                "has_all_optional_params": has_all_optional,
                "request_interface": request_interface_name,
                "return_type": return_type,
                "return_deserializer": deserializer,
                "is_primitive_return": is_primitive,
                "is_array_return": is_array,
                "is_blob_return": is_blob,
                "is_any_return": is_any_return,
                "item_deserializer": deserializer if is_array else None,
                "enum_defs": enum_defs,
                "security": security_info,
            }
        )

    # Sort methods alphabetically
    methods.sort(key=lambda m: m["method_name"])

    # Sort request interfaces to match method order
    method_order = {
        m["request_interface"]: i for i, m in enumerate(methods) if m["request_interface"]
    }
    request_interfaces.sort(key=lambda r: method_order.get(r["name"], 999))

    return {
        "api_title": api_title,
        "api_description": api_description,
        "api_version": api_version,
        "contact_email": contact_email,
        "class_name": api_class_name,
        "class_description": "",
        "model_imports": model_imports,
        "request_interfaces": request_interfaces,
        "methods": methods,
    }


def generate_api(
    tag: str,
    operations: List[Dict[str, Any]],
    api_title: str,
    api_description: str,
    api_version: str,
    contact_email: str,
    security_schemes: Optional[Dict[str, Any]] = None,
    spec: Optional[Dict[str, Any]] = None,
    use_api_prefix: bool = True,
) -> str:
    """
    Generate TypeScript API class code for a tag.

    Args:
        tag: The OpenAPI tag name
        operations: List of operations for this tag
        api_title: API title for header comment
        api_description: API description for header comment
        api_version: API version for header comment
        contact_email: Contact email for header comment
        security_schemes: Security schemes from spec components
        spec: Full OpenAPI spec for resolving refs
        use_api_prefix: If True, prefix request interfaces with API class name

    Returns:
        Generated TypeScript code as string
    """
    env = get_template_env()
    template = env.get_template("api.ts.j2")

    data = extract_api_data(
        tag,
        operations,
        api_title,
        api_description,
        api_version,
        contact_email,
        security_schemes,
        spec,
        use_api_prefix,
    )

    return template.render(**data)


def generate_apis(spec: Dict[str, Any], output_path: Path) -> List[str]:
    """
    Generate API class files from OpenAPI paths.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write API files to

    Returns:
        List of generated API class names
    """
    env = get_template_env()
    api_names: List[str] = []

    # Extract API metadata
    info = spec.get("info", {})
    api_title = info.get("title", "API")
    api_description = info.get("description", "")
    api_version = info.get("version", "1.0.0")
    contact = info.get("contact", {})
    contact_email = contact.get("email", "")

    # Extract security schemes
    components = spec.get("components", {})
    security_schemes = components.get("securitySchemes", {})

    paths = spec.get("paths", {})
    tag_operations = group_operations_by_tag(paths, spec)

    # Determine if we should use API prefix for request interfaces
    # When there's only one API (single tag), use simple names for cleaner output
    use_api_prefix = len(tag_operations) > 1

    # Create apis subdirectory
    apis_dir = output_path / "apis"
    apis_dir.mkdir(parents=True, exist_ok=True)

    for tag, operations in sorted(tag_operations.items()):
        api_class_name = _tag_to_api_class_name(tag)
        api_names.append(api_class_name)

        content = generate_api(
            tag,
            operations,
            api_title,
            api_description,
            api_version,
            contact_email,
            security_schemes,
            spec,
            use_api_prefix,
        )
        filename = f"{api_class_name}.ts"
        (apis_dir / filename).write_text(content)

    # Generate barrel export (index.ts)
    # Sort alphabetically (case-sensitive) to match OpenAPI Generator output
    sorted_api_names = sorted(api_names)
    index_template = env.get_template("apis_index.ts.j2")
    index_content = index_template.render(api_names=sorted_api_names)
    (apis_dir / "index.ts").write_text(index_content)

    return api_names

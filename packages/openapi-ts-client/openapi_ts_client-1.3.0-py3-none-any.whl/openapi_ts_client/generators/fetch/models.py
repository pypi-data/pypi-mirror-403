"""Generate model files with serialization functions."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from jinja2 import Environment, PackageLoader, select_autoescape

from openapi_ts_client.generators.shared import (
    create_extraction_registry,
    map_openapi_type_with_imports,
)
from openapi_ts_client.utils import schema_to_type_name

# Reserved words that need escaping in TypeScript interface property names
INTERFACE_RESERVED_WORDS = {
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


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase and escape reserved words."""
    components = name.split("_")
    result = components[0] + "".join(x.title() for x in components[1:])
    # Escape reserved words
    if result in INTERFACE_RESERVED_WORDS:
        return f"_{result}"
    return result


def _get_property_info(
    prop_name: str,
    prop_schema: Dict[str, Any],
    required_props: List[str],
    model_name: str = "",
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Extract property information for template rendering.

    Args:
        prop_name: The JSON property name (may be snake_case)
        prop_schema: The OpenAPI schema for this property
        required_props: List of required property names
        model_name: The name of the model containing this property
        registry: Optional extraction registry for titled anyOf schemas

    Returns:
        Dictionary with property metadata for template
    """
    ts_name = _snake_to_camel(prop_name)
    is_required = prop_name in required_props

    # Check for enum in string schema
    enum_info = None
    if prop_schema.get("type") == "string" and "enum" in prop_schema:
        # Generate enum name: ModelNamePropertyNameEnum
        cap_prop = prop_name[0].upper() + prop_name[1:]
        enum_name = f"{model_name}{cap_prop}Enum"
        enum_values = prop_schema["enum"]
        enum_info = {
            "name": enum_name,
            "enum_values": enum_values,
        }
        ts_type = enum_name
        type_imports: Set[str] = set()
    else:
        ts_type, type_imports = map_openapi_type_with_imports(prop_schema, registry)

    # Determine if nullable (either explicit nullable or anyOf with null)
    is_nullable = prop_schema.get("nullable", False)
    if "anyOf" in prop_schema:
        is_nullable = any(s.get("type") == "null" for s in prop_schema["anyOf"])

    # For interface type annotation, handle nullable
    # If optional and nullable, use `type | null`
    # If required and nullable, use `type | null`
    # The `?` for optional is handled separately in the template
    ts_type_for_interface = ts_type

    # Determine the doc type (without | null for @type annotation)
    # For enum types, use 'string' as the doc type
    if enum_info:
        ts_type_doc = "string"
    else:
        ts_type_doc = ts_type.replace(" | null", "")

    # Detect if this is an array type
    is_array = prop_schema.get("type") == "array"
    array_item_type = None
    array_item_imports: Set[str] = set()
    if is_array:
        items_schema = prop_schema.get("items", {})
        array_item_type, array_item_imports = map_openapi_type_with_imports(items_schema, registry)

    # Detect if this is a nested object (non-primitive reference or extracted type)
    nested_type = None
    if "$ref" in prop_schema:
        nested_type = prop_schema["$ref"].split("/")[-1]
    elif "anyOf" in prop_schema:
        # Check for non-null types in anyOf that reference schemas
        for sub_schema in prop_schema["anyOf"]:
            if sub_schema.get("type") != "null" and "$ref" in sub_schema:
                nested_type = sub_schema["$ref"].split("/")[-1]
                break
        # Also check if this is an extracted type (titled anyOf mapped to a type)
        if nested_type is None and type_imports and not is_array:
            # If we have imports from a titled anyOf, use that as the nested type
            nested_type = list(type_imports)[0]

    # Detect date/date-time format (check top-level and inside anyOf)
    is_date = False
    is_date_time = False
    schema_format = prop_schema.get("format")
    if prop_schema.get("type") == "string":
        if schema_format == "date":
            is_date = True
        elif schema_format == "date-time":
            is_date_time = True
    elif "anyOf" in prop_schema:
        # Check if any non-null schema in anyOf has date/date-time format
        for sub_schema in prop_schema["anyOf"]:
            if sub_schema.get("type") == "string":
                sub_format = sub_schema.get("format")
                if sub_format == "date":
                    is_date = True
                    break
                elif sub_format == "date-time":
                    is_date_time = True
                    break

    # Build FromJSON expression
    from_json_expr = _build_from_json_expr(
        prop_name,
        ts_name,
        is_required,
        is_nullable,
        is_array,
        array_item_type,
        array_item_imports,
        nested_type,
        is_date,
        is_date_time,
        prop_schema,
    )

    # Build ToJSON expression
    to_json_expr = _build_to_json_expr(
        prop_name,
        ts_name,
        is_required,
        is_nullable,
        is_array,
        array_item_type,
        array_item_imports,
        nested_type,
        is_date,
        is_date_time,
        prop_schema,
    )

    return {
        "json_name": prop_name,
        "ts_name": ts_name,
        "ts_type": ts_type_for_interface,
        "ts_type_doc": ts_type_doc,
        "required": is_required,
        "nullable": is_nullable,
        "description": prop_schema.get("description", ""),
        "type_imports": type_imports,
        "from_json_expr": from_json_expr,
        "to_json_expr": to_json_expr,
        "is_array": is_array,
        "array_item_type": array_item_type,
        "nested_type": nested_type,
        "is_date": is_date,
        "is_date_time": is_date_time,
        "enum_info": enum_info,
    }


def _build_from_json_expr(
    json_name: str,
    ts_name: str,
    is_required: bool,
    is_nullable: bool,
    is_array: bool,
    array_item_type: Optional[str],
    array_item_imports: Set[str],
    nested_type: Optional[str],
    is_date: bool,
    is_date_time: bool,
    schema: Dict[str, Any],
) -> str:
    """Build the FromJSON expression for a property."""
    json_access = f"json['{json_name}']"

    # Handle arrays
    if is_array:
        if array_item_imports:
            # Array of complex types - need to map through FromJSON
            item_type = list(array_item_imports)[0]
            inner_expr = f"(({json_access} as Array<any>).map({item_type}FromJSON))"
        else:
            # Array of primitives - pass through
            inner_expr = json_access

        if not is_required:
            return f"{json_access} == null ? undefined : {inner_expr}"
        return inner_expr

    # Handle nested objects (non-array references)
    if nested_type:
        inner_expr = f"{nested_type}FromJSON({json_access})"
        if not is_required:
            return f"{json_access} == null ? undefined : {inner_expr}"
        return inner_expr

    # Handle dates
    # For optional dates, use null check. For required dates, use direct Date conversion.
    if is_date or is_date_time:
        inner_expr = f"(new Date({json_access}))"
        if not is_required:
            return f"{json_access} == null ? undefined : {inner_expr}"
        return inner_expr

    # Handle primitives
    # Only use null check for OPTIONAL properties, not for nullable required ones
    if not is_required:
        return f"{json_access} == null ? undefined : {json_access}"

    # Required primitive - direct access (even if nullable, the type handles it)
    return json_access


def _build_to_json_expr(
    json_name: str,
    ts_name: str,
    is_required: bool,
    is_nullable: bool,
    is_array: bool,
    array_item_type: Optional[str],
    array_item_imports: Set[str],
    nested_type: Optional[str],
    is_date: bool,
    is_date_time: bool,
    schema: Dict[str, Any],
) -> str:
    """Build the ToJSON expression for a property."""
    value_access = f"value['{ts_name}']"

    # Handle arrays
    if is_array:
        if array_item_imports:
            # Array of complex types - need to map through ToJSON
            item_type = list(array_item_imports)[0]
            inner_expr = f"(({value_access} as Array<any>).map({item_type}ToJSON))"
            # Check for null on optional arrays
            if not is_required:
                return f"{value_access} == null ? undefined : {inner_expr}"
            return inner_expr
        # Array of primitives - pass through
        return value_access

    # Handle nested objects (non-array references)
    if nested_type:
        return f"{nested_type}ToJSON({value_access})"

    # Handle dates
    if is_date:
        # date format: YYYY-MM-DD
        if not is_required or is_nullable:
            return f"{value_access} == null ? {value_access} : {value_access}.toISOString().substring(0,10)"
        return f"{value_access}.toISOString().substring(0,10)"

    if is_date_time:
        # date-time format: full ISO string
        if not is_required or is_nullable:
            return f"{value_access} == null ? {value_access} : {value_access}.toISOString()"
        return f"{value_access}.toISOString()"

    # Primitives - direct access
    return value_access


def _collect_type_imports(properties: List[Dict[str, Any]]) -> List[str]:
    """Collect all type imports needed for a model, preserving property order."""
    seen: set = set()
    imports: List[str] = []
    for prop in properties:
        for type_import in prop.get("type_imports", set()):
            if type_import not in seen:
                seen.add(type_import)
                imports.append(type_import)
    return imports


def _get_api_info(spec: Dict[str, Any]) -> Dict[str, str]:
    """Extract API metadata from spec."""
    info = spec.get("info", {})
    return {
        "api_title": info.get("title", "API"),
        "api_description": info.get("description", ""),
        "api_version": info.get("version", "1.0.0"),
        "contact_email": info.get("contact", {}).get("email", ""),
    }


def _get_unique_extracted_types(registry: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Get unique extracted types from registry.

    The registry may have multiple paths pointing to the same type_name.
    We only need to generate each type once.

    Args:
        registry: Extraction registry from anyof_extractor

    Returns:
        Dict mapping type_name to type info (description, schema)
    """
    unique_types: Dict[str, Dict[str, Any]] = {}
    for info in registry.values():
        type_name = info["type_name"]
        if type_name not in unique_types:
            unique_types[type_name] = {
                "description": info.get("description", ""),
                "schema": info["schema"],
            }
    return unique_types


def generate_models(
    spec: Dict[str, Any],
    output_path: Path,
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[str]:
    """
    Generate model files from OpenAPI schemas.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write model files to
        registry: Optional extraction registry for titled anyOf schemas.
                  If not provided, one will be created automatically.

    Returns:
        List of generated model names
    """
    # Set up Jinja2 environment
    env = Environment(
        loader=PackageLoader("openapi_ts_client", "templates/fetch"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    model_template = env.get_template("model.ts.j2")
    index_template = env.get_template("models_index.ts.j2")

    # Create extraction registry if not provided
    if registry is None:
        registry = create_extraction_registry(spec)

    # Get schemas from spec
    schemas = spec.get("components", {}).get("schemas", {})

    # Create models directory
    models_dir = output_path / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    api_info = _get_api_info(spec)
    generated_models: List[str] = []

    # Generate model files for each schema
    for schema_name, model_schema in schemas.items():
        # Convert schema name to type name (handles reserved names like ApiResponse)
        type_name = schema_to_type_name(schema_name)

        # Process properties
        properties_schema = model_schema.get("properties", {})
        required_props = model_schema.get("required", [])

        properties = []
        for prop_name, prop_schema in properties_schema.items():
            prop_info = _get_property_info(
                prop_name, prop_schema, required_props, type_name, registry
            )
            properties.append(prop_info)

        # Collect enum definitions from properties
        enum_defs = [p["enum_info"] for p in properties if p.get("enum_info")]

        # Collect type imports
        type_imports = _collect_type_imports(properties)

        # Get required properties for instanceOf function
        required_properties = [p for p in properties if p["required"]]

        # Render template
        context = {
            **api_info,
            "model_name": type_name,
            "description": model_schema.get("description", ""),
            "properties": properties,
            "required_properties": required_properties,
            "type_imports": type_imports,
            "has_properties": len(properties) > 0,
            "enum_defs": enum_defs,
        }

        content = model_template.render(**context)

        # Write file
        model_file = models_dir / f"{type_name}.ts"
        model_file.write_text(content)
        generated_models.append(type_name)

    # Generate model files for extracted types from registry
    extracted_types = _get_unique_extracted_types(registry)
    for type_name, type_info in extracted_types.items():
        # Extracted types are empty interfaces (the actual type union
        # is handled at the usage site by the type_mapper)
        context = {
            **api_info,
            "model_name": type_name,
            "description": type_info.get("description", ""),
            "properties": [],
            "required_properties": [],
            "type_imports": [],
            "has_properties": False,
        }

        content = model_template.render(**context)

        # Write file
        model_file = models_dir / f"{type_name}.ts"
        model_file.write_text(content)
        generated_models.append(type_name)

    # Generate index.ts
    index_content = index_template.render(model_names=sorted(generated_models))
    index_file = models_dir / "index.ts"
    index_file.write_text(index_content)

    return generated_models

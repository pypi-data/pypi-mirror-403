"""Generate markdown documentation files."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, PackageLoader

from openapi_ts_client.utils import schema_to_type_name

# Reserved words that need escaping in TypeScript interface property names
# This is a subset of TypeScript reserved words - some like 'type' can be used
# as property names without issues
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
    """
    Convert snake_case to camelCase and escape reserved words.

    Examples:
        habitat_id -> habitatId
        first_name -> firstName
        id -> id
        package -> _package (reserved word)
    """
    if "_" not in name:
        result = name
    else:
        parts = name.split("_")
        result = parts[0] + "".join(word.capitalize() for word in parts[1:])

    # Escape reserved words that cannot be used as interface property names
    if result in INTERFACE_RESERVED_WORDS:
        return f"_{result}"
    return result


def _map_type_for_docs(
    schema: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Map an OpenAPI schema to a documentation type string.

    This produces human-readable types with markdown links and HTML entities
    for arrays.

    Args:
        schema: OpenAPI schema object
        registry: Optional extraction registry for titled anyOf schemas

    Returns:
        Documentation type string
    """
    if registry is None:
        registry = {}

    if not schema:
        return "any"

    # Handle $ref
    if "$ref" in schema:
        ref = schema["$ref"]
        raw_name = ref.split("/")[-1]
        type_name = schema_to_type_name(raw_name)
        return f"[{type_name}]({type_name}.md)"

    # Handle anyOf (commonly used for nullable types)
    if "anyOf" in schema:
        # Check if this is a titled anyOf that should use extracted type
        if "title" in schema:
            type_name = _lookup_extracted_type(schema, registry)
            if type_name:
                return type_name

        # For anyOf with null, take the non-null type
        non_null_schemas = [s for s in schema["anyOf"] if s.get("type") != "null"]
        if non_null_schemas:
            return _map_type_for_docs(non_null_schemas[0], registry)

        # Fall back to union
        types = []
        for sub_schema in schema["anyOf"]:
            if sub_schema.get("type") == "null":
                continue
            types.append(_map_type_for_docs(sub_schema, registry))
        return " | ".join(types) if types else "any"

    schema_type = schema.get("type")

    # Handle arrays
    if schema_type == "array":
        items = schema.get("items", {})
        item_type = _map_type_for_docs(items, registry)
        # If the item type is a reference (has markdown link), format differently
        if item_type.startswith("["):
            return f"[Array&lt;{item_type[1:].split(']')[0]}&gt;]({item_type.split('(')[1]}"
        return f"Array&lt;{item_type}&gt;"

    # Handle object with additionalProperties (map types)
    if schema_type == "object" and "additionalProperties" in schema:
        additional_props = schema["additionalProperties"]
        if additional_props and isinstance(additional_props, dict):
            value_type = _map_type_for_docs(additional_props, registry)
            return f"{{ [key: string]: {value_type}; }}"

    # Handle string with format: date-time -> Date
    if schema_type == "string" and schema.get("format") in ("date-time", "date"):
        return "Date"

    # Handle string with format: binary -> Blob
    if schema_type == "string" and schema.get("format") == "binary":
        return "Blob"

    # Basic type mapping
    type_map = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "object": "object",
    }

    if schema_type in type_map:
        return type_map[schema_type]

    return "any"


def _lookup_extracted_type(
    schema: Dict[str, Any], registry: Dict[str, Dict[str, Any]]
) -> Optional[str]:
    """
    Look up extracted type name for a schema in the registry.

    Args:
        schema: OpenAPI schema object to look up
        registry: Extraction registry mapping paths to type info

    Returns:
        Type name as markdown link if found in registry, None otherwise
    """
    for info in registry.values():
        if info["schema"] is schema:
            type_name = info["type_name"]
            return f"[{type_name}]({type_name}.md)"
    return None


def _get_example_value(schema: Dict[str, Any]) -> str:
    """
    Get an example value for a property schema.

    Args:
        schema: Property schema

    Returns:
        Example value as string for JSON output
    """
    # Check for explicit example
    if "example" in schema:
        example = schema["example"]
        if isinstance(example, str):
            return example  # Return unquoted - fixture shows unquoted strings
        elif isinstance(example, bool):
            return "true" if example else "false"
        elif isinstance(example, (int, float)):
            return str(example)
        elif example is None:
            return "null"
        else:
            return json.dumps(example)

    # For anyOf, check nested schemas for example
    if "anyOf" in schema:
        for sub_schema in schema["anyOf"]:
            if sub_schema.get("type") != "null" and "example" in sub_schema:
                return _get_example_value(sub_schema)

    return "null"


def _create_jinja_env() -> Environment:
    """Create Jinja2 environment for doc templates."""
    env = Environment(
        loader=PackageLoader("openapi_ts_client", "templates/fetch"),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def _get_property_info(
    prop_name: str,
    prop_schema: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Get property information for documentation template rendering.

    Args:
        prop_name: The property name (from OpenAPI schema)
        prop_schema: The property schema
        registry: Extraction registry for titled anyOf schemas

    Returns:
        Dict with camelCase name, documentation type, and example value
    """
    if registry is None:
        registry = {}

    # Convert property name to camelCase (e.g., habitat_id -> habitatId)
    camel_name = _snake_to_camel(prop_name)

    # Get type for documentation
    doc_type = _map_type_for_docs(prop_schema, registry)

    # Get example value
    example = _get_example_value(prop_schema)

    return {
        "name": camel_name,
        "type": doc_type,
        "example": example,
    }


def _generate_model_doc(
    env: Environment,
    schema_name: str,
    schema: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Generate markdown documentation for a single model.

    Args:
        env: Jinja2 environment
        schema_name: Name of the schema
        schema: The schema definition
        registry: Extraction registry for titled anyOf schemas

    Returns:
        Generated markdown content
    """
    if registry is None:
        registry = {}

    template = env.get_template("doc.md.j2")

    properties = schema.get("properties", {})
    description = schema.get("description", "")

    # Build property info list preserving schema order
    prop_infos = []
    for prop_name, prop_schema in properties.items():
        info = _get_property_info(prop_name, prop_schema, registry)
        prop_infos.append(info)

    return template.render(
        model_name=schema_name,
        description=description,
        properties=prop_infos,
    )


def generate_docs(
    spec: Dict[str, Any],
    output_path: Path,
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[str]:
    """
    Generate markdown documentation files.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write doc files to
        registry: Extraction registry for titled anyOf schemas

    Returns:
        List of generated model names
    """
    if registry is None:
        registry = {}

    env = _create_jinja_env()
    schemas = spec.get("components", {}).get("schemas", {})

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    generated_models = []

    # Generate extracted type docs first
    generated_types = set()
    for _path, info in registry.items():
        type_name = info["type_name"]
        if type_name not in generated_types:
            # Create empty schema for extracted types
            empty_schema = {"description": info.get("description", "")}
            content = _generate_model_doc(env, type_name, empty_schema, registry)

            output_file = output_path / f"{type_name}.md"
            output_file.write_text(content)

            generated_models.append(type_name)
            generated_types.add(type_name)

    # Generate schema model docs
    for schema_name, schema in schemas.items():
        # Transform name if needed (e.g., ApiResponse -> ModelApiResponse)
        type_name = schema_to_type_name(schema_name)
        content = _generate_model_doc(env, type_name, schema, registry)

        output_file = output_path / f"{type_name}.md"
        output_file.write_text(content)

        generated_models.append(type_name)

    return generated_models

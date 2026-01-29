"""Generate markdown documentation files for axios client."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, PackageLoader

from openapi_ts_client.generators.shared import create_extraction_registry


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
    if "_" not in name:
        return name
    parts = name.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def _map_type_for_docs(schema: Dict[str, Any]) -> str:
    """
    Map an OpenAPI schema to a documentation type string.

    Args:
        schema: OpenAPI schema object

    Returns:
        Documentation type string
    """
    if not schema:
        return "any"

    # Handle $ref
    if "$ref" in schema:
        type_name = schema["$ref"].split("/")[-1]
        return f"[{type_name}]({type_name}.md)"

    # Handle anyOf (commonly used for nullable types)
    if "anyOf" in schema:
        non_null_schemas = [s for s in schema["anyOf"] if s.get("type") != "null"]
        if non_null_schemas:
            return _map_type_for_docs(non_null_schemas[0])
        return "any"

    schema_type = schema.get("type")

    # Handle arrays
    if schema_type == "array":
        items = schema.get("items", {})
        item_type = _map_type_for_docs(items)
        if item_type.startswith("["):
            return f"[Array&lt;{item_type[1:].split(']')[0]}&gt;]({item_type.split('(')[1]}"
        return f"Array&lt;{item_type}&gt;"

    # Handle object
    if schema_type == "object":
        return "object"

    # Basic type mapping
    type_map = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
    }

    return type_map.get(schema_type, "any")


def _generate_model_doc(
    env: Environment,
    schema_name: str,
    schema: Dict[str, Any],
) -> str:
    """
    Generate markdown documentation for a single model.

    Args:
        env: Jinja2 environment
        schema_name: Name of the schema
        schema: The schema definition

    Returns:
        Generated markdown content
    """
    template = env.get_template("doc.md.j2")

    properties = schema.get("properties", {})
    description = schema.get("description", "")

    # Build property info list
    prop_infos = []
    for prop_name, prop_schema in properties.items():
        camel_name = _snake_to_camel(prop_name)
        doc_type = _map_type_for_docs(prop_schema)
        prop_infos.append(
            {
                "name": camel_name,
                "type": doc_type,
                "example": "null",
            }
        )

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
        registry = create_extraction_registry(spec)

    env = _get_template_env()
    schemas = spec.get("components", {}).get("schemas", {})

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    generated_models = []

    # Generate schema model docs
    for schema_name, schema in schemas.items():
        content = _generate_model_doc(env, schema_name, schema)

        output_file = output_path / f"{schema_name}.md"
        output_file.write_text(content)

        generated_models.append(schema_name)

    return generated_models

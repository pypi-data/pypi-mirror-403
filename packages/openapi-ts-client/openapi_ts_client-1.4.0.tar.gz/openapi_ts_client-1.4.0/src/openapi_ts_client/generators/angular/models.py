"""Generate Angular TypeScript model files from OpenAPI schemas."""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, PackageLoader

from openapi_ts_client.generators.shared import (
    create_extraction_registry,
    map_openapi_type_with_imports,
)
from openapi_ts_client.utils import schema_to_filename, schema_to_type_name


def _lower_first(s: str) -> str:
    """Convert first character to lowercase."""
    if not s:
        return s
    return s[0].lower() + s[1:]


def _is_top_level_enum_schema(schema: Dict[str, Any]) -> bool:
    """
    Check if a schema is a top-level enum (string enum with no properties).

    These should be generated as:
    export const Name = { ... } as const;
    export type Name = typeof Name[keyof typeof Name];

    Rather than as an interface.
    """
    # Must have enum values
    if "enum" not in schema:
        return False

    # Must be string type (or no type specified, which defaults to string for enum)
    schema_type = schema.get("type")
    if schema_type is not None and schema_type != "string":
        return False

    # Should not have properties (that would make it an object with enum property)
    if schema.get("properties"):
        return False

    return True


def _should_use_pascal_case(schema: Dict[str, Any]) -> bool:
    """
    Check if a schema should use PascalCase naming.

    PascalCase is used for:
    - String enum schemas (have 'enum' with type 'string')
    - Object schemas with properties

    Original case is preserved for:
    - Primitive types (string, integer, number, boolean without enum)
    - Array types

    Args:
        schema: The schema definition

    Returns:
        True if the schema should use PascalCase, False otherwise
    """
    # String enums should use PascalCase
    if _is_top_level_enum_schema(schema):
        return True

    # Object schemas with properties should use PascalCase
    if schema.get("properties"):
        return True

    # Primitive and array types keep original case
    return False


def _is_primitive_schema(schema: Dict[str, Any]) -> bool:
    """
    Check if a schema represents a primitive or array type (not an object with properties).

    Primitive schemas are inlined in references and don't need a separate model file
    with a namespace.
    """
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

    Special characters get converted to descriptive names:
    - '.' -> 'Period'
    - '-' -> 'Hyphen'
    - etc.

    Regular alphanumeric values get capitalized.
    """
    # Handle special characters
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

    # If it's a single special character, return its name
    if value in special_chars:
        return special_chars[value]

    # If it starts with a special character, prepend the name
    if value and value[0] in special_chars:
        return special_chars[value[0]] + value[1:].capitalize()

    # Regular alphanumeric - capitalize first letter
    if value:
        return value[0].upper() + value[1:] if len(value) > 1 else value.upper()

    return value


def _generate_enum_file(
    env: Environment,
    schema_name: str,
    schema: Dict[str, Any],
    api_title: str,
    contact_email: str,
) -> str:
    """
    Generate a TypeScript const/type pattern for a string enum schema.

    Args:
        env: Jinja2 environment
        schema_name: Name of the schema (already PascalCase)
        schema: The schema definition
        api_title: API title for the header
        contact_email: Contact email for the header

    Returns:
        Generated TypeScript content
    """
    template = env.get_template("enum.ts.j2")

    enum_values = schema.get("enum", [])
    description = schema.get("description", "")

    # Convert enum values to key-value pairs
    enum_members = []
    for value in enum_values:
        key = _enum_value_to_key(str(value))
        enum_members.append({"key": key, "value": value})

    return template.render(
        api_title=api_title,
        contact_email=contact_email,
        type_name=schema_name,
        description=description,
        enum_members=enum_members,
    )


def _generate_primitive_model_file(
    env: Environment,
    schema_name: str,
    schema: Dict[str, Any],
    api_title: str,
    contact_email: str,
) -> str:
    """
    Generate a minimal TypeScript interface file for a primitive/array schema.

    These schemas are typically inlined in references, but we still generate
    empty interface files to maintain consistency with OpenAPI Generator output.

    Args:
        env: Jinja2 environment
        schema_name: Name of the schema (keeps original case for primitives)
        schema: The schema definition
        api_title: API title for the header
        contact_email: Contact email for the header

    Returns:
        Generated TypeScript content
    """
    template = env.get_template("primitive_model.ts.j2")

    description = schema.get("description", "")

    return template.render(
        api_title=api_title,
        contact_email=contact_email,
        interface_name=schema_name,
        description=description,
    )


def _create_jinja_env() -> Environment:
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=PackageLoader("openapi_ts_client", "templates/angular"),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["lower_first"] = _lower_first
    return env


def _get_property_info(
    prop_name: str,
    prop_schema: Dict[str, Any],
    required_props: List[str],
    interface_name: str,
    registry: Dict[str, Dict[str, Any]] = None,
    all_schemas: Dict[str, Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get property information for template rendering.

    Args:
        prop_name: The property name
        prop_schema: The property schema
        required_props: List of required property names
        interface_name: Name of the parent interface (for enum type references)
        registry: Extraction registry for titled anyOf schemas
        all_schemas: All schemas for inlining primitive/array refs

    Returns:
        Dict with name, type, required status, and enum info
    """
    if registry is None:
        registry = {}
    if all_schemas is None:
        all_schemas = {}

    enum_values = prop_schema.get("enum")
    description = prop_schema.get("description", "")

    if enum_values:
        # Enum property - type references the namespace
        enum_name = prop_name[0].upper() + prop_name[1:] + "Enum"
        ts_type = f"{interface_name}.{enum_name}"
        imports = set()

        return {
            "name": prop_name,
            "type": ts_type,
            "required": prop_name in required_props,
            "imports": imports,
            "description": description,
            "is_enum": True,
            "enum_name": enum_name,
            "enum_values": enum_values,
        }

    # Non-enum property - pass registry for titled anyOf lookups
    # Angular uses string for dates, not Date objects, and doesn't prefix reserved names
    ts_type, imports = map_openapi_type_with_imports(
        prop_schema, registry, use_date_type=False, use_model_prefix=False, all_schemas=all_schemas
    )
    return {
        "name": prop_name,
        "type": ts_type,
        "required": prop_name in required_props,
        "imports": imports,
        "description": description,
        "is_enum": False,
        "enum_name": None,
        "enum_values": None,
    }


def _generate_model_file(
    env: Environment,
    schema_name: str,
    schema: Dict[str, Any],
    api_title: str,
    contact_email: str,
    registry: Dict[str, Dict[str, Any]] = None,
    all_schemas: Dict[str, Dict[str, Any]] = None,
) -> str:
    """
    Generate a single model file content.

    Args:
        env: Jinja2 environment
        schema_name: Name of the schema (e.g., "FeedingOut")
        schema: The schema definition
        api_title: API title for the header
        contact_email: Contact email for the header
        registry: Extraction registry for titled anyOf schemas
        all_schemas: All schemas for inlining primitive/array refs

    Returns:
        Generated TypeScript content
    """
    if registry is None:
        registry = {}
    if all_schemas is None:
        all_schemas = {}

    template = env.get_template("model.ts.j2")

    properties = schema.get("properties", {})
    required_props = schema.get("required", [])

    # Build property info list preserving schema order
    prop_infos = []
    all_imports = set()
    enums = []

    for prop_name, prop_schema in properties.items():
        info = _get_property_info(
            prop_name, prop_schema, required_props, schema_name, registry, all_schemas
        )
        prop_infos.append(info)
        all_imports.update(info["imports"])

        if info["is_enum"]:
            enums.append(
                {
                    "name": info["enum_name"],
                    "enum_values": info["enum_values"],
                }
            )

    # Sort imports alphabetically by lowercase (case-insensitive sort)
    sorted_imports = sorted(all_imports, key=str.lower)

    # Get schema-level description (not property descriptions)
    schema_description = schema.get("description", "")

    return template.render(
        api_title=api_title,
        contact_email=contact_email,
        interface_name=schema_name,
        description=schema_description,
        imports=sorted_imports,
        properties=prop_infos,
        enums=enums,
    )


def generate_models(spec: Dict[str, Any], output_dir: Path) -> None:
    """
    Generate all model files from an OpenAPI spec.

    Args:
        spec: OpenAPI specification dict
        output_dir: Directory to write model files to
    """
    api_title = spec.get("info", {}).get("title", "")
    contact_email = spec.get("info", {}).get("contact", {}).get("email", "")
    schemas = spec.get("components", {}).get("schemas", {})

    # Create extraction registry for titled anyOf schemas
    registry = create_extraction_registry(spec)

    generate_all_models(schemas, output_dir, api_title, contact_email, registry)


def generate_all_models(
    schemas: Dict[str, Any],
    output_dir: Path,
    api_title: str,
    contact_email: str,
    registry: Dict[str, Dict[str, Any]] = None,
) -> None:
    """
    Generate all model files from schemas.

    Args:
        schemas: OpenAPI schemas dict
        output_dir: Directory to write model files to
        api_title: API title for header comments
        contact_email: Contact email for header comments
        registry: Extraction registry for titled anyOf schemas
    """
    if registry is None:
        registry = {}

    env = _create_jinja_env()

    # Add the schema_to_filename_filter to the environment
    def _schema_to_filename_filter(name: str) -> str:
        """Jinja2 filter to convert schema name to filename without .ts extension."""
        filename = schema_to_filename(name)
        return filename[:-3] if filename.endswith(".ts") else filename

    env.filters["schema_to_filename_filter"] = _schema_to_filename_filter

    model_filenames = []

    # Generate extracted type files first
    generated_types = set()
    for _path, info in registry.items():
        type_name = info["type_name"]
        if type_name not in generated_types:
            filename = generate_extracted_type_file(
                type_name=type_name,
                description=info["description"],
                output_dir=output_dir,
                api_title=api_title,
                contact_email=contact_email,
            )
            model_filenames.append(filename)
            generated_types.add(type_name)

    # Generate schema model files
    for schema_name, schema in schemas.items():
        # Determine the type name based on schema type
        # - Enums and object schemas use PascalCase
        # - Primitive/array schemas keep original case
        # Angular doesn't need the Model prefix for reserved names
        if _should_use_pascal_case(schema):
            type_name = schema_to_type_name(schema_name, add_model_prefix=False)
        else:
            type_name = schema_name  # Keep original case

        # Check if this is a top-level enum schema
        if _is_top_level_enum_schema(schema):
            content = _generate_enum_file(env, type_name, schema, api_title, contact_email)
        elif _is_primitive_schema(schema):
            # Generate a minimal interface file for primitive/array schemas
            content = _generate_primitive_model_file(
                env, type_name, schema, api_title, contact_email
            )
        else:
            # Generate model file (interface with namespace)
            content = _generate_model_file(
                env, type_name, schema, api_title, contact_email, registry, schemas
            )

        # Get filename (without .ts extension for barrel export)
        filename = schema_to_filename(type_name)
        filename_without_ext = filename[:-3]  # Remove .ts

        model_filenames.append(filename_without_ext)

        # Write file
        output_file = output_dir / filename
        output_file.write_text(content)

    # Generate barrel export (models.ts)
    barrel_template = env.get_template("models.ts.j2")
    barrel_content = barrel_template.render(model_filenames=sorted(model_filenames))
    (output_dir / "models.ts").write_text(barrel_content)


def generate_extracted_type_file(
    type_name: str,
    description: str,
    output_dir: Path,
    api_title: str,
    contact_email: str,
) -> str:
    """
    Generate an empty interface file for an extracted anyOf type.

    Args:
        type_name: PascalCase type name (e.g., "Score", "CodeDuplication")
        description: Optional description for JSDoc
        output_dir: Directory to write the file
        api_title: API title for header
        contact_email: Contact email for header

    Returns:
        Filename without extension (for barrel export)
    """
    env = _create_jinja_env()
    template = env.get_template("extracted_type.ts.j2")

    content = template.render(
        api_title=api_title,
        contact_email=contact_email,
        interface_name=type_name,
        description=description,
    )

    filename = schema_to_filename(type_name)
    filename_without_ext = filename[:-3]

    output_file = output_dir / filename
    output_file.write_text(content)

    return filename_without_ext

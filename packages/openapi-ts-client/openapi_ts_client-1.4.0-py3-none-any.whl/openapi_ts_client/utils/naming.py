"""Naming convention utilities for TypeScript generation."""

# TypeScript reserved words that need escaping
# Schema names that conflict with fetch runtime types and need "Model" prefix
# These match the OpenAPI Generator behavior for typescript-fetch
FETCH_RESERVED_TYPE_NAMES = {
    "ApiResponse",
    "Response",
    "RequestInit",
    "Headers",
    "Request",
    "Blob",
    "File",
}


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
    "any",
    "boolean",
    "number",
    "string",
    "symbol",
    "type",
    "from",
    "of",
    "async",
    "await",
}


def schema_to_type_name(schema_name: str, add_model_prefix: bool = True) -> str:
    """
    Convert OpenAPI schema name to TypeScript type name.

    Capitalizes the first letter and optionally adds "Model" prefix to names that
    conflict with fetch runtime types.

    Args:
        schema_name: The OpenAPI schema name
        add_model_prefix: If True, add "Model" prefix for reserved names (Fetch style)
                         If False, just capitalize (Angular style)

    Examples:
        FeedingOut -> FeedingOut (unchanged)
        ApiResponse (add_model_prefix=True) -> ModelApiResponse (prefixed)
        ApiResponse (add_model_prefix=False) -> ApiResponse (just capitalized)
        mark -> Mark (capitalized)
        winner -> Winner (capitalized)
    """
    if not schema_name:
        return schema_name

    # Capitalize first letter
    capitalized = (
        schema_name[0].upper() + schema_name[1:] if len(schema_name) > 1 else schema_name.upper()
    )

    # Add Model prefix for reserved names (only for Fetch-style generators)
    if add_model_prefix and capitalized in FETCH_RESERVED_TYPE_NAMES:
        return f"Model{capitalized}"
    return capitalized


def schema_to_filename(schema_name: str) -> str:
    """
    Convert OpenAPI schema name to TypeScript filename.

    Examples:
        FeedingOut -> feedingOut.ts
        HTTPMetrics -> hTTPMetrics.ts
        Score -> score.ts
    """
    if not schema_name:
        return ".ts"

    # Lowercase first character only
    filename = (
        schema_name[0].lower() + schema_name[1:] if len(schema_name) > 1 else schema_name.lower()
    )

    return f"{filename}.ts"


def tag_to_service_name(tag: str) -> str:
    """
    Convert OpenAPI tag to Angular service class name.

    Examples:
        Feedings -> FeedingsService
        HTTPMetrics -> HTTPMetricsService
        Care Plans -> CarePlansService
    """
    # Remove spaces and ensure first letter of each word is capitalized
    words = tag.split()
    class_name = "".join(word[0].upper() + word[1:] if word else "" for word in words)

    return f"{class_name}Service"


def tag_to_service_filename(tag: str) -> str:
    """
    Convert OpenAPI tag to Angular service filename.

    Examples:
        Feedings -> feedings.service.ts
        HTTPMetrics -> hTTPMetrics.service.ts
        Care Plans -> carePlans.service.ts
        Audit fields -> auditFields.service.ts
    """
    # Remove spaces and join words
    words = tag.split()
    if not words:
        return ".service.ts"

    # First word: lowercase first char
    # Subsequent words: capitalize first char (camelCase join)
    result = words[0][0].lower() + words[0][1:] if words[0] else ""
    for word in words[1:]:
        if word:
            result += word[0].upper() + word[1:]

    return f"{result}.service.ts"


def operation_id_to_method_name(operation_id: str) -> str:
    """
    Convert OpenAPI operationId to TypeScript method name.

    Handles multiple naming conventions:
    - camelCase: addPet -> addPet (preserve)
    - kebab-case: get-board -> getBoard
    - snake_case: list_all -> listAll
    - dotted paths: zoo.api.endpoints.feedings_list_all -> listAll

    Examples:
        addPet -> addPet (preserve camelCase)
        get-board -> getBoard (convert kebab-case)
        put-square -> putSquare (convert kebab-case)
        zoo.api.endpoints.feedings_list_all -> listAll
        delete -> _delete (escape reserved)
        list_all -> listAll
    """
    # Extract last segment if dotted path
    from_dotted_path = "." in operation_id
    if from_dotted_path:
        operation_id = operation_id.split(".")[-1]

    # Check if conversion is needed (has dashes, underscores, or from dotted path)
    needs_conversion = "-" in operation_id or "_" in operation_id or from_dotted_path

    if not needs_conversion:
        method_name = operation_id
    else:
        # Split by both dash and underscore
        # Replace dashes with underscores first, then split
        normalized = operation_id.replace("-", "_")
        parts = normalized.split("_")
        if not parts:
            return ""

        # If from a dotted path and there are multiple parts, skip first (resource prefix)
        if from_dotted_path and len(parts) > 1:
            parts = parts[1:]

        # First part lowercase, rest capitalized (camelCase)
        method_name = parts[0].lower()
        for part in parts[1:]:
            if part:
                method_name += part[0].upper() + part[1:].lower() if len(part) > 1 else part.upper()

    # Escape reserved words
    if method_name in TYPESCRIPT_RESERVED_WORDS:
        method_name = f"_{method_name}"

    return method_name

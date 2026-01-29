"""Main generator module for creating TypeScript clients from OpenAPI specifications."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Union

import yaml

from .enums import ClientFormat
from .exceptions import OutputDirectoryNotEmptyError
from .generators.angular.generator import generate_angular_client
from .generators.axios.generator import generate_axios_client
from .generators.fetch.generator import generate_fetch_client
from .logging_config import get_logger, setup_logging

# Lazy logger initialization - don't call setup_logging() at import time
# This allows CLI to configure logging before we initialize
_logger = None


def _get_logger():
    """Get the logger, initializing on first use."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def _get_non_hidden_files(directory: Path) -> list:
    """Return list of non-hidden files/dirs in directory.

    Hidden files are those starting with a dot (e.g., .gitkeep, .gitignore).

    Args:
        directory: The directory to scan.

    Returns:
        List of Path objects for non-hidden files and directories.
    """
    if not directory.exists():
        return []
    return [p for p in directory.iterdir() if not p.name.startswith(".")]


def _clear_directory(directory: Path) -> None:
    """Remove all contents of directory (but not the directory itself).

    Removes both hidden and non-hidden files and subdirectories.

    Args:
        directory: The directory to clear.
    """
    if not directory.exists():
        return
    for item in directory.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def generate_typescript_client(
    openapi_spec: Union[Dict[str, Any], str],
    output_format: ClientFormat = ClientFormat.FETCH,
    output_path: Union[str, Path, None] = None,
    skip_validation: bool = False,
    clean: bool = False,
    force: bool = False,
) -> str:
    """
    Generate a TypeScript client from an OpenAPI specification.

    This function takes an OpenAPI specification (2.0/Swagger or 3.x) and generates
    a TypeScript client based on the specified output format.

    Args:
        openapi_spec: The OpenAPI specification. Can be provided as:
            - A dictionary containing the parsed JSON specification
            - A JSON string containing the specification
            Supports both OpenAPI 2.0 (Swagger) and OpenAPI 3.x specifications.
        output_format: The format of the generated TypeScript client.
            Defaults to ClientFormat.FETCH. Options are:
            - ClientFormat.FETCH: Native Fetch API client
            - ClientFormat.AXIOS: Axios HTTP library client
            - ClientFormat.ANGULAR: Angular-optimized client with services
        output_path: The directory path where the generated client will be written.
            Defaults to a temporary directory if not specified.
        skip_validation: If True, skip OpenAPI specification validation.
            Defaults to False.
        clean: If True, clear the output directory before generating.
            Cannot be used together with force. Defaults to False.
        force: If True, continue generation even if output directory is not empty.
            Files will be overwritten but existing files not part of the generated
            output will remain. Cannot be used together with clean. Defaults to False.

    Returns:
        A status message indicating the result of the generation process.

    Raises:
        ValueError: If the provided specification is not a valid OpenAPI spec,
            or if both clean and force are set to True.
        TypeError: If the openapi_spec parameter is neither a dict nor a string.
        OutputDirectoryNotEmptyError: If the output directory is not empty and
            neither clean nor force is set to True.

    Example:
        >>> from openapi_ts_client import generate_typescript_client, ClientFormat
        >>> # OpenAPI 3.x example
        >>> spec = {"openapi": "3.0.0", "info": {"title": "My API", "version": "1.0"}, "paths": {}}
        >>> result = generate_typescript_client(spec, ClientFormat.AXIOS, "./output")
        >>> print(result)
    """
    func_logger = get_logger("generator")

    func_logger.info("=" * 80)
    func_logger.info("Starting TypeScript client generation")
    func_logger.info("=" * 80)

    # Validate clean and force are not both set
    if clean and force:
        raise ValueError("clean and force are mutually exclusive - use one or the other")

    # Use temp directory if output_path not specified
    if output_path is None:
        output_path = Path(tempfile.mkdtemp(prefix="openapi_ts_client_"))
        func_logger.info(f"No output path specified, using temp directory: {output_path}")

    # Log input parameters
    func_logger.debug(f"Input parameter 'output_format': {output_format}")
    func_logger.debug(f"Input parameter 'output_format' type: {type(output_format)}")
    func_logger.debug(f"Input parameter 'output_path': {output_path}")
    func_logger.debug(f"Input parameter 'output_path' type: {type(output_path)}")
    func_logger.debug(f"Input parameter 'openapi_spec' type: {type(openapi_spec)}")

    # Parse the OpenAPI spec if it's a string
    func_logger.info("Processing OpenAPI specification input")
    if isinstance(openapi_spec, str):
        func_logger.debug("OpenAPI spec provided as string, attempting to parse")
        func_logger.debug(f"String length: {len(openapi_spec)} characters")
        try:
            parsed_spec = json.loads(openapi_spec)
            func_logger.info("Successfully parsed OpenAPI spec from JSON string")
            func_logger.debug(f"Parsed spec keys: {list(parsed_spec.keys())}")
        except json.JSONDecodeError as json_err:
            func_logger.debug(f"JSON parsing failed: {json_err}, trying YAML")
            try:
                parsed_spec = yaml.safe_load(openapi_spec)
                if not isinstance(parsed_spec, dict):
                    raise ValueError(
                        f"Invalid OpenAPI spec: expected dict, got {type(parsed_spec).__name__}"
                    )
                func_logger.info("Successfully parsed OpenAPI spec from YAML string")
                func_logger.debug(f"Parsed spec keys: {list(parsed_spec.keys())}")
            except yaml.YAMLError as yaml_err:
                func_logger.error("Failed to parse OpenAPI spec as JSON or YAML")
                func_logger.error(f"JSON error: {json_err}")
                func_logger.error(f"YAML error: {yaml_err}")
                raise ValueError(
                    f"Invalid OpenAPI spec: not valid JSON ({json_err}) or YAML ({yaml_err})"
                ) from yaml_err
    elif isinstance(openapi_spec, dict):
        func_logger.debug("OpenAPI spec provided as dictionary")
        func_logger.debug(f"Dictionary keys: {list(openapi_spec.keys())}")
        parsed_spec = openapi_spec
    else:
        func_logger.error(f"Invalid type for openapi_spec: {type(openapi_spec)}")
        func_logger.error("Expected dict or str, got something else")
        raise TypeError(
            f"openapi_spec must be a dict or JSON string, got {type(openapi_spec).__name__}"
        )

    # Validate OpenAPI specification
    if not skip_validation:
        func_logger.info("Validating OpenAPI specification")
        openapi_version = _validate_openapi_spec(parsed_spec, func_logger)
    else:
        func_logger.info("Skipping OpenAPI specification validation")
        openapi_version = parsed_spec.get("openapi") or parsed_spec.get("swagger", "unknown")

    # Resolve and validate output path
    func_logger.info("Resolving output path")
    resolved_output_path = _resolve_output_path(output_path, func_logger)

    # Check for non-empty directory
    non_hidden = _get_non_hidden_files(resolved_output_path)
    if non_hidden:
        if clean:
            func_logger.info(f"Clearing output directory: {resolved_output_path}")
            _clear_directory(resolved_output_path)
        elif force:
            func_logger.warning(
                f"Output directory is not empty ({len(non_hidden)} files), "
                f"continuing due to force=True"
            )
        else:
            raise OutputDirectoryNotEmptyError(resolved_output_path, len(non_hidden))

    # Log specification details
    func_logger.info("Extracting specification metadata")
    _log_spec_details(parsed_spec, func_logger)

    # Log generation configuration
    func_logger.info("-" * 60)
    func_logger.info("Generation Configuration Summary")
    func_logger.info("-" * 60)
    func_logger.info(f"  Output Format: {output_format.value}")
    func_logger.info(f"  Output Path: {resolved_output_path}")
    func_logger.info(f"  API Title: {parsed_spec.get('info', {}).get('title', 'Unknown')}")
    func_logger.info(f"  API Version: {parsed_spec.get('info', {}).get('version', 'Unknown')}")
    func_logger.info("-" * 60)

    # Build status message
    api_title = parsed_spec.get("info", {}).get("title", "Unknown API")
    api_version = parsed_spec.get("info", {}).get("version", "Unknown")
    paths_count = len(parsed_spec.get("paths", {}))

    # Dispatch to appropriate generator based on format
    if output_format == ClientFormat.ANGULAR:
        func_logger.info("Dispatching to Angular generator")
        generate_angular_client(parsed_spec, resolved_output_path)
        status_message = (
            f"TypeScript Angular client generated for '{api_title}' v{api_version} "
            f"(OpenAPI {openapi_version}). "
            f"Output: {resolved_output_path}"
        )
    elif output_format == ClientFormat.FETCH:
        func_logger.info("Dispatching to Fetch generator")
        generate_fetch_client(parsed_spec, resolved_output_path)
        status_message = (
            f"TypeScript Fetch client generated for '{api_title}' v{api_version} "
            f"(OpenAPI {openapi_version}). "
            f"Output: {resolved_output_path}"
        )
    elif output_format == ClientFormat.AXIOS:
        func_logger.info("Dispatching to Axios generator")
        generate_axios_client(parsed_spec, resolved_output_path)
        status_message = (
            f"TypeScript Axios client generated for '{api_title}' v{api_version} "
            f"(OpenAPI {openapi_version}). "
            f"Output: {resolved_output_path}"
        )
    else:
        # Placeholder for other formats
        func_logger.warning("=" * 80)
        func_logger.warning("CLIENT GENERATION LOGIC NOT IMPLEMENTED FOR THIS FORMAT")
        func_logger.warning("=" * 80)
        status_message = (
            f"TypeScript client generation initiated for '{api_title}' v{api_version} "
            f"(OpenAPI {openapi_version}). "
            f"Format: {output_format.value}, Output: {resolved_output_path}, "
            f"Paths to process: {paths_count}. "
            f"NOTE: Generation logic not yet implemented for this format."
        )

    func_logger.info("=" * 80)
    func_logger.info("Generation process completed")
    func_logger.info(f"Status: {status_message}")
    func_logger.info("=" * 80)

    return status_message


def _validate_openapi_spec(spec: Dict[str, Any], func_logger) -> str:
    """
    Validate that the specification is a valid OpenAPI document.

    Supports both OpenAPI 2.0 (Swagger) and OpenAPI 3.x specifications.

    Args:
        spec: The parsed OpenAPI specification dictionary.
        func_logger: Logger instance for verbose output.

    Returns:
        The detected OpenAPI version string (e.g., "2.0", "3.0.0", "3.1.0").

    Raises:
        ValueError: If the specification is not a valid OpenAPI spec.
    """
    func_logger.debug("Checking for OpenAPI version field in specification")
    func_logger.debug(f"Available top-level keys: {list(spec.keys())}")

    # Check for OpenAPI 3.x (openapi field) or OpenAPI 2.0 (swagger field)
    openapi_version = spec.get("openapi")
    swagger_version = spec.get("swagger")

    func_logger.debug(f"Found 'openapi' field: {openapi_version}")
    func_logger.debug(f"Found 'swagger' field: {swagger_version}")

    detected_version = None

    if openapi_version is not None:
        # OpenAPI 3.x specification
        func_logger.info(f"Detected OpenAPI 3.x specification (version: {openapi_version})")
        func_logger.debug(f"OpenAPI version string: {openapi_version}")

        # Validate version format (should be like 3.0.0, 3.0.1, 3.1.0, etc.)
        if not isinstance(openapi_version, str):
            func_logger.error(f"Invalid openapi version type: {type(openapi_version)}")
            raise ValueError(
                f"Invalid 'openapi' field: expected string, got {type(openapi_version).__name__}"
            )

        if not openapi_version.startswith("3."):
            func_logger.warning(f"Unexpected OpenAPI version format: {openapi_version}")
            func_logger.warning("Expected version starting with '3.' for OpenAPI 3.x specs")

        detected_version = openapi_version
        func_logger.info(f"OpenAPI version validated: {openapi_version}")

    elif swagger_version is not None:
        # OpenAPI 2.0 (Swagger) specification
        func_logger.info(
            f"Detected OpenAPI 2.0 (Swagger) specification (version: {swagger_version})"
        )
        func_logger.debug(f"Swagger version string: {swagger_version}")

        if not isinstance(swagger_version, str):
            func_logger.error(f"Invalid swagger version type: {type(swagger_version)}")
            raise ValueError(
                f"Invalid 'swagger' field: expected string, got {type(swagger_version).__name__}"
            )

        if swagger_version != "2.0":
            func_logger.warning(f"Unexpected Swagger version: {swagger_version}")
            func_logger.warning("Expected version '2.0' for Swagger specifications")

        detected_version = swagger_version
        func_logger.info(f"Swagger version validated: {swagger_version}")

    else:
        # No version field found
        func_logger.error("Missing OpenAPI version field in specification")
        func_logger.error("Expected either 'openapi' (for 3.x) or 'swagger' (for 2.0) field")
        func_logger.debug(f"Available top-level keys: {list(spec.keys())}")
        raise ValueError(
            "Invalid OpenAPI specification: missing version field. "
            "Expected 'openapi' field for OpenAPI 3.x or 'swagger' field for OpenAPI 2.0."
        )

    # Check for required 'info' field
    func_logger.debug("Checking for required 'info' field")
    if "info" not in spec:
        func_logger.error("Missing required 'info' field in specification")
        raise ValueError("Invalid OpenAPI specification: missing required 'info' field.")

    info = spec["info"]
    func_logger.debug(f"Info field contents: {info}")

    # Check for required 'title' in info
    if "title" not in info:
        func_logger.error("Missing required 'title' field in info object")
        raise ValueError("Invalid OpenAPI specification: missing required 'info.title' field.")

    func_logger.info(f"API title found: {info['title']}")

    # Check for required 'version' in info
    if "version" not in info:
        func_logger.error("Missing required 'version' field in info object")
        raise ValueError("Invalid OpenAPI specification: missing required 'info.version' field.")

    func_logger.info(f"API version found: {info['version']}")

    # Check for 'paths' field (optional but log if missing)
    func_logger.debug("Checking for 'paths' field")
    if "paths" not in spec:
        func_logger.warning("No 'paths' field found in specification")
        func_logger.warning("The generated client may have no API methods")
    else:
        paths_count = len(spec["paths"])
        func_logger.info(f"Found {paths_count} path(s) in specification")

    func_logger.info(
        f"OpenAPI specification validation completed successfully (version: {detected_version})"
    )
    return detected_version


def _resolve_output_path(output_path: Union[str, Path], func_logger) -> Path:
    """
    Resolve and validate the output path.

    Args:
        output_path: The output path as string or Path object.
        func_logger: Logger instance for verbose output.

    Returns:
        The resolved absolute Path object.
    """
    func_logger.debug(f"Input output_path: {output_path}")
    func_logger.debug(f"Input output_path type: {type(output_path)}")

    # Convert to Path object
    if isinstance(output_path, str):
        func_logger.debug("Converting string path to Path object")
        path = Path(output_path)
    else:
        path = output_path

    func_logger.debug(f"Path object created: {path}")

    # Resolve to absolute path
    func_logger.debug("Resolving to absolute path")
    absolute_path = path.resolve()
    func_logger.debug(f"Absolute path: {absolute_path}")

    # Check if path exists
    func_logger.debug(f"Checking if path exists: {absolute_path}")
    if absolute_path.exists():
        func_logger.info(f"Output path exists: {absolute_path}")
        func_logger.debug(f"Path is directory: {absolute_path.is_dir()}")
        func_logger.debug(f"Path is file: {absolute_path.is_file()}")

        if absolute_path.is_file():
            func_logger.warning(f"Output path is a file, not a directory: {absolute_path}")
    else:
        func_logger.warning(f"Output path does not exist: {absolute_path}")
        func_logger.info("Directory will need to be created during generation")

    # Log path components
    func_logger.debug(f"Path parts: {absolute_path.parts}")
    func_logger.debug(f"Path parent: {absolute_path.parent}")
    func_logger.debug(f"Path name: {absolute_path.name}")

    # Check write permissions on parent directory
    parent = absolute_path if absolute_path.is_dir() else absolute_path.parent
    if parent.exists():
        func_logger.debug(f"Checking write permissions on: {parent}")
        is_writable = os.access(parent, os.W_OK)
        func_logger.debug(f"Directory is writable: {is_writable}")
        if not is_writable:
            func_logger.warning(f"Directory may not be writable: {parent}")

    func_logger.info(f"Resolved output path: {absolute_path}")
    return absolute_path


def _log_spec_details(spec: Dict[str, Any], func_logger) -> None:
    """
    Log detailed information about the OpenAPI specification.

    Handles both OpenAPI 2.0 (Swagger) and OpenAPI 3.x specifications.

    Args:
        spec: The parsed OpenAPI specification dictionary.
        func_logger: Logger instance for verbose output.
    """
    func_logger.debug("-" * 40)
    func_logger.debug("OpenAPI Specification Details")
    func_logger.debug("-" * 40)

    # Detect version
    is_openapi_3 = "openapi" in spec
    func_logger.debug(f"  Spec Type: {'OpenAPI 3.x' if is_openapi_3 else 'OpenAPI 2.0 (Swagger)'}")
    func_logger.debug(f"  Spec Version: {spec.get('openapi') or spec.get('swagger', 'N/A')}")

    # Info section
    info = spec.get("info", {})
    func_logger.debug(f"  Title: {info.get('title', 'N/A')}")
    func_logger.debug(f"  Version: {info.get('version', 'N/A')}")
    func_logger.debug(
        f"  Description: {info.get('description', 'N/A')[:100] if info.get('description') else 'N/A'}"
    )

    if is_openapi_3:
        # OpenAPI 3.x: servers
        servers = spec.get("servers", [])
        func_logger.debug(f"  Servers: {len(servers)}")
        for i, server in enumerate(servers):
            func_logger.debug(f"    Server {i + 1}: {server.get('url', 'N/A')}")
            if server.get("description"):
                func_logger.debug(f"      Description: {server.get('description')}")
    else:
        # OpenAPI 2.0: host and basePath
        func_logger.debug(f"  Host: {spec.get('host', 'N/A')}")
        func_logger.debug(f"  Base Path: {spec.get('basePath', 'N/A')}")

        # Schemes (OpenAPI 2.0 only)
        schemes = spec.get("schemes", [])
        func_logger.debug(f"  Schemes: {', '.join(schemes) if schemes else 'N/A'}")

        # Consumes and produces (OpenAPI 2.0 only)
        consumes = spec.get("consumes", [])
        produces = spec.get("produces", [])
        func_logger.debug(f"  Consumes: {', '.join(consumes) if consumes else 'N/A'}")
        func_logger.debug(f"  Produces: {', '.join(produces) if produces else 'N/A'}")

    # Paths summary
    paths = spec.get("paths", {})
    func_logger.debug(f"  Total Paths: {len(paths)}")

    if paths:
        func_logger.debug("  Path endpoints:")
        for path_name, path_item in paths.items():
            if isinstance(path_item, dict):
                methods = [
                    m.upper()
                    for m in path_item.keys()
                    if m in ["get", "post", "put", "delete", "patch", "options", "head"]
                ]
                func_logger.debug(f"    {path_name}: {', '.join(methods) if methods else 'N/A'}")

    if is_openapi_3:
        # OpenAPI 3.x: components/schemas
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        func_logger.debug(f"  Total Schemas (Models): {len(schemas)}")
        if schemas:
            func_logger.debug(f"  Schema names: {', '.join(list(schemas.keys())[:10])}")
            if len(schemas) > 10:
                func_logger.debug(f"    ... and {len(schemas) - 10} more")

        # Security schemes (OpenAPI 3.x)
        security_schemes = components.get("securitySchemes", {})
        func_logger.debug(f"  Security Schemes: {len(security_schemes)}")
        if security_schemes:
            for sec_name, sec_def in security_schemes.items():
                func_logger.debug(f"    {sec_name}: {sec_def.get('type', 'unknown')}")
    else:
        # OpenAPI 2.0: definitions
        definitions = spec.get("definitions", {})
        func_logger.debug(f"  Total Definitions (Models): {len(definitions)}")
        if definitions:
            func_logger.debug(f"  Model names: {', '.join(list(definitions.keys())[:10])}")
            if len(definitions) > 10:
                func_logger.debug(f"    ... and {len(definitions) - 10} more")

        # Security definitions (OpenAPI 2.0)
        security_defs = spec.get("securityDefinitions", {})
        func_logger.debug(f"  Security Definitions: {len(security_defs)}")
        if security_defs:
            for sec_name, sec_def in security_defs.items():
                func_logger.debug(f"    {sec_name}: {sec_def.get('type', 'unknown')}")

    # Tags (common to both versions)
    tags = spec.get("tags", [])
    func_logger.debug(f"  Tags: {len(tags)}")
    if tags:
        tag_names = [t.get("name", "unnamed") for t in tags]
        func_logger.debug(f"  Tag names: {', '.join(tag_names)}")

    func_logger.debug("-" * 40)

"""Fetch client generator orchestrator."""

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, PackageLoader

from openapi_ts_client.generators.shared import create_extraction_registry

from .apis import generate_apis
from .docs import generate_docs
from .models import generate_models
from .runtime import generate_runtime


def _get_template_env() -> Environment:
    """Get Jinja2 environment with fetch templates loaded."""
    return Environment(
        loader=PackageLoader("openapi_ts_client", "templates/fetch"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def _generate_root_index(output_path: Path) -> None:
    """
    Generate root index.ts file with barrel exports.

    Args:
        output_path: Directory to write index.ts to
    """
    content = """/* tslint:disable */
/* eslint-disable */
export * from './runtime';
export * from './apis/index';
export * from './models/index';
"""
    (output_path / "index.ts").write_text(content)


def generate_fetch_client(spec: Dict[str, Any], output_path: Path) -> None:
    """
    Generate a Fetch-based TypeScript client from an OpenAPI spec.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write generated files to
    """
    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Create extraction registry for titled anyOf schemas
    # This registry is shared across all generators to ensure consistent type names
    registry = create_extraction_registry(spec)

    # Generate runtime.ts (configuration, base API class, utilities)
    generate_runtime(spec, output_path)

    # Generate model files (interfaces with serialization functions)
    generate_models(spec, output_path, registry=registry)

    # Generate API class files
    generate_apis(spec, output_path)

    # Generate documentation files
    docs_path = output_path / "docs"
    generate_docs(spec, docs_path, registry=registry)

    # Generate root index.ts barrel export
    _generate_root_index(output_path)

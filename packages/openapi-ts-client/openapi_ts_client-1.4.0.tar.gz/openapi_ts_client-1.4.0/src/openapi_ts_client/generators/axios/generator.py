"""Axios client generator orchestrator."""

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, PackageLoader

from openapi_ts_client.generators.shared import create_extraction_registry

from .api import generate_api_ts
from .base import generate_base_ts
from .common import generate_common_ts
from .configuration import generate_configuration_ts
from .docs import generate_docs


def _get_template_env() -> Environment:
    """Get Jinja2 environment with axios templates loaded."""
    return Environment(
        loader=PackageLoader("openapi_ts_client", "templates/axios"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def _generate_index_ts(spec: Dict[str, Any], output_path: Path) -> None:
    """
    Generate index.ts file with barrel exports.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write index.ts to
    """
    env = _get_template_env()
    template = env.get_template("index.ts.j2")

    info = spec.get("info", {})
    content = template.render(
        api_title=info.get("title", ""),
        api_description=info.get("description", ""),
        api_version=info.get("version", ""),
    )

    (output_path / "index.ts").write_text(content)


def generate_axios_client(spec: Dict[str, Any], output_path: Path) -> None:
    """
    Generate an Axios-based TypeScript client from an OpenAPI spec.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write generated files to
    """
    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Create extraction registry for titled anyOf schemas
    registry = create_extraction_registry(spec)

    # Generate base.ts (BASE_PATH, BaseAPI, RequiredError, etc.)
    generate_base_ts(spec, output_path)

    # Generate common.ts (utility functions)
    generate_common_ts(spec, output_path)

    # Generate configuration.ts (Configuration class)
    generate_configuration_ts(spec, output_path)

    # Generate api.ts (all models and API classes)
    generate_api_ts(spec, output_path, registry=registry)

    # Generate index.ts barrel export
    _generate_index_ts(spec, output_path)

    # Generate documentation files
    docs_path = output_path / "docs"
    generate_docs(spec, docs_path, registry=registry)

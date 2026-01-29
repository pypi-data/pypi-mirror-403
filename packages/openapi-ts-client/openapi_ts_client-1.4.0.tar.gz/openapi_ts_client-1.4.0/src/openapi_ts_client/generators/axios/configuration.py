"""Generate configuration.ts for axios client."""

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, PackageLoader


def _get_template_env() -> Environment:
    """Get Jinja2 environment with axios templates loaded."""
    return Environment(
        loader=PackageLoader("openapi_ts_client", "templates/axios"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def generate_configuration_ts(spec: Dict[str, Any], output_path: Path) -> None:
    """
    Generate configuration.ts file from template.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write configuration.ts to
    """
    env = _get_template_env()
    template = env.get_template("configuration.ts.j2")

    # Extract API metadata from spec
    info = spec.get("info", {})
    api_title = info.get("title", "")
    api_description = info.get("description", "")
    api_version = info.get("version", "")

    # Render template with extracted values
    content = template.render(
        api_title=api_title,
        api_description=api_description,
        api_version=api_version,
    )

    # Write the output file
    (output_path / "configuration.ts").write_text(content)

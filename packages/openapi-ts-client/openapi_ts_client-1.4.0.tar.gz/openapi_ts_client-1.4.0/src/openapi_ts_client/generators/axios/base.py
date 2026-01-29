"""Generate base.ts for axios client."""

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


def generate_base_ts(spec: Dict[str, Any], output_path: Path) -> None:
    """
    Generate base.ts file from template.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write base.ts to
    """
    env = _get_template_env()
    template = env.get_template("base.ts.j2")

    # Extract API metadata from spec
    info = spec.get("info", {})
    api_title = info.get("title", "")
    api_description = info.get("description", "")
    api_version = info.get("version", "")

    # Extract base path from servers array
    servers = spec.get("servers", [])
    if servers and isinstance(servers, list) and len(servers) > 0:
        base_path = servers[0].get("url", "http://localhost")
    else:
        base_path = "http://localhost"

    # Render template with extracted values
    content = template.render(
        api_title=api_title,
        api_description=api_description,
        api_version=api_version,
        base_path=base_path,
    )

    # Write the output file
    (output_path / "base.ts").write_text(content)

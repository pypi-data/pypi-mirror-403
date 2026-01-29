"""Generate runtime.ts from template."""

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, PackageLoader, select_autoescape


def get_template_env() -> Environment:
    """Get Jinja2 environment with fetch templates loaded."""
    env = Environment(
        loader=PackageLoader("openapi_ts_client", "templates/fetch"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def generate_runtime(spec: Dict[str, Any], output_path: Path) -> None:
    """
    Generate runtime.ts file from template.

    Args:
        spec: OpenAPI specification dict
        output_path: Directory to write runtime.ts to
    """
    env = get_template_env()
    template = env.get_template("runtime.ts.j2")

    # Extract API metadata from spec
    info = spec.get("info", {})
    api_title = info.get("title", "")
    api_description = info.get("description", "")
    api_version = info.get("version", "")

    # Extract contact email if present
    contact = info.get("contact", {})
    contact_email = contact.get("email", "")

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
        contact_email=contact_email,
        base_path=base_path,
    )

    # Write the output file
    (output_path / "runtime.ts").write_text(content)

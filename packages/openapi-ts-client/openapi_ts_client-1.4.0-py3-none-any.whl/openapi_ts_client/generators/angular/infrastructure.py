"""Generate Angular infrastructure files."""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, PackageLoader, select_autoescape


def get_template_env() -> Environment:
    """Get Jinja2 environment with templates loaded."""
    env = Environment(
        loader=PackageLoader("openapi_ts_client", "templates/angular"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


# Static infrastructure files (no template variables needed)
STATIC_FILES = [
    "index.ts.j2",
    "api.module.ts.j2",
    "provide-api.ts.j2",
    "variables.ts.j2",
    "encoder.ts.j2",
    "param.ts.j2",
    "query.params.ts.j2",
]

# Files that need template variables
TEMPLATED_FILES = [
    "api.base.service.ts.j2",
]


def generate_infrastructure(
    output_path: Path,
    api_title: str,
    contact_email: str,
    base_path: str = "http://localhost",
    security_schemes: Dict[str, Any] = None,
    api_description: str = "",
    api_version: str = "",
    model_files: List[str] = None,
    service_files: List[str] = None,
) -> None:
    """
    Generate all infrastructure files for Angular client.

    Args:
        output_path: Directory to write infrastructure files
        api_title: API title for templated files
        contact_email: Contact email for templated files
        base_path: Base path from OpenAPI servers
        security_schemes: Security schemes from OpenAPI spec
        api_description: API description for README
        api_version: API version for README
        model_files: List of generated model filenames
        service_files: List of generated service filenames
    """
    env = get_template_env()
    generated_files: List[str] = []

    # Generate static files (no variable substitution needed)
    for template_name in STATIC_FILES:
        template = env.get_template(template_name)
        output_name = template_name[:-3]  # Remove .j2 extension
        content = template.render()
        (output_path / output_name).write_text(content)
        generated_files.append(output_name)

    # Generate configuration.ts with security schemes
    config_template = env.get_template("configuration.ts.j2")
    config_content = config_template.render(security_schemes=security_schemes or {})
    (output_path / "configuration.ts").write_text(config_content)
    generated_files.append("configuration.ts")

    # Generate templated files
    for template_name in TEMPLATED_FILES:
        template = env.get_template(template_name)
        output_name = template_name[:-3]  # Remove .j2 extension
        content = template.render(
            api_title=api_title,
            contact_email=contact_email,
            base_path=base_path,
        )
        (output_path / output_name).write_text(content)
        generated_files.append(output_name)

    # Generate README.md
    readme_template = env.get_template("README.md.j2")
    readme_content = readme_template.render(
        api_description=api_description,
        api_version=api_version,
    )
    (output_path / "README.md").write_text(readme_content)
    generated_files.append("README.md")

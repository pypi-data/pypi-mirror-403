"""Angular TypeScript client generator orchestrator."""

from pathlib import Path
from typing import Any, Dict

from openapi_ts_client.logging_config import get_logger
from openapi_ts_client.utils.openapi import load_and_resolve_spec

from .infrastructure import generate_infrastructure
from .models import generate_models
from .services import generate_all_services


def generate_angular_client(
    spec: Dict[str, Any],
    output_path: Path,
) -> None:
    """
    Generate complete Angular TypeScript client.

    Args:
        spec: OpenAPI specification dictionary
        output_path: Directory to write generated files
    """
    logger = get_logger("angular.generator")

    logger.info("Starting Angular client generation")

    # Resolve all $refs
    resolved_spec = load_and_resolve_spec(spec)

    # Extract metadata
    info = resolved_spec.get("info", {})
    api_title = info.get("title", "API")
    api_description = info.get("description", "")
    api_version = info.get("version", "")
    contact = info.get("contact", {})
    contact_email = contact.get("email", "")

    # Extract base path from servers
    servers = resolved_spec.get("servers", [])
    base_path = servers[0].get("url", "http://localhost") if servers else "http://localhost"

    # Extract security schemes
    security_schemes = resolved_spec.get("components", {}).get("securitySchemes", {})

    # Create output directories
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "model").mkdir(exist_ok=True)
    (output_path / "api").mkdir(exist_ok=True)

    # Generate models
    logger.info("Generating models...")
    generate_models(resolved_spec, output_path / "model")

    # Collect model files (includes models.ts barrel export)
    model_files = [f.name for f in (output_path / "model").iterdir() if f.is_file()]

    # Generate services
    logger.info("Generating services...")
    paths = resolved_spec.get("paths", {})
    generate_all_services(paths, output_path / "api", api_title, contact_email, resolved_spec)

    # Collect service files (excludes api.ts barrel export, handled separately)
    service_files = [
        f.name for f in (output_path / "api").iterdir() if f.is_file() and f.name != "api.ts"
    ]

    # Generate infrastructure files
    logger.info("Generating infrastructure files...")
    generate_infrastructure(
        output_path,
        api_title,
        contact_email,
        base_path,
        security_schemes,
        api_description,
        api_version,
        model_files,
        service_files,
    )

    logger.info("Angular client generation complete")

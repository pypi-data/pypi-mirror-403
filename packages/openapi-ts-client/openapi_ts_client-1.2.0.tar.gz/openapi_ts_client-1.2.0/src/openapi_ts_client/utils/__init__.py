"""Shared utilities for OpenAPI TypeScript client generation."""

from .naming import (
    FETCH_RESERVED_TYPE_NAMES,
    TYPESCRIPT_RESERVED_WORDS,
    operation_id_to_method_name,
    schema_to_filename,
    schema_to_type_name,
    tag_to_service_filename,
    tag_to_service_name,
)
from .openapi import load_and_resolve_spec

__all__ = [
    "FETCH_RESERVED_TYPE_NAMES",
    "TYPESCRIPT_RESERVED_WORDS",
    "operation_id_to_method_name",
    "schema_to_filename",
    "schema_to_type_name",
    "tag_to_service_filename",
    "tag_to_service_name",
    "load_and_resolve_spec",
]

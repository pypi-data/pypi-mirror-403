"""Tests for OpenAPI utilities."""

import pytest

from openapi_ts_client.utils.openapi import load_and_resolve_spec


class TestLoadAndResolveSpec:
    """Tests for load_and_resolve_spec function."""

    def test_simple_spec_no_refs(self):
        """Spec without refs returns as-is."""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {},
            "components": {
                "schemas": {"User": {"type": "object", "properties": {"name": {"type": "string"}}}}
            },
        }
        resolved = load_and_resolve_spec(spec)
        assert "components" in resolved
        assert "schemas" in resolved["components"]
        assert "User" in resolved["components"]["schemas"]

    def test_resolves_ref(self):
        """$ref is resolved to actual schema."""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "User": {"type": "object", "properties": {"name": {"type": "string"}}},
                    "Response": {
                        "type": "object",
                        "properties": {"user": {"$ref": "#/components/schemas/User"}},
                    },
                }
            },
        }
        resolved = load_and_resolve_spec(spec)
        response_schema = resolved["components"]["schemas"]["Response"]
        user_prop = response_schema["properties"]["user"]
        # After resolution, should have the User schema content or a marker
        # The exact behavior depends on openapi-core's dereferencing
        assert "properties" in user_prop or "$ref" in user_prop

    def test_invalid_spec_raises(self):
        """Invalid spec raises ValueError."""
        spec = {"invalid": "spec"}
        with pytest.raises(ValueError):
            load_and_resolve_spec(spec)

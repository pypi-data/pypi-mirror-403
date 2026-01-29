"""Tests for anyOf type extraction."""

from openapi_ts_client.generators.shared.anyof_extractor import (
    assign_type_names,
    create_extraction_registry,
    discover_titled_anyofs,
)


class TestDiscoverTitledAnyofs:
    """Tests for discovering titled anyOf schemas."""

    def test_finds_titled_anyof_in_schema_properties(self):
        """Finds anyOf with title in schema properties."""
        spec = {
            "components": {
                "schemas": {
                    "TestSchema": {
                        "properties": {
                            "score": {
                                "anyOf": [{"type": "number"}, {"type": "string"}],
                                "title": "Score",
                                "description": "A score value",
                            }
                        }
                    }
                }
            }
        }
        discoveries = discover_titled_anyofs(spec)
        assert len(discoveries) == 1
        assert discoveries[0]["title"] == "Score"
        assert discoveries[0]["description"] == "A score value"

    def test_ignores_anyof_without_title(self):
        """Ignores anyOf schemas that lack a title."""
        spec = {
            "components": {
                "schemas": {
                    "TestSchema": {
                        "properties": {
                            "value": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            }
                        }
                    }
                }
            }
        }
        discoveries = discover_titled_anyofs(spec)
        assert len(discoveries) == 0

    def test_finds_titled_anyof_in_parameters(self):
        """Finds anyOf with title in operation parameters."""
        spec = {
            "paths": {
                "/api/test": {
                    "get": {
                        "parameters": [
                            {
                                "name": "score",
                                "in": "query",
                                "schema": {
                                    # Complex anyOf: mixed primitive types
                                    "anyOf": [{"type": "number"}, {"type": "string"}],
                                    "title": "Score",
                                },
                            }
                        ]
                    }
                }
            }
        }
        discoveries = discover_titled_anyofs(spec)
        assert len(discoveries) == 1
        assert discoveries[0]["title"] == "Score"


class TestAssignTypeNames:
    """Tests for assigning unique type names."""

    def test_converts_title_to_pascal_case(self):
        """Converts space-separated titles to PascalCase."""
        discoveries = [
            {"path": "/a", "title": "Code Duplication", "description": "", "schema": {}},
        ]
        registry = assign_type_names(discoveries, set())
        assert registry["/a"]["type_name"] == "CodeDuplication"

    def test_assigns_numeric_suffix_for_duplicates(self):
        """Second occurrence of same title gets numeric suffix when schemas differ."""
        # Different anyOf content triggers different type names
        discoveries = [
            {
                "path": "/a",
                "title": "Score",
                "description": "",
                "schema": {"anyOf": [{"type": "number"}]},
            },
            {
                "path": "/b",
                "title": "Score",
                "description": "",
                "schema": {"anyOf": [{"type": "string"}]},
            },
            {
                "path": "/c",
                "title": "Score",
                "description": "",
                "schema": {"anyOf": [{"type": "integer"}]},
            },
        ]
        registry = assign_type_names(discoveries, set())
        assert registry["/a"]["type_name"] == "Score"
        assert registry["/b"]["type_name"] == "Score1"
        assert registry["/c"]["type_name"] == "Score2"

    def test_conflict_with_existing_schema_gets_suffix(self):
        """Title conflicting with existing schema name gets suffix."""
        discoveries = [
            {"path": "/a", "title": "User", "description": "", "schema": {}},
        ]
        existing_schemas = {"User"}
        registry = assign_type_names(discoveries, existing_schemas)
        assert registry["/a"]["type_name"] == "User1"

    def test_deterministic_ordering_by_discovery_order(self):
        """Assignments preserve discovery order (first discovered gets base name)."""
        # Different anyOf content to ensure different type names
        discoveries = [
            {
                "path": "/z/prop",
                "title": "Score",
                "description": "",
                "schema": {"anyOf": [{"type": "string"}]},
            },
            {
                "path": "/a/prop",
                "title": "Score",
                "description": "",
                "schema": {"anyOf": [{"type": "number"}]},
            },
        ]
        registry = assign_type_names(discoveries, set())
        # /z was discovered first, so it gets "Score"
        assert registry["/z/prop"]["type_name"] == "Score"
        assert registry["/a/prop"]["type_name"] == "Score1"


class TestCreateExtractionRegistry:
    """Tests for the main entry point."""

    def test_creates_registry_from_spec(self):
        """Creates complete registry from OpenAPI spec."""
        spec = {
            "components": {
                "schemas": {
                    "ExistingSchema": {"type": "object"},
                    "TestSchema": {
                        "properties": {
                            "score": {
                                # Complex anyOf: mixed primitive types
                                "anyOf": [{"type": "number"}, {"type": "string"}],
                                "title": "Score",
                            }
                        }
                    },
                }
            }
        }
        registry = create_extraction_registry(spec)
        # Should have one entry for the titled anyOf
        assert len(registry) == 1
        path = "/components/schemas/TestSchema/properties/score"
        assert path in registry
        assert registry[path]["type_name"] == "Score"

    def test_returns_empty_for_spec_without_titled_anyofs(self):
        """Returns empty registry when no titled anyOf schemas exist."""
        spec = {"components": {"schemas": {}}}
        registry = create_extraction_registry(spec)
        assert registry == {}

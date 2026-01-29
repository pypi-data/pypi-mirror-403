"""Tests for TypeScript type mapper."""

from openapi_ts_client.generators.shared import (
    map_openapi_type,
    map_openapi_type_with_imports,
)


class TestMapOpenapiTypeBasic:
    """Tests for basic OpenAPI to TypeScript type mapping."""

    def test_string_type(self):
        """string -> string"""
        schema = {"type": "string"}
        assert map_openapi_type(schema) == "string"

    def test_integer_type(self):
        """integer -> number"""
        schema = {"type": "integer"}
        assert map_openapi_type(schema) == "number"

    def test_number_type(self):
        """number -> number"""
        schema = {"type": "number"}
        assert map_openapi_type(schema) == "number"

    def test_boolean_type(self):
        """boolean -> boolean"""
        schema = {"type": "boolean"}
        assert map_openapi_type(schema) == "boolean"

    def test_object_type_no_properties(self):
        """object without properties -> object"""
        schema = {"type": "object"}
        assert map_openapi_type(schema) == "object"

    def test_string_with_format(self):
        """string with date-time format returns Date."""
        schema = {"type": "string", "format": "date-time"}
        assert map_openapi_type(schema) == "Date"


class TestMapOpenapiTypeArrays:
    """Tests for array type mapping."""

    def test_array_of_strings(self):
        """Array of strings."""
        schema = {"type": "array", "items": {"type": "string"}}
        assert map_openapi_type(schema) == "Array<string>"

    def test_array_of_integers(self):
        """Array of integers."""
        schema = {"type": "array", "items": {"type": "integer"}}
        assert map_openapi_type(schema) == "Array<number>"

    def test_array_of_refs(self):
        """Array of schema references."""
        schema = {"type": "array", "items": {"$ref": "#/components/schemas/User"}}
        result, imports = map_openapi_type_with_imports(schema)
        assert result == "Array<User>"
        assert "User" in imports


class TestMapOpenapiTypeRefs:
    """Tests for $ref type mapping."""

    def test_simple_ref(self):
        """$ref extracts schema name."""
        schema = {"$ref": "#/components/schemas/FeedingOut"}
        result, imports = map_openapi_type_with_imports(schema)
        assert result == "FeedingOut"
        assert "FeedingOut" in imports

    def test_nested_ref(self):
        """Nested $ref in properties."""
        schema = {"$ref": "#/components/schemas/BiomeTypeIn"}
        result, imports = map_openapi_type_with_imports(schema)
        assert result == "BiomeTypeIn"
        assert "BiomeTypeIn" in imports


class TestMapOpenapiTypeNullable:
    """Tests for nullable type mapping (anyOf with null)."""

    def test_anyof_string_null(self):
        """anyOf [string, null] -> string | null"""
        schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        assert map_openapi_type(schema) == "string | null"

    def test_anyof_integer_null(self):
        """anyOf [integer, null] -> number | null"""
        schema = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
        assert map_openapi_type(schema) == "number | null"

    def test_anyof_ref_null(self):
        """anyOf [ref, null] -> RefType | null"""
        schema = {"anyOf": [{"$ref": "#/components/schemas/Score"}, {"type": "null"}]}
        result, imports = map_openapi_type_with_imports(schema)
        assert result == "Score | null"
        assert "Score" in imports

    def test_anyof_without_null(self):
        """anyOf without null becomes union."""
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        assert map_openapi_type(schema) == "string | number"


class TestMapOpenapiTypeWithRegistry:
    """Tests for type mapping with extraction registry."""

    def test_titled_anyof_uses_extracted_type(self):
        """Titled anyOf returns extracted type name from registry."""
        schema = {
            "anyOf": [{"type": "number"}, {"type": "string"}],
            "title": "Score",
        }
        registry = {
            "test/path": {
                "type_name": "Score",
                "title": "Score",
                "description": "",
                "schema": schema,
            }
        }
        # Need to pass registry and match by schema identity
        result, imports = map_openapi_type_with_imports(schema, registry)
        assert result == "Score"
        assert "Score" in imports

    def test_untitled_anyof_still_inlines(self):
        """anyOf without title still produces inline union."""
        schema = {
            "anyOf": [{"type": "string"}, {"type": "null"}],
        }
        result, imports = map_openapi_type_with_imports(schema, {})
        assert result == "string | null"

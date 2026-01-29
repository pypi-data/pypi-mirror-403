"""Comprehensive tests for the generator module."""

import json
import tempfile
from pathlib import Path

import pytest

from openapi_ts_client import ClientFormat, generate_typescript_client


class TestGenerateTypescriptClient:
    """Tests for the main generate_typescript_client function."""

    def test_basic_openapi_3_spec_dict(self):
        """Test generation with a basic OpenAPI 3.x spec as dict."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result
        assert "1.0.0" in result
        assert "OpenAPI 3.0.0" in result

    def test_basic_openapi_3_spec_json_string(self):
        """Test generation with a JSON string input."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "String API", "version": "2.0.0"},
            "paths": {},
        }
        json_string = json.dumps(spec)
        result = generate_typescript_client(json_string)
        assert "String API" in result
        assert "2.0.0" in result

    def test_swagger_2_spec(self):
        """Test generation with an OpenAPI 2.0 (Swagger) spec."""
        spec = {
            "swagger": "2.0",
            "info": {"title": "Swagger API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec)
        assert "Swagger API" in result
        assert "OpenAPI 2.0" in result

    def test_with_paths(self):
        """Test that paths are processed successfully."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Path API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {}},
                "/items": {"get": {}, "post": {}},
                "/orders": {"get": {}, "put": {}, "delete": {}},
            },
        }
        result = generate_typescript_client(spec)
        assert "Path API" in result

    def test_default_output_format(self):
        """Test that default format is FETCH."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec)
        # Default format is FETCH - verify successful generation
        assert "Fetch client generated" in result

    def test_axios_output_format(self):
        """Test generation with AXIOS format."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec, output_format=ClientFormat.AXIOS)
        # Axios format now generates a client
        assert "Axios client generated" in result

    def test_angular_output_format(self):
        """Test generation with ANGULAR format."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec, output_format=ClientFormat.ANGULAR)
        # Angular format now actually generates, so check for success message
        assert "Angular client generated" in result

    def test_custom_output_path_string(self):
        """Test generation with custom output path as string."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_typescript_client(spec, output_path=tmpdir)
            assert tmpdir in result or Path(tmpdir).name in result

    def test_custom_output_path_pathlib(self):
        """Test generation with custom output path as Path object."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            result = generate_typescript_client(spec, output_path=path)
            assert tmpdir in result or path.name in result

    def test_generation_returns_success_message(self):
        """Test that result contains success message."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec)
        # Generator now implements full client generation
        assert "Fetch client generated" in result or "Test API" in result


class TestInputValidation:
    """Tests for input validation and error handling."""

    def test_invalid_type_raises_type_error(self):
        """Test that invalid input type raises TypeError."""
        with pytest.raises(TypeError) as excinfo:
            generate_typescript_client(12345)
        assert "must be a dict or JSON string" in str(excinfo.value)

    def test_invalid_type_list_raises_type_error(self):
        """Test that list input raises TypeError."""
        with pytest.raises(TypeError) as excinfo:
            generate_typescript_client([])
        assert "must be a dict or JSON string" in str(excinfo.value)

    def test_invalid_json_yaml_string_raises_value_error(self):
        """Test that string that parses to non-dict raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client("not valid json")
        assert "expected dict" in str(excinfo.value)

    def test_empty_json_object_string(self):
        """Test that empty JSON object raises ValueError for missing version."""
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client("{}")
        assert "missing version field" in str(excinfo.value)


class TestOpenAPIVersionValidation:
    """Tests for OpenAPI version field validation."""

    def test_missing_version_field(self):
        """Test that missing version field raises ValueError."""
        spec = {"info": {"title": "Test", "version": "1.0"}, "paths": {}}
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client(spec)
        assert "missing version field" in str(excinfo.value)

    def test_openapi_version_not_string(self):
        """Test that non-string openapi version raises ValueError."""
        spec = {
            "openapi": 3.0,  # Should be "3.0.0"
            "info": {"title": "Test", "version": "1.0"},
            "paths": {},
        }
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client(spec)
        assert "expected string" in str(excinfo.value)

    def test_swagger_version_not_string(self):
        """Test that non-string swagger version raises ValueError."""
        spec = {
            "swagger": 2.0,  # Should be "2.0"
            "info": {"title": "Test", "version": "1.0"},
            "paths": {},
        }
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client(spec)
        assert "expected string" in str(excinfo.value)

    def test_openapi_3_1_version(self):
        """Test that OpenAPI 3.1 version works."""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec)
        assert "OpenAPI 3.1.0" in result


class TestInfoFieldValidation:
    """Tests for info field validation."""

    def test_missing_info_field(self):
        """Test that missing info field raises ValueError."""
        spec = {"openapi": "3.0.0", "paths": {}}
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client(spec)
        assert "missing required 'info' field" in str(excinfo.value)

    def test_missing_title_in_info(self):
        """Test that missing title in info raises ValueError."""
        spec = {"openapi": "3.0.0", "info": {"version": "1.0.0"}, "paths": {}}
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client(spec)
        assert "missing required 'info.title' field" in str(excinfo.value)

    def test_missing_version_in_info(self):
        """Test that missing version in info raises ValueError."""
        spec = {"openapi": "3.0.0", "info": {"title": "Test"}, "paths": {}}
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client(spec)
        assert "missing required 'info.version' field" in str(excinfo.value)


class TestPathsField:
    """Tests for paths field handling."""

    def test_missing_paths_field_accepted(self):
        """Test that missing paths field is accepted."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result

    def test_empty_paths(self):
        """Test that empty paths is handled correctly."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result


class TestOutputPathResolution:
    """Tests for output path resolution."""

    def test_existing_directory(self):
        """Test with an existing directory."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_typescript_client(spec, output_path=tmpdir)
            assert "Test API" in result

    def test_nonexistent_path(self):
        """Test with a non-existent path creates the directory."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent" / "output"
            result = generate_typescript_client(spec, output_path=str(nonexistent))
            assert "Test API" in result
            assert nonexistent.exists()


class TestOpenAPI3Features:
    """Tests for OpenAPI 3.x specific features."""

    def test_servers_field(self):
        """Test that servers field is handled."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "servers": [
                {"url": "https://api.example.com", "description": "Production"},
                {"url": "https://staging.example.com", "description": "Staging"},
            ],
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result

    def test_components_schemas(self):
        """Test that components/schemas is handled."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "User": {"type": "object"},
                    "Item": {"type": "object"},
                }
            },
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result

    def test_security_schemes(self):
        """Test that securitySchemes is handled."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"},
                }
            },
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result


class TestSwagger2Features:
    """Tests for OpenAPI 2.0 (Swagger) specific features."""

    def test_host_and_basepath(self):
        """Test that host and basePath fields are handled."""
        spec = {
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "host": "api.example.com",
            "basePath": "/v1",
            "paths": {},
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result

    def test_schemes(self):
        """Test that schemes field is handled."""
        spec = {
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "schemes": ["https", "http"],
            "paths": {},
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result

    def test_definitions(self):
        """Test that definitions field is handled."""
        spec = {
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "definitions": {
                "User": {"type": "object"},
                "Item": {"type": "object"},
            },
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result

    def test_consumes_produces(self):
        """Test that consumes and produces fields are handled."""
        spec = {
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "consumes": ["application/json"],
            "produces": ["application/json"],
            "paths": {},
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result

    def test_security_definitions(self):
        """Test that securityDefinitions is handled."""
        spec = {
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "securityDefinitions": {
                "api_key": {"type": "apiKey", "name": "api_key", "in": "header"},
            },
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result


class TestTagsField:
    """Tests for tags field handling."""

    def test_tags_in_spec(self):
        """Test that tags field is handled correctly."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "tags": [
                {"name": "users", "description": "User operations"},
                {"name": "items", "description": "Item operations"},
            ],
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result


class TestPathMethods:
    """Tests for path method handling."""

    def test_all_http_methods(self):
        """Test that all HTTP methods are handled."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/resource": {
                    "get": {},
                    "post": {},
                    "put": {},
                    "delete": {},
                    "patch": {},
                    "options": {},
                    "head": {},
                },
            },
        }
        result = generate_typescript_client(spec)
        assert "Test API" in result


class TestOutputDirectoryNotEmpty:
    """Tests for non-empty output directory handling."""

    def test_error_is_importable(self):
        """Test that OutputDirectoryNotEmptyError can be imported."""
        from openapi_ts_client import OutputDirectoryNotEmptyError

        assert issubclass(OutputDirectoryNotEmptyError, Exception)

    def test_nonempty_raises_error_by_default(self, tmp_path: Path):
        """Test that non-empty directory raises error without flags."""
        from openapi_ts_client import OutputDirectoryNotEmptyError

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        (tmp_path / "existing.ts").touch()
        with pytest.raises(OutputDirectoryNotEmptyError) as excinfo:
            generate_typescript_client(spec, output_path=tmp_path)
        assert "not empty" in str(excinfo.value)
        assert "1 files" in str(excinfo.value)

    def test_clean_true_clears_directory(self, tmp_path: Path):
        """Test that clean=True clears the directory."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        (tmp_path / "old_file.ts").touch()
        generate_typescript_client(spec, output_path=tmp_path, clean=True)
        assert not (tmp_path / "old_file.ts").exists()
        assert (tmp_path / "index.ts").exists()

    def test_force_true_continues_without_clearing(self, tmp_path: Path):
        """Test that force=True continues without clearing."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        (tmp_path / "keep_me.txt").touch()
        generate_typescript_client(spec, output_path=tmp_path, force=True)
        assert (tmp_path / "keep_me.txt").exists()
        assert (tmp_path / "index.ts").exists()

    def test_clean_and_force_raises_error(self, tmp_path: Path):
        """Test that both clean and force raises ValueError."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        with pytest.raises(ValueError) as excinfo:
            generate_typescript_client(spec, output_path=tmp_path, clean=True, force=True)
        assert "mutually exclusive" in str(excinfo.value).lower()

    def test_dotfiles_only_treated_as_empty(self, tmp_path: Path):
        """Test that directory with only dotfiles is treated as empty."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        (tmp_path / ".gitkeep").touch()
        (tmp_path / ".gitignore").touch()
        # Should not raise - dotfiles are ignored
        result = generate_typescript_client(spec, output_path=tmp_path)
        assert "Test API" in result

    def test_empty_directory_proceeds(self, tmp_path: Path):
        """Test that empty directory proceeds normally."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = generate_typescript_client(spec, output_path=tmp_path)
        assert "Test API" in result


class TestGetNonHiddenFiles:
    """Tests for _get_non_hidden_files helper."""

    def test_empty_directory_returns_empty_list(self, tmp_path: Path):
        """Test that empty directory returns empty list."""
        from openapi_ts_client.generator import _get_non_hidden_files

        result = _get_non_hidden_files(tmp_path)
        assert result == []

    def test_returns_non_hidden_files(self, tmp_path: Path):
        """Test that non-hidden files are returned."""
        from openapi_ts_client.generator import _get_non_hidden_files

        (tmp_path / "file1.ts").touch()
        (tmp_path / "file2.ts").touch()
        result = _get_non_hidden_files(tmp_path)
        assert len(result) == 2

    def test_ignores_dotfiles(self, tmp_path: Path):
        """Test that dotfiles are ignored."""
        from openapi_ts_client.generator import _get_non_hidden_files

        (tmp_path / ".gitkeep").touch()
        (tmp_path / ".gitignore").touch()
        result = _get_non_hidden_files(tmp_path)
        assert result == []

    def test_mixed_files(self, tmp_path: Path):
        """Test with mix of hidden and non-hidden files."""
        from openapi_ts_client.generator import _get_non_hidden_files

        (tmp_path / ".gitkeep").touch()
        (tmp_path / "index.ts").touch()
        (tmp_path / "models").mkdir()
        result = _get_non_hidden_files(tmp_path)
        assert len(result) == 2
        names = [p.name for p in result]
        assert "index.ts" in names
        assert "models" in names

    def test_nonexistent_directory_returns_empty(self, tmp_path: Path):
        """Test that nonexistent directory returns empty list."""
        from openapi_ts_client.generator import _get_non_hidden_files

        nonexistent = tmp_path / "nonexistent"
        result = _get_non_hidden_files(nonexistent)
        assert result == []


class TestClearDirectory:
    """Tests for _clear_directory helper."""

    def test_clears_all_files(self, tmp_path: Path):
        """Test that all files are cleared."""
        from openapi_ts_client.generator import _clear_directory

        (tmp_path / "file1.ts").touch()
        (tmp_path / "file2.ts").touch()
        _clear_directory(tmp_path)
        assert list(tmp_path.iterdir()) == []

    def test_clears_subdirectories(self, tmp_path: Path):
        """Test that subdirectories are cleared."""
        from openapi_ts_client.generator import _clear_directory

        subdir = tmp_path / "models"
        subdir.mkdir()
        (subdir / "User.ts").touch()
        _clear_directory(tmp_path)
        assert list(tmp_path.iterdir()) == []

    def test_preserves_directory_itself(self, tmp_path: Path):
        """Test that the directory itself is preserved."""
        from openapi_ts_client.generator import _clear_directory

        (tmp_path / "file.ts").touch()
        _clear_directory(tmp_path)
        assert tmp_path.exists()
        assert tmp_path.is_dir()

    def test_clears_dotfiles_too(self, tmp_path: Path):
        """Test that dotfiles are also cleared."""
        from openapi_ts_client.generator import _clear_directory

        (tmp_path / ".gitkeep").touch()
        (tmp_path / "index.ts").touch()
        _clear_directory(tmp_path)
        assert list(tmp_path.iterdir()) == []

    def test_empty_directory_no_error(self, tmp_path: Path):
        """Test that empty directory doesn't raise error."""
        from openapi_ts_client.generator import _clear_directory

        _clear_directory(tmp_path)
        assert tmp_path.exists()

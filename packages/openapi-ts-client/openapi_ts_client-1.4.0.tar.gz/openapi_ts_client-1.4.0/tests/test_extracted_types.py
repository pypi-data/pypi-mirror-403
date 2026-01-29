"""Tests for extracted type file generation."""

from pathlib import Path

from openapi_ts_client.generators.angular.models import (
    generate_extracted_type_file,
    generate_models,
)


class TestGenerateExtractedTypeFile:
    """Tests for generating extracted type files."""

    def test_generates_empty_interface(self, tmp_path: Path):
        """Generates empty interface file for extracted type."""
        output_dir = tmp_path / "model"
        output_dir.mkdir()

        generate_extracted_type_file(
            type_name="Score",
            description="",
            output_dir=output_dir,
            api_title="Test API",
            contact_email="",
        )

        output_file = output_dir / "score.ts"
        assert output_file.exists()
        content = output_file.read_text()
        assert "export interface Score {" in content

    def test_includes_description_as_jsdoc(self, tmp_path: Path):
        """Includes description as JSDoc comment when provided."""
        output_dir = tmp_path / "model"
        output_dir.mkdir()

        generate_extracted_type_file(
            type_name="CodeDuplication",
            description="Percentage of code duplications in main branch",
            output_dir=output_dir,
            api_title="Test API",
            contact_email="",
        )

        output_file = output_dir / "codeDuplication.ts"
        content = output_file.read_text()
        assert "Percentage of code duplications in main branch" in content
        assert "export interface CodeDuplication {" in content

    def test_returns_filename_without_extension(self, tmp_path: Path):
        """Returns filename without .ts extension for barrel export."""
        output_dir = tmp_path / "model"
        output_dir.mkdir()

        result = generate_extracted_type_file(
            type_name="TestCoverage",
            description="",
            output_dir=output_dir,
            api_title="Test API",
            contact_email="",
        )

        assert result == "testCoverage"


class TestGenerateModelsWithExtraction:
    """Tests for model generation with anyOf extraction."""

    def test_generates_extracted_type_files(self, tmp_path: Path):
        """Generates separate files for titled anyOf schemas."""
        spec = {
            "info": {"title": "Test API"},
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
            },
        }

        generate_models(spec, tmp_path)

        # Should generate both testSchema.ts and score.ts
        assert (tmp_path / "testSchema.ts").exists()
        assert (tmp_path / "score.ts").exists()

        # score.ts should be an empty interface with description
        score_content = (tmp_path / "score.ts").read_text()
        assert "export interface Score {" in score_content
        assert "A score value" in score_content

    def test_extracted_types_in_barrel_export(self, tmp_path: Path):
        """Extracted types are included in models.ts barrel export."""
        spec = {
            "info": {"title": "Test API"},
            "components": {
                "schemas": {
                    "TestSchema": {
                        "properties": {
                            "score": {
                                # Complex anyOf: mixed primitive types
                                "anyOf": [{"type": "number"}, {"type": "string"}],
                                "title": "Score",
                            }
                        }
                    }
                }
            },
        }

        generate_models(spec, tmp_path)

        barrel = (tmp_path / "models.ts").read_text()
        assert "export * from './score';" in barrel
        assert "export * from './testSchema';" in barrel


class TestModelPropertyReferences:
    """Tests for model properties referencing extracted types."""

    def test_property_references_extracted_type(self, tmp_path: Path):
        """Property with titled anyOf references the extracted type."""
        spec = {
            "info": {"title": "Test API"},
            "components": {
                "schemas": {
                    "TestSchema": {
                        "properties": {
                            "score": {
                                "anyOf": [{"type": "number"}, {"type": "string"}],
                                "title": "Score",
                            }
                        }
                    }
                }
            },
        }

        generate_models(spec, tmp_path)

        # testSchema.ts should reference Score, not inline number | string
        content = (tmp_path / "testSchema.ts").read_text()
        assert "score?: Score;" in content
        assert "import { Score } from './score';" in content
        assert "number | string" not in content

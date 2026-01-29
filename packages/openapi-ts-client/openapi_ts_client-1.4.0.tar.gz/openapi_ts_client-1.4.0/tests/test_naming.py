"""Tests for naming utilities."""

from openapi_ts_client.utils.naming import (
    operation_id_to_method_name,
    schema_to_filename,
    tag_to_service_filename,
    tag_to_service_name,
)


class TestSchemaToFilename:
    """Tests for schema_to_filename function."""

    def test_simple_name(self):
        """Simple PascalCase becomes camelCase."""
        assert schema_to_filename("FeedingOut") == "feedingOut.ts"

    def test_single_word(self):
        """Single word gets lowercased."""
        assert schema_to_filename("Score") == "score.ts"

    def test_acronym_preserved(self):
        """Acronyms preserve their casing pattern from fixture."""
        # From fixture: HTTPMetrics -> hTTPMetrics.ts
        assert schema_to_filename("HTTPMetrics") == "hTTPMetrics.ts"

    def test_db_prefix(self):
        """DB prefix follows fixture pattern."""
        # From fixture: DBMetrics -> dBMetrics.ts
        assert schema_to_filename("DBMetrics") == "dBMetrics.ts"

    def test_already_camelcase(self):
        """Already camelCase stays the same."""
        assert schema_to_filename("biomeTypeIn") == "biomeTypeIn.ts"


class TestTagToServiceName:
    """Tests for tag_to_service_name function."""

    def test_simple_tag(self):
        """Simple tag becomes ServiceName."""
        assert tag_to_service_name("Feedings") == "FeedingsService"

    def test_multi_word_tag(self):
        """Multi-word tag preserves casing."""
        assert tag_to_service_name("HealthReports") == "HealthReportsService"

    def test_acronym_tag(self):
        """Acronym tags preserve casing."""
        assert tag_to_service_name("HTTPMetrics") == "HTTPMetricsService"

    def test_spaces_in_tag(self):
        """Spaces are removed and words concatenated."""
        assert tag_to_service_name("Care Plans") == "CarePlansService"


class TestTagToServiceFilename:
    """Tests for tag_to_service_filename function."""

    def test_simple_tag(self):
        """Simple tag becomes lowercase.service.ts."""
        assert tag_to_service_filename("Feedings") == "feedings.service.ts"

    def test_multi_word_tag(self):
        """Multi-word tag becomes camelCase.service.ts."""
        assert tag_to_service_filename("HealthReports") == "healthReports.service.ts"

    def test_acronym_tag(self):
        """Acronym tags follow fixture pattern."""
        # From fixture: HTTPMetrics -> hTTPMetrics.service.ts
        assert tag_to_service_filename("HTTPMetrics") == "hTTPMetrics.service.ts"

    def test_spaces_in_tag(self):
        """Spaces removed, camelCase result."""
        assert tag_to_service_filename("Care Plans") == "carePlans.service.ts"


class TestOperationIdToMethodName:
    """Tests for operation_id_to_method_name function."""

    def test_dotted_path_with_underscores(self):
        """Extract last segment and convert to camelCase."""
        assert operation_id_to_method_name("zoo.api.endpoints.feedings_list_all") == "listAll"

    def test_simple_operation(self):
        """Simple operation ID stays as-is."""
        assert operation_id_to_method_name("count") == "count"

    def test_snake_case(self):
        """Snake case becomes camelCase."""
        assert operation_id_to_method_name("list_all") == "listAll"

    def test_reserved_word_delete(self):
        """Reserved word 'delete' gets underscore prefix."""
        assert operation_id_to_method_name("delete") == "_delete"

    def test_reserved_word_in_path(self):
        """Reserved word at end of path gets underscore prefix."""
        assert operation_id_to_method_name("zoo.api.endpoints.delete") == "_delete"

    def test_decrease_action(self):
        """Action with underscore becomes camelCase."""
        assert (
            operation_id_to_method_name("zoo.api.endpoints.feedings_decrease_action")
            == "decreaseAction"
        )

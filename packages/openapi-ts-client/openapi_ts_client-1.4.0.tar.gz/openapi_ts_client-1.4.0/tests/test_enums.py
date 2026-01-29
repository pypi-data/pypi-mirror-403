"""Tests for the enums module."""

import pytest

from openapi_ts_client import ClientFormat


class TestClientFormat:
    """Tests for the ClientFormat enum."""

    def test_fetch_value(self):
        """Test that FETCH has correct value."""
        assert ClientFormat.FETCH.value == "fetch"

    def test_axios_value(self):
        """Test that AXIOS has correct value."""
        assert ClientFormat.AXIOS.value == "axios"

    def test_angular_value(self):
        """Test that ANGULAR has correct value."""
        assert ClientFormat.ANGULAR.value == "angular"

    def test_str_fetch(self):
        """Test string representation of FETCH."""
        assert str(ClientFormat.FETCH) == "fetch"

    def test_str_axios(self):
        """Test string representation of AXIOS."""
        assert str(ClientFormat.AXIOS) == "axios"

    def test_str_angular(self):
        """Test string representation of ANGULAR."""
        assert str(ClientFormat.ANGULAR) == "angular"

    def test_all_values(self):
        """Test that all expected values exist."""
        values = [e.value for e in ClientFormat]
        assert "fetch" in values
        assert "axios" in values
        assert "angular" in values
        assert len(values) == 3

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert ClientFormat.FETCH in ClientFormat
        assert ClientFormat.AXIOS in ClientFormat
        assert ClientFormat.ANGULAR in ClientFormat

    def test_enum_comparison(self):
        """Test that enum members are equal to themselves."""
        assert ClientFormat.FETCH == ClientFormat.FETCH
        assert ClientFormat.AXIOS == ClientFormat.AXIOS
        assert ClientFormat.ANGULAR == ClientFormat.ANGULAR

    def test_enum_inequality(self):
        """Test that different enum members are not equal."""
        assert ClientFormat.FETCH != ClientFormat.AXIOS
        assert ClientFormat.AXIOS != ClientFormat.ANGULAR
        assert ClientFormat.ANGULAR != ClientFormat.FETCH

    def test_from_value(self):
        """Test creating enum from value."""
        assert ClientFormat("fetch") == ClientFormat.FETCH
        assert ClientFormat("axios") == ClientFormat.AXIOS
        assert ClientFormat("angular") == ClientFormat.ANGULAR

    def test_invalid_value_raises(self):
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            ClientFormat("invalid")

"""Enums for the openapi-ts-client package."""

from enum import Enum


class ClientFormat(Enum):
    """
    Enum representing the output client format for TypeScript client generation.

    Attributes:
        FETCH: Generate a client using the native Fetch API (default).
        AXIOS: Generate a client using Axios HTTP library.
        ANGULAR: Generate a client optimized for Angular applications with services.
    """

    FETCH = "fetch"
    AXIOS = "axios"
    ANGULAR = "angular"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

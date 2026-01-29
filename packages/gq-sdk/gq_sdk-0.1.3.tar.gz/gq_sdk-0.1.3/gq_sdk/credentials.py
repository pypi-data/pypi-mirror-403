"""
Credentials endpoint definitions for the gq-sdk.
"""

from enum import Enum


class Credentials(str, Enum):
    """Credentials API endpoints."""

    LOGIN = "/api/v5/credentials/login"
    LIST = "/api/v5/credentials/list"
    DELETE = "/api/v5/credentials/delete"

    def __str__(self) -> str:
        return self.value

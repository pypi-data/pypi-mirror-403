"""
Authentication endpoint definitions for the gq-sdk.
"""

from enum import Enum


class Auth(str, Enum):
    """Authentication API endpoints."""

    VALIDATE_USER = "/api/v5/auth/validate_user"
    VALIDATE_TOKEN = "/api/v5/auth/validate-token"
    GENERATE_TOKEN = "/api/v5/auth/generate-token"
    LOGOUT = "/api/v5/auth/logout"

    def __str__(self) -> str:
        return self.value

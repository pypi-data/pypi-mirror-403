"""
Authentication HTTP module for the gq-sdk.
"""

from typing import Optional

from ._http_manager import _HTTPManager
from .auth import Auth
from .exceptions import AuthenticationError


class AuthHTTP(_HTTPManager):
    """Authentication HTTP mixin class."""

    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with the GoQuant platform. See documentation for details."""
        payload = {"email": email, "password": password}

        # This endpoint doesn't require prior authentication
        response = self._submit_request(
            method="POST",
            path=Auth.VALIDATE_USER,
            query=payload,
            auth_required=False,
        )

        # Check for successful response
        if (
            isinstance(response, dict)
            and response.get("type") == "success"
            and response.get("data")
        ):
            access_token = response["data"].get("access_token")
            if access_token:
                self.access_token = access_token
                self.authenticated = True
                self.logger.debug("Authentication successful")
                return True

        # Authentication failed
        error_msg = "Invalid credentials or server error"
        if isinstance(response, dict):
            error_msg = response.get("message", error_msg)

        raise AuthenticationError(message=error_msg, email=email)

    def validate_token(self, access_token: Optional[str] = None) -> dict:
        """Validate an access token."""
        token = access_token or self.access_token
        if not token:
            return {"is_valid_token": False, "message": "No token provided"}

        payload = {"access_token": token}

        return self._submit_request(
            method="POST",
            path=Auth.VALIDATE_TOKEN,
            query=payload,
            auth_required=False,
        )

    def logout(self) -> dict:
        """Logout and invalidate the current session."""
        response = self._submit_request(
            method="POST",
            path=Auth.LOGOUT,
            auth_required=True,
        )

        # Clear local authentication state
        self.access_token = None
        self.authenticated = False

        return response

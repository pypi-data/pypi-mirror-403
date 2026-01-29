"""
Custom exceptions for the gq-sdk.

These exceptions provide detailed error information for API failures,
authentication issues, and request errors.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class GQPYError(Exception):
    """Base exception for all gq-sdk errors."""

    pass


class AuthenticationError(GQPYError):
    """
    Exception raised when authentication fails.

    Attributes:
        message -- Explanation of the error.
        email -- The email used in the authentication attempt (if applicable).
    """

    def __init__(self, message: str, email: Optional[str] = None):
        self.message = message
        self.email = email
        super().__init__(f"Authentication failed: {message}")


class FailedRequestError(GQPYError):
    """Exception raised for failed HTTP requests."""

    def __init__(
        self,
        request: str,
        message: str,
        status_code: Optional[int] = None,
        time: Optional[str] = None,
        resp_headers: Optional[Dict[str, Any]] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ):
        self.request = request
        self.message = message
        self.status_code = status_code
        self.time = time or datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.resp_headers = resp_headers
        self.response_body = response_body
        super().__init__(
            f"{message} (ErrCode: {status_code}) (ErrTime: {self.time})"
            f".\nRequest → {request}."
        )


class InvalidRequestError(GQPYError):
    """
    Exception raised for API errors returned by the server.

    Attributes:
        request -- The original request that caused the error.
        message -- Explanation of the error from the API.
        status_code -- The error code returned by the API.
        time -- The time of the error.
        resp_headers -- The response headers from API.
    """

    def __init__(
        self,
        request: str,
        message: str,
        status_code: Optional[int] = None,
        time: Optional[str] = None,
        resp_headers: Optional[Dict[str, Any]] = None,
    ):
        self.request = request
        self.message = message
        self.status_code = status_code
        self.time = time or datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.resp_headers = resp_headers
        super().__init__(
            f"{message} (ErrCode: {status_code}) (ErrTime: {self.time})"
            f".\nRequest → {request}."
        )


class NotAuthenticatedError(GQPYError):
    """
    Exception raised when attempting to use an API that requires authentication
    without being authenticated first.
    """

    def __init__(self, message: str = "Must authenticate first"):
        self.message = message
        super().__init__(message)


class ExchangeLoginError(GQPYError):
    """
    Exception raised when login to an exchange fails.

    Attributes:
        message -- Explanation of the error.
        exchange_name -- The exchange that failed to login.
        account_name -- The account name used.
    """

    def __init__(
        self,
        message: str,
        exchange_name: Optional[str] = None,
        account_name: Optional[str] = None,
    ):
        self.message = message
        self.exchange_name = exchange_name
        self.account_name = account_name
        super().__init__(
            f"Exchange login failed for {exchange_name}/{account_name}: {message}"
        )


class InvalidConfigurationError(GQPYError):
    """
    Exception raised when the SDK is configured with invalid parameters.

    Attributes:
        parameter -- The name of the invalid parameter.
        value -- The invalid value provided.
        message -- Explanation of what's wrong and how to fix it.
    """

    def __init__(
        self,
        parameter: str,
        value: str,
        message: str,
    ):
        self.parameter = parameter
        self.value = value
        self.message = message
        super().__init__(
            f"Invalid configuration for '{parameter}': {message}\n"
            f"  Provided value: {value}"
        )

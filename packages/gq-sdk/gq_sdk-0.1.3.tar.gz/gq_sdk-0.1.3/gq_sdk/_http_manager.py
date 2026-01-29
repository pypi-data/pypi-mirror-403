"""
Core HTTP Manager for the gq-sdk.

This module provides the base HTTP client functionality including:
- Request handling with retries
- Authentication header management
- Error handling and response parsing
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from .exceptions import (
    AuthenticationError,
    FailedRequestError,
    InvalidConfigurationError,
    InvalidRequestError,
    NotAuthenticatedError,
)
from . import _helpers

# Requests will use simplejson if available.
try:
    from simplejson.errors import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError


@dataclass
class _HTTPManager:
    """
    Base HTTP manager for making authenticated requests to the GoQuant API.

    This class handles:
    - Two-level authentication (Client-API-Key and Bearer token)
    - Request retries with configurable delays
    - Error handling and response parsing
    - Logging of requests and responses

    Attributes:
        base_url: The base URL of the GoQuant API server.
        client_api_key: The static client API key for authentication.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts for failed requests.
        retry_delay: Delay between retries in seconds.
        log_requests: Whether to log request/response details.
        logging_level: Logging level for the SDK logger.
    """

    base_url: str
    client_api_key: str
    timeout: int = field(default=30)
    max_retries: int = field(default=3)
    retry_delay: int = field(default=1)
    log_requests: bool = field(default=False)
    logging_level: int = field(default=logging.INFO)

    # Internal state - set after authentication
    access_token: Optional[str] = field(default=None, repr=False)
    authenticated: bool = field(default=False)

    def __post_init__(self):
        """Initialize the HTTP session and logger after dataclass creation."""
        # Validate base_url
        self._validate_base_url()
        
        # Validate client_api_key
        self._validate_client_api_key()
        
        # Clean up base URL
        self.base_url = self.base_url.rstrip("/")

        # Setup logger
        self.logger = logging.getLogger(__name__)
        if len(logging.root.handlers) == 0:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            handler.setLevel(self.logging_level)
            self.logger.addHandler(handler)

        self.logger.debug("Initializing HTTP session.")

        # Initialize requests session
        self.client = requests.Session()
        self.client.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Client-API-Key": self.client_api_key,
            }
        )

    def _validate_base_url(self) -> None:
        """
        Validate the base_url configuration.
        
        Raises:
            InvalidConfigurationError: If base_url is invalid.
        """
        if not self.base_url:
            raise InvalidConfigurationError(
                parameter="base_url",
                value="(empty)",
                message="base_url cannot be empty. Please provide your GoQuant backend URL."
            )
        
        # Check for placeholder values
        placeholder_patterns = ["<", ">", "your-", "example", "placeholder"]
        base_url_lower = self.base_url.lower()
        for pattern in placeholder_patterns:
            if pattern in base_url_lower:
                raise InvalidConfigurationError(
                    parameter="base_url",
                    value=self.base_url,
                    message=(
                        "base_url appears to be a placeholder value. "
                        "Please replace it with your actual GoQuant backend URL.\n"
                        "  Example: 'https://api.goquant.io'"
                    )
                )
        
        # Check for valid URL scheme
        if not self.base_url.startswith(("http://", "https://")):
            raise InvalidConfigurationError(
                parameter="base_url",
                value=self.base_url,
                message=(
                    "base_url must start with 'http://' or 'https://'. "
                    f"Did you mean 'https://{self.base_url}'?"
                )
            )

    def _validate_client_api_key(self) -> None:
        """
        Validate the client_api_key configuration.
        
        Raises:
            InvalidConfigurationError: If client_api_key is invalid.
        """
        if not self.client_api_key:
            raise InvalidConfigurationError(
                parameter="client_api_key",
                value="(empty)",
                message="client_api_key cannot be empty. Please provide your GoQuant client API key."
            )
        
        # Check for placeholder values
        placeholder_patterns = ["<", ">", "your-", "example", "placeholder"]
        api_key_lower = self.client_api_key.lower()
        for pattern in placeholder_patterns:
            if pattern in api_key_lower:
                raise InvalidConfigurationError(
                    parameter="client_api_key",
                    value=self.client_api_key,
                    message=(
                        "client_api_key appears to be a placeholder value. "
                        "Please replace it with your actual GoQuant client API key."
                    )
                )

    def _prepare_headers(self) -> Dict[str, str]:
        """
        Prepare headers for a request.

        Returns:
            Dictionary of headers including auth token if authenticated.
        """
        headers = {
            "Content-Type": "application/json",
            "Client-API-Key": self.client_api_key,
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _submit_request(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        auth_required: bool = True,
    ) -> Any:
        """
        Submit an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API endpoint path.
            query: Request parameters/body.
            auth_required: Whether authentication is required for this request.

        Returns:
            Parsed JSON response from the API.

        Raises:
            NotAuthenticatedError: If auth is required but not authenticated.
            FailedRequestError: If the request fails after retries.
            InvalidRequestError: If the API returns an error response.
        """
        if auth_required and not self.authenticated:
            raise NotAuthenticatedError()

        # Clean query parameters
        query = self._clean_query(query)
        retries_attempted = self.max_retries

        while retries_attempted > 0:
            retries_attempted -= 1
            try:
                # Prepare request
                url = f"{self.base_url}{path}"
                headers = self._prepare_headers()

                # Log request if enabled
                if self.log_requests:
                    self.logger.debug(
                        f"Request -> {method} {url}. Body: {query}. Headers: {headers}"
                    )

                # Make request
                if method.upper() == "GET":
                    response = self.client.request(
                        method=method,
                        url=url,
                        params=query,
                        headers=headers,
                        timeout=self.timeout,
                    )
                else:
                    response = self.client.request(
                        method=method,
                        url=url,
                        json=query,
                        headers=headers,
                        timeout=self.timeout,
                    )

                # Check HTTP status
                if response.status_code != 200:
                    self._handle_http_error(response, method, path, query)

                # Parse and return response
                return self._handle_response(response, method, path, query)

            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
            ) as e:
                if retries_attempted > 0:
                    self.logger.error(f"{e}. Retrying...")
                    time.sleep(self.retry_delay)
                else:
                    raise FailedRequestError(
                        request=f"{method} {path}: {query}",
                        message=str(e),
                        status_code=None,
                        time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    )

            except JSONDecodeError as e:
                if retries_attempted > 0:
                    self.logger.error(f"JSON decode error: {e}. Retrying...")
                    time.sleep(self.retry_delay)
                else:
                    raise FailedRequestError(
                        request=f"{method} {path}",
                        message="Could not decode JSON response.",
                        status_code=None,
                        time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    )

        raise FailedRequestError(
            request=f"{method} {path}: {query}",
            message="Bad Request. Retries exceeded maximum.",
            status_code=400,
            time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
        )

    def _clean_query(self, query: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Clean query parameters by removing None values.

        Args:
            query: Dictionary of query parameters.

        Returns:
            Cleaned dictionary with None values removed.
        """
        if query is None:
            return {}
        return {k: v for k, v in query.items() if v is not None}

    def _handle_http_error(
        self,
        response: requests.Response,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]],
    ) -> None:
        """Handle HTTP error responses."""
        # Try to extract error message and body from response
        error_msg = "HTTP status code is not 200."
        response_body = None
        
        try:
            response_body = response.json()
            if isinstance(response_body, dict):
                # Try common error message fields
                error_msg = (
                    response_body.get("message") 
                    or response_body.get("error") 
                    or response_body.get("detail")
                    or error_msg
                )
        except (JSONDecodeError, ValueError):
            pass
        
        # Fallback to generic messages for specific status codes
        if error_msg == "HTTP status code is not 200.":
            if response.status_code == 403:
                error_msg = "Access forbidden. Check your API key."
            elif response.status_code == 401:
                error_msg = "Unauthorized. Check your authentication."

        self.logger.debug(f"Response text: {response.text}")

        raise FailedRequestError(
            request=f"{method} {path}: {query}",
            message=error_msg,
            status_code=response.status_code,
            time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            resp_headers=dict(response.headers),
            response_body=response_body,
        )

    def _handle_response(
        self,
        response: requests.Response,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]],
    ) -> Any:
        """
        Handle and parse API response.

        Args:
            response: The HTTP response object.
            method: HTTP method used.
            path: API endpoint path.
            query: Request parameters.

        Returns:
            Parsed JSON response.

        Raises:
            InvalidRequestError: If the API returns an error in the response body.
        """
        try:
            s_json = response.json()
        except JSONDecodeError:
            raise FailedRequestError(
                request=f"{method} {path}",
                message="Could not decode JSON response.",
                status_code=response.status_code,
                time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            )

        if self.log_requests:
            self.logger.debug(f"Response: {s_json}")

        # Check for error in response body
        if isinstance(s_json, dict):
            # Check for error field
            if s_json.get("error") and isinstance(s_json["error"], bool):
                error_msg = s_json.get("message", s_json.get("body", "Unknown error"))
                raise InvalidRequestError(
                    request=f"{method} {path}: {query}",
                    message=error_msg,
                    status_code=s_json.get("status_code"),
                    time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    resp_headers=dict(response.headers),
                )

            # Check for type field (GoTrade response format)
            if s_json.get("type") == "error":
                error_msg = s_json.get("message", "Unknown error")
                raise InvalidRequestError(
                    request=f"{method} {path}: {query}",
                    message=error_msg,
                    status_code=s_json.get("code"),
                    time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    resp_headers=dict(response.headers),
                )

        return s_json

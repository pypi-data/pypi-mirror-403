"""
Credentials HTTP module for the gq-sdk.
"""

from typing import Any, Dict, Optional

from ._http_manager import _HTTPManager
from .credentials import Credentials
from .exceptions import ExchangeLoginError, FailedRequestError, NotAuthenticatedError


class CredentialsHTTP(_HTTPManager):
    """Credentials HTTP mixin class."""

    def login_exchange(
        self,
        exchange_name: str,
        account_name: str,
        api_key: str,
        api_secret: str,
        api_password: str = "",
        is_testnet: bool = True,
        mode: Optional[str] = "",
    ) -> Dict[str, Any]:
        """Login to an exchange account. See documentation for details."""
        if not self.authenticated:
            raise NotAuthenticatedError(
                "Must authenticate with GoQuant before logging into an exchange"
            )

        payload = {
            "exchange_name": exchange_name,
            "account_name": account_name,
            "key": api_key,
            "secret": api_secret,
            "password": api_password,
            "is_testnet": is_testnet,
            "authenticate": True,
            "mode": mode,
        }

        try:
            response = self._submit_request(
                method="POST",
                path=Credentials.LOGIN,
                query=payload,
                auth_required=True,
            )

            # Return the exact API response
            return response

        except FailedRequestError as e:
            # Check if account already exists - return the API response as success
            if "already exists" in e.message.lower() or "already logged in" in e.message.lower():
                self.logger.info(e.message)
                # Return the actual API response body if available
                if e.response_body:
                    return e.response_body
                return {"type": "success", "message": e.message}

            raise ExchangeLoginError(
                message=e.message,
                exchange_name=exchange_name,
                account_name=account_name,
            )

        except Exception as e:
            raise ExchangeLoginError(
                message=str(e),
                exchange_name=exchange_name,
                account_name=account_name,
            )

    def list_credentials(self) -> list:
        """List all registered exchange credentials."""
        response = self._submit_request(
            method="GET",
            path=Credentials.LIST,
            auth_required=True,
        )

        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and "data" in response:
            return response["data"]

        return []

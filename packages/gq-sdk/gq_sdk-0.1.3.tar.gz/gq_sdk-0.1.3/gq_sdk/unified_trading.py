"""
Unified Trading Client for the gq-sdk.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from ._v5_auth import AuthHTTP
from ._v5_credentials import CredentialsHTTP
from ._v5_market_edge import MarketEdgeHTTP
from ._v5_limit_edge import LimitEdgeHTTP
from ._v5_twap_edge import TwapEdgeHTTP
from ._v5_exchange import ExchangeHTTP


@dataclass
class Client(
    AuthHTTP,
    CredentialsHTTP,
    MarketEdgeHTTP,
    LimitEdgeHTTP,
    TwapEdgeHTTP,
    ExchangeHTTP,
):
    """
    GoQuant Trading Client.

    For documentation, visit: https://docs.goquant.io
    """

    def __init__(
        self,
        base_url: str,
        client_api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1,
        log_requests: bool = False,
        logging_level: int = logging.INFO,
    ):
        """Initialize the client."""
        object.__setattr__(self, "base_url", base_url)
        object.__setattr__(self, "client_api_key", client_api_key)
        object.__setattr__(self, "timeout", timeout)
        object.__setattr__(self, "max_retries", max_retries)
        object.__setattr__(self, "retry_delay", retry_delay)
        object.__setattr__(self, "log_requests", log_requests)
        object.__setattr__(self, "logging_level", logging_level)
        object.__setattr__(self, "access_token", None)
        object.__setattr__(self, "authenticated", False)

        self.__post_init__()

    def __repr__(self) -> str:
        return (
            f"Client(base_url='{self.base_url}', "
            f"authenticated={self.authenticated})"
        )

"""
Exchange endpoint definitions for the gq-sdk.
"""

from enum import Enum


class Exchange(str, Enum):
    """Exchange data API endpoints."""

    # Account data endpoints (with path parameters)
    BALANCE = "/api/v5/exchange/account/balance/{exchange}/{account}"
    POSITIONS = "/api/v5/exchange/account/positions/{exchange}/{account}"

    # Algorithm endpoints
    ALGO_ORDERS = "/api/v5/exchange/algo-orders"
    ALGO_STATUS = "/api/v5/exchange/algo-status"

    def __str__(self) -> str:
        return self.value

    def format(self, **kwargs) -> str:
        """Format the endpoint path with the given parameters."""
        return self.value.format(**kwargs)

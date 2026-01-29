"""
Trade endpoint definitions for the gq-sdk.
"""

from enum import Enum


class Trade(str, Enum):
    """Trade API endpoints."""

    PLACE_ORDER = "/api/v5/gotrade/order/place"
    CANCEL_ALGO = "/api/v5/gotrade/order/cancel_algo"
    MODIFY_ALGO = "/api/v5/gotrade/order/modify_algo"

    def __str__(self) -> str:
        return self.value

"""
Limit Edge HTTP module for the gq-sdk.
"""

from typing import Any, Dict, Optional

from ._http_manager import _HTTPManager
from .trade import Trade
from . import _helpers


class LimitEdgeHTTP(_HTTPManager):
    """Limit Edge HTTP mixin class."""

    def place_limit_edge_order(
        self,
        exchange_name: str,
        account_name: str,
        symbol: str,
        side: str,
        quantity: float,
        duration: int,
        threshold_value: float,
        threshold_type: str = "percentage",
        algorithm_type: str = "limit_edge",
        price: Optional[float] = None,
        client_algo_id: Optional[str] = None,
        instrument_type: str = "",
        **kwargs,
    ) -> Optional[str]:
        """Place a limit edge order. See documentation for details."""
        if threshold_type not in ["percentage", "dollar"]:
            raise ValueError(
                f"threshold_type must be 'percentage' or 'dollar', got '{threshold_type}'"
            )

        if client_algo_id is None:
            client_algo_id = _helpers.generate_client_algo_id()

        payload: Dict[str, Any] = {
            "exchange_name": exchange_name,
            "account_name": account_name,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "algorithm_type": algorithm_type,
            "duration": duration,
            "threshold": {
                "value": threshold_value,
                "type": threshold_type,
            },
            "client_algo_id": client_algo_id,
            "instrument_type": instrument_type,
        }

        if price is not None:
            payload["price"] = price

        payload.update(kwargs)

        response = self._submit_request(
            method="POST",
            path=Trade.PLACE_ORDER,
            query=payload,
            auth_required=True,
        )

        if isinstance(response, dict) and response.get("type") == "error":
            self.logger.error(f"Order placement failed: {response.get('message')}")
            return None

        return client_algo_id

"""
TWAP Edge HTTP module for the gq-sdk.
"""

from typing import Any, Dict, Optional

from ._http_manager import _HTTPManager
from .trade import Trade
from . import _helpers


class TwapEdgeHTTP(_HTTPManager):
    """TWAP Edge HTTP mixin class."""

    def place_twap_edge_order(
        self,
        exchange_name: str,
        account_name: str,
        symbol: str,
        side: str,
        quantity: float,
        duration: int,
        interval: int,
        decay_factor: float = 1.0,
        algorithm_type: str = "twap_edge",
        client_algo_id: Optional[str] = None,
        instrument_type: str = "",
        **kwargs,
    ) -> Optional[str]:
        """Place a TWAP edge order. See documentation for details."""
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
            "decay_factor": decay_factor,
            "interval": interval,
            "client_algo_id": client_algo_id,
            "instrument_type": instrument_type,
        }

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

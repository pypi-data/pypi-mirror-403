"""
Market Edge HTTP module for the gq-sdk.
"""

from typing import Any, Dict, Optional

from ._http_manager import _HTTPManager
from .trade import Trade
from . import _helpers


class MarketEdgeHTTP(_HTTPManager):
    """Market Edge HTTP mixin class."""

    def place_market_edge_order(
        self,
        exchange_name: str,
        account_name: str,
        symbol: str,
        side: str,
        quantity: float,
        duration: int = 600,
        decay_factor: float = 1.0,
        algorithm_type: str = "market_edge",
        client_algo_id: Optional[str] = None,
        stop_loss_pct: Optional[float] = None,
        stop_loss_px: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        take_profit_px: Optional[float] = None,
        instrument_type: str = "",
        **kwargs,
    ) -> Optional[str]:
        """Place a market edge order. See documentation for details."""
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
            "client_algo_id": client_algo_id,
            "instrument_type": instrument_type,
        }

        # Add stop loss parameters
        if stop_loss_pct is not None:
            payload["stop_loss_pct"] = stop_loss_pct
        if stop_loss_px is not None:
            payload["stop_loss_px"] = stop_loss_px

        # Add take profit parameters
        if take_profit_pct is not None:
            payload["take_profit_pct"] = take_profit_pct
        if take_profit_px is not None:
            payload["take_profit_px"] = take_profit_px

        # Add any additional kwargs
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

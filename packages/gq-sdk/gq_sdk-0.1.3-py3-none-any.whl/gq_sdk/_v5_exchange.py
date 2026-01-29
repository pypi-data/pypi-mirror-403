"""
Exchange HTTP module for the gq-sdk.
"""

from typing import Any, Dict, List, Optional, Union

from ._http_manager import _HTTPManager
from .exchange import Exchange
from .trade import Trade
from . import _helpers


class ExchangeHTTP(_HTTPManager):
    """Exchange HTTP mixin class."""

    def get_account_balance(
        self,
        exchange_name: str,
        account_name: str,
        asset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get account balance. See documentation for details."""
        # Format the endpoint path
        path = Exchange.BALANCE.format(
            exchange=exchange_name.lower(),
            account=account_name,
        )

        response = self._submit_request(
            method="GET",
            path=path,
            auth_required=True,
        )

        # Process response
        if not response or not isinstance(response, dict):
            return response

        if "account_data" not in response:
            return response

        account_data = response["account_data"]

        # Handle different response formats
        if isinstance(account_data, list):
            balances_list = account_data
        elif isinstance(account_data, dict) and "data" in account_data:
            balances_list = account_data["data"]
        else:
            balances_list = []

        currency_balances = []
        total_equity = 0.0
        available_assets = []

        for bal_info in balances_list:
            currency = bal_info.get("ccy", "")
            if currency:
                available_assets.append(currency)

            # Apply asset filter
            if asset and asset.lower() != "all":
                if currency.upper() != asset.upper():
                    continue

            eq_usd = _helpers.safe_float(bal_info.get("eq_usd", 0))
            total_equity += eq_usd

            currency_balances.append({
                "currency": currency,
                "available_balance": bal_info.get("avail_bal", bal_info.get("avail_eq", "0")),
                "total_balance": bal_info.get("eq", "0"),
                "equity_usd": bal_info.get("eq_usd", "0"),
                "cash_balance": bal_info.get("cash_bal", "0"),
                "frozen_balance": bal_info.get("frozen_bal", "0"),
            })

        if asset and asset.lower() != "all" and not currency_balances:
            return {
                "error": True,
                "message": f"Asset '{asset}' not found in account balance",
                "exchange_name": response.get("exchange_name", exchange_name),
                "account_name": response.get("account_name", account_name),
                "currency_balances": [],
                "available_assets": available_assets,
            }

        return {
            "exchange_name": response.get("exchange_name", exchange_name),
            "account_name": response.get("account_name", account_name),
            "total_equity": total_equity,
            "currency_balances": currency_balances,
            "available_assets": available_assets,
        }

    def get_account_positions(
        self,
        exchange_name: str,
        account_name: str,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get account positions. See documentation for details."""
        path = Exchange.POSITIONS.format(
            exchange=exchange_name.lower(),
            account=account_name,
        )

        response = self._submit_request(
            method="GET",
            path=path,
            auth_required=True,
        )

        if not response or not isinstance(response, dict):
            return response

        if "position_data" not in response:
            return response

        position_data = response["position_data"]

        # Handle different formats
        if isinstance(position_data, dict) and "data" in position_data:
            positions_list = position_data["data"]
        elif isinstance(position_data, dict):
            positions_list = []
            for pos_symbol, pos_info in position_data.items():
                pos_info["symbol"] = pos_symbol
                positions_list.append(pos_info)
        elif isinstance(position_data, list):
            positions_list = position_data
        else:
            positions_list = []

        positions = []
        available_symbols = []

        for pos_info in positions_list:
            pos_symbol = pos_info.get("symbol", "")
            if pos_symbol:
                available_symbols.append(pos_symbol)

            # Apply symbol filter
            if symbol and symbol.lower() != "all":
                if pos_symbol.upper() != symbol.upper():
                    continue

            positions.append({
                "symbol": pos_symbol,
                "position_size": pos_info.get("pos", 0),
                "fee": pos_info.get("fee", 0),
                "notional_usd": pos_info.get("notional_usd", pos_info.get("notional", 0)),
                "unrealized_pnl": pos_info.get("upl", 0),
                "realized_pnl": pos_info.get("realized_pnl", pos_info.get("realizedPnl", 0)),
                "average_price": pos_info.get("avg_price", pos_info.get("entry_price", 0)),
                "entry_price": pos_info.get("entry_price", pos_info.get("avg_price", 0)),
            })

        if symbol and symbol.lower() != "all" and not positions:
            return {
                "error": True,
                "message": f"Symbol '{symbol}' not found in account positions",
                "exchange_name": response.get("exchange_name", exchange_name),
                "account_name": response.get("account_name", account_name),
                "positions": [],
                "available_symbols": available_symbols,
            }

        return {
            "exchange_name": response.get("exchange_name", exchange_name),
            "account_name": response.get("account_name", account_name),
            "positions": positions,
            "available_symbols": available_symbols,
        }

    def fetch_algo_orders(self, algorithm_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Fetch orders for a given algorithm ID."""
        # Ensure algorithm_id is an integer for the API
        if isinstance(algorithm_id, str):
            try:
                algorithm_id = int(algorithm_id)
            except ValueError:
                self.logger.warning(
                    f"Could not convert algorithm_id '{algorithm_id}' to integer"
                )

        payload = {"algorithm_id": algorithm_id}

        response = self._submit_request(
            method="POST",
            path=Exchange.ALGO_ORDERS,
            query=payload,
            auth_required=True,
        )

        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            if "orders" in response:
                return response["orders"]
            elif "data" in response and isinstance(response["data"], list):
                return response["data"]

        return []

    def fetch_algo_status(self, algorithm_id: Union[str, int]) -> Dict[str, Any]:
        """Fetch status for a given algorithm ID."""
        # Ensure algorithm_id is an integer for the API
        if isinstance(algorithm_id, str):
            try:
                algorithm_id = int(algorithm_id)
            except ValueError:
                self.logger.warning(
                    f"Could not convert algorithm_id '{algorithm_id}' to integer"
                )

        payload = {"algorithm_id": algorithm_id}

        response = self._submit_request(
            method="POST",
            path=Exchange.ALGO_STATUS,
            query=payload,
            auth_required=True,
        )

        if not isinstance(response, dict):
            return {"status": "unknown", "status_details": {}, "full_response": response}

        # Extract status and status details
        status = response.get("state", "unknown")
        algorithm_update = response.get("algorithm_update", {})
        status_details = (
            algorithm_update.get(status, {})
            if isinstance(algorithm_update, dict)
            else {}
        )

        return {
            "status": status,
            "status_details": status_details,
            "full_response": response,
        }

    def cancel_algorithm(
        self,
        exchange_name: str,
        algorithm_type: str,
        client_algo_id: Union[str, int],
    ) -> Dict[str, Any]:
        """Cancel an active algorithm."""
        payload = {
            "exchange_name": exchange_name,
            "algorithm_type": algorithm_type,
            "client_algo_id": client_algo_id,
        }

        response = self._submit_request(
            method="POST",
            path=Trade.CANCEL_ALGO,
            query=payload,
            auth_required=True,
        )

        return response

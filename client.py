"""
Binance Futures Testnet REST client.

Wraps raw HMAC-signed requests to the Binance USDT-M Futures Testnet API.
Keeps HTTP/auth concerns separate from business logic.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

BASE_URL = "https://testnet.binancefuture.com"

logger = setup_logger("client")


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""


class BinanceFuturesClient:
    """
    Lightweight Binance USDT-M Futures Testnet client.

    Uses direct REST calls (requests) — no third-party SDK dependency.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self._api_key})

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Append server timestamp and HMAC-SHA256 signature to params."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> Any:
        """
        Execute an HTTP request and return parsed JSON.

        Args:
            method:  HTTP verb ("GET", "POST", …).
            path:    API path, e.g. "/fapi/v1/order".
            params:  Query / body parameters.
            signed:  Whether to add timestamp + signature.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            BinanceClientError: on API-level errors.
            requests.RequestException: on network failures.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = self._base_url + path
        logger.debug("REQUEST  %s %s  params=%s", method, url, params)

        try:
            if method.upper() in ("GET", "DELETE"):
                resp = self._session.request(method, url, params=params, timeout=10)
            else:
                resp = self._session.request(method, url, data=params, timeout=10)
        except requests.RequestException as exc:
            logger.error("Network error: %s", exc)
            raise

        logger.debug("RESPONSE status=%s body=%s", resp.status_code, resp.text[:500])

        data = resp.json()

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            msg = data.get("msg", "Unknown API error")
            logger.error("API error %s: %s", data["code"], msg)
            raise BinanceClientError(f"[{data['code']}] {msg}")

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> dict:
        """Fetch exchange metadata (symbol list, filters, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account_info(self) -> dict:
        """Fetch futures account balances and positions."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **kwargs) -> dict:
        """
        Place a new futures order.

        Keyword args are passed directly as POST parameters.
        Required by Binance: symbol, side, type, quantity.
        Optional: price (LIMIT), timeInForce, stopPrice, etc.
        """
        return self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order by ID."""
        return self._request(
            "DELETE",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def get_open_orders(self, symbol: str | None = None) -> list:
        """List open orders, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

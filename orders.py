"""
Order placement logic — business layer between the CLI and the raw client.

Constructs the correct Binance parameter set for each order type,
calls the client, and returns a structured result dict.
"""

from __future__ import annotations

from typing import Any

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger

logger = setup_logger("orders")

# Time-in-force used for LIMIT orders
DEFAULT_TIF = "GTC"


def _build_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
    stop_price: float | None = None,
    time_in_force: str = DEFAULT_TIF,
) -> dict[str, Any]:
    """
    Build the raw parameter dict for a Binance Futures order.

    Args:
        symbol:        Trading pair, e.g. "BTCUSDT".
        side:          "BUY" or "SELL".
        order_type:    "MARKET", "LIMIT", or "STOP_MARKET".
        quantity:      Contract quantity.
        price:         Limit price (required for LIMIT).
        stop_price:    Stop trigger price (required for STOP_MARKET).
        time_in_force: "GTC", "IOC", "FOK" — only for LIMIT.

    Returns:
        Dict ready to be sent as POST parameters.
    """
    params: dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("price is required for LIMIT orders.")
        params["price"] = price
        params["timeInForce"] = time_in_force

    elif order_type == "STOP_MARKET":
        if stop_price is None:
            raise ValueError("stopPrice is required for STOP_MARKET orders.")
        params["stopPrice"] = stop_price

    return params


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
    stop_price: float | None = None,
    time_in_force: str = DEFAULT_TIF,
) -> dict[str, Any]:
    """
    Build, log, and submit an order via *client*.

    Returns:
        A result dict with keys:
            success (bool), order_id, status, executed_qty,
            avg_price, raw_response, error (on failure).
    """
    params = _build_order_params(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        time_in_force=time_in_force,
    )

    logger.info(
        "Placing %s %s order | symbol=%s qty=%s price=%s stop=%s",
        side,
        order_type,
        symbol,
        quantity,
        price,
        stop_price,
    )

    try:
        response = client.place_order(**params)
    except Exception as exc:
        logger.error("Order placement failed: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "raw_response": None,
        }

    logger.info(
        "Order accepted | orderId=%s status=%s executedQty=%s avgPrice=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
        response.get("avgPrice"),
    )

    return {
        "success": True,
        "order_id": response.get("orderId"),
        "client_order_id": response.get("clientOrderId"),
        "symbol": response.get("symbol"),
        "side": response.get("side"),
        "type": response.get("type"),
        "status": response.get("status"),
        "orig_qty": response.get("origQty"),
        "executed_qty": response.get("executedQty"),
        "avg_price": response.get("avgPrice"),
        "price": response.get("price"),
        "time_in_force": response.get("timeInForce"),
        "raw_response": response,
    }

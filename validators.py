"""
Input validation helpers for the trading bot CLI.
All functions raise ValueError with descriptive messages on failure.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_side(side: str) -> str:
    """Ensure side is BUY or SELL (case-insensitive). Returns normalised value."""
    normalised = side.strip().upper()
    if normalised not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}"
        )
    return normalised


def validate_order_type(order_type: str) -> str:
    """Ensure order_type is a supported type (case-insensitive). Returns normalised value."""
    normalised = order_type.strip().upper()
    if normalised not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}"
        )
    return normalised


def validate_symbol(symbol: str) -> str:
    """Basic symbol sanity check — non-empty and alphanumeric."""
    normalised = symbol.strip().upper()
    if not normalised:
        raise ValueError("Symbol cannot be empty.")
    if not normalised.isalnum():
        raise ValueError(
            f"Symbol '{symbol}' contains invalid characters. "
            "Expected an alphanumeric string like BTCUSDT."
        )
    return normalised


def validate_quantity(quantity: str | float) -> float:
    """Parse and validate quantity — must be a positive number."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be positive, got {qty}.")
    return qty


def validate_price(price: str | float | None, order_type: str) -> float | None:
    """
    Parse and validate price.

    - LIMIT and STOP_MARKET orders require a positive price.
    - MARKET orders ignore price (returns None).
    """
    order_type = order_type.upper()
    if order_type == "MARKET":
        return None  # price irrelevant for market orders

    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Price '{price}' is not a valid number.")
    if p <= 0:
        raise ValueError(f"Price must be positive, got {p}.")
    return p


def validate_stop_price(stop_price: str | float | None, order_type: str) -> float | None:
    """Stop price is only required for STOP_MARKET orders."""
    if order_type.upper() != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValueError("--stop-price is required for STOP_MARKET orders.")
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be positive, got {sp}.")
    return sp

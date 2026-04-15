#!/usr/bin/env python3
"""
cli.py — Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples:
    python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 80000
    python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 75000
    python cli.py orders --symbol BTCUSDT
    python cli.py balance
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from bot.client import BinanceClientError, BinanceFuturesClient
from bot.logging_config import setup_logger
from bot.orders import place_order
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger("cli")

# ──────────────────────────────────────────────────────────────────────────────
# Pretty-print helpers
# ──────────────────────────────────────────────────────────────────────────────

SEPARATOR = "─" * 60


def _section(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def _print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
    stop_price: float | None,
) -> None:
    _section("ORDER REQUEST SUMMARY")
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price is not None:
        print(f"  Price      : {price}")
    if stop_price is not None:
        print(f"  Stop Price : {stop_price}")


def _print_order_result(result: dict) -> None:
    if result["success"]:
        _section("ORDER RESPONSE ✓")
        print(f"  Order ID      : {result.get('order_id')}")
        print(f"  Client OID    : {result.get('client_order_id')}")
        print(f"  Symbol        : {result.get('symbol')}")
        print(f"  Side          : {result.get('side')}")
        print(f"  Type          : {result.get('type')}")
        print(f"  Status        : {result.get('status')}")
        print(f"  Original Qty  : {result.get('orig_qty')}")
        print(f"  Executed Qty  : {result.get('executed_qty')}")
        print(f"  Avg Price     : {result.get('avg_price')}")
        print(f"  Limit Price   : {result.get('price')}")
        print(f"  Time-in-Force : {result.get('time_in_force')}")
        print(f"\n  ✅ Order placed successfully!\n")
    else:
        _section("ORDER FAILED ✗")
        print(f"  Error : {result.get('error')}")
        print(f"\n  ❌ Order placement failed.\n")


# ──────────────────────────────────────────────────────────────────────────────
# Sub-command handlers
# ──────────────────────────────────────────────────────────────────────────────

def cmd_place(args: argparse.Namespace, client: BinanceFuturesClient) -> int:
    """Validate inputs, print summary, place order, print result."""
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        print(f"\n  ⚠️  Validation error: {exc}\n")
        logger.warning("Validation error: %s", exc)
        return 1

    _print_order_summary(symbol, side, order_type, quantity, price, stop_price)

    result = place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    _print_order_result(result)
    return 0 if result["success"] else 1


def cmd_orders(args: argparse.Namespace, client: BinanceFuturesClient) -> int:
    """List open orders for an optional symbol."""
    symbol = validate_symbol(args.symbol) if args.symbol else None
    logger.info("Fetching open orders (symbol=%s)", symbol)
    try:
        orders = client.get_open_orders(symbol=symbol)
    except (BinanceClientError, Exception) as exc:
        print(f"\n  ❌ Failed to fetch orders: {exc}\n")
        logger.error("Failed to fetch open orders: %s", exc)
        return 1

    _section(f"OPEN ORDERS{' — ' + symbol if symbol else ''}")
    if not orders:
        print("  (no open orders)")
    else:
        for o in orders:
            print(
                f"  [{o.get('orderId')}] {o.get('symbol')} "
                f"{o.get('side')} {o.get('type')} "
                f"qty={o.get('origQty')} price={o.get('price')} "
                f"status={o.get('status')}"
            )
    print()
    return 0


def cmd_balance(args: argparse.Namespace, client: BinanceFuturesClient) -> int:
    """Print USDT balance from the futures account."""
    logger.info("Fetching account balance")
    try:
        account = client.get_account_info()
    except (BinanceClientError, Exception) as exc:
        print(f"\n  ❌ Failed to fetch balance: {exc}\n")
        logger.error("Failed to fetch account info: %s", exc)
        return 1

    assets = account.get("assets", [])
    _section("ACCOUNT BALANCE")
    usdt_assets = [a for a in assets if float(a.get("walletBalance", 0)) > 0]
    if not usdt_assets:
        print("  (no non-zero balances)")
    for asset in usdt_assets:
        print(
            f"  {asset.get('asset'):<10} "
            f"wallet={float(asset.get('walletBalance', 0)):.4f}  "
            f"unrealised PnL={float(asset.get('unrealizedProfit', 0)):.4f}"
        )
    print()
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet trading bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("BINANCE_API_KEY"),
        help="Binance Testnet API key (or set BINANCE_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret",
        default=os.getenv("BINANCE_API_SECRET"),
        help="Binance Testnet API secret (or set BINANCE_API_SECRET env var)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── place ──────────────────────────────────────────────────────────────
    place_p = sub.add_parser("place", help="Place a new order")
    place_p.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    place_p.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side")
    place_p.add_argument(
        "--type", required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        help="Order type",
    )
    place_p.add_argument("--quantity", required=True, type=float, help="Contract quantity")
    place_p.add_argument("--price", type=float, default=None, help="Limit price (LIMIT orders)")
    place_p.add_argument(
        "--stop-price", dest="stop_price",
        type=float, default=None,
        help="Stop trigger price (STOP_MARKET orders)",
    )

    # ── orders ─────────────────────────────────────────────────────────────
    orders_p = sub.add_parser("orders", help="List open orders")
    orders_p.add_argument("--symbol", default=None, help="Filter by symbol")

    # ── balance ────────────────────────────────────────────────────────────
    sub.add_parser("balance", help="Show account balance")

    return parser


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.api_key or not args.api_secret:
        parser.error(
            "API credentials are required. "
            "Pass --api-key / --api-secret or set BINANCE_API_KEY / BINANCE_API_SECRET."
        )

    client = BinanceFuturesClient(api_key=args.api_key, api_secret=args.api_secret)

    command_map = {
        "place": cmd_place,
        "orders": cmd_orders,
        "balance": cmd_balance,
    }

    handler = command_map[args.command]
    try:
        exit_code = handler(args, client)
    except KeyboardInterrupt:
        print("\n  Interrupted by user.\n")
        logger.info("Session interrupted by user.")
        exit_code = 0

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

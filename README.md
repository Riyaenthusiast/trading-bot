# 🤖 Binance Futures Testnet Trading Bot

A clean, production-structured Python trading bot that places **Market**, **Limit**, and **Stop-Market** orders on the **Binance USDT-M Futures Testnet** via a typed CLI.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance REST client (HMAC-signed requests)
│   ├── orders.py            # Order placement business logic
│   ├── validators.py        # Input validation helpers
│   └── logging_config.py   # Structured logging (file + console)
├── cli.py                   # Argparse CLI entry point
├── logs/                    # Auto-created; log files written here
│   └── trading_bot_YYYYMMDD.log
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Register on Binance Futures Testnet

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Sign in with your GitHub account
3. Go to **API Key** → click **Generate HMAC_SHA256 Key**
4. Copy your **API Key** and **Secret Key** — the secret is shown only once

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set credentials

**Option A — environment variables (recommended):**
```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

**Option B — pass directly per command:**
```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET place ...
```

---

## Usage

All commands follow this shape:
```
python cli.py [--api-key KEY] [--api-secret SECRET] <command> [options]
```

### Place a MARKET order

```bash
# Buy 0.001 BTC at market price
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Sell 0.01 ETH at market price
python cli.py place --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
# Sell 0.001 BTC with a limit at $99,500
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 99500

# Buy 0.01 ETH with a limit at $3,200
python cli.py place --symbol ETHUSDT --side BUY --type LIMIT --quantity 0.01 --price 3200
```

### Place a STOP_MARKET order (bonus order type)

```bash
# Protective stop-sell: trigger a market sell if BTC drops to $95,000
python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 95000
```

### List open orders

```bash
python cli.py orders                       # all symbols
python cli.py orders --symbol BTCUSDT      # filtered
```

### Check account balance

```bash
python cli.py balance
```

---

## Sample Output

```
────────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001

────────────────────────────────────────────────────────────
  ORDER RESPONSE ✓
────────────────────────────────────────────────────────────
  Order ID      : 4022876304
  Client OID    : web_aBcDeFgHiJkLmNoPqRsT
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Original Qty  : 0.001
  Executed Qty  : 0.001
  Avg Price     : 97423.50
  Limit Price   : 0
  Time-in-Force : GTC

  ✅ Order placed successfully!
```

---

## Logging

Logs are written to `logs/trading_bot_YYYYMMDD.log` automatically.

- **Console**: INFO level and above (clean summaries)
- **File**: DEBUG level and above (full request params + raw API responses)

Example log entries:
```
2025-07-14 09:12:01 | INFO     | orders | Placing BUY MARKET order | symbol=BTCUSDT qty=0.001 price=None stop=None
2025-07-14 09:12:02 | DEBUG    | client | REQUEST  POST https://testnet.binancefuture.com/fapi/v1/order  params={...}
2025-07-14 09:12:02 | DEBUG    | client | RESPONSE status=200 body={...}
2025-07-14 09:12:02 | INFO     | orders | Order accepted | orderId=4022876304 status=FILLED executedQty=0.001 avgPrice=97423.50
```

---

## Validation & Error Handling

| Scenario | Behaviour |
|---|---|
| Missing required field | Clear error message, exit code 1 |
| Invalid side / type | Validation error with allowed values |
| Non-positive quantity or price | Validation error with the bad value |
| LIMIT order without price | Validation error |
| STOP_MARKET without stop-price | Validation error |
| API error (e.g. insufficient margin) | Logs error code + Binance message |
| Network timeout / connection refused | Logs exception, returns failure result |
| Missing API credentials | argparse error before any network call |

---

## Assumptions

- **Testnet only** — the base URL is hardcoded to `https://testnet.binancefuture.com`. Swap `BASE_URL` in `bot/client.py` to go live (with appropriate caution).
- **One-way mode** — orders use `positionSide=BOTH` (default). Hedge-mode is not supported.
- **Quantity precision** — the testnet is lenient about precision; a production bot should query `exchangeInfo` and round to the symbol's `stepSize`.
- **No order book depth check** — market orders execute at whatever price the testnet fills them at.
- **Stop-Market trigger** — uses `workingType=CONTRACT_PRICE` (Binance default).

---

## Bonus Feature

**STOP_MARKET** orders are implemented as the bonus third order type, allowing traders to place protective stop-loss orders that trigger a market order when a specified price level is hit.

---

## Requirements

- Python 3.9+
- `requests>=2.31.0`
- A Binance Futures Testnet account with API credentials

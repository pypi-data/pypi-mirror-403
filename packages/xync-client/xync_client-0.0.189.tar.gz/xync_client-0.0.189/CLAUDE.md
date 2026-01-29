# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```bash
make install      # Install dependencies and pre-commit hooks (uses venv/bin/python)
make test         # Run pytest tests
make clean        # Clean cache, dist, egg-info
make build        # Build the package (python -m build)
make twine        # Build and upload to PyPI
make patch        # Create git tag from version and push
make all          # Run: install, test, clean, build
```

Single test: `venv/bin/python -m pytest tests/TestEx.py -k test_name`

## Linting

Ruff (line-length 120) runs automatically via pre-commit hooks. Pre-commit also auto-tags commits with `feat:` or `fix:` prefixes.

## Architecture

This is a **Python async client library for cryptocurrency P2P exchange platforms**. It provides a unified interface for trading across multiple exchanges (Binance, Bybit, OKX, HTX, BingX, Gate, etc.) and payment method providers.

### Core Class Hierarchy (Abc/)

- **BaseExClient** - Exchange public API client (currencies, coins, payment methods, ads)
- **BaseAuthClient** - Authentication mixin with auto-refresh on 401
- **BaseAgentClient** - User-specific client for private methods (orders, credentials)
- **BaseOrderClient** - Order operations (mark_payed, confirm, cancel, appeal flow)
- **BaseInAgentClient** - Inbound event handler (WebSocket/polling for notifications)
- **PmAgentClient** - Payment method agent operations

### Directory Structure

```
xync_client/
├── Abc/                 # Abstract base classes and data types (xtype.py)
├── <Exchange>/          # Binance, Bybit, OKX, HTX, BingX, Gate, etc.
│   ├── ex.py           # ExClient implementation
│   ├── agent.py        # AgentClient implementation
│   ├── order.py        # OrderClient implementation
│   └── etype/          # Exchange-specific data types
└── Pms/                 # Payment method providers (Alfa, Sber, Tinkoff, Payeer, etc.)
```

### Key Patterns

- **Async-first**: All I/O operations use async/await
- **Bidirectional ID mapping**: Each exchange has `x2e` (internal→exchange) and `e2x` (exchange→internal) converters
- **Pydantic models**: Data validation/serialization throughout
- **Payment normalization**: `PmUnifier` normalizes payment method names across exchanges
- **Database ORM**: Tortoise ORM with models from `xync_schema`
- **Model.client() factory**: DB models (`Agent`, `Ex`, `PmAgent`) have `.client()` methods that instantiate corresponding client classes
- **Dependency injection**: External services (`XyncBot`, `FileClient`) are passed as method parameters where needed, not stored as class attributes

### Order State Flow

Orders follow a state machine: requested → created → payed → completed/canceled. Appeals can be started after payment, with dispute/counter-dispute flow. See README.md for full mermaid diagram.

## Dependencies

- **HTTP**: aiohttp (via x_client.aiohttp.Client)
- **Database**: tortoise-orm
- **Exchange SDKs**: bybit-p2p, python-binance, python-okx, pybit, asynchuobi
- **Telegram**: kurigram, pyrogram-client
- **Internal**: xn-client, xync-schema, xync-bot

### External Services

- **XyncBot** (`xync_bot`) - Telegram bot for notifications (2FA codes, price alerts)
- **FileClient** (`pyro_client`) - File transfer client for documents/screenshots

## Environment Variables

Copy `.env.sample` to `.env`. Key vars: `POSTGRES_*` (DB connection), `TOKEN` (bot token), `TG_API_ID`/`TG_API_HASH` (Telegram).

Config is loaded in `xync_client/loader.py`: `PAY_TOKEN`, `NET_TOKEN`, `TORM` (Tortoise ORM config), `PRX` (proxy).

## Development

Each exchange module (`Bybit/agent.py`, `Mexc/agent.py`, etc.) has a `main()` function for testing/debugging. Run directly: `venv/bin/python -m xync_client.Bybit.agent`

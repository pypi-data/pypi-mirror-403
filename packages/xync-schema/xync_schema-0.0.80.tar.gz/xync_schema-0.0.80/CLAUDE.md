# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `xync-schema`, a shared database schema package for the XyncNet project. It defines Tortoise ORM models for a P2P cryptocurrency trading platform with multi-exchange support.

## Commands

```bash
# Install dependencies
pip install -r requirements.dev.txt

# Run tests (also runs as pre-commit hook)
pytest

# Run a single test
pytest tests/test_db.py::test_init_db

# Initialize database schema
python -m xync_schema
```

## Environment Setup

Requires PostgreSQL. Copy `.env.sample` to `.env` and set `DB_URL` connection string.

## Architecture

### Core Domain Modules

- **`xync_schema/models.py`** - All Tortoise ORM models (~70 models)
- **`xync_schema/enums.py`** - IntEnum definitions for statuses and types
- **`xync_schema/graph.py`** - Order state machine transitions (OrderStatus -> OrderAction -> OrderStatus)
- **`xync_schema/xtype.py`** - Pydantic types for exchange API interop

### Key Model Relationships

**Exchange Domain:**
- `Ex` (Exchange) -> `Actor` (exchange account) -> `Agent` (authenticated session)
- `Coin`/`Cur` (crypto/fiat) linked to exchanges via `CoinEx`/`CurEx` through-tables
- `Pair` (coin/cur trading pair) -> `PairSide` (buy/sell direction) -> `PairEx` (pair on exchange)

**P2P Trading:**
- `Ad` (P2P advertisement) -> `MyAd` (managed ad with race tracking)
- `Order` (trade) references `Ad`, `Cred` (payment credential), `Actor` as taker/maker
- `Hot` (warm-up session) aggregates ads and orders for a user trading session

**Payment Methods:**
- `Pm` (payment method) -> `PmCur` (pm+currency) -> `PmEx` (pm on exchange)
- `Cred` (user's payment credential) -> `CredEx` (credential on specific exchange)

**Users:**
- `Person` -> `User` (Telegram user extension) with Ed25519 keypair for signing
- `Transaction` - internal transfer with cryptographic proof (sender + validator signatures)

### Conventions

- Uses custom unsigned integer fields: `UInt1Field`, `UInt2Field`, `UInt4Field`, `UInt8Field`
- Monetary values stored as integers with scale factor (e.g., `/10^cur.scale`)
- `_name` class attribute defines fields for model string representation
- Dynamic client loading via `Ex.client()`, `Agent.client()`, `Pm.client()` from `xync_client` package
- `TsTrait` mixin adds `created_at`/`updated_at` timestamps
- `CASCADE` on_update for all foreign keys

### Dependencies

- `tortoise-orm` with asyncpg for PostgreSQL
- `xn-auth` and `x_model` - shared authentication/model utilities
- `aerich` - database migrations
- `cryptography` - Ed25519 for transaction signing
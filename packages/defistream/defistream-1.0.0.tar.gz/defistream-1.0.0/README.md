# DeFiStream Python Client

Official Python client for the [DeFiStream API](https://defistream.dev) - access historical DeFi events from 45+ EVM networks.

## Installation

```bash
pip install defistream
```

This includes pandas and pyarrow by default for DataFrame support.

With polars support (in addition to pandas):
```bash
pip install defistream[polars]
```

## Quick Start

```python
from defistream import DeFiStream

# Initialize client (reads DEFISTREAM_API_KEY from environment if not provided)
client = DeFiStream()

# Or with explicit API key
client = DeFiStream(api_key="dsk_your_api_key")

# Query ERC20 transfers using builder pattern
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_dict()
)

for transfer in transfers:
    print(f"{transfer['sender']} -> {transfer['receiver']}: {transfer['amount']}")
```

## Features

- **Builder pattern**: Fluent query API with chainable methods
- **Type-safe**: Full type hints and Pydantic models
- **Multiple formats**: JSON, CSV, Parquet, pandas DataFrame, polars DataFrame
- **Async support**: Native async/await with `AsyncDeFiStream`
- **All protocols**: AAVE, Uniswap, Lido, ERC20, Native tokens, and more
- **Verbose mode**: Include all metadata fields (tx_hash, tx_id, log_index, network, name)

## Supported Protocols

| Protocol | Events |
|----------|--------|
| ERC20 | `transfers`, `approvals` |
| Native Token | `transfers` |
| AAVE V3 | `deposits`, `withdrawals`, `borrows`, `repays`, `liquidations` |
| Uniswap V3 | `swaps`, `mints`, `burns` |
| Lido | `deposits`, `withdrawals` |
| Stader | `deposits`, `withdrawals` |
| Threshold | `mints`, `burns` |

## Usage Examples

### Builder Pattern

The client uses a fluent builder pattern. The query is only executed when you call a terminal method like `as_dict()`, `as_df()`, or `as_file()`.

```python
from defistream import DeFiStream

client = DeFiStream()

# Build query step by step
query = client.erc20.transfers("USDT")
query = query.network("ETH")
query = query.start_block(24000000)
query = query.end_block(24100000)
query = query.min_amount(1000)

# Execute and get results
transfers = query.as_dict()

# Or chain everything
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .min_amount(1000)
    .as_dict()
)
```

### ERC20 Transfers

```python
# Get USDT transfers over 10,000 USDT
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .min_amount(10000)
    .as_dict()
)

# Filter by sender
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .sender("0x28c6c06298d514db089934071355e5743bf21d60")
    .as_dict()
)

# Or use aliases: from_address/to_address
transfers = (
    client.erc20.transfers()
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .token("USDC")
    .from_address("0x...")
    .to_address("0x...")
    .as_dict()
)
```

### AAVE Events

```python
# Get deposits
deposits = (
    client.aave.deposits()
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_dict()
)

# Get liquidations for a specific user
liquidations = (
    client.aave.liquidations()
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .user("0x...")
    .as_dict()
)
```

### Uniswap Swaps

```python
# Get swaps for WETH/USDC pool with 0.05% fee tier
swaps = (
    client.uniswap.swaps("WETH", "USDC", 500)
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_dict()
)

# Or build with chain methods
swaps = (
    client.uniswap.swaps()
    .symbol0("WETH")
    .symbol1("USDC")
    .fee(500)
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_dict()
)
```

### Native Token Transfers

```python
# Get ETH transfers >= 1 ETH
transfers = (
    client.native_token.transfers()
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .min_amount(1.0)
    .as_dict()
)
```

### Verbose Mode

By default, responses omit metadata fields to reduce payload size. Use `.verbose()` to include all fields:

```python
# Default: compact response (no tx_hash, tx_id, log_index, network, name)
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_dict()
)
# Returns: [{"block_number": 24000050, "sender": "0x...", "receiver": "0x...", "amount": 1000.0, ...}]

# Verbose: includes all metadata fields
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .verbose()
    .as_dict()
)
# Returns: [{"name": "TransferEvent", "network": "ETH", "tx_id": "0x...", "tx_hash": "0x...", "log_index": 5, "block_number": 24000050, ...}]
```

### Return as DataFrame

```python
# As pandas DataFrame (default)
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_df()
)

# As polars DataFrame
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_df("polars")
)
```

### Save to File

Format is automatically determined by file extension:

```python
# Save as CSV
(
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_file("transfers.csv")
)

# Save as Parquet
(
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_file("transfers.parquet")
)

# Save as JSON
(
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_file("transfers.json")
)

# Explicit format (when path has no extension)
(
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_file("transfers", format="csv")
)
```

### Async Usage

```python
import asyncio
from defistream import AsyncDeFiStream

async def main():
    async with AsyncDeFiStream() as client:
        transfers = await (
            client.erc20.transfers("USDT")
            .network("ETH")
            .start_block(24000000)
            .end_block(24100000)
            .as_dict()
        )
        print(f"Found {len(transfers)} transfers")

asyncio.run(main())
```

### Multiple Networks in Parallel

```python
import asyncio
from defistream import AsyncDeFiStream

async def fetch_all_networks():
    async with AsyncDeFiStream() as client:
        networks = ["ETH", "ARB", "BASE", "OP"]
        tasks = [
            client.erc20.transfers("USDC")
            .network(net)
            .start_block(24000000)
            .end_block(24100000)
            .as_dict()
            for net in networks
        ]
        results = await asyncio.gather(*tasks)
        return dict(zip(networks, results))

all_transfers = asyncio.run(fetch_all_networks())
```

## Configuration

### Environment Variables

```bash
export DEFISTREAM_API_KEY=dsk_your_api_key
export DEFISTREAM_BASE_URL=https://api.defistream.dev/v1  # optional
```

```python
from defistream import DeFiStream

# API key from environment
client = DeFiStream()

# Or explicit
client = DeFiStream(api_key="dsk_...", base_url="https://api.defistream.dev/v1")
```

### Timeout and Retries

```python
client = DeFiStream(
    api_key="dsk_...",
    timeout=60.0,  # seconds
    max_retries=3
)
```

## Error Handling

```python
from defistream import DeFiStream
from defistream.exceptions import (
    DeFiStreamError,
    AuthenticationError,
    QuotaExceededError,
    RateLimitError,
    ValidationError
)

client = DeFiStream()

try:
    transfers = (
        client.erc20.transfers("USDT")
        .network("ETH")
        .start_block(24000000)
        .end_block(24100000)
        .as_dict()
    )
except AuthenticationError:
    print("Invalid API key")
except QuotaExceededError as e:
    print(f"Quota exceeded. Remaining: {e.remaining}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except DeFiStreamError as e:
    print(f"API error: {e}")
```

## Response Headers

Access rate limit and quota information:

```python
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .start_block(24000000)
    .end_block(24100000)
    .as_dict()
)

# Access response metadata
print(f"Rate limit: {client.last_response.rate_limit}")
print(f"Remaining quota: {client.last_response.quota_remaining}")
print(f"Request cost: {client.last_response.request_cost}")
```

## Builder Methods Reference

### Common Methods (all protocols)

| Method | Description |
|--------|-------------|
| `.network(net)` | Set network (ETH, ARB, BASE, OP, etc.) |
| `.start_block(n)` | Set starting block number |
| `.end_block(n)` | Set ending block number |
| `.block_range(start, end)` | Set both start and end blocks |
| `.start_time(ts)` | Set starting time (ISO format or Unix timestamp) |
| `.end_time(ts)` | Set ending time (ISO format or Unix timestamp) |
| `.time_range(start, end)` | Set both start and end times |
| `.verbose()` | Include all metadata fields |

### Filter Methods

| Method | Protocols | Description |
|--------|-----------|-------------|
| `.sender(addr)` | ERC20, Native | Filter by sender address |
| `.receiver(addr)` | ERC20, Native | Filter by receiver address |
| `.from_address(addr)` | ERC20, Native | Alias for sender |
| `.to_address(addr)` | ERC20, Native | Alias for receiver |
| `.min_amount(amt)` | ERC20, Native | Minimum transfer amount |
| `.token(symbol)` | ERC20 | Token symbol (USDT, USDC, etc.) |
| `.owner(addr)` | ERC20 Approvals, Lido | Filter by owner |
| `.spender(addr)` | ERC20 Approvals | Filter by spender |
| `.user(addr)` | AAVE | Filter by user |
| `.reserve(addr)` | AAVE | Filter by reserve |
| `.liquidator(addr)` | AAVE Liquidations | Filter by liquidator |
| `.symbol0(sym)` | Uniswap | First token symbol |
| `.symbol1(sym)` | Uniswap | Second token symbol |
| `.fee(tier)` | Uniswap | Fee tier (100, 500, 3000, 10000) |
| `.pool(addr)` | Uniswap | Pool address |

### Terminal Methods

| Method | Description |
|--------|-------------|
| `.as_dict()` | Execute and return list of dicts (JSON) |
| `.as_df()` | Execute and return pandas DataFrame |
| `.as_df("polars")` | Execute and return polars DataFrame |
| `.as_file(path)` | Execute and save to file (format from extension) |
| `.as_file(path, format="csv")` | Execute and save with explicit format |

## License

MIT License

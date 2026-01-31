# Moonwell Adapter

Adapter for interacting with the [Moonwell](https://moonwell.fi/) lending protocol on Base chain.

- Entrypoint: `adapters.moonwell_adapter.adapter.MoonwellAdapter`
- Tests: `test_adapter.py`

## Capabilities

The adapter provides the following capabilities:

- Lending: Supply and withdraw tokens
- Borrowing: Borrow and repay tokens
- Collateral management: Enable/disable markets as collateral
- Rewards: Claim WELL token rewards
- Position & market queries: Get balances, APYs, and liquidity info

## Overview

The MoonwellAdapter provides functionality for:

- **Lending**: Supply tokens to earn yield
- **Borrowing**: Borrow against collateral
- **Collateral Management**: Enable/disable markets as collateral
- **Rewards**: Claim WELL token rewards
- **Position Queries**: Get balances, APYs, and liquidity info

## Supported Markets (Base Chain)

| Token  | mToken Address                               | Underlying Address                           |
| ------ | -------------------------------------------- | -------------------------------------------- |
| USDC   | `0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22` | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| WETH   | `0x628ff693426583D9a7FB391E54366292F509D457` | `0x4200000000000000000000000000000000000006` |
| wstETH | `0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b` | `0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452` |

## Protocol Addresses (Base Chain)

- **Comptroller**: `0xfbb21d0380bee3312b33c4353c8936a0f13ef26c`
- **Reward Distributor**: `0xe9005b078701e2a0948d2eac43010d35870ad9d2`
- **WELL Token**: `0xA88594D404727625A9437C3f886C7643872296AE`

## Construction

```python
from wayfinder_paths.adapters.moonwell_adapter import MoonwellAdapter

config = {
    "strategy_wallet": {"address": "0x...your_wallet..."},
    "moonwell_adapter": {
        "chain_id": 8453,  # Base chain (default)
    }
}
adapter = MoonwellAdapter(config=config)
```

## Usage

```python
# Supply tokens
await adapter.lend(
    mtoken="0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22",  # mUSDC
    underlying_token="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
    amount=1000 * 10**6,  # 1000 USDC
)

# Enable as collateral
await adapter.set_collateral(
    mtoken="0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b",  # mwstETH
)

# Borrow
await adapter.borrow(
    mtoken="0x628ff693426583D9a7FB391E54366292F509D457",  # mWETH
    amount=10**17,  # 0.1 WETH
)

# Get position info
success, position = await adapter.get_pos(
    mtoken="0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22",
)
# Returns: {mtoken_balance, underlying_balance, borrow_balance, exchange_rate, balances}

# Get collateral factor
success, cf = await adapter.get_collateral_factor(
    mtoken="0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b",
)
# Returns: 0.75 (75% LTV)

# Get APY
success, apy = await adapter.get_apy(
    mtoken="0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22",
    apy_type="supply",  # or "borrow"
)

# Claim rewards
await adapter.claim_rewards()
```

## API Reference

### Lending Operations

| Method                                   | Description                   |
| ---------------------------------------- | ----------------------------- |
| `lend(mtoken, underlying_token, amount)` | Supply tokens to earn yield   |
| `unlend(mtoken, amount)`                 | Withdraw by redeeming mTokens |

### Borrowing Operations

| Method                                    | Description              |
| ----------------------------------------- | ------------------------ |
| `borrow(mtoken, amount)`                  | Borrow underlying tokens |
| `repay(mtoken, underlying_token, amount)` | Repay borrowed tokens    |

### Collateral Management

| Method                      | Description                                |
| --------------------------- | ------------------------------------------ |
| `set_collateral(mtoken)`    | Enable market as collateral (enterMarkets) |
| `remove_collateral(mtoken)` | Disable market as collateral (exitMarket)  |

### Position & Market Data

| Method                                     | Description                                        |
| ------------------------------------------ | -------------------------------------------------- |
| `get_pos(mtoken, account)`                 | Get position data (balances, debt, rewards)        |
| `get_collateral_factor(mtoken)`            | Get collateral factor (LTV)                        |
| `get_apy(mtoken, apy_type)`                | Get supply or borrow APY                           |
| `get_borrowable_amount(account)`           | Get max borrowable in USD                          |
| `max_withdrawable_mtoken(mtoken, account)` | Calculate safe withdrawal amount via binary search |

### Rewards

| Method                           | Description                                   |
| -------------------------------- | --------------------------------------------- |
| `claim_rewards(min_rewards_usd)` | Claim WELL rewards (skips if below threshold) |

### Utilities

| Method             | Description      |
| ------------------ | ---------------- |
| `wrap_eth(amount)` | Wrap ETH to WETH |

All methods return `(success: bool, payload: Any)` tuples. On failure the payload is an error string.

## Testing

```bash
poetry run pytest wayfinder_paths/adapters/moonwell_adapter/ -v
```

## Configuration

The adapter can be configured via the `moonwell_adapter` config key:

```python
config = {
    "strategy_wallet": {"address": "0x..."},
    "moonwell_adapter": {
        "chain_id": 8453,  # Chain ID (default: Base)
        "comptroller": "0x...",  # Override comptroller address
        "reward_distributor": "0x...",  # Override reward distributor
        "m_usdc": "0x...",  # Override mUSDC address
        "m_weth": "0x...",  # Override mWETH address
        "m_wsteth": "0x...",  # Override mwstETH address
    }
}
```

## Error handling

Any exception raised by the underlying web3 calls is caught and returned as a `(False, "message")` tuple. The inherited `health_check()` method reports adapter status, making it safe to call from `Strategy.health_check`.

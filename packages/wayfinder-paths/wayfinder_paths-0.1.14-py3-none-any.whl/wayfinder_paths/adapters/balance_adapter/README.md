# Balance Adapter

Adapter that exposes wallet, token, and pool balances backed by `WalletClient`/`TokenClient` and now orchestrates transfers between the configured main/strategy wallets (with ledger bookkeeping).

- Entrypoint: `adapters.balance_adapter.adapter.BalanceAdapter`
- Tests: `test_adapter.py`

## Capabilities

The adapter provides both wallet read and wallet transfer capabilities. Transfers are executed by leveraging the shared `DefaultWeb3Service.token_transactions` helper, but ledger recording + wallet selection now live inside the adapter.

## Construction

```python
from wayfinder_paths.core.services.web3_service import DefaultWeb3Service
from wayfinder_paths.adapters.balance_adapter.adapter import BalanceAdapter

web3_service = DefaultWeb3Service(config)
balance = BalanceAdapter(config, web3_service=web3_service)
```

`web3_service` is required so the adapter can share the same wallet provider (and `TokenTxn` helper) as the rest of the strategy.

## API surface

### `get_balance(*, query: str | dict, wallet_address: str, chain_id: int | None = None)`
Returns the raw balance (as an integer) for a specific token or pool on a wallet.

`query`: token_id/address string or a dict with a `"token_id"` key. When `query` is a token identifier (e.g. `"usd-coin-base"`), `chain_id` is auto-resolved from token info; when it is a pool address, `chain_id` must be provided.

```python
# Token balance (chain_id auto-resolved)
success, balance = await balance.get_balance(
    query="usd-coin-base",
    wallet_address=config["main_wallet"]["address"],
)

# Pool balance (chain_id required)
success, pool_balance = await balance.get_balance(
    query="0xPool...",
    wallet_address=config["strategy_wallet"]["address"],
    chain_id=8453,
)
```

### `move_from_main_wallet_to_strategy_wallet(token_id: str, amount: float, strategy_name="unknown", skip_ledger=False)`
Sends the specified token from the configured `main_wallet` to the strategy wallet, records the ledger deposit (unless `skip_ledger=True`), and returns the `(success, tx_result)` tuple from the underlying send helper.

```python
success, tx = await balance.move_from_main_wallet_to_strategy_wallet(
    token_id="usd-coin-base",
    amount=1.5,
    strategy_name="MyStrategy",
)
```

### `move_from_strategy_wallet_to_main_wallet(token_id: str, amount: float, strategy_name="unknown", skip_ledger=False)`
Mirrors the previous method but withdraws from the strategy wallet back to the main wallet while recording a ledger withdrawal entry.

```python
await balance.move_from_strategy_wallet_to_main_wallet(
    token_id="usd-coin-base",
    amount=0.75,
    strategy_name="MyStrategy",
)
```

All methods return `(success: bool, payload: Any)` tuples. On failure the payload is an error string.

## Usage inside strategies

```python
class MyStrategy(Strategy):
    def __init__(self, config):
        super().__init__()
        web3_service = DefaultWeb3Service(config)
        balance_adapter = BalanceAdapter(config, web3_service=web3_service)
        self.register_adapters([balance_adapter])
        self.balance_adapter = balance_adapter

    async def _status(self):
        success, pool_balance = await self.balance_adapter.get_balance(
            query=self.current_pool["address"],
            wallet_address=self.config["strategy_wallet"]["address"],
            chain_id=self.current_pool["chain"]["id"],
        )
        return {"portfolio_value": float(pool_balance or 0), ...}
```

## Error handling and health checks

Any exception raised by the underlying `WalletClient`/`TokenClient` is caught and emitted as a `(False, "message")` tuple. The inherited `health_check()` method reports adapter status plus dependency status, making it safe to call from `Strategy.health_check`.

# Hyperlend Stable Yield Strategy

- Entrypoint: `strategies.hyperlend_stable_yield_strategy.strategy.HyperlendStableYieldStrategy`
- Examples: `examples.json`
- Tests: `test_strategy.py`

## What it does

Allocates USDT0 on HyperEVM across HyperLend stablecoin markets. The strategy:

1. Pulls USDT0 (plus a configurable HYPE gas buffer) from the main wallet into the strategy wallet.
2. Samples HyperLend hourly rate history, applies a bootstrap tournament (horizon = 6h, blocks = 6h, 4,000 trials, 7-day half-life) to estimate which stablecoin should outperform.
3. Tops up the small HYPE gas buffer if needed, swaps USDT0 into the target stablecoin, and supplies it to HyperLend.
4. Enforces a hysteresis rotation policy so minor APY noise does not churn capital.

## Key parameters

- `MIN_USDT0_DEPOSIT_AMOUNT = 1`
- `GAS_MAXIMUM = 0.1` HYPE (max accepted per deposit)
- `HORIZON_HOURS = 6`, `BLOCK_LEN = 6`, `TRIALS = 4000`
- `HYSTERESIS_DWELL_HOURS = 168`, `HYSTERESIS_Z = 1.15`
- `ROTATION_COOLDOWN = 168 hours`
- `APY_REBALANCE_THRESHOLD = 0.0035` (35 bps edge required to rotate when not short-circuiting)
- `MIN_STABLE_SWAP_TOKENS = 1e-3` → dust threshold when sweeping balances

## Adapters used

- `BalanceAdapter` for token/pool balances and orchestrating wallet transfers with ledger tracking.
- `TokenAdapter` for metadata (USDT0, HYPE, wrapping info).
- `LedgerAdapter` for net deposit + rotation history.
- `BRAPAdapter` to source quotes/swap stablecoins.
- `HyperlendAdapter` for asset views, lend/withdraw ops, supply caps.

## Actions

### Deposit

- Validates USDT0 and HYPE balances in the main wallet.
- Transfers HYPE into the strategy wallet when a top-up is required, ensuring the strategy maintains the configured buffer.
- Moves USDT0 from the main wallet into the strategy wallet through `BalanceAdapter.move_from_main_wallet_to_strategy_wallet`.
- Clears cached asset snapshots so the next update starts from on-chain reality.

### Update

- Refreshes HyperLend asset snapshots, calculates tournament winners, and filters markets that respect supply caps + buffer requirements.
- Reads rotation history through `LedgerAdapter.get_strategy_latest_transactions` to enforce the cooldown (unless the short-circuit policy is triggered).
- If a new asset wins the tournament and passes hysteresis checks, BRAP quotes are fetched and executed to rotate into the better performer.
- Sweeps residual stable balances, lends via `HyperlendAdapter`, and records ledger operations.

### Status

`_status()` returns:

- `portfolio_value`: active lend balance (converted to float),
- `net_deposit`: fetched from `LedgerAdapter`,
- `strategy_status`: includes current lent asset, APY, idle balances, and tournament projections.

### Withdraw

- Unwinds existing HyperLend positions, swaps back to USDT0 when necessary, returns USDT0 and residual HYPE to the main wallet via `BalanceAdapter`, and clears cached state.

## Running locally

```bash
# Install dependencies
poetry install

# Generate main wallet (writes config.json)
# Creates a main wallet (or use 'just create-strategy' which auto-creates wallets)
poetry run python wayfinder_paths/scripts/make_wallets.py -n 1

# Copy config and edit credentials
cp wayfinder_paths/config.example.json config.json

# Check status / health
poetry run python wayfinder_paths/run_strategy.py hyperlend_stable_yield_strategy --action status --config $(pwd)/config.json

# Perform a deposit/update/withdraw cycle
poetry run python wayfinder_paths/run_strategy.py hyperlend_stable_yield_strategy --action deposit --main-token-amount 25 --gas-token-amount 0.02 --config $(pwd)/config.json
poetry run python wayfinder_paths/run_strategy.py hyperlend_stable_yield_strategy --action update --config $(pwd)/config.json
poetry run python wayfinder_paths/run_strategy.py hyperlend_stable_yield_strategy --action withdraw --config $(pwd)/config.json
```

Wallet addresses/labels are auto-resolved from `config.json`. Set `NETWORK=testnet` in your config to run the orchestration without touching live HyperEVM endpoints.

# Stablecoin Yield Strategy

- Entrypoint: `strategies.stablecoin_yield_strategy.strategy.StablecoinYieldStrategy`
- Examples: `examples.json`
- Tests: `test_strategy.py`

## What it does

Actively manages Base USDC deposits. Deposits pull USDC (plus an ETH gas buffer) from the main wallet into the strategy wallet, then the strategy searches Base-native pools for the best USD-denominated APY. Updates monitor DeFi Llama feeds and Wayfinder pool analytics, respecting a rotation cooldown and minimum APY improvement before rebalancing via the BRAP router. Withdrawals unwind the current position, sweep residual tokens back into USDC, and return funds to the main wallet.

## On-chain policy

Transactions are scoped to the strategy wallet and Enso Router approval/swap calls:

```
(wallet.id == 'FORMAT_WALLET_ID') && ((eth.tx.data[0..10] == '0x095ea7b3' && eth.tx.data[34..74] == 'f75584ef6673ad213a685a1b58cc0330b8ea22cf') || (eth.tx.to == '0xF75584eF6673aD213a685a1B58Cc0330B8eA22Cf'))
```

## Key parameters (from `strategy.py`)

- `MIN_AMOUNT_USDC = 2` → deposits smaller than 2 USDC are rejected.
- `MIN_TVL = 1_000_000` → pools below $1M TVL are ignored.
- `ROTATION_MIN_INTERVAL = 14 days` → once rotated, the strategy waits ~2 weeks unless the new candidate dramatically outperforms.
- `DUST_APY = 0.01` (1%) → pools below this APY are treated as dust.
- `SEARCH_DEPTH = 10` → how many pools to examine when selecting candidates.
- `MIN_GAS = 0.001` and `GAS_MAXIMUM = 0.02` Base ETH → minimum buffer required in the strategy wallet plus the upper bound accepted per deposit.

## Adapters used

- `BalanceAdapter` for wallet/pool balances and orchestrating transfers between the main and strategy wallets (with ledger recording).
- `PoolAdapter` for pool metadata, llama reports, and yield analytics.
- `BRAPAdapter` to source swap quotes and execute rotations.
- `TokenAdapter` for metadata (gas token, USDC info).
- `LedgerAdapter` for net-deposit tracking and cooldown enforcement.

## Actions

### Deposit

- Validates `main_token_amount` ≥ `MIN_AMOUNT_USDC` and `gas_token_amount` ≤ `GAS_MAXIMUM`.
- Confirms the main wallet holds enough USDC and Base ETH.
- Moves Base ETH into the strategy wallet (when requested or when the strategy needs a top-up), then transfers the requested USDC amount via `BalanceAdapter.move_from_main_wallet_to_strategy_wallet`.
- Hydrates the on-chain position snapshot so future updates know which pool is active.

### Update

- Fetches the latest strategy balances, idle assets, and current target pool.
- Runs `_find_best_pool()` which uses `PoolAdapter` and DeFi Llama data to score up to `SEARCH_DEPTH` pools that satisfy the APY/TVL filters.
- Checks `LedgerAdapter.get_strategy_latest_transactions()` to enforce the rotation cooldown, unless the new candidate clears the APY-improvement threshold.
- If rotation is approved, requests a BRAP quote, ensures the strategy has enough gas, executes the swap via `BRAPAdapter.swap_from_quote`, and sweeps any idle balances back into the target token.
- Records informative status messages when no better pool exists or when cooldown blocks a move.

### Status

`_status()` reports:

- `portfolio_value`: refreshed pool balance (in base units) converted to float.
- `net_deposit`: data pulled from `LedgerAdapter.get_strategy_net_deposit`.
- `strategy_status`: dictionary exposing the active pool, APY estimates, and wallet balances.

### Withdraw

- Requires a prior deposit (the strategy tracks `self.DEPOSIT_USDC`).
- Reads the pool balance via `BalanceAdapter.get_balance` (with pool address and chain_id), unwinds via BRAP swaps back to USDC, and moves USDC from the strategy wallet to the main wallet via `BalanceAdapter.move_from_strategy_wallet_to_main_wallet`.
- Updates the ledger and clears cached pool state.

## Running locally

```bash
# Install dependencies
poetry install

# Generate main wallet (writes config.json)
# Creates a main wallet (or use 'just create-strategy' which auto-creates wallets)
poetry run python wayfinder_paths/scripts/make_wallets.py -n 1

# Copy the example config and set credentials if needed
cp wayfinder_paths/config.example.json config.json

# Smoke test the strategy
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --action status --config $(pwd)/config.json

# Perform a funded deposit/update cycle
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --action deposit --main-token-amount 60 --gas-token-amount 0.001 --config $(pwd)/config.json
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --action update --config $(pwd)/config.json
```

Wallet addresses are auto-populated from `config.json` when you run `wayfinder_paths/scripts/make_wallets.py`. Set `NETWORK=testnet` in `config.json` to dry-run operations against mocked services.

# Moonwell wstETH Loop Strategy

- Entrypoint: `strategies.moonwell_wsteth_loop_strategy.strategy.MoonwellWstethLoopStrategy`
- Examples: `examples.json`
- Tests: `test_strategy.py`

## What it does

A leveraged liquid-staking carry trade on Base that loops USDC collateral into wstETH exposure. The strategy:

1. Deposits USDC as initial collateral on Moonwell lending protocol.
2. Borrows WETH against the USDC collateral.
3. Swaps WETH to wstETH via Aerodrome/BRAP routing.
4. Lends wstETH back to Moonwell as additional collateral.
5. Repeats the loop until target leverage is reached or marginal gains fall below threshold.

The position is **delta-neutral**: WETH debt offsets wstETH collateral, so PnL is driven by the spread between wstETH staking yield and WETH borrow cost.

## Key parameters

- `MIN_GAS = 0.002` ETH (minimum Base ETH for gas)
- `MIN_USDC_DEPOSIT = 20` USDC (minimum initial collateral)
- `MAX_DEPEG = 0.01` (1% max stETH/ETH depeg threshold)
- `MIN_HEALTH_FACTOR = 1.2` (triggers deleveraging if below)
- `MAX_HEALTH_FACTOR = 1.5` (triggers leverage loop if above)
- `leverage_limit = 10` (maximum leverage multiplier)
- `COLLATERAL_SAFETY_FACTOR = 0.98` (2% safety buffer on borrows)
- `MAX_SLIPPAGE_TOLERANCE = 0.03` (3% max slippage to prevent MEV)
- `_MIN_LEVERAGE_GAIN_BPS = 50e-4` (stop looping if marginal gain < 50 bps)

## Safety features

- **Depeg guard**: `_max_safe_F()` calculates leverage ceiling based on wstETH collateral factor and max depeg tolerance.
- **Delta-neutrality**: `_post_run_guard()` enforces wstETH collateral ≥ WETH debt (within tolerance) via `_reconcile_wallet_into_position()` and `_settle_weth_debt_to_target_usd()`.
- **Swap retries**: `_swap_with_retries()` uses progressive slippage (0.5% → 1% → 1.5%) with exponential backoff.
- **Health monitoring**: Automatic deleveraging when health factor drops below `MIN_HEALTH_FACTOR`.
- **Deterministic Base reads**: waits 2 blocks after receipts by default and pins ETH/ERC20 balance reads to the confirmed block to avoid stale RPC reads on Base.
- **Rollback protection**: Checks actual balances before rollback swaps to prevent failed transactions.

## Adapters used

- `BalanceAdapter` for token balances and wallet transfers with ledger tracking.
- `TokenAdapter` for token metadata and price feeds.
- `LedgerAdapter` for net deposit tracking.
- `BRAPAdapter` for swap quotes and execution via Aerodrome/routing.
- `MoonwellAdapter` for lending, borrowing, collateral management, and position queries.

## Actions

### Deposit

- Validates USDC and ETH balances in the main wallet.
- Transfers ETH (gas) into the strategy wallet if needed.
- Moves USDC from main wallet to strategy wallet.
- Lends USDC on Moonwell and enables as collateral.
- Executes leverage loop: borrow WETH → swap to wstETH → lend wstETH → repeat.

### Update

- Checks gas balance meets maintenance threshold.
- Reconciles wallet leftovers into the intended position (`_reconcile_wallet_into_position()`).
- Computes HF/LTV/delta from a single accounting snapshot.
- If HF < MIN: triggers deleveraging via `_settle_weth_debt_to_target_usd()`.
- If HF > MAX: executes additional leverage loops to optimize yield.
- Claims WELL rewards if above minimum threshold.

### Status

`_status()` returns:

- `portfolio_value`: sum of all position values (USDC lent + wstETH lent - WETH debt)
- `net_deposit`: fetched from LedgerAdapter
- `strategy_status`: includes current leverage, health factor, LTV, peg diff, credit remaining

### Withdraw

- Sweeps miscellaneous token balances to WETH.
- Repays all WETH debt via `_settle_weth_debt_to_target_usd(target_debt_usd=0.0, mode="exit")`.
- Unlends wstETH, swaps to USDC.
- Unlends USDC collateral.
- Returns USDC and remaining ETH to main wallet.

## Running locally

```bash
# Install dependencies
poetry install

# Generate wallets (writes config.json)
poetry run python wayfinder_paths/scripts/make_wallets.py -n 1

# Copy config and edit credentials
cp wayfinder_paths/config.example.json config.json

# Check status / health
poetry run python wayfinder_paths/run_strategy.py moonwell_wsteth_loop_strategy --action status --config $(pwd)/config.json

# Perform a deposit/update/withdraw cycle
poetry run python wayfinder_paths/run_strategy.py moonwell_wsteth_loop_strategy --action deposit --main-token-amount 100 --gas-token-amount 0.01 --config $(pwd)/config.json
poetry run python wayfinder_paths/run_strategy.py moonwell_wsteth_loop_strategy --action update --config $(pwd)/config.json
poetry run python wayfinder_paths/run_strategy.py moonwell_wsteth_loop_strategy --action withdraw --config $(pwd)/config.json
```

## Testing

```bash
poetry run pytest wayfinder_paths/strategies/moonwell_wsteth_loop_strategy/ -v
```

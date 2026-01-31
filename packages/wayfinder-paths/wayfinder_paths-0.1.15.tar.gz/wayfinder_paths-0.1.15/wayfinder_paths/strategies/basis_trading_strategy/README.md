# Basis Trading Strategy

Delta-neutral basis trading on Hyperliquid that captures funding rate payments through matched spot long and perpetual short positions.

## How It Works

### Delta-Neutral Basis Trading

The strategy maintains market neutrality by holding equal-and-opposite positions:
- **Long Spot**: Buy the underlying asset (e.g., HYPE)
- **Short Perp**: Short the perpetual contract for the same asset

This creates a "basis trade" where:
- Price movements cancel out (if HYPE goes up 10%, spot gains +10%, perp loses -10%)
- You collect funding payments when longs pay shorts (positive funding rate)
- The position is "delta-neutral" - profit comes from funding, not price direction

### Position Sizing with Leverage

Given a deposit of `D` USDC and leverage `L`:
- **Order Size**: `order_usd = D * (L / (L + 1))`
- **Margin Reserved**: `D / (L + 1)`

Example with $100 deposit at 2x leverage:
- Order size: $100 * (2/3) = $66.67 per leg
- Margin: $100 / 3 = $33.33

## Opportunity Selection

### 1. Candidate Discovery

The strategy scans all Hyperliquid markets to find spot-perp pairs:
- Spots quoted in USDC that have matching perpetual contracts
- Filters: minimum open interest, daily volume, order book depth

### 2. Historical Analysis (Backtesting)

For each candidate, fetches up to 180 days of hourly data:
- **Funding rates**: Mean, volatility, negative hour fraction, worst 24h/7d sums
- **Price candles**: Hourly closes and highs for volatility calculation

### 3. Safe Leverage Calculation

Uses a deterministic "stress test" approach over rolling historical windows:

```
For each window of N hours:
  - Track cumulative negative funding (adjusted for price run-up)
  - Track maximum price run-up (high / entry - 1)
  - Calculate buffer requirement:
    buffer = maintenance_margin * (1 + runup) + runup + cum_neg_funding + fees
```

The worst-case buffer across all windows determines the maximum safe leverage:
- If buffer requirement is 50%, max safe leverage = 2x
- If buffer requirement is 33%, max safe leverage = 3x

### 4. Bootstrap Simulation (Optional)

For additional statistical confidence, the strategy can run Monte Carlo simulations:
- Resamples historical funding/price data in blocks (default 24h blocks)
- Runs N simulations (configurable, e.g., 1000)
- Calculates VaR at specified confidence level (default 97.5%)

Configure via:
```json
{
  "strategy_config": {
    "bootstrap_sims": 1000,
    "bootstrap_block_hours": 24
  }
}
```

### 5. Ranking

Opportunities are ranked by expected APY:
```
expected_apy = mean_hourly_funding * 24 * 365 * safe_leverage
```

## Position Management

### Opening a Position

1. Transfers USDC from main wallet to strategy wallet
2. Bridges USDC to Hyperliquid via Arbitrum
3. Splits between perp margin and spot
4. Uses `PairedFiller` to atomically execute both legs (buy spot + sell perp)
5. Places protective orders:
   - **Stop-loss**: Triggers if price approaches liquidation (default 65% of distance)
   - **Limit sell**: Closes spot if funding flips negative

### Incremental Scaling

When you deposit additional funds with an existing position:
- Detects idle capital (undeployed USDC on Hyperliquid)
- Calculates additional units to add to each leg
- Uses `PairedFiller` to atomically add to both positions
- Maintains delta neutrality throughout

### Monitoring (update)

The `update` action:
1. Checks if position needs rebalancing (funding flipped, leverage drift, etc.)
2. Deploys any idle capital via scale-up
3. Verifies leg balance (spot amount ≈ perp amount)
4. Updates stop-loss/limit orders if liquidation price changed

### Closing a Position

1. Cancels all open orders
2. Uses `PairedFiller` to atomically close both legs (sell spot + buy perp)
3. Withdraws USDC from Hyperliquid to Arbitrum
4. Sends funds back to main wallet

## CLI Usage

```bash
# Analyze opportunities for a $1000 deposit (doesn't open position)
poetry run python wayfinder_paths/run_strategy.py basis_trading_strategy \
    --action analyze --amount 1000 --config config.json

# Deposit $100 USDC from main wallet
poetry run python wayfinder_paths/run_strategy.py basis_trading_strategy \
    --action deposit --main-token-amount 100 --config config.json

# Analyze and open/manage position
poetry run python wayfinder_paths/run_strategy.py basis_trading_strategy \
    --action update --config config.json

# Check current status
poetry run python wayfinder_paths/run_strategy.py basis_trading_strategy \
    --action status --config config.json

# Withdraw all funds back to main wallet
poetry run python wayfinder_paths/run_strategy.py basis_trading_strategy \
    --action withdraw --config config.json

# Generate batch snapshot of all opportunities
poetry run python wayfinder_paths/run_strategy.py basis_trading_strategy \
    --action snapshot --amount 1000 --config config.json
```

## Configuration

```json
{
  "main_wallet": {
    "address": "0x...",
    "private_key": "0x..."
  },
  "strategy_wallet": {
    "address": "0x...",
    "private_key": "0x..."
  },
  "strategy_config": {
    "max_leverage": 3,
    "lookback_days": 180,
    "bootstrap_sims": 0,
    "bootstrap_block_hours": 24
  }
}
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_leverage` | 3 | Maximum leverage allowed |
| `lookback_days` | 180 | Days of historical data for analysis |
| `confidence` | 0.975 | VaR confidence level (97.5%) |
| `fee_eps` | 0.003 | Fee buffer (0.3%) |
| `oi_floor` | 50 | Minimum open interest (USD) |
| `day_vlm_floor` | 100,000 | Minimum daily volume (USD) |
| `bootstrap_sims` | 50 | Monte Carlo simulations for VaR estimation |
| `bootstrap_block_hours` | 24 | Block size for bootstrap resampling |

### Thresholds

| Constant | Value | Description |
|----------|-------|-------------|
| `MIN_DEPOSIT_USDC` | 50 | Minimum deposit |
| `LIQUIDATION_REBALANCE_THRESHOLD` | 0.65 | Stop-loss at 65% of liquidation distance |
| `MIN_UNUSED_USD` | 5.0 | Minimum idle capital to trigger scale-up |
| `UNUSED_REL_EPS` | 0.05 | Relative threshold (5% of deposit) |

## Adapters Used

- **BALANCE**: Wallet balances and ERC20 transfers
- **LEDGER**: Transaction recording for deposit/withdraw tracking
- **TOKEN**: Token metadata (decimals, addresses)
- **HYPERLIQUID**: Market data, order execution, account state

## Risk Factors

1. **Funding Rate Flips**: Rates can turn negative, causing losses instead of gains
2. **Liquidation Risk**: High leverage + adverse price movement can liquidate the perp
3. **Execution Slippage**: Large orders may move the market
4. **Withdrawal Delays**: Hyperliquid withdrawals take ~15-30 minutes
5. **Smart Contract Risk**: Funds are held on Hyperliquid's L1

## Architecture

```
BasisTradingStrategy
├── HyperliquidAdapter       # Market data, account state
├── LocalHyperliquidExecutor # Order execution (spot + perp)
├── PairedFiller             # Atomic paired order execution
├── BalanceAdapter           # Arbitrum wallet balances
├── LedgerAdapter            # Deposit/withdraw tracking
└── LocalEvmTxn              # Arbitrum transaction signing
```

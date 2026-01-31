# Strategy Template

This template provides scaffolding for a new strategy.

## Quick Start

1. Copy the template:
   ```bash
   cp -r wayfinder_paths/templates/strategy wayfinder_paths/strategies/my_strategy
   ```
   Or use the convenience command:
   ```bash
   just create-strategy "My Strategy Name"
   ```
2. Rename the class in `strategy.py` to match your strategy name.
3. Implement the required methods (`deposit`, `update`, `exit`, `_status`).
4. Add tests in `test_strategy.py`.
5. Fill out `examples.json` with sample CLI invocations.

## Directory Structure

```
my_strategy/
├── strategy.py          # Strategy implementation
├── examples.json        # Example CLI payloads
├── test_strategy.py     # Pytest tests
└── README.md            # Strategy documentation
```

## Required Methods

```python
async def deposit(self, main_token_amount: float, gas_token_amount: float) -> StatusTuple:
    """Move funds from main wallet into strategy wallet and deploy capital."""

async def update(self) -> StatusTuple:
    """Periodic rebalance/optimization loop."""

async def exit(self, **kwargs) -> StatusTuple:
    """Transfer funds from strategy wallet back to main wallet."""

async def _status(self) -> StatusDict:
    """Return portfolio_value, net_deposit, and strategy_status."""
```

## Optional Methods

```python
async def withdraw(self, **kwargs) -> StatusTuple:
    """Unwind positions. Default implementation unwinds ledger operations."""

async def partial_liquidate(self, usd_value: float) -> tuple[bool, LiquidationResult]:
    """Liquidate a portion of the position by USD value."""

async def setup(self) -> None:
    """Post-construction initialization."""

async def health_check(self) -> dict:
    """Check strategy and adapter health."""
```

## Strategy Structure

```python
from wayfinder_paths.core.strategies.Strategy import StatusDict, StatusTuple, Strategy
from wayfinder_paths.adapters.balance_adapter.adapter import BalanceAdapter


class MyStrategy(Strategy):
    name = "My Strategy"

    def __init__(self, config: dict | None = None, **kwargs):
        super().__init__(config, **kwargs)
        self.config = config or {}

        # Initialize and register adapters
        balance_adapter = BalanceAdapter(
            self.config,
            main_wallet_signing_callback=kwargs.get("main_wallet_signing_callback"),
            strategy_wallet_signing_callback=kwargs.get("strategy_wallet_signing_callback"),
        )
        self.register_adapters([balance_adapter])
        self.balance_adapter = balance_adapter

    async def deposit(
        self, main_token_amount: float = 0.0, gas_token_amount: float = 0.0
    ) -> StatusTuple:
        if main_token_amount <= 0:
            return (False, "Nothing to deposit")

        # Implement deposit logic
        return (True, f"Deposited {main_token_amount} tokens")

    async def update(self) -> StatusTuple:
        # Implement rebalancing logic
        return (True, "Update complete")

    async def exit(self, **kwargs) -> StatusTuple:
        # Implement exit logic
        return (True, "Exit complete")

    async def _status(self) -> StatusDict:
        return {
            "portfolio_value": 0.0,
            "net_deposit": 0.0,
            "strategy_status": {"message": "healthy"},
            "gas_available": 0.0,
            "gassed_up": True,
        }
```

## Testing

Create `test_strategy.py` using `examples.json`:

```python
import pytest
from pathlib import Path
from tests.test_utils import load_strategy_examples
from .strategy import MyStrategy


@pytest.mark.asyncio
async def test_smoke():
    """Basic strategy lifecycle test."""
    examples = load_strategy_examples(Path(__file__))
    smoke_example = examples["smoke"]

    s = MyStrategy()

    # Deposit
    deposit_params = smoke_example.get("deposit", {})
    ok, _ = await s.deposit(**deposit_params)
    assert ok

    # Update
    ok, _ = await s.update()
    assert ok

    # Status
    st = await s._status()
    assert "portfolio_value" in st
    assert "net_deposit" in st
    assert "strategy_status" in st
```

Run tests:

```bash
poetry run pytest wayfinder_paths/strategies/my_strategy/ -v
```

## Running the Strategy

```bash
# Install dependencies
poetry install

# Generate wallets
just create-wallets
just create-wallet my_strategy

# Configure API key in config.json

# Check status
poetry run python wayfinder_paths/run_strategy.py my_strategy --action status --config config.json

# Deposit
poetry run python wayfinder_paths/run_strategy.py my_strategy \
    --action deposit --main-token-amount 100 --gas-token-amount 0.01 --config config.json

# Run update
poetry run python wayfinder_paths/run_strategy.py my_strategy --action update --config config.json

# Withdraw
poetry run python wayfinder_paths/run_strategy.py my_strategy --action withdraw --config config.json
```

## Best Practices

- Return `(success: bool, message: str)` tuples from all action methods
- Always populate `portfolio_value`, `net_deposit`, and `strategy_status` in `_status`
- Register adapters via `register_adapters()` in `__init__`
- Use adapters for external operations, not clients directly
- Keep strategy logic clear and well-documented
- Add error handling with informative messages

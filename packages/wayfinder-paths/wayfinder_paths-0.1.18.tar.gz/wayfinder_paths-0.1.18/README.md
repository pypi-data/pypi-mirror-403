# 🔐 Wayfinder Paths

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![Discord](https://img.shields.io/badge/discord-join-7289da.svg)](https://discord.gg/fUVwGMXjm3)

Open-source platform for community-contributed crypto trading strategies and adapters. Build, test, and deploy automated trading strategies with direct wallet integration.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/wayfinder-ai/wayfinder-paths.git
cd wayfinder-paths

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# ⚠️ Generate test wallets FIRST (required!)
# This creates config.json with a main wallet for local testing
just create-wallets
# Or manually: poetry run python wayfinder_paths/scripts/make_wallets.py -n 1

# To test a specific strategy
just create-wallet stablecoin_yield_strategy

# Copy and configure
cp wayfinder_paths/config.example.json config.json
# Edit config.json with your Wayfinder credentials

# Run a strategy locally (one-shot status check)
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --action status --config config.json

# Run continuously (production mode)
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --config config.json
```

## 📁 Repository Structure

```
wayfinder_paths/
├── wayfinder_paths/              # Main package directory
│   ├── core/                      # Core engine (maintained by team)
│   │   ├── clients/              # API client managers
│   │   ├── adapters/             # Base adapter interfaces
│   │   ├── engine/               # Trading engine & StrategyJob
│   │   ├── strategies/           # Base strategy classes
│   │   └── config.py             # Configuration system
│   ├── adapters/                 # Your exchange/protocol integrations (community contributions)
│   │   ├── balance_adapter/
│   │   │   ├── adapter.py        # Adapter implementation
│   │   │   ├── examples.json     # Example inputs for smoke
│   │   │   ├── README.md         # Local notes
│   │   │   └── test_adapter.py   # Local smoke test
│   │   ├── brap_adapter/
│   │   └── ...
│   ├── strategies/               # Your trading strategies (community contributions)
│   │   ├── stablecoin_yield_strategy/
│   │   │   ├── strategy.py       # Strategy implementation
│   │   │   ├── examples.json     # Example inputs
│   │   │   ├── README.md         # Local notes
│   │   │   └── test_strategy.py  # Local smoke test
│   │   └── ...
│   ├── tests/                    # Test suite
│   ├── CONFIG_GUIDE.md           # Configuration documentation
│   ├── config.example.json       # Example configuration
│   ├── scripts/                  # Utility scripts
│   └── run_strategy.py           # Strategy runner script
├── config.json                   # Your local config with credentials and wallets
├── pyproject.toml                # Poetry configuration
└── README.md                     # This file
```

## 🤝 Contributing

We welcome contributions! This is an open-source project where community members can contribute adapters and strategies.

### Quick Contribution Guide

1. **Fork the repository** and clone your fork
2. **Create a feature branch**: `git checkout -b feature/my-strategy`
3. **Copy a template** to get started:
   - **For adapters**: Copy `wayfinder_paths/templates/adapter/` to `wayfinder_paths/adapters/my_adapter/`
   - **For strategies**: Copy `wayfinder_paths/templates/strategy/` to `wayfinder_paths/strategies/my_strategy/`
4. **Customize** the template (rename classes, implement methods)
5. **Test your code** thoroughly using the provided test framework
6. **Submit a Pull Request** with a clear description of your changes

### What You Can Contribute

- **Adapters**: Exchange/protocol integrations (e.g., Uniswap, Aave, Compound)
- **Strategies**: Trading algorithms and yield optimization strategies
- **Improvements**: Bug fixes, documentation, or core system enhancements

### Contributor Guidelines

#### For Adapters

- **Start from the template**: Copy `wayfinder_paths/templates/adapter/` as a starting point
- Extend `BaseAdapter` from `wayfinder_paths/core/adapters/BaseAdapter.py`
- Implement your adapter methods
- Add comprehensive tests in `test_adapter.py`
- Include usage examples in `examples.json`
- Document your adapter in `README.md`

#### For Strategies

- **Start from the template**: Use `just create-strategy "Strategy Name"` to create a new strategy with its own wallet, or copy `wayfinder_paths/templates/strategy/` manually
- Extend `Strategy` from `wayfinder_paths/core/strategies/Strategy.py`
- Implement required methods: `deposit()`, `update()`, `status()`, `withdraw()`
- Include test cases in `test_strategy.py`
- Add example configurations in `examples.json`

#### General Guidelines

- **Code Quality**: Follow existing patterns and use type hints
- **Testing**: See [TESTING.md](TESTING.md) - minimum: smoke test for strategies, basic tests for adapters
- **Documentation**: Update README files and add docstrings
- **Security**: Never hardcode API keys or private keys
- **Architecture**: Use adapters for external integrations, not direct API calls

### Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/yourusername/wayfinder-paths.git
cd wayfinder-paths

# 2. Install dependencies
poetry install

# 3. Generate test wallets (required before testing!)
# Creates a main wallet (or use 'just create-strategy' which auto-creates wallets)
just create-wallets
# Or manually: poetry run python wayfinder_paths/scripts/make_wallets.py -n 1

# 4. Create a new strategy (recommended - automatically creates wallet)
just create-strategy "My Strategy Name"

# Or manually copy a template:
# For adapters:
cp -r wayfinder_paths/templates/adapter wayfinder_paths/adapters/my_adapter
# For strategies:
cp -r wayfinder_paths/templates/strategy wayfinder_paths/strategies/my_strategy

# 5. Customize the template (see template README.md files for details)

# 6. Run tests
poetry run pytest -k smoke -v

# Or test your specific contribution
poetry run pytest wayfinder_paths/strategies/your_strategy/ -v
poetry run pytest wayfinder_paths/adapters/your_adapter/ -v

# 8. Test your contribution locally
poetry run python wayfinder_paths/run_strategy.py your_strategy --action status
```

### Getting Help

- 📖 Check existing adapters/strategies for examples
- 🐛 Open an issue for bugs or feature requests

## 🏗️ Architecture

### Client System

The platform uses a unified client system for all API interactions. Clients are thin wrappers that handle low-level API calls, authentication, and network communication. **Strategies should not call clients directly** - use adapters instead for domain-specific operations.

### Clients vs Adapters

- **Clients**: Low-level, reusable service wrappers that talk to networks and external APIs. They handle auth, headers, retries, and response parsing, and expose generic capabilities (e.g., token info, tx building). Examples: `TokenClient`, `WalletClient`.
- **Adapters**: Strategy-facing integrations for a specific exchange/protocol. They compose one or more clients to implement a set of capabilities (e.g., `supply`, `borrow`, `place_order`). Adapters encapsulate protocol-specific semantics and raise `NotImplementedError` for unsupported ops.

Recommended usage:

- Strategies call adapters (not clients directly) for domain actions.
- Add or change a client when you need a new low-level capability shared across adapters.
- Add or change an adapter when integrating a new protocol/exchange or changing protocol-specific behavior.

Data flow: `Strategy` → `Adapter` → `Client(s)` → network/API.

### Configuration

Configuration is split between:

- **User Config**: Your credentials and preferences
- **System Config**: Platform settings
- **Strategy Config**: Strategy-specific parameters

See [CONFIG_GUIDE.md](wayfinder_paths/CONFIG_GUIDE.md) for details.

### Authentication

Wayfinder Paths uses API key authentication via the `X-API-KEY` header.

**Add API key to config.json:**

```json
{
  "system": {
    "api_key": "sk_live_abc123...",
    "api_base_url": "https://wayfinder.ai/api/v1",
    "wallets_path": "wallets.json"
  }
}
```

**How It Works:**

- API key is automatically loaded from `system.api_key` in config.json
- The API key is sent as the `X-API-KEY` header on all API requests
- All clients automatically include the API key header
- No need to pass API keys explicitly to strategies or clients

See [CONFIG_GUIDE.md](wayfinder_paths/CONFIG_GUIDE.md) for detailed configuration documentation.

## 🔌 Creating Adapters

Adapters connect to exchanges and DeFi protocols using the client system.

```python
# wayfinder_paths/adapters/my_adapter/adapter.py
from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.PoolClient import PoolClient


class MyAdapter(BaseAdapter):
    """Thin wrapper around PoolClient that exposes pool metadata to strategies."""

    adapter_type = "POOL"

    def __init__(self, config: dict | None = None):
        super().__init__("my_adapter", config)
        self.pool_client = PoolClient()

    async def connect(self) -> bool:
        """No-op for read-only adapters, but kept for interface consistency."""
        return True

    async def get_pools(self, pool_ids: list[str]):
        data = await self.pool_client.get_pools_by_ids(
            pool_ids=pool_ids
        )
        return (True, data)
```

## 📈 Building Strategies

Strategies implement trading logic using adapters and the unified client system.

```python
# wayfinder_paths/strategies/my_strategy/strategy.py
from wayfinder_paths.core.strategies.Strategy import StatusDict, StatusTuple, Strategy
from wayfinder_paths.adapters.balance_adapter.adapter import BalanceAdapter


class MyStrategy(Strategy):
    name = "Demo Strategy"

    def __init__(
        self,
        config: dict | None = None,
        *,
        api_key: str | None = None,  # Optional: API key for service account auth
    ):
        super().__init__(api_key=api_key)  # Pass to base class for auto-discovery
        self.config = config or {}
        # Adapters automatically discover API key from constructor or config.json
        balance_adapter = BalanceAdapter(self.config)
        self.register_adapters([balance_adapter])
        self.balance_adapter = balance_adapter

    async def deposit(
        self, main_token_amount: float = 0.0, gas_token_amount: float = 0.0
    ) -> StatusTuple:
        """Move funds from main wallet into the strategy wallet."""
        if main_token_amount <= 0:
            return (False, "Nothing to deposit")

        success, _ = await self.balance_adapter.get_balance(
            query=self.config.get("token_id"),
            wallet_address=self.config.get("main_wallet", {}).get("address"),
        )
        if not success:
            return (False, "Unable to fetch balances")

        self.last_deposit = main_token_amount
        return (True, f"Deposited {main_token_amount} tokens")

    async def update(self) -> StatusTuple:
        """Periodic strategy update"""
        return (True, "No-op update")

    async def _status(self) -> StatusDict:
        """Report balances back to the runner"""
        success, balance = await self.balance_adapter.get_balance(
            query=self.config.get("token_id"),
            wallet_address=self.config.get("strategy_wallet", {}).get("address"),
        )
        return {
            "portfolio_value": float(balance or 0),
            "net_deposit": float(getattr(self, "last_deposit", 0.0)),
            "strategy_status": {"message": "healthy" if success else "unknown"},
        }
```

### Built-in Strategies

The following strategies are available and can be run using the CLI:

| Strategy                          | Description                 | Chain    |
| --------------------------------- | --------------------------- | -------- |
| `basis_trading_strategy`          | Delta-neutral basis trading | -        |
| `hyperlend_stable_yield_strategy` | Stable yield on HyperLend   | HyperEVM |
| `moonwell_wsteth_loop_strategy`   | Leveraged wstETH yield loop | Base     |

#### Running Strategies

### Built-in adapters

- **BALANCE (BalanceAdapter)**: wraps `WalletClient`/`TokenClient` to read wallet, token, and pool balances and now orchestrates transfers between the main/strategy wallets with ledger bookkeeping. Requires a `Web3Service` so it can share the same wallet provider as the strategy.
- **POOL (PoolAdapter)**: composes `PoolClient` to fetch pools, llama analytics, combined reports, high-yield searches, and search helpers.
- **BRAP (BRAPAdapter)**: integrates the cross-chain quote service for swaps/bridges, including fee breakdowns, route comparisons, validation helpers, and swap execution/ledger recording when provided a `Web3Service`.
- **LEDGER (LedgerAdapter)**: records deposits, withdrawals, custom operations, and cashflows via `LedgerClient`, and can read strategy transaction summaries.
- **TOKEN (TokenAdapter)**: lightweight wrapper around `TokenClient` for token metadata, live price snapshots, and gas token lookups.
- **HYPERLEND (HyperlendAdapter)**: connects to `HyperlendClient` for lending/supply caps inside the HyperLend strategy.
- **MOONWELL (MoonwellAdapter)**: interfaces with Moonwell protocol on Base for lending, borrowing, collateral management, and WELL rewards.

Strategies register the adapters they need in their `__init__` method. Adapters implement their specific capabilities and raise `NotImplementedError` for unsupported operations.

## 🧪 Testing

**📖 For detailed testing guidance, see [TESTING.md](TESTING.md)**

### Quick Start

```bash
# 1. Generate test wallets (required!)
# Creates a main wallet (or use 'just create-strategy' which auto-creates wallets)
just create-wallets
# Or manually: poetry run python wayfinder_paths/scripts/make_wallets.py -n 1

# 2. Run smoke tests
poetry run pytest -k smoke -v

# 3. Test your specific contribution
poetry run pytest wayfinder_paths/strategies/my_strategy/ -v     # Strategy
poetry run pytest wayfinder_paths/adapters/my_adapter/ -v       # Adapter
```

### Testing Your Contribution

**Strategies**: Add a simple smoke test in `test_strategy.py` that exercises deposit → update → status → withdraw.

**Adapters**: Add basic functionality tests with mocked dependencies. Use `examples.json` to drive your tests.

See [TESTING.md](TESTING.md) for complete examples and best practices.

## 💻 Local Development

### Setup

```bash
# Clone repo
git clone https://github.com/wayfinder-ai/wayfinder-paths.git
cd wayfinder-paths

# Install dependencies
poetry install

# Generate test wallets (essential!)
# Creates a main wallet (or use 'just create-strategy' which auto-creates wallets)
just create-wallets
# Or manually: poetry run python wayfinder_paths/scripts/make_wallets.py -n 1

# Copy and configure
cp wayfinder_paths/config.example.json config.json
# Edit config.json with your Wayfinder credentials

# Run a strategy (status check)
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --action status --config config.json

# Run with custom config
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --config my_config.json

# Run continuously with debug output
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --debug --config config.json
```

### Wallet Generation for Testing

**Before running any strategies, generate test wallets.** This creates `config.json` in the repository root with throwaway wallets for local testing:

```bash
# Essential: Create main wallet for testing
just create-wallets
# Or manually: poetry run python wayfinder_paths/scripts/make_wallets.py -n 1
```

This creates:

- `main` wallet - your main wallet for testing (labeled "main" in config.json)
- `config.json` - wallet addresses and private keys for local testing

**Note:** Strategy-specific wallets are automatically created when you use `just create-strategy "Strategy Name"`. For manual creation, use `just create-wallet "strategy_name"` or `poetry run python wayfinder_paths/scripts/make_wallets.py --label "strategy_name"`.

**Important:** These wallets are for testing only. Never use them with real funds or on mainnet.

**Per-Strategy Wallets:** Each strategy should have its own dedicated wallet. When you create a new strategy using `just create-strategy`, a wallet is automatically generated with a label matching the strategy directory name. The system automatically uses this wallet when running the strategy. See [CONFIG_GUIDE.md](wayfinder_paths/CONFIG_GUIDE.md) for details.

Additional options:

```bash
# Add 3 extra wallets for multi-account testing
poetry run python wayfinder_paths/scripts/make_wallets.py -n 3

# Create a wallet with a specific label (e.g., for a strategy)
poetry run python wayfinder_paths/scripts/make_wallets.py --label "my_strategy_name"

# Generate keystore files (for geth/web3 compatibility)
poetry run python wayfinder_paths/scripts/make_wallets.py -n 1 --keystore-password "my-password"
```

### Configuration

See [CONFIG_GUIDE.md](wayfinder_paths/CONFIG_GUIDE.md) for detailed configuration documentation.

#### Setup Configuration

```bash
# Copy example config
cp wayfinder_paths/config.example.json config.json

# Edit config.json with your settings
# Required fields:
#   - user.username: Your Wayfinder username
#   - user.password: Your Wayfinder password
#   - OR user.refresh_token: Your refresh token
#   - system.wallets_path: Path to config.json (default: "config.json")
#
# Wallet addresses are auto-loaded from config.json by default.
# Then run with:
poetry run python wayfinder_paths/run_strategy.py stablecoin_yield_strategy --config config.json
```

## 📦 Versioning

This package follows [Semantic Versioning](https://semver.org/) (SemVer) and is published to PyPI as a public package.

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR** (X.0.0): Breaking changes that require code updates
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

### Version Bumping Rules

- **PATCH**: Bug fixes, security patches, documentation updates
- **MINOR**: New adapters, new strategies, new features (backward compatible)
- **MAJOR**: Breaking API changes, removed features, incompatible changes

### Important Notes

- **Versions are immutable**: Once published to PyPI, a version cannot be changed or deleted
- **Versions must be unique**: Each release must have a new, unique version number
- **Publishing is restricted**: Only publish from the `main` branch to prevent accidental releases

### Publishing Workflow and Order of Operations

**Critical**: Changes must follow this strict order:

1. **Merge to main**: All changes must be merged to the `main` branch first
2. **Publish to PyPI**: The new version must be published to PyPI from `main` branch
3. **Dependent changes**: Only after publishing can dependent changes be merged in other applications

**Why this order matters:**

- Other applications depend on this package from PyPI
- They cannot merge changes that depend on new versions until those versions are available on PyPI
- Publishing from `main` ensures the published version matches what's in the repository
- This prevents dependency resolution failures in downstream applications

**Example workflow:**

```bash
# 1. Make changes in a feature branch
git checkout -b feature/new-adapter
# ... make changes ...
git commit -m "Add new adapter"

# 2. Merge to main
git checkout main
git merge feature/new-adapter

# 3. Bump version in pyproject.toml (e.g., 0.1.3 → 0.2.0)
# Edit pyproject.toml: version = "0.2.0"
git commit -m "Bump version to 0.2.0"
git push origin main

# 4. Publish to PyPI (must be on main branch)
just publish

# 5. Now dependent applications can update their dependencies
# pip install wayfinder-paths==0.2.0
```

## 📦 Publishing

Publish to PyPI:

```bash
export PUBLISH_TOKEN="your_pypi_token"
just publish
```

**Important:**

- ⚠️ **Publishing is only allowed from the `main` branch** - the publish command will fail if run from any other branch
- ⚠️ **Versions must be unique** - ensure the version in `pyproject.toml` has been bumped and is unique
- ⚠️ **Follow the order of operations** - see [Versioning](#-versioning) section above for the required workflow
- ⚠️ **Versions are immutable** - once published, a version cannot be changed or deleted from PyPI

Install the published package:

```bash
pip install wayfinder-paths
# or
poetry add wayfinder-paths
```

Install from Git (development):

```bash
pip install git+https://github.com/wayfinder-ai/wayfinder-paths.git
```

### Managing Package Access

To add collaborators who can publish updates:

1. Go to https://pypi.org/project/wayfinder-paths/
2. Click "Manage" → "Collaborators"
3. Add users as "Maintainers" (can publish) or "Owners" (full control)

## 🔒 Security

- **Never hardcode API keys or Private keys** - use config.json for credentials
- **Never commit config.json** - add it to .gitignore
- **Test on testnet first** - use test network when available
- **Validate all inputs** - sanitize user data
- **Set gas limits** - prevent excessive fees

## 📊 Backtesting

Coming soon

## 🌟 Community

Need help or want to discuss strategies? Join our [Discord](https://discord.gg/fUVwGMXjm3)!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

🚀 **Happy Wayfinding!**

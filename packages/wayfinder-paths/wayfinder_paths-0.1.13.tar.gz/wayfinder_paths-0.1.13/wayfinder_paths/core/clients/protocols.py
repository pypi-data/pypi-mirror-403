"""
Protocol definitions for API clients.

These protocols define the interface that all client implementations must satisfy.
When used as an SDK, users can provide custom implementations that match these protocols.

Note: AuthClient is excluded as SDK users handle their own authentication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from wayfinder_paths.core.clients.BRAPClient import BRAPQuote
    from wayfinder_paths.core.clients.HyperlendClient import (
        AssetsView,
        LendRateHistory,
        MarketEntry,
        StableMarket,
    )
    from wayfinder_paths.core.clients.LedgerClient import (
        StrategyTransactionList,
        TransactionRecord,
    )
    from wayfinder_paths.core.clients.PoolClient import (
        LlamaMatch,
        PoolList,
    )
    from wayfinder_paths.core.clients.TokenClient import (
        GasToken,
        TokenDetails,
    )
    from wayfinder_paths.core.clients.WalletClient import (
        PoolBalance,
        TokenBalance,
    )


class TokenClientProtocol(Protocol):
    """Protocol for token-related operations"""

    async def get_token_details(
        self, token_id: str, force_refresh: bool = False
    ) -> TokenDetails:
        """Get token data including price from the token-details endpoint"""
        ...

    async def get_gas_token(self, chain_code: str) -> GasToken:
        """Fetch the native gas token for a given chain code"""
        ...


class HyperlendClientProtocol(Protocol):
    """Protocol for Hyperlend-related operations"""

    async def get_stable_markets(
        self,
        *,
        chain_id: int,
        required_underlying_tokens: float | None = None,
        buffer_bps: int | None = None,
        min_buffer_tokens: float | None = None,
        is_stable_symbol: bool | None = None,
    ) -> list[StableMarket]:
        """Fetch stable markets from Hyperlend"""
        ...

    async def get_assets_view(
        self,
        *,
        chain_id: int,
        user_address: str,
    ) -> AssetsView:
        """Fetch assets view for a user address from Hyperlend"""
        ...

    async def get_market_entry(
        self,
        *,
        chain_id: int,
        token_address: str,
    ) -> MarketEntry:
        """Fetch market entry from Hyperlend"""
        ...

    async def get_lend_rate_history(
        self,
        *,
        chain_id: int,
        token_address: str,
        lookback_hours: int,
    ) -> LendRateHistory:
        """Fetch lend rate history from Hyperlend"""
        ...


class LedgerClientProtocol(Protocol):
    """Protocol for strategy transaction history and bookkeeping operations"""

    async def get_strategy_transactions(
        self,
        *,
        wallet_address: str,
        limit: int = 50,
        offset: int = 0,
    ) -> StrategyTransactionList:
        """Fetch a paginated list of transactions for a given strategy wallet"""
        ...

    async def get_strategy_net_deposit(self, *, wallet_address: str) -> float:
        """Fetch the net deposit (deposits - withdrawals) for a strategy"""
        ...

    async def get_strategy_latest_transactions(
        self, *, wallet_address: str
    ) -> StrategyTransactionList:
        """Fetch the latest transactions for a strategy"""
        ...

    async def add_strategy_deposit(
        self,
        *,
        wallet_address: str,
        chain_id: int,
        token_address: str,
        token_amount: str | float,
        usd_value: str | float,
        data: dict[str, Any] | None = None,
        strategy_name: str | None = None,
    ) -> TransactionRecord:
        """Record a deposit for a strategy"""
        ...

    async def add_strategy_withdraw(
        self,
        *,
        wallet_address: str,
        chain_id: int,
        token_address: str,
        token_amount: str | float,
        usd_value: str | float,
        data: dict[str, Any] | None = None,
        strategy_name: str | None = None,
    ) -> TransactionRecord:
        """Record a withdrawal for a strategy"""
        ...

    async def add_strategy_operation(
        self,
        *,
        wallet_address: str,
        operation_data: dict[str, Any],
        usd_value: str | float,
        strategy_name: str | None = None,
    ) -> TransactionRecord:
        """Record a strategy operation (e.g., swaps, rebalances)"""
        ...


class WalletClientProtocol(Protocol):
    """Protocol for wallet-related operations"""

    async def get_token_balance_for_wallet(
        self,
        *,
        token_id: str,
        wallet_address: str,
        human_readable: bool = True,
    ) -> TokenBalance:
        """Fetch a single token balance for an explicit wallet address"""
        ...

    async def get_pool_balance_for_wallet(
        self,
        *,
        pool_address: str,
        chain_id: int,
        user_address: str,
        human_readable: bool = True,
    ) -> PoolBalance:
        """Fetch a wallet's LP/share balance for a given pool address and chain"""
        ...


class PoolClientProtocol(Protocol):
    """Protocol for pool-related read operations"""

    async def get_pools_by_ids(
        self,
        *,
        pool_ids: str,
    ) -> PoolList:
        """Fetch pools by comma-separated pool ids"""
        ...

    async def get_pools(self) -> dict[str, LlamaMatch]:
        """Fetch Llama matches for pools"""
        ...


class BRAPClientProtocol(Protocol):
    """Protocol for BRAP (Bridge/Router/Adapter Protocol) quote operations"""

    async def get_quote(
        self,
        *,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        from_address: str,
        to_address: str,
        amount1: str,
        slippage: float | None = None,
        wayfinder_fee: float | None = None,
    ) -> BRAPQuote:
        """Get a quote for a bridge/swap operation"""
        ...


class HyperliquidExecutorProtocol(Protocol):
    """Protocol for Hyperliquid order execution operations."""

    async def place_market_order(
        self,
        *,
        asset_id: int,
        is_buy: bool,
        slippage: float,
        size: float,
        address: str,
        reduce_only: bool = False,
        cloid: Any = None,
        builder: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Place a market order."""
        ...

    async def cancel_order(
        self,
        *,
        asset_id: int,
        order_id: int,
        address: str,
    ) -> dict[str, Any]:
        """Cancel an open order."""
        ...

    async def update_leverage(
        self,
        *,
        asset_id: int,
        leverage: int,
        is_cross: bool,
        address: str,
    ) -> dict[str, Any]:
        """Update leverage for an asset."""
        ...

    async def transfer_spot_to_perp(
        self,
        *,
        amount: float,
        address: str,
    ) -> dict[str, Any]:
        """Transfer USDC from spot to perp balance."""
        ...

    async def transfer_perp_to_spot(
        self,
        *,
        amount: float,
        address: str,
    ) -> dict[str, Any]:
        """Transfer USDC from perp to spot balance."""
        ...

    async def place_stop_loss(
        self,
        *,
        asset_id: int,
        is_buy: bool,
        trigger_price: float,
        size: float,
        address: str,
    ) -> dict[str, Any]:
        """Place a stop-loss order."""
        ...

    async def place_limit_order(
        self,
        *,
        asset_id: int,
        is_buy: bool,
        price: float,
        size: float,
        address: str,
        reduce_only: bool = False,
        builder: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Place a limit order."""
        ...

    async def withdraw(
        self,
        *,
        amount: float,
        address: str,
    ) -> dict[str, Any]:
        """Withdraw USDC from Hyperliquid to Arbitrum."""
        ...

    async def approve_builder_fee(
        self,
        *,
        builder: str,
        max_fee_rate: str,
        address: str,
    ) -> dict[str, Any]:
        """Approve a builder fee for the user."""
        ...

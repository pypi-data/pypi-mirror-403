from __future__ import annotations

import traceback
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from loguru import logger

from wayfinder_paths.core.clients.TokenClient import TokenDetails
from wayfinder_paths.core.strategies.descriptors import StratDescriptor


class StatusDict(TypedDict):
    portfolio_value: float
    net_deposit: float
    strategy_status: Any
    gas_available: float
    gassed_up: bool


StatusTuple = tuple[bool, str]


class WalletConfig(TypedDict, total=False):
    """Wallet configuration structure - allows additional fields for flexibility"""

    address: str
    private_key: str | None
    private_key_hex: str | None
    wallet_type: str | None


class StrategyConfig(TypedDict, total=False):
    """Base strategy configuration structure - allows additional fields for flexibility"""

    main_wallet: WalletConfig | None
    strategy_wallet: WalletConfig | None
    wallet_type: str | None


class LiquidationResult(TypedDict):
    usd_value: float
    token: TokenDetails
    amt: int


class Strategy(ABC):
    name: str | None = None
    INFO: StratDescriptor | None = None

    def __init__(
        self,
        config: StrategyConfig | dict[str, Any] | None = None,
        *,
        main_wallet: WalletConfig | dict[str, Any] | None = None,
        strategy_wallet: WalletConfig | dict[str, Any] | None = None,
        api_key: str | None = None,
        main_wallet_signing_callback: Callable[[dict], Awaitable[str]] | None = None,
        strategy_wallet_signing_callback: Callable[[dict], Awaitable[str]]
        | None = None,
    ):
        self.adapters = {}
        self.ledger_adapter = None
        self.logger = logger.bind(strategy=self.__class__.__name__)
        self.config = config
        self.main_wallet_signing_callback = main_wallet_signing_callback
        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback

    async def setup(self) -> None:
        """Initialize strategy-specific setup after construction"""
        pass

    async def log(self, msg: str) -> None:
        """Log messages - can be overridden by subclasses"""
        self.logger.info(msg)

    async def quote(self) -> None:
        """Get quotes for potential trades - optional for strategies"""
        pass

    def _get_strategy_wallet_address(self) -> str:
        """Get strategy wallet address with validation."""
        strategy_wallet = self.config.get("strategy_wallet")
        if not strategy_wallet or not isinstance(strategy_wallet, dict):
            raise ValueError("strategy_wallet not configured in strategy config")
        address = strategy_wallet.get("address")
        if not address:
            raise ValueError("strategy_wallet address not found in config")
        return str(address)

    def _get_main_wallet_address(self) -> str:
        """Get main wallet address with validation."""
        main_wallet = self.config.get("main_wallet")
        if not main_wallet or not isinstance(main_wallet, dict):
            raise ValueError("main_wallet not configured in strategy config")
        address = main_wallet.get("address")
        if not address:
            raise ValueError("main_wallet address not found in config")
        return str(address)

    @abstractmethod
    async def deposit(self, **kwargs) -> StatusTuple:
        """
        Deposit funds into the strategy.

        Args:
            **kwargs: Strategy-specific deposit parameters. Common parameters include:
                - main_token_amount: Amount of main token to deposit (float)
                - gas_token_amount: Amount of gas token to deposit (float)

        Returns:
            Tuple of (success: bool, message: str)

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        pass

    async def withdraw(self, **kwargs) -> StatusTuple:
        """
        Withdraw funds from the strategy.
        Default implementation unwinds all operations.

        Args:
            **kwargs: Strategy-specific withdrawal parameters (optional).

        Returns:
            Tuple of (success: bool, message: str)

        Note:
            Subclasses may override this method to add validation or custom
            withdrawal logic. The base implementation unwinds all ledger operations.
        """
        if hasattr(self, "ledger_adapter") and self.ledger_adapter:
            while self.ledger_adapter.positions.operations:
                node = self.ledger_adapter.positions.operations[-1]
                adapter = self.adapters.get(node.adapter)
                if adapter and hasattr(adapter, "unwind_op"):
                    await adapter.unwind_op(node)
                self.ledger_adapter.positions.operations.pop()

            await self.ledger_adapter.save()

        return (True, "Withdrawal complete")

    @abstractmethod
    async def update(self) -> StatusTuple:
        """
        Deploy funds to protocols (no main wallet access).
        Called after deposit() has transferred assets to strategy wallet.

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @abstractmethod
    async def exit(self, **kwargs) -> StatusTuple:
        """
        Transfer funds from strategy wallet to main wallet.
        Called after withdraw() has liquidated all positions.

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @staticmethod
    async def policies() -> list[str]:
        """Return policy strings for this strategy."""
        raise NotImplementedError

    @abstractmethod
    async def _status(self) -> StatusDict:
        """
        Return status payload. Subclasses should implement this.
        Should include keys (portfolio_value, net_deposit, strategy_status).
        Backward-compatible keys (active_amount, total_earned) may also be included.
        """
        pass

    async def status(self) -> StatusDict:
        """
        Wrapper to compute and return strategy status and record a snapshot.
        Here we simply delegate to _status for compatibility.
        """

        status = await self._status()
        await self.ledger_adapter.record_strategy_snapshot(
            wallet_address=self._get_strategy_wallet_address(),
            strategy_status=status,
        )

        return status

    def register_adapters(self, adapters: list[Any]) -> None:
        """Register adapters for use by the strategy"""
        self.adapters = {}
        for adapter in adapters:
            if hasattr(adapter, "adapter_type"):
                self.adapters[adapter.adapter_type] = adapter
            elif hasattr(adapter, "__class__"):
                self.adapters[adapter.__class__.__name__] = adapter

    def unwind_on_error(
        self, func: Callable[..., Awaitable[StatusTuple]]
    ) -> Callable[..., Awaitable[StatusTuple]]:
        """
        Decorator to unwind operations on error
        Useful for deposit operations that need cleanup on failure
        """

        async def wrapper(*args: Any, **kwargs: Any) -> StatusTuple:
            try:
                return await func(*args, **kwargs)
            except Exception:
                trace = traceback.format_exc()
                try:
                    await self.withdraw()
                    return (
                        False,
                        f"Strategy failed during operation and was unwound. Failure: {trace}",
                    )
                except Exception:
                    trace2 = traceback.format_exc()
                    return (
                        False,
                        f"Strategy failed and unwinding also failed. Operation error: {trace}. Unwind error: {trace2}",
                    )
            finally:
                if hasattr(self, "ledger_adapter") and self.ledger_adapter:
                    await self.ledger_adapter.save()

        return wrapper

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """
        Return metadata about this strategy.
        Can be overridden to provide discovery information.

        Returns:
            Dictionary containing strategy metadata. The following keys are optional
            and will be None if not defined on the class:
            - name: Strategy name
            - description: Strategy description
            - summary: Strategy summary
        """
        return {
            "name": getattr(cls, "name", None),
            "description": getattr(cls, "description", None),
            "summary": getattr(cls, "summary", None),
        }

    async def health_check(self) -> dict[str, Any]:
        """
        Check strategy health and dependencies
        """
        health = {"status": "healthy", "strategy": self.name, "adapters": {}}

        for name, adapter in self.adapters.items():
            if hasattr(adapter, "health_check"):
                health["adapters"][name] = await adapter.health_check()
            else:
                health["adapters"][name] = {"status": "unknown"}

        return health

    async def partial_liquidate(
        self, usd_value: float
    ) -> tuple[bool, LiquidationResult]:
        """
        Partially liquidate strategy positions by USD value.
        Optional method that can be overridden by subclasses.

        Args:
            usd_value: USD value to liquidate (must be positive).

        Returns:
            Tuple of (success: bool, message: str)

        Raises:
            ValueError: If usd_value is not positive.

        Note:
            Base implementation returns failure. Subclasses should override
            to implement partial liquidation logic.
        """
        if usd_value <= 0:
            raise ValueError(f"usd_value must be positive, got {usd_value}")
        return (False, "Partial liquidation not implemented for this strategy")

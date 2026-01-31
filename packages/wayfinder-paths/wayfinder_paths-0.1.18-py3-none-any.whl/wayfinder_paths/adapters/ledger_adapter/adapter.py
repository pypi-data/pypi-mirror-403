from typing import Any

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.adapters.models import Operation
from wayfinder_paths.core.clients.LedgerClient import (
    LedgerClient,
    NetDeposit,
    StrategyTransactionList,
    TransactionRecord,
)
from wayfinder_paths.core.strategies.Strategy import StatusDict


class LedgerAdapter(BaseAdapter):
    """
    Ledger adapter for strategy transaction history and bookkeeping operations.

    Provides high-level operations for:
    - Fetching strategy transaction history
    - Getting net deposit amounts
    - Getting last rotation time
    - Recording deposits, withdrawals, and operations
    """

    adapter_type: str = "LEDGER"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        ledger_client: LedgerClient | None = None,
    ):
        super().__init__("ledger_adapter", config)
        self.ledger_client = ledger_client or LedgerClient()

    async def get_strategy_transactions(
        self, wallet_address: str, limit: int = 50, offset: int = 0
    ) -> tuple[bool, StrategyTransactionList | str]:
        """
        Get paginated strategy transaction history.

        Args:
            wallet_address: Strategy wallet address
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip

        Returns:
            Tuple of (success, data) where data is transaction list or error message
        """
        try:
            data = await self.ledger_client.get_strategy_transactions(
                wallet_address=wallet_address, limit=limit, offset=offset
            )
            return (True, data)
        except Exception as e:
            self.logger.error(f"Error fetching strategy transactions: {e}")
            return (False, str(e))

    async def get_strategy_net_deposit(
        self, wallet_address: str
    ) -> tuple[bool, NetDeposit | str]:
        """
        Get net deposit amount (deposits - withdrawals) for a strategy.

        Args:
            wallet_address: Strategy wallet address

        Returns:
            Tuple of (success, data) where data contains net_deposit or error message
        """
        try:
            data = await self.ledger_client.get_strategy_net_deposit(
                wallet_address=wallet_address
            )
            return (True, data)
        except Exception as e:
            self.logger.error(f"Error fetching strategy net deposit: {e}")
            return (False, str(e))

    async def get_strategy_latest_transactions(
        self, wallet_address: str
    ) -> tuple[bool, StrategyTransactionList | str]:
        """
        Get the latest transactions for a strategy.

        Args:
            wallet_address: Strategy wallet address

        Returns:
            Tuple of (success, data) where data contains latest transactions or error message
        """
        try:
            data = await self.ledger_client.get_strategy_latest_transactions(
                wallet_address=wallet_address
            )
            return (True, data)
        except Exception as e:
            self.logger.error(f"Error fetching strategy last transactions: {e}")
            return (False, str(e))

    async def record_deposit(
        self,
        wallet_address: str,
        chain_id: int,
        token_address: str,
        token_amount: str | float,
        usd_value: str | float,
        data: dict[str, Any] | None = None,
        strategy_name: str | None = None,
    ) -> tuple[bool, TransactionRecord | str]:
        """
        Record a strategy deposit transaction.

        Args:
            wallet_address: Strategy wallet address
            chain_id: Blockchain chain ID
            token_address: Token contract address
            token_amount: Amount deposited (in token units)
            usd_value: USD value of the deposit
            data: Additional transaction data
            strategy_name: Name of the strategy making the deposit

        Returns:
            Tuple of (success, data) where data is transaction record or error message
        """
        try:
            result = await self.ledger_client.add_strategy_deposit(
                wallet_address=wallet_address,
                chain_id=chain_id,
                token_address=token_address,
                token_amount=token_amount,
                usd_value=usd_value,
                data=data,
                strategy_name=strategy_name,
            )
            return (True, result)
        except Exception as e:
            self.logger.error(f"Error recording deposit: {e}")
            return (False, str(e))

    async def record_withdrawal(
        self,
        wallet_address: str,
        chain_id: int,
        token_address: str,
        token_amount: str | float,
        usd_value: str | float,
        data: dict[str, Any] | None = None,
        strategy_name: str | None = None,
    ) -> tuple[bool, TransactionRecord | str]:
        """
        Record a strategy withdrawal transaction.

        Args:
            wallet_address: Strategy wallet address
            chain_id: Blockchain chain ID
            token_address: Token contract address
            token_amount: Amount withdrawn (in token units)
            usd_value: USD value of the withdrawal
            data: Additional transaction data
            strategy_name: Name of the strategy making the withdrawal

        Returns:
            Tuple of (success, data) where data is transaction record or error message
        """
        try:
            result = await self.ledger_client.add_strategy_withdraw(
                wallet_address=wallet_address,
                chain_id=chain_id,
                token_address=token_address,
                token_amount=token_amount,
                usd_value=usd_value,
                data=data,
                strategy_name=strategy_name,
            )
            return (True, result)
        except Exception as e:
            self.logger.error(f"Error recording withdrawal: {e}")
            return (False, str(e))

    async def record_operation(
        self,
        wallet_address: str,
        operation_data: Operation,
        usd_value: str | float,
        strategy_name: str | None = None,
    ) -> tuple[bool, TransactionRecord | str]:
        """
        Record a strategy operation (e.g., swaps, rebalances) for bookkeeping.

        Args:
            wallet_address: Strategy wallet address
            operation_data: Operation model (SWAP, LEND, BORROW, etc.)
            usd_value: USD value of the operation
            strategy_name: Name of the strategy performing the operation

        Returns:
            Tuple of (success, data) where data is operation record or error message
        """
        try:
            result = await self.ledger_client.add_strategy_operation(
                wallet_address=wallet_address,
                operation_data=operation_data,
                usd_value=usd_value,
                strategy_name=strategy_name,
            )
            return (True, result)
        except Exception as e:
            self.logger.error(f"Error recording operation: {e}")
            return (False, str(e))

    async def get_transaction_summary(
        self, wallet_address: str, limit: int = 10
    ) -> tuple[bool, Any]:
        """
        Get a summary of recent strategy transactions.

        Args:
            wallet_address: Strategy wallet address
            limit: Number of recent transactions to include

        Returns:
            Tuple of (success, data) where data is transaction summary or error message
        """
        try:
            success, transactions_data = await self.get_strategy_transactions(
                wallet_address=wallet_address, limit=limit
            )

            if not success:
                return (False, transactions_data)

            transactions = transactions_data.get("transactions", [])

            # Create summary
            summary = {
                "total_transactions": len(transactions),
                "recent_transactions": transactions[:limit],
                "operations": {
                    "deposits": len(
                        [t for t in transactions if t.get("operation") == "DEPOSIT"]
                    ),
                    "withdrawals": len(
                        [t for t in transactions if t.get("operation") == "WITHDRAW"]
                    ),
                    "operations": len(
                        [
                            t
                            for t in transactions
                            if t.get("operation") not in ["DEPOSIT", "WITHDRAW"]
                        ]
                    ),
                },
            }

            return (True, summary)
        except Exception as e:
            self.logger.error(f"Error creating transaction summary: {e}")
            return (False, str(e))

    async def record_strategy_snapshot(
        self, wallet_address: str, strategy_status: StatusDict
    ) -> tuple[bool, None | str]:
        """
        Record a strategy snapshot with current state.

        Args:
            wallet_address: Strategy wallet address
            strat_portfolio_value: Current portfolio value
            net_deposit: Net deposit amount
            strategy_status: Current strategy status dictionary
            gas_available: Available gas amount
            gassed_up: Whether the strategy is gassed up

        Returns:
            Tuple of (success, None) on success or (False, error_message) on failure
        """
        try:
            await self.ledger_client.strategy_snapshot(
                wallet_address=wallet_address,
                strat_portfolio_value=strategy_status["portfolio_value"],
                net_deposit=strategy_status["net_deposit"],
                strategy_status=strategy_status["strategy_status"],
                gas_available=strategy_status["gas_available"],
                gassed_up=strategy_status["gassed_up"],
            )
            return (True, None)
        except Exception as e:
            self.logger.error(f"Error recording strategy snapshot: {e}")
            return (False, str(e))

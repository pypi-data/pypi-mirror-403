from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NotRequired, Required, TypedDict

from wayfinder_paths.core.adapters.models import Operation


class StrategyTransaction(TypedDict):
    """Individual strategy transaction structure"""

    id: Required[str]
    operation: Required[str]
    timestamp: Required[str]
    amount: Required[str]
    token_address: Required[str]
    usd_value: Required[str]
    strategy_name: NotRequired[str | None]
    chain_id: NotRequired[int | None]


class StrategyTransactionList(TypedDict):
    """Vault transaction list response structure"""

    transactions: Required[list[StrategyTransaction]]
    total: Required[int]
    limit: Required[int]
    offset: Required[int]


class NetDeposit(TypedDict):
    """Net deposit response structure"""

    net_deposit: Required[str]
    total_deposits: Required[str]
    total_withdrawals: Required[str]
    wallet_address: NotRequired[str | None]


class TransactionRecord(TypedDict):
    """Transaction record response structure"""

    transaction_id: Required[str]
    status: Required[str]
    timestamp: Required[str]


class LedgerClient:
    """
    Client for strategy transaction history and bookkeeping operations using local JSON files.

    Supports:
    - GET strategy transactions
    - GET strategy net deposit
    - GET strategy latest transactions
    - POST add deposit
    - POST add withdraw
    - POST add operation
    - POST record snapshot
    """

    def __init__(self, ledger_dir: Path | str | None = None) -> None:
        """
        Initialize the ledger client.

        Args:
            ledger_dir: Directory to store ledger JSON files. Defaults to .ledger in project root
        """
        if ledger_dir is None:
            # Default to .ledger directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            ledger_dir = project_root / ".ledger"

        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

        self.transactions_file = self.ledger_dir / "transactions.json"
        self.snapshots_file = self.ledger_dir / "snapshots.json"

        # File locks for thread-safe operations
        self._transactions_lock = asyncio.Lock()
        self._snapshots_lock = asyncio.Lock()

        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self) -> None:
        """Create initial JSON files if they don't exist."""
        if not self.transactions_file.exists():
            self.transactions_file.write_text(
                json.dumps({"transactions": []}, indent=2)
            )

        if not self.snapshots_file.exists():
            self.snapshots_file.write_text(json.dumps({"snapshots": []}, indent=2))

    async def _read_transactions(self) -> dict[str, Any]:
        """Read transactions from file with lock."""
        async with self._transactions_lock:
            if not self.transactions_file.exists():
                return {"transactions": []}
            try:
                content = self.transactions_file.read_text()
                return json.loads(content)
            except json.JSONDecodeError:
                return {"transactions": []}

    async def _write_transactions(self, data: dict[str, Any]) -> None:
        """Write transactions to file with lock."""
        async with self._transactions_lock:
            self.transactions_file.write_text(json.dumps(data, indent=2))

    async def _read_snapshots(self) -> dict[str, Any]:
        """Read snapshots from file with lock."""
        async with self._snapshots_lock:
            if not self.snapshots_file.exists():
                return {"snapshots": []}
            try:
                content = self.snapshots_file.read_text()
                return json.loads(content)
            except json.JSONDecodeError:
                return {"snapshots": []}

    async def _write_snapshots(self, data: dict[str, Any]) -> None:
        """Write snapshots to file with lock."""
        async with self._snapshots_lock:
            self.snapshots_file.write_text(json.dumps(data, indent=2))

    # ===================== Read Endpoints =====================

    async def get_strategy_transactions(
        self,
        *,
        wallet_address: str,
        limit: int = 100,
        offset: int = 0,
    ) -> StrategyTransactionList:
        """
        Fetch a paginated list of transactions for a given strategy wallet address.

        Args:
            wallet_address: The strategy wallet address to filter by
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip

        Returns:
            StrategyTransactionList with transactions, total, limit, and offset
        """
        data = await self._read_transactions()
        all_transactions = data.get("transactions", [])

        # Filter by wallet_address
        filtered = [
            tx
            for tx in all_transactions
            if tx.get("wallet_address", "").lower() == wallet_address.lower()
        ]

        # Sort by timestamp descending (most recent first)
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        total = len(filtered)
        paginated = filtered[offset : offset + limit]

        return {
            "transactions": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def get_strategy_net_deposit(self, *, wallet_address: str) -> float:
        """
        Calculate the net deposit (deposits - withdrawals) for a strategy wallet.

        Args:
            wallet_address: The strategy wallet address

        Returns:
            NetDeposit with net_deposit, total_deposits, total_withdrawals
        """
        data = await self._read_transactions()
        all_transactions = data.get("transactions", [])

        # Filter by wallet_address
        filtered = [
            tx
            for tx in all_transactions
            if tx.get("wallet_address", "").lower() == wallet_address.lower()
        ]

        total_deposits = 0.0
        total_withdrawals = 0.0

        for tx in filtered:
            operation = tx.get("operation", "").upper()
            usd_value = float(tx.get("usd_value", 0))

            if operation == "DEPOSIT":
                total_deposits += usd_value
            elif operation == "WITHDRAW":
                total_withdrawals += usd_value

        net_deposit = total_deposits - total_withdrawals

        return float(net_deposit)

    async def get_strategy_latest_transactions(
        self, *, wallet_address: str, limit: int = 10
    ) -> StrategyTransactionList:
        """
        Fetch the most recent transactions for a strategy wallet.

        Args:
            wallet_address: The strategy wallet address
            limit: Maximum number of transactions to return (default 10)

        Returns:
            StrategyTransactionList with the latest transactions
        """
        return await self.get_strategy_transactions(
            wallet_address=wallet_address,
            limit=limit,
            offset=0,
        )

    # ===================== Write Endpoints =====================

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
        """
        Record a deposit for a strategy.

        Args:
            wallet_address: The strategy wallet address
            chain_id: The blockchain chain ID
            token_address: The token contract address
            token_amount: Amount of tokens deposited
            usd_value: USD value of the deposit
            data: Additional metadata
            strategy_name: Name of the strategy

        Returns:
            TransactionRecord with transaction_id, status, and timestamp
        """
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        transaction = {
            "id": transaction_id,
            "wallet_address": wallet_address,
            "operation": "DEPOSIT",
            "timestamp": timestamp,
            "chain_id": chain_id,
            "token_address": token_address,
            "token_amount": str(token_amount),
            "amount": str(token_amount),  # For backward compatibility
            "usd_value": str(usd_value),
            "data": data or {},
        }

        if strategy_name is not None:
            transaction["strategy_name"] = strategy_name

        # Add to transactions
        file_data = await self._read_transactions()
        file_data["transactions"].append(transaction)
        await self._write_transactions(file_data)

        return {
            "transaction_id": transaction_id,
            "status": "success",
            "timestamp": timestamp,
        }

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
        """
        Record a withdrawal for a strategy.

        Args:
            wallet_address: The strategy wallet address
            chain_id: The blockchain chain ID
            token_address: The token contract address
            token_amount: Amount of tokens withdrawn
            usd_value: USD value of the withdrawal
            data: Additional metadata
            strategy_name: Name of the strategy

        Returns:
            TransactionRecord with transaction_id, status, and timestamp
        """
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        transaction = {
            "id": transaction_id,
            "wallet_address": wallet_address,
            "operation": "WITHDRAW",
            "timestamp": timestamp,
            "chain_id": chain_id,
            "token_address": token_address,
            "token_amount": str(token_amount),
            "amount": str(token_amount),  # For backward compatibility
            "usd_value": str(usd_value),
            "data": data or {},
        }

        if strategy_name is not None:
            transaction["strategy_name"] = strategy_name

        # Add to transactions
        file_data = await self._read_transactions()
        file_data["transactions"].append(transaction)
        await self._write_transactions(file_data)

        return {
            "transaction_id": transaction_id,
            "status": "success",
            "timestamp": timestamp,
        }

    async def add_strategy_operation(
        self,
        *,
        wallet_address: str,
        operation_data: Operation,
        usd_value: str | float,
        strategy_name: str | None = None,
    ) -> TransactionRecord:
        """
        Record a strategy operation (e.g., swaps, rebalances) for bookkeeping.

        Args:
            wallet_address: Strategy wallet address
            operation_data: Operation model (SWAP, LEND, UNLEND, etc.)
            usd_value: USD value of the operation
            strategy_name: Optional strategy name

        Returns:
            TransactionRecord with transaction_id, status, and timestamp
        """
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        op_dict = operation_data.model_dump(mode="json")
        operation_type = op_dict.get("type", "OPERATION")

        transaction = {
            "id": transaction_id,
            "wallet_address": wallet_address,
            "operation": operation_type,
            "timestamp": timestamp,
            "usd_value": str(usd_value),
            "op_data": op_dict,
            "data": {},
        }

        # Extract relevant fields from operation data for easier querying
        if operation_type == "SWAP":
            transaction["token_address"] = op_dict.get("to_token_id", "")
            transaction["amount"] = op_dict.get("to_amount", "0")
        elif operation_type in ("LEND", "UNLEND"):
            transaction["token_address"] = op_dict.get("contract", "")
            transaction["amount"] = str(op_dict.get("amount", 0))

        if strategy_name is not None:
            transaction["strategy_name"] = strategy_name

        # Add to transactions
        file_data = await self._read_transactions()
        file_data["transactions"].append(transaction)
        await self._write_transactions(file_data)

        return {
            "transaction_id": transaction_id,
            "status": "success",
            "timestamp": timestamp,
        }

    async def strategy_snapshot(
        self,
        wallet_address: str,
        strat_portfolio_value: float,
        net_deposit: float,
        strategy_status: dict,
        gas_available: float,
        gassed_up: bool,
    ) -> None:
        """
        Record a periodic snapshot of strategy state.

        Args:
            wallet_address: Strategy wallet address
            strat_portfolio_value: Total portfolio value in USD
            net_deposit: Net deposit amount in USD
            strategy_status: Arbitrary strategy status data
            gas_available: Available gas tokens
            gassed_up: Whether strategy has sufficient gas
        """
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        snapshot = {
            "id": snapshot_id,
            "wallet_address": wallet_address,
            "timestamp": timestamp,
            "portfolio_value": strat_portfolio_value,
            "net_deposit": net_deposit,
            "gas_available": gas_available,
            "gassed_up": gassed_up,
            "strategy_status": strategy_status,
        }

        # Add to snapshots
        file_data = await self._read_snapshots()
        file_data["snapshots"].append(snapshot)
        await self._write_snapshots(file_data)

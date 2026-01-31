from typing import Any

from wayfinder_paths.adapters.ledger_adapter.adapter import LedgerAdapter
from wayfinder_paths.adapters.token_adapter.adapter import TokenAdapter
from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.clients.WalletClient import WalletClient
from wayfinder_paths.core.utils.evm_helpers import resolve_chain_id
from wayfinder_paths.core.utils.tokens import build_send_transaction
from wayfinder_paths.core.utils.transaction import send_transaction


class BalanceAdapter(BaseAdapter):
    adapter_type = "BALANCE"

    def __init__(
        self,
        config: dict[str, Any],
        main_wallet_signing_callback=None,
        strategy_wallet_signing_callback=None,
    ):
        super().__init__("balance", config)
        self.main_wallet_signing_callback = main_wallet_signing_callback
        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback
        self.wallet_client = WalletClient()
        self.token_client = TokenClient()
        self.token_adapter = TokenAdapter()
        self.ledger_adapter = LedgerAdapter()

    def _parse_balance(self, raw: Any) -> int:
        if raw is None:
            return 0
        try:
            return int(raw)
        except (ValueError, TypeError):
            try:
                return int(float(raw))
            except (ValueError, TypeError):
                return 0

    async def get_balance(
        self,
        *,
        query: str | dict[str, Any] | None = None,
        token_id: str | None = None,
        wallet_address: str,
        chain_id: int | None = None,
    ) -> tuple[bool, str | int]:
        effective_query = query if query is not None else token_id
        resolved = (
            effective_query
            if isinstance(effective_query, str)
            else (effective_query or {}).get("token_id")
        )
        if not resolved:
            return (False, "missing query")
        try:
            if chain_id is None:
                token_info = await self.token_client.get_token_details(resolved)
                if not token_info:
                    return (False, f"Token not found: {resolved}")
                resolved_chain_id = resolve_chain_id(token_info, self.logger)
                if resolved_chain_id is None:
                    return (False, f"Token {resolved} is missing a chain id")
                chain_id = resolved_chain_id

            data = await self.wallet_client.get_token_balance_for_address(
                wallet_address=wallet_address,
                query=resolved,
                chain_id=int(chain_id),
            )
            raw = (
                data.get("balance_raw") or data.get("balance")
                if isinstance(data, dict)
                else None
            )
            return (True, self._parse_balance(raw))
        except Exception as e:
            return (False, str(e))

    async def move_from_main_wallet_to_strategy_wallet(
        self,
        token_id: str,
        amount: float,
        strategy_name: str = "unknown",
        skip_ledger: bool = False,
    ) -> tuple[bool, Any]:
        return await self._move_between_wallets(
            token_id=token_id,
            amount=amount,
            from_wallet=self.config.get("main_wallet"),
            to_wallet=self.config.get("strategy_wallet"),
            ledger_method=self.ledger_adapter.record_deposit,
            ledger_wallet="to",
            strategy_name=strategy_name,
            skip_ledger=skip_ledger,
        )

    async def move_from_strategy_wallet_to_main_wallet(
        self,
        token_id: str,
        amount: float,
        strategy_name: str = "unknown",
        skip_ledger: bool = False,
    ) -> tuple[bool, Any]:
        return await self._move_between_wallets(
            token_id=token_id,
            amount=amount,
            from_wallet=self.config.get("strategy_wallet"),
            to_wallet=self.config.get("main_wallet"),
            ledger_method=self.ledger_adapter.record_withdrawal,
            ledger_wallet="from",
            strategy_name=strategy_name,
            skip_ledger=skip_ledger,
        )

    async def send_to_address(
        self,
        token_id: str,
        amount: int,
        from_wallet: dict[str, Any] | None,
        to_address: str,
        signing_callback=None,
        skip_ledger: bool = True,
    ) -> tuple[bool, Any]:
        from_address = self._wallet_address(from_wallet)
        if not from_address:
            return False, "from_wallet missing or invalid"

        if not to_address:
            return False, "to_address is required"

        token_info = await self.token_client.get_token_details(token_id)
        if not token_info:
            return False, f"Token not found: {token_id}"

        chain_id = resolve_chain_id(token_info, self.logger)
        if chain_id is None:
            return False, f"Token {token_id} is missing chain_id"

        token_address = token_info.get("address")

        tx = await build_send_transaction(
            from_address=from_address,
            to_address=to_address,
            token_address=token_address,
            chain_id=chain_id,
            amount=int(amount),
        )

        if not signing_callback:
            return False, "signing_callback is required"

        tx_hash = await send_transaction(tx, signing_callback)
        return True, tx_hash

    async def _move_between_wallets(
        self,
        *,
        token_id: str,
        amount: float,
        from_wallet: dict[str, Any] | None,
        to_wallet: dict[str, Any] | None,
        ledger_method,
        ledger_wallet: str,
        strategy_name: str,
        skip_ledger: bool,
    ) -> tuple[bool, Any]:
        from_address = self._wallet_address(from_wallet)
        to_address = self._wallet_address(to_wallet)
        if not from_address or not to_address:
            return False, "main_wallet or strategy_wallet missing"

        token_info = await self.token_client.get_token_details(token_id)
        if not token_info:
            return False, f"Token not found: {token_id}"

        chain_id = resolve_chain_id(token_info, self.logger)
        if chain_id is None:
            return False, f"Token {token_id} is missing chain_id"

        decimals = token_info.get("decimals", 18)
        raw_amount = int(amount * (10**decimals))

        tx = await build_send_transaction(
            from_address=from_address,
            to_address=to_address,
            token_address=token_info.get("address"),
            chain_id=chain_id,
            amount=raw_amount,
        )
        broadcast_result = await self._send_tx(tx, from_address)

        if broadcast_result[0] and not skip_ledger and ledger_method is not None:
            wallet_for_ledger = from_address if ledger_wallet == "from" else to_address
            await self._record_ledger_entry(
                ledger_method=ledger_method,
                wallet_address=wallet_for_ledger,
                token_info=token_info,
                amount=amount,
                strategy_name=strategy_name,
            )

        return broadcast_result

    async def _send_tx(self, tx: dict[str, Any], from_address: str) -> tuple[bool, Any]:
        main_wallet = self.config.get("main_wallet") or {}
        main_addr = main_wallet.get("address", "").lower()

        if from_address.lower() == main_addr:
            callback = self.main_wallet_signing_callback
        else:
            callback = self.strategy_wallet_signing_callback

        txn_hash = await send_transaction(tx, callback)
        return True, txn_hash

    async def _record_ledger_entry(
        self,
        *,
        ledger_method,
        wallet_address: str,
        token_info: dict[str, Any],
        amount: float,
        strategy_name: str,
    ) -> None:
        chain_id = resolve_chain_id(token_info, self.logger)
        if chain_id is None:
            return

        usd_value = await self._token_amount_usd(token_info, amount)
        try:
            token_id = token_info.get("token_id") or token_info.get("id")
            success, response = await ledger_method(
                wallet_address=wallet_address,
                chain_id=chain_id,
                token_address=token_info.get("address"),
                token_amount=str(amount),
                usd_value=usd_value,
                data={
                    "token_id": token_id,
                    "amount": str(amount),
                    "usd_value": usd_value,
                },
                strategy_name=strategy_name,
            )
            if not success:
                self.logger.warning(
                    "Ledger entry failed",
                    wallet=wallet_address,
                    token_id=token_id,
                    amount=amount,
                    error=response,
                )
        except Exception as exc:  # noqa: BLE001
            token_id = token_info.get("token_id") or token_info.get("id")
            self.logger.warning(
                f"Ledger entry raised: {exc}",
                wallet=wallet_address,
                token_id=token_id,
            )

    async def _token_amount_usd(
        self, token_info: dict[str, Any], amount: float
    ) -> float:
        token_id = token_info.get("token_id")
        if not token_id:
            return 0.0
        success, price_data = await self.token_adapter.get_token_price(token_id)
        if not success or not price_data:
            return 0.0
        return float(price_data.get("current_price", 0.0)) * float(amount)

    def _wallet_address(self, wallet: dict[str, Any] | None) -> str | None:
        if not wallet:
            return None
        address = wallet.get("address")
        if address:
            return str(address)
        evm_wallet = wallet.get("evm") if isinstance(wallet, dict) else None
        if isinstance(evm_wallet, dict):
            return evm_wallet.get("address")
        return None

from __future__ import annotations

from typing import Any

from eth_utils import to_checksum_address

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.HyperlendClient import (
    AssetsView,
    HyperlendClient,
    LendRateHistory,
    MarketEntry,
    StableMarketsHeadroomResponse,
)
from wayfinder_paths.core.constants.hyperlend_abi import (
    POOL_ABI,
    WRAPPED_TOKEN_GATEWAY_ABI,
)
from wayfinder_paths.core.utils.tokens import (
    build_approve_transaction,
    get_token_allowance,
)
from wayfinder_paths.core.utils.transaction import send_transaction
from wayfinder_paths.core.utils.web3 import web3_from_chain_id

HYPERLEND_DEFAULTS = {
    "pool": "0x00A89d7a5A02160f20150EbEA7a2b5E4879A1A8b",
    "wrapped_token_gateway": "0x49558c794ea2aC8974C9F27886DDfAa951E99171",
    "wrapped_native_underlying": "0x5555555555555555555555555555555555555555",
}


class HyperlendAdapter(BaseAdapter):
    adapter_type = "HYPERLEND"

    def __init__(
        self,
        config: dict[str, Any],
        strategy_wallet_signing_callback=None,
    ) -> None:
        super().__init__("hyperlend_adapter", config)
        cfg = config or {}
        adapter_cfg = cfg.get("hyperlend_adapter") or {}

        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback
        self.hyperlend_client = HyperlendClient()

        self.strategy_wallet = cfg.get("strategy_wallet") or {}
        self.pool_address = self._checksum(
            adapter_cfg.get("pool_address") or HYPERLEND_DEFAULTS["pool"]
        )
        self.gateway_address = self._checksum(
            adapter_cfg.get("wrapped_token_gateway")
            or HYPERLEND_DEFAULTS["wrapped_token_gateway"]
        )
        self.wrapped_native = self._checksum(
            adapter_cfg.get("wrapped_native_underlying")
            or HYPERLEND_DEFAULTS["wrapped_native_underlying"]
        )
        self.gateway_deposit_takes_pool = adapter_cfg.get(
            "gateway_deposit_takes_pool", True
        )

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    async def get_stable_markets(
        self,
        *,
        required_underlying_tokens: float | None = None,
        buffer_bps: int | None = None,
        min_buffer_tokens: float | None = None,
    ) -> tuple[bool, StableMarketsHeadroomResponse | str]:
        try:
            data = await self.hyperlend_client.get_stable_markets(
                required_underlying_tokens=required_underlying_tokens,
                buffer_bps=buffer_bps,
                min_buffer_tokens=min_buffer_tokens,
            )
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def get_assets_view(
        self,
        *,
        user_address: str,
    ) -> tuple[bool, AssetsView | str]:
        try:
            data = await self.hyperlend_client.get_assets_view(
                user_address=user_address
            )
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def get_market_entry(
        self,
        *,
        token: str,
    ) -> tuple[bool, MarketEntry | str]:
        try:
            data = await self.hyperlend_client.get_market_entry(token=token)
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def get_lend_rate_history(
        self,
        *,
        token: str,
        lookback_hours: int,
        force_refresh: bool | None = None,
    ) -> tuple[bool, LendRateHistory | str]:
        try:
            data = await self.hyperlend_client.get_lend_rate_history(
                token=token,
                lookback_hours=lookback_hours,
                force_refresh=force_refresh,
            )
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def lend(
        self,
        *,
        underlying_token: str,
        qty: int,
        chain_id: int,
        native: bool = False,
    ) -> tuple[bool, Any]:
        strategy = self._strategy_address()
        qty = int(qty)
        if qty <= 0:
            return False, "qty must be positive"
        chain_id = int(chain_id)

        if native:
            tx = await self._encode_call(
                target=self.gateway_address,
                abi=WRAPPED_TOKEN_GATEWAY_ABI,
                fn_name="depositETH",
                args=[self._gateway_first_arg(underlying_token), strategy, 0],
                from_address=strategy,
                chain_id=chain_id,
                value=qty,
            )
        else:
            token_addr = self._checksum(underlying_token)
            approved = await self._ensure_allowance(
                token_address=token_addr,
                owner=strategy,
                spender=self.pool_address,
                amount=qty,
                chain_id=chain_id,
            )
            if not approved[0]:
                return approved
            tx = await self._encode_call(
                target=self.pool_address,
                abi=POOL_ABI,
                fn_name="supply",
                args=[token_addr, qty, strategy, 0],
                from_address=strategy,
                chain_id=chain_id,
            )
        return await self._send_tx(tx)

    async def unlend(
        self,
        *,
        underlying_token: str,
        qty: int,
        chain_id: int,
        native: bool = False,
    ) -> tuple[bool, Any]:
        strategy = self._strategy_address()
        qty = int(qty)
        if qty <= 0:
            return False, "qty must be positive"
        chain_id = int(chain_id)

        if native:
            tx = await self._encode_call(
                target=self.gateway_address,
                abi=WRAPPED_TOKEN_GATEWAY_ABI,
                fn_name="withdrawETH",
                args=[self._gateway_first_arg(underlying_token), qty, strategy],
                from_address=strategy,
                chain_id=chain_id,
            )
        else:
            token_addr = self._checksum(underlying_token)
            tx = await self._encode_call(
                target=self.pool_address,
                abi=POOL_ABI,
                fn_name="withdraw",
                args=[token_addr, qty, strategy],
                from_address=strategy,
                chain_id=chain_id,
            )
        return await self._send_tx(tx)

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    async def _send_tx(self, tx: dict[str, Any]) -> tuple[bool, Any]:
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)
        return True, txn_hash

    async def _ensure_allowance(
        self,
        *,
        token_address: str,
        owner: str,
        spender: str,
        amount: int,
        chain_id: int,
    ) -> tuple[bool, Any]:
        allowance = await get_token_allowance(token_address, chain_id, owner, spender)
        if allowance >= amount:
            return True, {}
        approve_tx = await build_approve_transaction(
            from_address=owner,
            chain_id=chain_id,
            token_address=token_address,
            spender_address=spender,
            amount=amount,
        )
        return await self._send_tx(approve_tx)

    async def _encode_call(
        self,
        *,
        target: str,
        abi: list[dict[str, Any]],
        fn_name: str,
        args: list[Any],
        from_address: str,
        chain_id: int,
        value: int = 0,
    ) -> dict[str, Any]:
        async with web3_from_chain_id(chain_id) as web3:
            contract = web3.eth.contract(address=target, abi=abi)
            try:
                data = (
                    await getattr(contract.functions, fn_name)(*args).build_transaction(
                        {"from": from_address}
                    )
                )["data"]
            except ValueError as exc:
                raise ValueError(f"Failed to encode {fn_name}: {exc}") from exc

            tx: dict[str, Any] = {
                "chainId": int(chain_id),
                "from": to_checksum_address(from_address),
                "to": to_checksum_address(target),
                "data": data,
                "value": int(value),
            }
            return tx

    def _strategy_address(self) -> str:
        addr = None
        if isinstance(self.strategy_wallet, dict):
            addr = self.strategy_wallet.get("address") or (
                (self.strategy_wallet.get("evm") or {}).get("address")
            )
        elif isinstance(self.strategy_wallet, str):
            addr = self.strategy_wallet
        if not addr:
            raise ValueError(
                "strategy_wallet address is required for HyperLend operations"
            )
        return to_checksum_address(addr)

    def _gateway_first_arg(self, underlying_token: str) -> str:
        if self.gateway_deposit_takes_pool:
            return self.pool_address
        return self._checksum(underlying_token) or self.wrapped_native

    def _checksum(self, address: str | None) -> str:
        if not address:
            raise ValueError("Missing required contract address in HyperLend config")
        return to_checksum_address(address)

from __future__ import annotations

import asyncio
from decimal import ROUND_DOWN, Decimal
from typing import Any

from eth_utils import to_checksum_address
from loguru import logger
from web3 import Web3

from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.constants import ZERO_ADDRESS
from wayfinder_paths.core.constants.erc20_abi import ERC20_ABI, ERC20_APPROVAL_ABI
from wayfinder_paths.core.services.base import EvmTxn, TokenTxn
from wayfinder_paths.core.utils.evm_helpers import resolve_chain_id


class LocalTokenTxnService(TokenTxn):
    """Default transaction builder used by adapters."""

    def __init__(
        self,
        config: dict[str, Any] | None,
        *,
        wallet_provider: EvmTxn,
    ) -> None:
        del config
        self.wallet_provider = wallet_provider
        self.logger = logger.bind(service="DefaultEvmTransactionService")
        self.token_client = TokenClient()

    async def build_send(
        self,
        *,
        token_id: str,
        amount: float,
        from_address: str,
        to_address: str,
        token_info: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any] | str]:
        """Build the transaction dict for sending tokens between wallets."""
        token_meta = token_info
        if token_meta is None:
            token_meta = await self.token_client.get_token_details(token_id)
            if not token_meta:
                return False, f"Token not found: {token_id}"

        chain_id = resolve_chain_id(token_meta, self.logger)
        if chain_id is None:
            return False, f"Token {token_id} is missing a chain id"

        token_address = (token_meta or {}).get("address") or ZERO_ADDRESS
        is_native = not token_address or token_address.lower() == ZERO_ADDRESS.lower()

        if is_native:
            amount_wei = self._to_base_units(
                amount, 18
            )  # Native tokens use 18 decimals
        else:
            decimals = int((token_meta or {}).get("decimals") or 18)
            amount_wei = self._to_base_units(amount, decimals)

        try:
            tx = await self.build_send_transaction(
                from_address=from_address,
                to_address=to_address,
                token_address=token_address,
                amount=amount_wei,
                chain_id=int(chain_id),
                is_native=is_native,
            )
        except Exception as exc:  # noqa: BLE001
            return False, f"Failed to build send transaction: {exc}"

        return True, tx

    def build_erc20_approve(
        self,
        *,
        chain_id: int,
        token_address: str,
        from_address: str,
        spender: str,
        amount: int,
    ) -> tuple[bool, dict[str, Any] | str]:
        """Build the transaction dictionary for an ERC20 approval."""
        try:
            token_checksum = to_checksum_address(token_address)
            from_checksum = to_checksum_address(from_address)
            spender_checksum = to_checksum_address(spender)
            amount_int = int(amount)
        except (TypeError, ValueError) as exc:
            return False, str(exc)

        approve_tx = self.build_erc20_approval_transaction(
            chain_id=chain_id,
            token_address=token_checksum,
            from_address=from_checksum,
            spender=spender_checksum,
            amount=amount_int,
        )
        return True, approve_tx

    async def read_erc20_allowance(
        self,
        chain: Any,
        token_address: str,
        from_address: str,
        spender_address: str,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        try:
            chain_id = self._chain_id(chain)
        except (TypeError, ValueError) as exc:
            return {"error": str(exc), "allowance": 0}

        last_error = None
        for attempt in range(max_retries):
            w3 = self.wallet_provider.get_web3(chain_id)
            try:
                contract = w3.eth.contract(
                    address=to_checksum_address(token_address), abi=ERC20_APPROVAL_ABI
                )
                allowance = await contract.functions.allowance(
                    to_checksum_address(from_address),
                    to_checksum_address(spender_address),
                ).call()
                return {"allowance": int(allowance)}
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                error_str = str(exc)
                if "429" in error_str or "Too Many Requests" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = 3.0 * (2**attempt)  # 3, 6, 12 seconds
                        self.logger.warning(
                            f"Rate limited reading allowance, retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                self.logger.error(f"Failed to read allowance: {exc}")
                return {"error": f"Allowance query failed: {exc}", "allowance": 0}
            finally:
                await self.wallet_provider._close_web3(w3)

        self.logger.error(
            f"Failed to read allowance after {max_retries} retries: {last_error}"
        )
        return {
            "error": f"Allowance query failed after retries: {last_error}",
            "allowance": 0,
        }

    def _chain_id(self, chain: Any) -> int:
        if isinstance(chain, dict):
            chain_id = chain.get("id")
        else:
            chain_id = getattr(chain, "id", None)
        if chain_id is None:
            raise ValueError("Chain ID is required")
        return int(chain_id)

    def _to_base_units(self, amount: float, decimals: int) -> int:
        """Convert human-readable amount to base units (wei for native, token units for ERC20)."""
        scale = Decimal(10) ** int(decimals)
        quantized = (Decimal(str(amount)) * scale).to_integral_value(
            rounding=ROUND_DOWN
        )
        return int(quantized)

    async def build_send_transaction(
        self,
        *,
        from_address: str,
        to_address: str,
        token_address: str | None,
        amount: int,
        chain_id: int,
        is_native: bool,
    ) -> dict[str, Any]:
        """Build the transaction dict for sending native or ERC20 tokens."""
        from_checksum = to_checksum_address(from_address)
        to_checksum = to_checksum_address(to_address)
        chain_id_int = int(chain_id)

        if is_native:
            return {
                "chainId": chain_id_int,
                "from": from_checksum,
                "to": to_checksum,
                "value": int(amount),
            }

        token_checksum = to_checksum_address(token_address or ZERO_ADDRESS)
        w3_sync = Web3()
        contract = w3_sync.eth.contract(address=token_checksum, abi=ERC20_ABI)
        data = contract.functions.transfer(
            to_checksum, int(amount)
        )._encode_transaction_data()

        return {
            "chainId": chain_id_int,
            "from": from_checksum,
            "to": token_checksum,
            "data": data,
            "value": 0,
        }

    def build_erc20_approval_transaction(
        self,
        *,
        chain_id: int,
        token_address: str,
        from_address: str,
        spender: str,
        amount: int,
    ) -> dict[str, Any]:
        """Build an ERC20 approval transaction dict."""
        token_checksum = to_checksum_address(token_address)
        spender_checksum = to_checksum_address(spender)
        from_checksum = to_checksum_address(from_address)
        amount_int = int(amount)

        # Use synchronous Web3 for encoding (encodeABI doesn't exist in web3.py v7)
        w3_sync = Web3()
        contract = w3_sync.eth.contract(address=token_checksum, abi=ERC20_APPROVAL_ABI)

        # In web3.py v7, use _encode_transaction_data to encode without network calls
        data = contract.functions.approve(
            spender_checksum, amount_int
        )._encode_transaction_data()

        return {
            "chainId": int(chain_id),
            "from": from_checksum,
            "to": token_checksum,
            "data": data,
            "value": 0,
        }

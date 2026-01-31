import asyncio
from typing import Any

from eth_account import Account
from eth_utils import to_checksum_address
from loguru import logger
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.module import Module

from wayfinder_paths.core.constants.base import DEFAULT_TRANSACTION_TIMEOUT
from wayfinder_paths.core.services.base import EvmTxn
from wayfinder_paths.core.utils.evm_helpers import (
    resolve_private_key_for_from_address,
    resolve_rpc_url,
)

SUGGESTED_GAS_PRICE_MULTIPLIER = 1.5
SUGGESTED_PRIORITY_FEE_MULTIPLIER = 1.5
MAX_BASE_FEE_GROWTH_MULTIPLIER = 2
GAS_LIMIT_BUFFER_MULTIPLIER = 1.5

# Base chain ID (Base mainnet)
BASE_CHAIN_ID = 8453

# Chains that don't support EIP-1559 (London) and need legacy gas pricing
PRE_LONDON_GAS_CHAIN_IDS: set[int] = {56, 42161}
POA_MIDDLEWARE_CHAIN_IDS: set = {56, 137, 43114}


def _looks_like_revert_error(error: Any) -> bool:
    msg = str(error).lower()
    return any(
        needle in msg
        for needle in (
            "execution reverted",
            "revert",
            "always failing transaction",
            "gas required exceeds",
            "out of gas",
            "insufficient funds",
            "transfer amount exceeds balance",
            "insufficient balance",
            "insufficient allowance",
        )
    )


class HyperModule(Module):
    def __init__(self, w3):
        super().__init__(w3)

    async def big_block_gas_price(self):
        big_block_gas_price = await self.w3.manager.coro_request(
            "eth_bigBlockGasPrice", []
        )
        return int(big_block_gas_price, 16)


class LocalEvmTxn(EvmTxn):
    """
    Local wallet provider using private keys stored in config.json or config.json.

    This provider implements the current default behavior:
    - Resolves private keys from config.json or config.json
    - Signs transactions using eth_account
    - Broadcasts transactions via RPC
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.logger = logger.bind(provider="LocalWalletProvider")

    def get_web3(self, chain_id: int) -> AsyncWeb3:
        rpc_url = self._resolve_rpc_url(chain_id)
        web3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        if chain_id in POA_MIDDLEWARE_CHAIN_IDS:
            web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        if chain_id == 999:
            web3.attach_modules({"hype": (HyperModule)})
        return web3

    def _validate_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
        tx = dict(transaction)

        assert "from" in tx, "Transaction missing 'from' address"
        assert "to" in tx, "Transaction missing 'to' address"
        assert "chainId" in tx, "Transaction missing 'chainId'"

        tx["from"] = to_checksum_address(tx["from"])
        tx["to"] = to_checksum_address(tx["to"])
        if "value" in tx:
            tx["value"] = self._normalize_int(tx["value"])

        tx.pop("gas", None)
        tx.pop("gasPrice", None)
        tx.pop("maxFeePerGas", None)
        tx.pop("maxPriorityFeePerGas", None)
        tx.pop("nonce", None)

        return tx

    async def _nonce_transaction(
        self, transaction: dict[str, Any], w3: AsyncWeb3
    ) -> dict[str, Any]:
        transaction["nonce"] = await w3.eth.get_transaction_count(
            transaction["from"], "pending"
        )
        return transaction

    async def _gas_limit_transaction(
        self, transaction: dict[str, Any], w3: AsyncWeb3
    ) -> dict[str, Any]:
        # Pop existing gas limit before estimating - if present, the node uses it as
        # a ceiling and fails with "out of gas" instead of returning actual estimate
        existing_gas = transaction.pop("gas", None)
        try:
            transaction.pop("gas", None)  # Remove any existing gas limit
            estimated = await w3.eth.estimate_gas(transaction)
            transaction["gas"] = int(estimated * GAS_LIMIT_BUFFER_MULTIPLIER)
            self.logger.debug(
                f"Estimated gas with buffer: {estimated} -> {transaction['gas']}"
            )
        except Exception as exc:  # noqa: BLE001
            if _looks_like_revert_error(exc):
                raise ValueError(
                    f"Gas estimation failed (tx likely to revert): {exc}"
                ) from exc
            self.logger.warning(f"Gas estimation failed. Reason: {exc}")
            # Restore existing gas limit if estimation failed, otherwise error
            if existing_gas is not None:
                transaction["gas"] = existing_gas
            else:
                raise ValueError(
                    f"Gas estimation failed and no gas limit set: {exc}"
                ) from exc

        return transaction

    async def _get_gas_price(self, w3: AsyncWeb3) -> int:
        return await w3.eth.gas_price

    async def _get_base_fee(self, w3: AsyncWeb3) -> int:
        latest_block = await w3.eth.get_block("latest")
        return latest_block.baseFeePerGas

    async def _get_priority_fee(self, w3: AsyncWeb3) -> int:
        lookback_blocks = 10
        percentile = 80
        fee_history = await w3.eth.fee_history(lookback_blocks, "latest", [percentile])
        historical_priority_fees = [i[0] for i in fee_history.reward]
        return sum(historical_priority_fees) // len(historical_priority_fees)

    async def _gas_price_transaction(
        self, transaction: dict[str, Any], chain_id: int, w3: AsyncWeb3
    ) -> dict[str, Any]:
        if chain_id in PRE_LONDON_GAS_CHAIN_IDS:
            gas_price = await self._get_gas_price(w3)

            transaction["gasPrice"] = int(gas_price * SUGGESTED_GAS_PRICE_MULTIPLIER)
        # elif chain_id == 999:
        #     big_block_gas_price = await w3.hype.big_block_gas_price()

        #     transaction["maxFeePerGas"] = int(
        #         big_block_gas_price * SUGGESTED_PRIORITY_FEE_MULTIPLIER
        #     )
        #     transaction["maxPriorityFeePerGas"] = 0
        else:
            base_fee = await self._get_base_fee(w3)
            priority_fee = await self._get_priority_fee(w3)

            transaction["maxFeePerGas"] = int(
                base_fee * MAX_BASE_FEE_GROWTH_MULTIPLIER
                + priority_fee * SUGGESTED_PRIORITY_FEE_MULTIPLIER
            )
            transaction["maxPriorityFeePerGas"] = int(
                priority_fee * SUGGESTED_PRIORITY_FEE_MULTIPLIER
            )

        return transaction

    async def broadcast_transaction(
        self,
        transaction: dict[str, Any],
        *,
        wait_for_receipt: bool = True,
        timeout: int = DEFAULT_TRANSACTION_TIMEOUT,
        confirmations: int | None = None,
    ) -> tuple[bool, Any]:
        try:
            chain_id = transaction["chainId"]
            from_address = transaction["from"]

            # Default confirmation behavior:
            # - Base: wait for 2 additional blocks after the receipt block
            # - Others: do not wait for additional confirmations
            effective_confirmations = confirmations
            if effective_confirmations is None:
                effective_confirmations = 2 if int(chain_id) == BASE_CHAIN_ID else 0
            effective_confirmations = max(0, int(effective_confirmations))

            web3 = self.get_web3(chain_id)
            try:
                transaction = self._validate_transaction(transaction)
                transaction = await self._nonce_transaction(transaction, web3)
                transaction = await self._gas_limit_transaction(transaction, web3)
                transaction = await self._gas_price_transaction(
                    transaction, chain_id, web3
                )

                signed_tx = self._sign_transaction(transaction, from_address)

                tx_hash = await web3.eth.send_raw_transaction(signed_tx)
                tx_hash_hex = tx_hash.hex()

                result: dict[str, Any] = {"tx_hash": tx_hash_hex}
                if wait_for_receipt:
                    receipt = await web3.eth.wait_for_transaction_receipt(
                        tx_hash, timeout=timeout
                    )
                    result["receipt"] = self._format_receipt(receipt)
                    # Add block_number at top level for convenience
                    result["block_number"] = result["receipt"].get("blockNumber")
                    result["confirmations"] = effective_confirmations
                    result["confirmed_block_number"] = result["block_number"]

                    receipt_status = result["receipt"].get("status")
                    if receipt_status is not None and int(receipt_status) != 1:
                        return (
                            False,
                            f"Transaction reverted (status={receipt_status}): {tx_hash_hex}",
                        )

                    # Wait for additional confirmations if requested
                    if effective_confirmations > 0:
                        tx_block = result["receipt"].get("blockNumber")
                        if tx_block:
                            await self._wait_for_confirmations(
                                web3, tx_block, effective_confirmations
                            )
                            result["confirmed_block_number"] = int(tx_block) + int(
                                effective_confirmations
                            )

                return (True, result)

            finally:
                await self._close_web3(web3)

        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Transaction broadcast failed: {exc}")
            return (False, f"Transaction broadcast failed: {exc}")

    async def transaction_succeeded(
        self, tx_hash: str, chain_id: int, timeout: int = 120
    ) -> bool:
        w3 = self.get_web3(chain_id)
        try:
            receipt = await w3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=timeout
            )
            status = getattr(receipt, "status", None)
            if status is None and isinstance(receipt, dict):
                status = receipt.get("status")
            return status == 1
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                f"Failed to confirm transaction {tx_hash} on chain {chain_id}: {exc}"
            )
            return False
        finally:
            await self._close_web3(w3)

    def _sign_transaction(
        self, transaction: dict[str, Any], from_address: str
    ) -> bytes:
        private_key = resolve_private_key_for_from_address(from_address, self.config)
        if not private_key:
            raise ValueError(f"No private key available for address {from_address}")
        signed = Account.sign_transaction(transaction, private_key)
        return signed.raw_transaction

    def _resolve_rpc_url(self, chain_id: int) -> str:
        return resolve_rpc_url(chain_id, self.config or {}, None)

    async def _close_web3(self, web3: AsyncWeb3) -> None:
        try:
            if hasattr(web3.provider, "disconnect"):
                await web3.provider.disconnect()
        except Exception as e:  # noqa: BLE001
            self.logger.debug(f"Error disconnecting provider: {e}")

    async def _wait_for_confirmations(
        self, w3: AsyncWeb3, tx_block: int, confirmations: int
    ) -> None:
        """Wait until the transaction has the specified number of confirmations."""
        target_block = tx_block + confirmations
        while True:
            current_block = await w3.eth.block_number
            if current_block >= target_block:
                break
            await asyncio.sleep(1)

    def _format_receipt(self, receipt: Any) -> dict[str, Any]:
        tx_hash = getattr(receipt, "transactionHash", None)
        if hasattr(tx_hash, "hex"):
            tx_hash = tx_hash.hex()

        return {
            "transactionHash": tx_hash,
            "status": (
                getattr(receipt, "status", None)
                if not isinstance(receipt, dict)
                else receipt.get("status")
            ),
            "blockNumber": (
                getattr(receipt, "blockNumber", None)
                if not isinstance(receipt, dict)
                else receipt.get("blockNumber")
            ),
            "gasUsed": (
                getattr(receipt, "gasUsed", None)
                if not isinstance(receipt, dict)
                else receipt.get("gasUsed")
            ),
            "logs": (
                [
                    dict(log_entry) if not isinstance(log_entry, dict) else log_entry
                    for log_entry in getattr(receipt, "logs", [])
                ]
                if hasattr(receipt, "logs")
                else receipt.get("logs")
                if isinstance(receipt, dict)
                else []
            ),
        }

    def _normalize_int(self, value: Any) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            if value.startswith("0x"):
                return int(value, 16)
            try:
                return int(value)
            except ValueError:
                return int(float(value))
        raise ValueError(f"Unable to convert value '{value}' to int")
